"""
Modern file browser view with grid/list modes and improved visuals.
"""
from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import Qt, Signal, QSize, QTimer, QEasingCurve, QPropertyAnimation, QPoint, Property
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
    QMenu,
    QScrollBar,
)
from PySide6.QtGui import QIcon, QPixmap, QFont, QWheelEvent

from ...core.search import SearchResult
from ...db.models import File
from ...services.thumbnail_service import ThumbnailService
from ...config import load_config

logger = logging.getLogger(__name__)


class SmoothScrollBar(QScrollBar):
    """
    Custom scrollbar with inertial/momentum scrolling.
    Provides smooth deceleration after wheel events.
    """
    
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._velocity = 0.0
        self._friction = 0.95  # Friction coefficient (0-1), higher = less friction
        self._min_velocity = 1.0  # Minimum velocity to continue animation
        self._max_velocity = 150.0  # Maximum scroll velocity
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_scroll)
        self._scroll_anim: QPropertyAnimation | None = None
        
    def _setup_animation(self, target_value: int, duration: int = 300) -> None:
        """Setup smooth scroll animation to target value."""
        if self._scroll_anim is not None:
            self._scroll_anim.stop()
            self._scroll_anim.deleteLater()
        
        self._scroll_anim = QPropertyAnimation(self, b"value")
        self._scroll_anim.setDuration(duration)
        self._scroll_anim.setStartValue(self.value())
        self._scroll_anim.setEndValue(target_value)
        self._scroll_anim.setEasingCurve(QEasingCurve.OutCubic)
        self._scroll_anim.start()
        
    def _update_scroll(self) -> None:
        """Update scroll position based on current velocity."""
        if abs(self._velocity) < self._min_velocity:
            self._timer.stop()
            self._velocity = 0.0
            return
            
        new_value = int(self.value() - self._velocity)
        new_value = max(self.minimum(), min(self.maximum(), new_value))
        self.setValue(new_value)
        
        # Apply friction
        self._velocity *= self._friction
        
        # Stop if at bounds
        if new_value <= self.minimum() or new_value >= self.maximum():
            self._timer.stop()
            self._velocity = 0.0
            
    def wheelEvent(self, event: QWheelEvent) -> None:
        """
        Handle wheel event with inertia.
        Accumulates scroll delta into velocity for smooth deceleration.
        """
        delta = event.angleDelta().y()
        
        # Log scroll behavior for debugging
        logger.debug(f"Wheel event: delta={delta}, current_velocity={self._velocity:.2f}")
        
        # Normalize delta and add to velocity
        scroll_step = delta / 8.0  # Convert to standard units
        
        # Cap velocity to prevent excessive speed
        self._velocity = max(-self._max_velocity, min(self._max_velocity,
                                                       self._velocity + scroll_step * 0.5))
        
        logger.debug(f"Updated velocity: {self._velocity:.2f}")
        
        # Start inertia timer if not running
        if not self._timer.isActive():
            self._timer.start(16)  # ~60 FPS for smooth animation
            
        event.accept()


