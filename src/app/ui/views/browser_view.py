from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtWidgets import (
    QAbstractItemView,
    QListView,
    QListWidget,
    QListWidgetItem,
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
        config = load_config()
        self._thumb_service = ThumbnailService(config.thumbs_dir)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout()
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.list_widget.itemSelectionChanged.connect(self._on_selection_changed)

        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderHidden(True)
        self.tree_widget.itemSelectionChanged.connect(self._on_tree_selection_changed)

        self.stack = QStackedWidget()
        self.stack.addWidget(self.list_widget)
        self.stack.addWidget(self.tree_widget)

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

    def _on_tree_selection_changed(self) -> None:
        items = self.tree_widget.selectedItems()
        if not items:
            self.selected_file_id = None
            self.selection_changed.emit(0)
            return
        file_id = items[0].data(0, Qt.UserRole)
        if isinstance(file_id, int):
            self.selected_file_id = file_id
            self.file_selected.emit(file_id)
        self.selection_changed.emit(len(items))

    def selected_file_ids(self) -> list[int]:
        ids: list[int] = []
        if self._layout_mode == "folders":
            for item in self.tree_widget.selectedItems():
                file_id = item.data(0, Qt.UserRole)
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
        else:
            self.list_widget.setViewMode(QListView.ListMode)
            self.list_widget.setIconSize(QSize(16, 16))
            self.list_widget.setGridSize(QSize())
        self._render_list()

    def set_layout_mode(self, mode: str) -> None:
        self._layout_mode = mode
        if mode == "folders":
            self.stack.setCurrentWidget(self.tree_widget)
        else:
            self.stack.setCurrentWidget(self.list_widget)
        self._render()

    def _set_items(self, items: list[dict], root: Path | None) -> None:
        self._items = items
        self._root = root
        self.selected_file_id = None
        self.selection_changed.emit(0)
        self._render()

    def _render(self) -> None:
        if self._layout_mode == "folders":
            self._render_tree()
        else:
            self._render_list()

    def _render_list(self) -> None:
        self.list_widget.clear()
        if self._layout_mode != "all":
            return
        for item in self._items:
            list_item = QListWidgetItem(item["name"])
            list_item.setData(Qt.UserRole, item["id"])
            list_item.setToolTip(item["path"])
            if self._view_mode == "grid":
                icon = self._icon_for_item(item)
                if icon is not None:
                    list_item.setIcon(icon)
            self.list_widget.addItem(list_item)

    def _render_tree(self) -> None:
        self.tree_widget.clear()
        if not self._items:
            return

        root_item = None
        if self._root is not None:
            root_item = QTreeWidgetItem([self._root.name])
            self.tree_widget.addTopLevelItem(root_item)

        nodes: dict[str, QTreeWidgetItem] = {}

        def get_parent_node(parent: QTreeWidgetItem | None, parts: list[str]) -> QTreeWidgetItem:
            current = parent
            current_path = ""
            for part in parts:
                current_path = f"{current_path}/{part}" if current_path else part
                if current_path in nodes:
                    current = nodes[current_path]
                    continue
                node = QTreeWidgetItem([part])
                if current is None:
                    self.tree_widget.addTopLevelItem(node)
                else:
                    current.addChild(node)
                nodes[current_path] = node
                current = node
            return current

        for item in self._items:
            path = Path(item["path"])
            parts = list(path.parts)
            if self._root is not None:
                try:
                    parts = list(path.relative_to(self._root).parts)
                except ValueError:
                    parts = list(path.parts)
            if not parts:
                continue
            folder_parts = parts[:-1]
            file_name = parts[-1]
            parent_node = get_parent_node(root_item, folder_parts)
            file_node = QTreeWidgetItem([file_name])
            file_node.setData(0, Qt.UserRole, item["id"])
            file_node.setToolTip(0, item["path"])
            if parent_node is None:
                self.tree_widget.addTopLevelItem(file_node)
            else:
                parent_node.addChild(file_node)

        self.tree_widget.expandToDepth(0)

    def _icon_for_item(self, item: dict) -> QIcon | None:
        file_type = item.get("type")
        path = Path(item.get("path", ""))
        if not path.exists():
            return None
        icon_size = self.list_widget.iconSize()

        if file_type == "image":
            thumb_path = self._thumb_service.generate_image_thumbnail(
                path, (icon_size.width(), icon_size.height())
            )
        elif file_type == "video":
            thumb_path = self._thumb_service.generate_video_thumbnail(
                path, (icon_size.width(), icon_size.height())
            )
        else:
            return None

        if thumb_path is None or not thumb_path.exists():
            return None
        pixmap = QPixmap(str(thumb_path))
        if pixmap.isNull():
            return None
        scaled = pixmap.scaled(
            icon_size,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        return QIcon(scaled)
