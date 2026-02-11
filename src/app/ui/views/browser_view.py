from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtWidgets import (
    QAbstractItemView,
    QListView,
    QListWidget,
    QListWidgetItem,
    QSplitter,
    QStackedWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtGui import QIcon, QPixmap

from app.core.search import SearchResult
from app.db.models import File
from app.services.thumbnail_service import ThumbnailService
from app.config import load_config


class FileBrowserView(QWidget):
    file_selected = Signal(int)
    selection_changed = Signal(int)

    def __init__(self) -> None:
        super().__init__()
        self.selected_file_id: int | None = None
        self._layout_mode = "all"
        self._view_mode = "list"
        self._items: list[dict] = []
        self._root: Path | None = None
        self._folder_map: dict[str, list[dict]] = {}
        self._current_folder: str | None = None
        config = load_config()
        self._thumb_service = ThumbnailService(config.thumbs_dir)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout()
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.list_widget.itemSelectionChanged.connect(self._on_selection_changed)

        self.folder_list_widget = QListWidget()
        self.folder_list_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.folder_list_widget.itemSelectionChanged.connect(
            self._on_folder_list_selection_changed
        )

        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderHidden(True)
        self.tree_widget.itemSelectionChanged.connect(self._on_tree_selection_changed)

        self.folder_splitter = QSplitter()
        self.folder_splitter.addWidget(self.tree_widget)
        self.folder_splitter.addWidget(self.folder_list_widget)
        self.folder_splitter.setStretchFactor(1, 1)

        self.stack = QStackedWidget()
        self.stack.addWidget(self.list_widget)
        self.stack.addWidget(self.folder_splitter)

        layout.addWidget(self.stack)
        self.setLayout(layout)

        self.set_view_mode(self._view_mode)
        self.set_layout_mode(self._layout_mode)

    def set_files(self, files: list[File], root: Path | None = None) -> None:
        items = []
        for file_row in files:
            file_id = getattr(file_row, "id", None)
            if file_id is None:
                continue
            items.append(
                {
                    "id": int(file_id),
                    "name": str(file_row.name),
                    "path": str(file_row.path),
                    "type": str(file_row.type),
                }
            )
        self._set_items(items, root)

    def set_search_results(
        self, results: list[SearchResult], root: Path | None = None
    ) -> None:
        items = []
        for result in results:
            items.append(
                {
                    "id": int(result.file_id),
                    "name": str(result.name),
                    "path": str(result.path),
                    "type": str(result.type),
                }
            )
        self._set_items(items, root)

    def _on_selection_changed(self) -> None:
        items = self.list_widget.selectedItems()
        if not items:
            self.selected_file_id = None
            self.selection_changed.emit(0)
            return
        file_id = items[0].data(Qt.UserRole)
        if isinstance(file_id, int):
            self.selected_file_id = file_id
            self.file_selected.emit(file_id)
        self.selection_changed.emit(len(items))

    def _on_folder_list_selection_changed(self) -> None:
        items = self.folder_list_widget.selectedItems()
        if not items:
            self.selected_file_id = None
            self.selection_changed.emit(0)
            return
        file_id = items[0].data(Qt.UserRole)
        if isinstance(file_id, int):
            self.selected_file_id = file_id
            self.file_selected.emit(file_id)
        self.selection_changed.emit(len(items))

    def _on_tree_selection_changed(self) -> None:
        items = self.tree_widget.selectedItems()
        if not items:
            self.selected_file_id = None
            self.selection_changed.emit(0)
            return
        folder_path = items[0].data(0, Qt.UserRole)
        if isinstance(folder_path, str):
            self._current_folder = folder_path
            self.selected_file_id = None
            self.selection_changed.emit(0)
            self._render_folder_list()

    def selected_file_ids(self) -> list[int]:
        ids: list[int] = []
        if self._layout_mode == "folders":
            for item in self.folder_list_widget.selectedItems():
                file_id = item.data(Qt.UserRole)
                if isinstance(file_id, int):
                    ids.append(file_id)
            return ids
        for item in self.list_widget.selectedItems():
            file_id = item.data(Qt.UserRole)
            if isinstance(file_id, int):
                ids.append(file_id)
        return ids

    def set_view_mode(self, mode: str) -> None:
        self._view_mode = mode
        if mode == "grid":
            self.list_widget.setViewMode(QListView.IconMode)
            self.list_widget.setResizeMode(QListView.Adjust)
            self.list_widget.setIconSize(QSize(96, 96))
            self.list_widget.setGridSize(QSize(120, 120))
            self.list_widget.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
            scroll = self.list_widget.verticalScrollBar()
            icon_size = self.list_widget.iconSize()
            scroll.setSingleStep(max(24, icon_size.height() // 2))
            scroll.setPageStep(max(120, icon_size.height() * 3))
            self.folder_list_widget.setViewMode(QListView.IconMode)
            self.folder_list_widget.setResizeMode(QListView.Adjust)
            self.folder_list_widget.setIconSize(QSize(96, 96))
            self.folder_list_widget.setGridSize(QSize(120, 120))
            self.folder_list_widget.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
            folder_scroll = self.folder_list_widget.verticalScrollBar()
            folder_icon_size = self.folder_list_widget.iconSize()
            folder_scroll.setSingleStep(max(24, folder_icon_size.height() // 2))
            folder_scroll.setPageStep(max(120, folder_icon_size.height() * 3))
        else:
            self.list_widget.setViewMode(QListView.ListMode)
            self.list_widget.setIconSize(QSize(16, 16))
            self.list_widget.setGridSize(QSize())
            self.list_widget.setVerticalScrollMode(QAbstractItemView.ScrollPerItem)
            scroll = self.list_widget.verticalScrollBar()
            scroll.setSingleStep(1)
            scroll.setPageStep(10)
            self.folder_list_widget.setViewMode(QListView.ListMode)
            self.folder_list_widget.setIconSize(QSize(16, 16))
            self.folder_list_widget.setGridSize(QSize())
            self.folder_list_widget.setVerticalScrollMode(QAbstractItemView.ScrollPerItem)
            folder_scroll = self.folder_list_widget.verticalScrollBar()
            folder_scroll.setSingleStep(1)
            folder_scroll.setPageStep(10)
        self._render()

    def set_layout_mode(self, mode: str) -> None:
        self._layout_mode = mode
        if mode == "folders":
            self.stack.setCurrentWidget(self.folder_splitter)
        else:
            self.stack.setCurrentWidget(self.list_widget)
        self._render()

    def _set_items(self, items: list[dict], root: Path | None) -> None:
        self._items = items
        self._root = root
        self._folder_map = self._build_folder_map(items, root)
        if root is not None:
            self._folder_map.setdefault(str(root), [])
            self._current_folder = str(root)
        else:
            self._current_folder = None
        self.selected_file_id = None
        self.selection_changed.emit(0)
        self._render()

    def _render(self) -> None:
        if self._layout_mode == "folders":
            self._render_tree()
        else:
            self._render_list()

    def _render_list(self) -> None:
        if self._layout_mode != "all":
            return
        self._render_list_widget(self.list_widget, self._items)

    def _render_tree(self) -> None:
        self.tree_widget.clear()
        if not self._folder_map:
            return

        root_item = None
        if self._root is not None:
            root_item = QTreeWidgetItem([self._root.name])
            root_item.setData(0, Qt.UserRole, str(self._root))
            root_item.setData(0, Qt.UserRole + 1, True)
            self.tree_widget.addTopLevelItem(root_item)

        nodes: dict[str, QTreeWidgetItem] = {}
        if root_item is not None and self._root is not None:
            nodes[str(self._root)] = root_item
        folder_role = Qt.UserRole + 1

        for folder_path in sorted(self._folder_map.keys()):
            folder = Path(folder_path)
            if self._root is not None:
                try:
                    parts = list(folder.relative_to(self._root).parts)
                    current = root_item
                    current_path = self._root
                except ValueError:
                    parts = list(folder.parts)
                    current = None
                    current_path = None
            else:
                parts = list(folder.parts)
                current = None
                current_path = None

            for part in parts:
                if current_path is None:
                    current_path = Path(part)
                else:
                    current_path = current_path / part
                key = str(current_path)
                node = nodes.get(key)
                if node is None:
                    node = QTreeWidgetItem([part])
                    node.setData(0, Qt.UserRole, key)
                    node.setData(0, folder_role, True)
                    if current is None:
                        self.tree_widget.addTopLevelItem(node)
                    else:
                        current.addChild(node)
                    nodes[key] = node
                current = node
        self._reorder_tree_items(folder_role)
        self.tree_widget.expandToDepth(0)
        self._select_initial_folder()

    def _reorder_tree_items(self, folder_role: int) -> None:
        def sort_key(node: QTreeWidgetItem) -> tuple[int, str]:
            is_folder = bool(node.data(0, folder_role))
            return (0 if is_folder else 1, node.text(0).lower())

        def reorder_node(node: QTreeWidgetItem) -> None:
            children: list[QTreeWidgetItem] = []
            while node.childCount() > 0:
                child = node.takeChild(0)
                if child is not None:
                    children.append(child)
            children.sort(key=sort_key)
            for child in children:
                node.addChild(child)
                reorder_node(child)

        top_level: list[QTreeWidgetItem] = []
        while self.tree_widget.topLevelItemCount() > 0:
            item = self.tree_widget.takeTopLevelItem(0)
            if item is not None:
                top_level.append(item)
        top_level.sort(key=sort_key)
        for item in top_level:
            self.tree_widget.addTopLevelItem(item)
            reorder_node(item)

    def _select_initial_folder(self) -> None:
        if self._current_folder is not None:
            item = self._find_folder_item(self._current_folder)
            if item is not None:
                self.tree_widget.setCurrentItem(item)
                return
        if self.tree_widget.topLevelItemCount() > 0:
            self.tree_widget.setCurrentItem(self.tree_widget.topLevelItem(0))

    def _find_folder_item(self, folder_path: str) -> QTreeWidgetItem | None:
        def search(node: QTreeWidgetItem) -> QTreeWidgetItem | None:
            if node.data(0, Qt.UserRole) == folder_path:
                return node
            for index in range(node.childCount()):
                found = search(node.child(index))
                if found is not None:
                    return found
            return None

        for index in range(self.tree_widget.topLevelItemCount()):
            found = search(self.tree_widget.topLevelItem(index))
            if found is not None:
                return found
        return None

    def _render_folder_list(self) -> None:
        if self._current_folder is None:
            self.folder_list_widget.clear()
            return
        items = self._folder_map.get(self._current_folder, [])
        self._render_list_widget(self.folder_list_widget, items)

    def _render_list_widget(self, widget: QListWidget, items: list[dict]) -> None:
        widget.clear()
        icon_size = widget.iconSize()
        preheat_items: list[tuple[Path, str]] = []
        for item in items:
            list_item = QListWidgetItem(item["name"])
            list_item.setData(Qt.UserRole, item["id"])
            list_item.setToolTip(item["path"])
            if self._view_mode == "grid":
                icon = self._icon_for_item(item)
                if icon is not None:
                    list_item.setIcon(icon)
            widget.addItem(list_item)
            if self._view_mode == "grid":
                path = Path(item.get("path", ""))
                file_type = item.get("type")
                if path.exists():
                    kind = str(file_type) if file_type in {"image", "video"} else "shell"
                    preheat_items.append((path, kind))
        if self._view_mode == "grid" and preheat_items:
            self._thumb_service.preheat_disk_thumbnails(
                preheat_items,
                (icon_size.width(), icon_size.height()),
            )

    def _build_folder_map(self, items: list[dict], root: Path | None) -> dict[str, list[dict]]:
        folder_map: dict[str, list[dict]] = {}
        for item in items:
            path = Path(item.get("path", ""))
            if not path.parent:
                continue
            folder_key = str(path.parent)
            folder_map.setdefault(folder_key, []).append(item)
        return folder_map

    def _icon_for_item(self, item: dict) -> QIcon | None:
        file_type = item.get("type")
        path = Path(item.get("path", ""))
        if not path.exists():
            return None
        if self._layout_mode == "folders":
            icon_size = self.folder_list_widget.iconSize()
        else:
            icon_size = self.list_widget.iconSize()

        if file_type == "image":
            pixmap = self._thumb_service.generate_image_thumbnail(
                path, (icon_size.width(), icon_size.height())
            )
        elif file_type == "video":
            pixmap = self._thumb_service.generate_video_thumbnail(
                path, (icon_size.width(), icon_size.height())
            )
        else:
            pixmap = self._thumb_service.generate_shell_thumbnail(
                path, (icon_size.width(), icon_size.height())
            )
            if pixmap is None or pixmap.isNull():
                return None

        if pixmap is None or pixmap.isNull():
            return None
        scaled = pixmap.scaled(
            icon_size,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        return QIcon(scaled)