class FileBrowserView(QWidget):
    """
    Modern file browser with list and grid view modes.
    
    Features:
    - Smooth list/grid view switching
    - Folder tree navigation
    - Custom file item rendering
    - Context menu actions
    """
    
    file_selected = Signal(int)
    selection_changed = Signal(int)
    delete_requested = Signal()
    move_requested = Signal()
    copy_requested = Signal()
    open_folder_requested = Signal()
    open_file_requested = Signal()

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
        """Build the modern browser UI."""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # List widget for all files view
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.list_widget.itemSelectionChanged.connect(self._on_selection_changed)
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self._on_context_menu)
        self._style_list_widget(self.list_widget)
        # Replace scrollbar with smooth scrolling version
        self.list_widget.setVerticalScrollBar(SmoothScrollBar(self.list_widget))

        # Folder view widgets
        self.folder_list_widget = QListWidget()
        self.folder_list_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.folder_list_widget.itemSelectionChanged.connect(
            self._on_folder_list_selection_changed
        )
        self.folder_list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.folder_list_widget.customContextMenuRequested.connect(self._on_context_menu)
        self._style_list_widget(self.folder_list_widget)
        # Replace scrollbar with smooth scrolling version
        self.folder_list_widget.setVerticalScrollBar(SmoothScrollBar(self.folder_list_widget))

        # Tree widget for folder navigation
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderHidden(True)
        self.tree_widget.itemSelectionChanged.connect(self._on_tree_selection_changed)
        self.tree_widget.setStyleSheet("""
            QTreeWidget {
                background: transparent;
                border: none;
            }
            QTreeWidget::item {
                border-radius: 6px;
                padding: 6px 8px;
                margin: 1px 0;
                min-height: 20px;
            }
            QTreeWidget::item:selected {
                background: #eff6ff;
                color: #1e293b;
                border: 1px solid #bfdbfe;
            }
            QTreeWidget::item:hover {
                background: #f8fafc;
            }
        """)

        # Folder splitter with tree and file list
        self.folder_splitter = QSplitter(Qt.Horizontal)
        self.folder_splitter.addWidget(self.tree_widget)
        self.folder_splitter.addWidget(self.folder_list_widget)
        self.folder_splitter.setStretchFactor(1, 1)
        self.folder_splitter.setSizes([200, 400])
        self.folder_splitter.setHandleWidth(4)

        # Stacked widget to switch between views
        self.stack = QStackedWidget()
        self.stack.addWidget(self.list_widget)
        self.stack.addWidget(self.folder_splitter)

        layout.addWidget(self.stack)
        self.setLayout(layout)

        self.set_view_mode(self._view_mode)
        self.set_layout_mode(self._layout_mode)

    def _style_list_widget(self, widget: QListWidget) -> None:
        """Apply modern styling to list widget."""
        widget.setStyleSheet("""
            QListWidget {
                background: transparent;
                border: none;
                outline: none;
            }
            QListWidget::item {
                border-radius: 8px;
                padding: 8px 12px;
                margin: 2px 4px;
                min-height: 24px;
            }
            QListWidget::item:selected {
                background: #eff6ff;
                color: #1e293b;
                border: 1px solid #bfdbfe;
            }
            QListWidget::item:hover {
                background: #f8fafc;
            }
            QListWidget::item:selected:hover {
                background: #dbeafe;
            }
        """)

    def set_files(self, files: list[File], root: Path | None = None) -> None:
        """Set the list of files to display."""
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
        """Set search results to display."""
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
        """Handle selection change in list view."""
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
        """Handle selection change in folder list view."""
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
        """Handle folder tree selection change."""
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
        """Get IDs of selected files."""
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
        """Set the view mode (list or grid)."""
        self._view_mode = mode
        if mode == "grid":
            # Grid view settings
            for widget in [self.list_widget, self.folder_list_widget]:
                widget.setViewMode(QListView.IconMode)
                widget.setResizeMode(QListView.Adjust)
                widget.setIconSize(QSize(100, 100))
                widget.setGridSize(QSize(140, 140))
                widget.setSpacing(8)
                widget.setWordWrap(True)
                widget.setTextElideMode(Qt.ElideMiddle)
                widget.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
                scroll = widget.verticalScrollBar()
                icon_size = widget.iconSize()
                scroll.setSingleStep(max(36, icon_size.height() // 2))
                scroll.setPageStep(max(240, icon_size.height() * 3))
        else:
            # List view settings
            for widget in [self.list_widget, self.folder_list_widget]:
                widget.setViewMode(QListView.ListMode)
                widget.setIconSize(QSize(20, 20))
                widget.setGridSize(QSize())
                widget.setSpacing(2)
                widget.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
                scroll = widget.verticalScrollBar()
                scroll.setSingleStep(20)
                scroll.setPageStep(120)
        self._render()

    def set_layout_mode(self, mode: str) -> None:
        """Set the layout mode (all files or folder view)."""
        self._layout_mode = mode
        if mode == "folders":
            self.stack.setCurrentWidget(self.folder_splitter)
        else:
            self.stack.setCurrentWidget(self.list_widget)
        self._render()

    def _set_items(self, items: list[dict], root: Path | None) -> None:
        """Set items and rebuild folder map."""
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
        """Render the current view."""
        if self._layout_mode == "folders":
            self._render_tree()
        else:
            self._render_list()

    def _render_list(self) -> None:
        """Render the list view."""
        if self._layout_mode != "all":
            return
        self._render_list_widget(self.list_widget, self._items)

    def _render_tree(self) -> None:
        """Render the folder tree."""
        self.tree_widget.clear()
        if not self._folder_map:
            return

        root_item = None
        if self._root is not None:
            root_item = QTreeWidgetItem([f"📁 {self._root.name}"])
            root_item.setData(0, Qt.UserRole, str(self._root))
            root_item.setData(0, Qt.UserRole + 1, True)
            root_item.setFont(0, self._bold_font())
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
                    node = QTreeWidgetItem([f"📁 {part}"])
                    node.setData(0, Qt.UserRole, key)
                    node.setData(0, folder_role, True)
                    if current is None:
                        self.tree_widget.addTopLevelItem(node)
                    else:
                        current.addChild(node)
                    nodes[key] = node
                current = node
        
        self._reorder_tree_items(folder_role)
        self.tree_widget.expandToDepth(1)
        self._select_initial_folder()

    def _bold_font(self):
        """Get a bold font."""
        font = QFont()
        font.setBold(True)
        return font

    def _reorder_tree_items(self, folder_role: int) -> None:
        """Reorder tree items alphabetically."""
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
        """Select the initial folder in tree."""
        if self._current_folder is not None:
            item = self._find_folder_item(self._current_folder)
            if item is not None:
                self.tree_widget.setCurrentItem(item)
                return
        if self.tree_widget.topLevelItemCount() > 0:
            self.tree_widget.setCurrentItem(self.tree_widget.topLevelItem(0))

    def _find_folder_item(self, folder_path: str) -> QTreeWidgetItem | None:
        """Find a folder item by path."""
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
        """Render files in current folder."""
        if self._current_folder is None:
            self.folder_list_widget.clear()
            return
        items = self._folder_map.get(self._current_folder, [])
        self._render_list_widget(self.folder_list_widget, items)

    def _render_list_widget(self, widget: QListWidget, items: list[dict]) -> None:
        """Render items in a list widget."""
        widget.clear()
        icon_size = widget.iconSize()
        preheat_items: list[tuple[Path, str]] = []
        
        for item in items:
            display_name = item["name"]
            if self._view_mode == "grid" and len(display_name) > 20:
                display_name = display_name[:17] + "..."
                
            list_item = QListWidgetItem(display_name)
            list_item.setData(Qt.UserRole, item["id"])
            list_item.setToolTip(item["path"])
            
            if self._view_mode == "grid":
                icon = self._icon_for_item(item)
                if icon is not None:
                    list_item.setIcon(icon)
                # Center text in grid mode
                list_item.setTextAlignment(Qt.AlignHCenter | Qt.AlignBottom)
            else:
                # Add file type icon for list mode
                file_type = item.get("type", "")
                icon = self._get_type_icon(file_type)
                if icon:
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

    def _get_type_icon(self, file_type: str) -> QIcon | None:
        """Get icon for file type."""
        # In list mode, use emoji or simple icons
        icon_map = {
            "image": "🖼️",
            "video": "🎬",
            "audio": "🎵",
            "doc": "📄",
        }
        # Return None for now - can implement proper icon loading later
        return None

    def _on_context_menu(self, position) -> None:
        """Show context menu."""
        widget = self.sender()
        if not isinstance(widget, QListWidget):
            return
        item = widget.itemAt(position)
        if item is None:
            return
        if not item.isSelected():
            widget.clearSelection()
            item.setSelected(True)
        widget.setCurrentItem(item)
        
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 6px;
            }
            QMenu::item {
                padding: 8px 24px 8px 12px;
                border-radius: 4px;
                font-size: 13px;
            }
            QMenu::item:selected {
                background: #eff6ff;
                color: #2563eb;
            }
            QMenu::separator {
                height: 1px;
                background: #e2e8f0;
                margin: 6px 12px;
            }
        """)
        
        open_file = menu.addAction("📂 Open File")
        open_folder = menu.addAction("📁 Open Folder")
        menu.addSeparator()
        move_action = menu.addAction("📦 Move")
        copy_action = menu.addAction("📋 Copy")
        menu.addSeparator()
        delete_action = menu.addAction("🗑️ Delete")
        
        action = menu.exec(widget.mapToGlobal(position))
        if action == open_file:
            self.open_file_requested.emit()
        elif action == open_folder:
            self.open_folder_requested.emit()
        elif action == move_action:
            self.move_requested.emit()
        elif action == copy_action:
            self.copy_requested.emit()
        elif action == delete_action:
            self.delete_requested.emit()

    def _build_folder_map(self, items: list[dict], root: Path | None) -> dict[str, list[dict]]:
        """Build a map of folder paths to items."""
        folder_map: dict[str, list[dict]] = {}
        for item in items:
            path = Path(item.get("path", ""))
            if not path.parent:
                continue
            folder_key = str(path.parent)
            folder_map.setdefault(folder_key, []).append(item)
        return folder_map

    def _icon_for_item(self, item: dict) -> QIcon | None:
        """Get icon for a file item."""
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
