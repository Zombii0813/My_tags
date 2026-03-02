from __future__ import annotations

from pathlib import Path
from typing import cast

from PySide6.QtCore import QObject, QThread, Signal, QUrl, QSize, Qt, QTimer
from PySide6.QtWidgets import (
    QLabel,
    QFileDialog,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QInputDialog,
    QSplitter,
    QStatusBar,
    QToolBar,
    QToolButton,
    QButtonGroup,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QMenu,
)
from PySide6.QtGui import QDesktopServices, QAction

from ..config import AppConfig, workspace_db_path, save_last_workspace
from ..core.search import SearchQuery
from .controllers import AppController
from .views.browser_view import FileBrowserView
from .views.detail_panel import DetailPanel
from .views.tag_panel import TagPanel
from ..services.watch_service import WatchService
from .resources import get_icon, set_theme
from .resources.styles import get_stylesheet
from .widgets.acrylic_effects import ModernSidePanel, create_card_widget


class MainWindow(QMainWindow):
    def __init__(self, config: AppConfig) -> None:
        super().__init__()
        self.config = config
        self.controller = AppController(config)
        self.active_workspace = config.default_workspace
        self._scan_thread: QThread | None = None
        self._scan_worker: ScanWorker | None = None
        self._watch_service = WatchService()
        self._view_mode_value = "list"
        self._layout_mode_value = "all"
        self._type_filter_value = ""
        self._sort_filter_value: tuple[str | None, bool] = ("name", False)
        self._current_theme = "light"
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(300)
        self._search_timer.timeout.connect(self._apply_filters)
        
        self.setWindowTitle("My Tags")
        self.resize(1400, 900)
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the modern, sleek UI."""
        self._build_menu()
        
        # Create modern toolbar with search
        toolbar = self._build_toolbar()
        self.addToolBar(toolbar)

        # Create main content area
        content = self._build_content_area()
        self.setCentralWidget(content)

        # Create status bar
        self._build_status_bar()

        # Apply theme
        self._apply_theme_preset("light")

        # Load initial data
        if self.active_workspace is not None:
            self.config = AppConfig(
                data_dir=self.config.data_dir,
                db_path=workspace_db_path(self.config.data_dir, self.active_workspace),
                thumbs_dir=self.config.thumbs_dir,
                default_workspace=self.active_workspace,
            )
            from ..db.session import init_db

            init_db(self.config.db_path)
            self.controller = AppController(self.config)
        self._load_initial_files()
        self._load_tags()
        self._refresh_workspace_ui()

    def _build_toolbar(self) -> QToolBar:
        """Build a modern, organized toolbar."""
        toolbar = QToolBar("Main")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(20, 20))

        # Left side: Search with icon
        search_container = QWidget()
        search_container.setObjectName("searchContainer")
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(8)

        search_icon = QLabel("🔍")
        search_icon.setObjectName("searchIcon")
        search_layout.addWidget(search_icon)

        self.search_input = QLineEdit()
        self.search_input.setObjectName("searchInput")
        self.search_input.setPlaceholderText("Search files, tags...")
        self.search_input.setMinimumWidth(280)
        self.search_input.returnPressed.connect(self._on_search)
        self.search_input.textChanged.connect(self._on_search_text_changed)
        search_layout.addWidget(self.search_input)

        toolbar.addWidget(search_container)
        toolbar.addSeparator()

        # View mode buttons
        toolbar.addWidget(QLabel("View:"))
        self.view_group = QButtonGroup(self)
        self.view_group.setExclusive(True)
        
        self.list_btn = self._create_tool_button("list", "List view", True)
        self.grid_btn = self._create_tool_button("grid", "Grid view", True)
        self.view_group.addButton(self.list_btn)
        self.view_group.addButton(self.grid_btn)
        self.list_btn.clicked.connect(lambda: self._set_view_mode("list"))
        self.grid_btn.clicked.connect(lambda: self._set_view_mode("grid"))
        toolbar.addWidget(self.list_btn)
        toolbar.addWidget(self.grid_btn)
        
        toolbar.addSeparator()

        # Layout mode buttons
        toolbar.addWidget(QLabel("Layout:"))
        self.layout_group = QButtonGroup(self)
        self.layout_group.setExclusive(True)
        
        self.all_btn = self._create_tool_button("home", "All files", True)
        self.folder_btn = self._create_tool_button("folder", "Folders", True)
        self.layout_group.addButton(self.all_btn)
        self.layout_group.addButton(self.folder_btn)
        self.all_btn.clicked.connect(lambda: self._set_layout_mode("all"))
        self.folder_btn.clicked.connect(lambda: self._set_layout_mode("folders"))
        toolbar.addWidget(self.all_btn)
        toolbar.addWidget(self.folder_btn)
        
        toolbar.addSeparator()

        # Type filter buttons
        toolbar.addWidget(QLabel("Filter:"))
        self.type_group = QButtonGroup(self)
        self.type_group.setExclusive(True)
        
        self.type_all_btn = self._create_tool_button("clear", "All types", True)
        self.type_image_btn = self._create_tool_button("image", "Images", True)
        self.type_video_btn = self._create_tool_button("video", "Videos", True)
        self.type_doc_btn = self._create_tool_button("document", "Documents", True)
        self.type_audio_btn = self._create_tool_button("audio", "Audio", True)
        self.type_other_btn = self._create_tool_button("more", "Other", True)
        
        for btn in [self.type_all_btn, self.type_image_btn, self.type_video_btn,
                    self.type_doc_btn, self.type_audio_btn, self.type_other_btn]:
            self.type_group.addButton(btn)
            toolbar.addWidget(btn)
        
        self.type_all_btn.clicked.connect(lambda: self._set_type_filter(""))
        self.type_image_btn.clicked.connect(lambda: self._set_type_filter("image"))
        self.type_video_btn.clicked.connect(lambda: self._set_type_filter("video"))
        self.type_doc_btn.clicked.connect(lambda: self._set_type_filter("doc"))
        self.type_audio_btn.clicked.connect(lambda: self._set_type_filter("audio"))
        self.type_other_btn.clicked.connect(lambda: self._set_type_filter("other"))
        
        toolbar.addSeparator()

        # Sort buttons
        toolbar.addWidget(QLabel("Sort:"))
        self.sort_group = QButtonGroup(self)
        self.sort_group.setExclusive(True)
        
        self.sort_name_asc = self._create_tool_button("arrow_up", "Name ascending", True)
        self.sort_name_desc = self._create_tool_button("arrow_down", "Name descending", True)
        self.sort_modified = self._create_tool_button("clock", "Modified time", True)
        self.sort_size = self._create_tool_button("trash", "Size", True)
        
        for btn in [self.sort_name_asc, self.sort_name_desc, self.sort_modified, self.sort_size]:
            self.sort_group.addButton(btn)
            toolbar.addWidget(btn)
        
        self.sort_name_asc.clicked.connect(lambda: self._set_sort_filter("name", False))
        self.sort_name_desc.clicked.connect(lambda: self._set_sort_filter("name", True))
        self.sort_modified.clicked.connect(lambda: self._set_sort_filter("modified_at", True))
        self.sort_size.clicked.connect(lambda: self._set_sort_filter("size", True))

        # Store references
        self._icon_buttons = {
            "view_list": self.list_btn,
            "view_grid": self.grid_btn,
            "layout_all": self.all_btn,
            "layout_folders": self.folder_btn,
            "type_all": self.type_all_btn,
            "type_image": self.type_image_btn,
            "type_video": self.type_video_btn,
            "type_doc": self.type_doc_btn,
            "type_audio": self.type_audio_btn,
            "type_other": self.type_other_btn,
            "sort_name_asc": self.sort_name_asc,
            "sort_name_desc": self.sort_name_desc,
            "sort_modified": self.sort_modified,
            "sort_size": self.sort_size,
        }

        self._sync_icon_buttons()
        return toolbar

    def _create_tool_button(self, icon_name: str, tooltip: str, checkable: bool = False) -> QToolButton:
        """Create a modern tool button with custom icon."""
        button = QToolButton()
        button.setCheckable(checkable)
        button.setIcon(get_icon(icon_name))
        button.setToolTip(tooltip)
        button.setAutoRaise(True)
        button.setFixedSize(32, 32)
        return button

    def _build_content_area(self) -> QWidget:
        """Build the main content area with modern acrylic side panel."""
        # Create panels
        self.tag_panel = TagPanel()
        self.detail_panel = DetailPanel()
        self.browser_view = FileBrowserView()

        # Create modern side panel with acrylic effect
        side_panel = ModernSidePanel(theme="light")
        side_panel.setObjectName("sidePanel")
        side_layout = QVBoxLayout()
        side_layout.setContentsMargins(0, 0, 0, 0)
        side_layout.setSpacing(12)
        
        # Add section titles with modern styling
        tag_title = QLabel("🏷️ Tags")
        tag_title.setObjectName("sectionTitle")
        side_layout.addWidget(tag_title)
        side_layout.addWidget(self.tag_panel)
        
        detail_title = QLabel("📄 Details")
        detail_title.setObjectName("sectionTitle")
        side_layout.addWidget(detail_title)
        side_layout.addWidget(self.detail_panel, 1)
        
        side_panel.setLayout(side_layout)

        # side_panel.setMaximumWidth(320)
        side_panel.setMinimumWidth(360)

        # Create main splitter
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(side_panel)
        splitter.addWidget(self.browser_view)
        splitter.setStretchFactor(1, 1)
        splitter.setCollapsible(0, False)
        splitter.setHandleWidth(4)
        splitter.setSizes([300, 1100])

        # Connect signals
        self.browser_view.file_selected.connect(self._on_file_selected)
        self.browser_view.selection_changed.connect(self._on_selection_count)
        self.browser_view.delete_requested.connect(self._on_delete_files)
        self.browser_view.move_requested.connect(self._on_move_files)
        self.browser_view.copy_requested.connect(self._on_copy_files)
        self.browser_view.open_folder_requested.connect(self._on_open_folder)
        self.browser_view.open_file_requested.connect(self._on_open_file)
        self.tag_panel.add_button.clicked.connect(self._on_add_tag)
        self.tag_panel.delete_button.clicked.connect(self._on_delete_tag)
        self.tag_panel.apply_button.clicked.connect(self._on_apply_tags)
        self.tag_panel.remove_button.clicked.connect(self._on_remove_tags)
        self.tag_panel.filter_button.clicked.connect(self._on_tag_filter_clicked)
        self.tag_panel.clear_filter_button.clicked.connect(self._on_clear_filter)
        self.detail_panel.tag_remove_requested.connect(self._on_detail_tag_removed)

        return splitter

    def _build_status_bar(self) -> None:
        """Build the modern status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Progress bar (hidden by default)
        self.progress = QProgressBar()
        self.progress.setObjectName("statusProgressBar")
        self.progress.setVisible(False)
        self.progress.setFixedWidth(120)
        self.progress.setTextVisible(False)
        self.status_bar.addPermanentWidget(self.progress)

        # Memory cache stats label
        self.cache_stats_label = QLabel("")
        self.cache_stats_label.setObjectName("cacheStatsLabel")
        self.status_bar.addPermanentWidget(self.cache_stats_label)

        # Selection counter
        self.selection_label = QLabel("0 items selected")
        self.selection_label.setObjectName("selectionLabel")
        self.status_bar.addPermanentWidget(self.selection_label)

        # Workspace indicator
        self.workspace_label = QLabel("No workspace")
        self.workspace_label.setObjectName("workspaceLabel")
        self.status_bar.addWidget(self.workspace_label)
        
        # Setup cache stats timer
        self._cache_stats_timer = QTimer(self)
        self._cache_stats_timer.timeout.connect(self._update_cache_stats)
        self._cache_stats_timer.start(2000)  # Update every 2 seconds

    def _build_menu(self) -> None:
        """Build the menu bar."""
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("File")
        edit_menu = menu_bar.addMenu("Edit")
        view_menu = menu_bar.addMenu("View")
        tools_menu = menu_bar.addMenu("Tools")

        # Theme submenu - dynamically populated from available themes
        theme_menu = QMenu("Theme", self)
        view_menu.addMenu(theme_menu)
        self._theme_actions: list[QAction] = []
        self._build_theme_menu(theme_menu)

        # File menu actions
        file_menu.addAction(QAction("📁 Open Workspace", self, triggered=self._on_choose_workspace))
        file_menu.addAction(QAction("🧹 Clean Databases", self, triggered=self._on_clean_databases))
        file_menu.addSeparator()
        file_menu.addAction(QAction("🗑️ Clean Thumbnail Cache", self, triggered=self._on_clean_thumbnail_cache))
        file_menu.addSeparator()
        file_menu.addAction(QAction("❌ Exit", self, triggered=self.close))

        # Edit menu actions
        edit_menu.addAction(QAction("🔄 Refresh", self, triggered=self._on_scan))

        # About
        about_menu = menu_bar.addMenu("Help")
        about_menu.addAction(QAction("ℹ️ About", self))

    def _build_theme_menu(self, theme_menu: QMenu) -> None:
        """Build dynamic theme menu from available QSS files."""
        from .resources.styles import get_available_themes
        
        # Clear existing actions
        for action in self._theme_actions:
            theme_menu.removeAction(action)
        self._theme_actions.clear()
        
        # Get available themes
        themes = get_available_themes()
        
        # Theme name mapping for display
        theme_display_names = {
            "light": "☀️ Light",
            "dark": "🌙 Dark",
            "midnight": "🌌 Midnight",
        }
        
        # Create action for each theme
        for theme_name in themes:
            display_name = theme_display_names.get(theme_name, theme_name.capitalize())
            action = QAction(display_name, self)
            action.triggered.connect(lambda checked, t=theme_name: self._apply_theme_preset(t))
            theme_menu.addAction(action)
            self._theme_actions.append(action)

    def _apply_theme_preset(self, theme_id: str) -> None:
        """Apply the selected theme preset."""
        self._current_theme = theme_id
        set_theme("dark" if theme_id in ("dark", "midnight") else "light")
        self.setStyleSheet(get_stylesheet(theme_id))
        
        # Update side panel theme
        side_panel = self.findChild(ModernSidePanel)
        if side_panel:
            side_panel.set_theme("dark" if theme_id in ("dark", "midnight") else "light")
        
        # Update icons for new theme
        for btn in self._icon_buttons.values():
            btn.setIcon(get_icon(self._get_icon_name_for_button(btn)))

    def _get_icon_name_for_button(self, button: QToolButton) -> str:
        """Get icon name for a button."""
        icon_map = {
            self.list_btn: "list",
            self.grid_btn: "grid",
            self.all_btn: "home",
            self.folder_btn: "folder",
            self.type_all_btn: "clear",
            self.type_image_btn: "image",
            self.type_video_btn: "video",
            self.type_doc_btn: "document",
            self.type_audio_btn: "audio",
            self.type_other_btn: "more",
            self.sort_name_asc: "arrow_up",
            self.sort_name_desc: "arrow_down",
            self.sort_modified: "clock",
            self.sort_size: "trash",
        }
        return icon_map.get(button, "clear")

    def _load_initial_files(self) -> None:
        self._apply_filters()

    def _load_tags(self) -> None:
        tags = self.controller.list_tags()
        self.tag_panel.set_tags(tags)

    def _refresh_workspace_ui(self) -> None:
        if self.active_workspace is not None:
            self.workspace_label.setText(f"📁 {self.active_workspace.name}")
            self.statusBar().showMessage(f"Workspace: {self.active_workspace}")
        else:
            self.workspace_label.setText("No workspace")

    def _on_scan(self) -> None:
        if not self.active_workspace:
            QMessageBox.warning(self, "Workspace", "Set MYTAGS_WORKSPACE first.")
            return

        if self.config.db_path != workspace_db_path(
            self.config.data_dir, self.active_workspace
        ):
            self.config = AppConfig(
                data_dir=self.config.data_dir,
                db_path=workspace_db_path(self.config.data_dir, self.active_workspace),
                thumbs_dir=self.config.thumbs_dir,
                default_workspace=self.active_workspace,
            )
            from ..db.session import init_db

            init_db(self.config.db_path)
            self.controller = AppController(self.config)

        root = self.active_workspace
        if self._scan_thread is not None:
            try:
                if self._scan_thread.isRunning():
                    return
            except RuntimeError:
                self._scan_thread = None
                self._scan_worker = None

        self.statusBar().showMessage("🔍 Scanning...")
        self.progress.setRange(0, 0)
        self.progress.setVisible(True)

        scan_thread = QThread(self)
        scan_worker = ScanWorker(self.controller, root)
        scan_worker.moveToThread(scan_thread)

        scan_thread.started.connect(scan_worker.run)
        scan_worker.progress.connect(self._on_scan_progress)
        scan_worker.finished.connect(self._on_scan_finished)
        scan_worker.failed.connect(self._on_scan_failed)

        scan_worker.finished.connect(scan_thread.quit)
        scan_worker.failed.connect(scan_thread.quit)
        scan_worker.finished.connect(scan_worker.deleteLater)
        scan_worker.failed.connect(scan_worker.deleteLater)
        scan_thread.finished.connect(scan_thread.deleteLater)

        self._scan_thread = scan_thread
        self._scan_worker = scan_worker
        scan_thread.start()

    def _on_search(self) -> None:
        text = self.search_input.text().strip()
        types = self._selected_types()
        sort_by, sort_desc = self._selected_sort()
        query = SearchQuery(
            text=text if text else None,
            root=str(self.active_workspace) if self.active_workspace else None,
            types=types,
            sort_by=sort_by if sort_by else None,
            sort_desc=sort_desc,
        )
        results = self.controller.search(query)
        self.browser_view.set_search_results(results, root=self.active_workspace)
        self.detail_panel.set_file(None)
        self.selection_label.setText("0 items selected")

    def _on_search_text_changed(self, text: str) -> None:
        self._search_timer.stop()
        if not text:
            self._apply_filters()
            return
        self._search_timer.start()

    def _on_filter_changed(self) -> None:
        self._apply_filters()

    def _apply_filters(self) -> None:
        text = self.search_input.text().strip()
        types = self._selected_types()
        sort_by, sort_desc = self._selected_sort()
        query = SearchQuery(
            text=text if text else None,
            root=str(self.active_workspace) if self.active_workspace else None,
            types=types,
            sort_by=sort_by if sort_by else None,
            sort_desc=sort_desc,
        )
        results = self.controller.search(query)
        self.browser_view.set_search_results(results, root=self.active_workspace)
        self.detail_panel.set_file(None)
        self.selection_label.setText("0 items selected")

    def _selected_types(self) -> tuple[str, ...]:
        value = self._type_filter_value
        if not value:
            return ()
        return (value,)

    def _selected_sort(self) -> tuple[str | None, bool]:
        return self._sort_filter_value

    def _on_tag_filter_clicked(self) -> None:
        tag_names = self.tag_panel.selected_tag_names()
        if not tag_names:
            return
        types = self._selected_types()
        sort_by, sort_desc = self._selected_sort()
        match_all = self.tag_panel.match_all_tags()
        query = SearchQuery(
            tags=tuple(tag_names),
            match_all_tags=match_all,
            root=str(self.active_workspace) if self.active_workspace else None,
            types=types,
            sort_by=sort_by if sort_by else None,
            sort_desc=sort_desc,
        )
        results = self.controller.search(query)
        self.browser_view.set_search_results(results, root=self.active_workspace)
        self.detail_panel.set_file(None)

    def _on_clear_filter(self) -> None:
        self.search_input.clear()
        self._type_filter_value = ""
        self._sort_filter_value = ("name", False)
        self._view_mode_value = "list"
        self._layout_mode_value = "all"
        self._set_view_mode(self._view_mode_value)
        self._set_layout_mode(self._layout_mode_value)
        self._sync_icon_buttons()
        self._apply_filters()

    def _on_apply_tags(self) -> None:
        file_ids = self.browser_view.selected_file_ids()
        if not file_ids:
            return
        tag_ids = self.tag_panel.selected_tag_ids()
        for file_id in file_ids:
            self.controller.attach_tags(file_id, tag_ids)
        self._on_file_selected(file_ids[0])

    def _on_remove_tags(self) -> None:
        file_ids = self.browser_view.selected_file_ids()
        if not file_ids:
            return
        tag_ids = self.tag_panel.selected_tag_ids()
        for file_id in file_ids:
            self.controller.remove_tags(file_id, tag_ids)
        self._on_file_selected(file_ids[0])

    def _on_detail_tag_removed(self, file_id: int, tag_name: str) -> None:
        """Handle tag removal from detail panel."""
        # Get tag id from name
        tags = self.controller.list_tags()
        tag_id = None
        for tag in tags:
            if tag.name == tag_name:
                tag_id = tag.id
                break
        if tag_id is not None:
            self.controller.remove_tags(file_id, [tag_id])
            # Refresh the detail panel
            self._on_file_selected(file_id)

    def _on_delete_files(self) -> None:
        file_ids = self.browser_view.selected_file_ids()
        if not file_ids:
            return
        confirm = QMessageBox.question(
            self,
            "Delete",
            f"Delete {len(file_ids)} files from index?",
        )
        if confirm != QMessageBox.Yes:
            return
        self.controller.delete_files(file_ids)
        self._load_initial_files()
        self.detail_panel.set_file(None)
        self.selection_label.setText("0 items selected")

    def _on_choose_workspace(self) -> None:
        selected = QFileDialog.getExistingDirectory(self, "Select Workspace")
        if not selected:
            return
        self.active_workspace = Path(selected)
        self.config = AppConfig(
            data_dir=self.config.data_dir,
            db_path=workspace_db_path(self.config.data_dir, self.active_workspace),
            thumbs_dir=self.config.thumbs_dir,
            default_workspace=self.active_workspace,
        )
        from ..db.session import init_db

        init_db(self.config.db_path)
        self.controller = AppController(self.config)
        self._load_tags()
        save_last_workspace(self.config.data_dir, self.active_workspace)
        self._refresh_workspace_ui()
        self._restart_watch()
        self._on_scan()

    def _on_clean_databases(self) -> None:
        if not self.config.data_dir:
            return
        confirm = QMessageBox.question(
            self,
            "Clean Databases",
            "Delete all workspace database files except the current one?",
        )
        if confirm != QMessageBox.Yes:
            return
        workspace_dir = self.config.data_dir / "workspaces"
        if not workspace_dir.exists():
            self.statusBar().showMessage("No workspace databases found")
            return
        current_db = None
        if self.active_workspace is not None:
            current_db = workspace_db_path(self.config.data_dir, self.active_workspace)
        deleted = 0
        for db_file in workspace_dir.glob("*.db"):
            if current_db is not None and db_file.resolve() == current_db.resolve():
                continue
            try:
                db_file.unlink()
                deleted += 1
            except Exception:
                continue
        self.statusBar().showMessage(f"✓ Removed {deleted} workspace databases")

    def _on_move_files(self) -> None:
        file_ids = self.browser_view.selected_file_ids()
        if not file_ids:
            return
        destination = QFileDialog.getExistingDirectory(self, "Move To")
        if not destination:
            return
        moved, errors = self.controller.move_files(
            file_ids, Path(destination), self.active_workspace
        )
        self._load_initial_files()
        self.detail_panel.set_file(None)
        self.selection_label.setText("0 items selected")
        if errors:
            QMessageBox.warning(self, "Move", "\n".join(errors))
        else:
            self.statusBar().showMessage(f"✓ Moved {moved} files")

    def _on_copy_files(self) -> None:
        file_ids = self.browser_view.selected_file_ids()
        if not file_ids:
            return
        destination = QFileDialog.getExistingDirectory(self, "Copy To")
        if not destination:
            return
        copied, errors = self.controller.copy_files(
            file_ids, Path(destination), self.active_workspace
        )
        self._load_initial_files()
        self.detail_panel.set_file(None)
        self.selection_label.setText("0 items selected")
        if errors:
            QMessageBox.warning(self, "Copy", "\n".join(errors))
        else:
            self.statusBar().showMessage(f"✓ Copied {copied} files")

    def _on_open_folder(self) -> None:
        file_id = self.browser_view.selected_file_id
        if file_id is None:
            return
        file_row = self.controller.get_file(file_id)
        if file_row is None:
            return
        file_path = Path(cast(str, file_row.path))
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(file_path.parent)))

    def _on_open_file(self) -> None:
        file_id = self.browser_view.selected_file_id
        if file_id is None:
            return
        file_row = self.controller.get_file(file_id)
        if file_row is None:
            return
        file_path = Path(cast(str, file_row.path))
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(file_path)))

    def _on_selection_count(self, count: int) -> None:
        self.selection_label.setText(f"{count} item{'s' if count != 1 else ''} selected")

    def _on_file_selected(self, file_id: int) -> None:
        file_row = self.controller.get_file(file_id)
        tags = self.controller.tags_for_file(file_id)
        tag_names = [str(tag.name) for tag in tags]
        selected_ids = self.browser_view.selected_file_ids()
        self.detail_panel.set_file(file_row, tag_names, len(selected_ids))

    def _on_add_tag(self) -> None:
        name, ok = QInputDialog.getText(self, "Add Tag", "Tag name")
        if not ok or not name.strip():
            return
        self.controller.create_tag(name.strip())
        self._load_tags()

    def _on_delete_tag(self) -> None:
        ids = self.tag_panel.selected_tag_ids()
        for tag_id in ids:
            self.controller.delete_tag(tag_id)
        if ids:
            self._load_tags()

    def _on_scan_progress(self, count: int) -> None:
        self.statusBar().showMessage(f"🔍 Scanning... {count} files")

    def _on_scan_finished(self, count: int) -> None:
        self.progress.setRange(0, 1)
        self.progress.setValue(1)
        self.progress.setVisible(False)
        self.statusBar().showMessage(f"✓ Scan complete: {count} files")
        self._load_initial_files()
        self.detail_panel.set_file(None)
        self._restart_watch()

    def closeEvent(self, event) -> None:
        self._watch_service.stop()
        super().closeEvent(event)

    def _on_scan_failed(self, message: str) -> None:
        self.progress.setVisible(False)
        print(f"Scan failed: {message}")
        QMessageBox.critical(self, "Scan failed", message)

    def _restart_watch(self) -> None:
        if not self.active_workspace:
            return
        self._watch_service.stop()
        self._watch_service.start(
            self.active_workspace,
            on_change=self.controller.handle_file_changed,
            on_delete=self.controller.handle_file_deleted,
        )

    def _set_view_mode(self, mode: str) -> None:
        self._view_mode_value = mode
        self.browser_view.set_view_mode(mode)
        self._sync_icon_buttons()
        self._apply_filters()

    def _set_layout_mode(self, mode: str) -> None:
        self._layout_mode_value = mode
        self.browser_view.set_layout_mode(mode)
        self._sync_icon_buttons()
        self._apply_filters()

    def _set_type_filter(self, value: str) -> None:
        self._type_filter_value = value
        self._sync_icon_buttons()
        self._apply_filters()

    def _set_sort_filter(self, sort_by: str | None, sort_desc: bool) -> None:
        self._sort_filter_value = (sort_by, sort_desc)
        self._sync_icon_buttons()
        self._apply_filters()

    def _sync_icon_buttons(self) -> None:
        if not hasattr(self, "_icon_buttons"):
            return
        self._icon_buttons["view_list"].setChecked(self._view_mode_value == "list")
        self._icon_buttons["view_grid"].setChecked(self._view_mode_value == "grid")
        self._icon_buttons["layout_all"].setChecked(self._layout_mode_value == "all")
        self._icon_buttons["layout_folders"].setChecked(
            self._layout_mode_value == "folders"
        )
        self._icon_buttons["type_all"].setChecked(self._type_filter_value == "")
        self._icon_buttons["type_image"].setChecked(self._type_filter_value == "image")
        self._icon_buttons["type_video"].setChecked(self._type_filter_value == "video")
        self._icon_buttons["type_doc"].setChecked(self._type_filter_value == "doc")
        self._icon_buttons["type_audio"].setChecked(self._type_filter_value == "audio")
        self._icon_buttons["type_other"].setChecked(self._type_filter_value == "other")
        sort_by, sort_desc = self._sort_filter_value
        self._icon_buttons["sort_name_asc"].setChecked(
            sort_by == "name" and not sort_desc
        )
        self._icon_buttons["sort_name_desc"].setChecked(
            sort_by == "name" and sort_desc
        )
        self._icon_buttons["sort_modified"].setChecked(sort_by == "modified_at")
        self._icon_buttons["sort_size"].setChecked(sort_by == "size")

    def _update_cache_stats(self) -> None:
        """Update thumbnail cache statistics"""
        thumb_service = self.browser_view._thumb_service
        stats = thumb_service.cache_stats
        self.cache_stats_label.setText(
            f"📷 Cache: {stats['cache_items']} items, {stats['cache_memory_mb']} MB"
        )
    
    def _on_clean_thumbnail_cache(self) -> None:
        """Clean thumbnail cache"""
        from PySide6.QtWidgets import QMessageBox
        
        thumb_service = self.browser_view._thumb_service
        deleted = thumb_service.cleanup_old_cache_files(max_age_days=7)
        
        QMessageBox.information(
            self,
            "Cache Cleanup",
            f"Deleted {deleted} old thumbnail cache files."
        )


class ScanWorker(QObject):
    progress = Signal(int)
    finished = Signal(int)
    failed = Signal(str)

    def __init__(self, controller: AppController, root) -> None:
        super().__init__()
        self.controller = controller
        self.root = root

    def run(self) -> None:
        try:
            count = self.controller.scan_workspace(
                self.root, on_progress=self.progress.emit
            )
        except Exception as exc:
            self.failed.emit(str(exc))
            return
        self.finished.emit(count)
