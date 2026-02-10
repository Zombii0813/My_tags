from __future__ import annotations

from pathlib import Path
from typing import cast

from PySide6.QtCore import QObject, QThread, Signal, QUrl
from PySide6.QtWidgets import (
    QLabel,
    QFileDialog,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QInputDialog,
    QComboBox,
    QSplitter,
    QStatusBar,
    QToolBar,
)
from PySide6.QtGui import QDesktopServices

from app.config import AppConfig
from app.core.search import SearchQuery
from app.ui.controllers import AppController
from app.ui.views.browser_view import FileBrowserView
from app.ui.views.detail_panel import DetailPanel
from app.ui.views.tag_panel import TagPanel
from app.services.watch_service import WatchService


class MainWindow(QMainWindow):
    def __init__(self, config: AppConfig) -> None:
        super().__init__()
        self.config = config
        self.controller = AppController(config)
        self.active_workspace = config.default_workspace
        self._scan_thread: QThread | None = None
        self._scan_worker: ScanWorker | None = None
        self._watch_service = WatchService()
        self.setWindowTitle("My Tags")
        self.resize(1200, 800)
        self._build_ui()

    def _build_ui(self) -> None:
        toolbar = QToolBar("Main")
        self.addToolBar(toolbar)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search files...")
        self.search_input.returnPressed.connect(self._on_search)

        self.type_filter = QComboBox()
        self.type_filter.addItem("All", "")
        self.type_filter.addItem("Images", "image")
        self.type_filter.addItem("Videos", "video")
        self.type_filter.addItem("Docs", "doc")
        self.type_filter.addItem("Audio", "audio")
        self.type_filter.addItem("Other", "other")
        self.type_filter.currentIndexChanged.connect(self._on_filter_changed)

        self.view_mode = QComboBox()
        self.view_mode.addItem("List", "list")
        self.view_mode.addItem("Grid", "grid")
        self.view_mode.currentIndexChanged.connect(self._on_view_mode_changed)

        self.layout_mode = QComboBox()
        self.layout_mode.addItem("All", "all")
        self.layout_mode.addItem("Folders", "folders")
        self.layout_mode.currentIndexChanged.connect(self._on_layout_mode_changed)

        self.sort_filter = QComboBox()
        self.sort_filter.addItem("Name (Asc)", ("name", False))
        self.sort_filter.addItem("Name (Desc)", ("name", True))
        self.sort_filter.addItem("Modified", ("updated_at", True))
        self.sort_filter.addItem("Modified", ("modified_at", True))
        self.sort_filter.addItem("Updated", ("updated_at", True))
        self.sort_filter.addItem("Size", ("size", True))
        self.sort_filter.currentIndexChanged.connect(self._on_filter_changed)

        scan_button = QPushButton("Scan")
        scan_button.clicked.connect(self._on_scan)

        delete_button = QPushButton("Delete")
        delete_button.clicked.connect(self._on_delete_files)

        workspace_button = QPushButton("Workspace")
        workspace_button.clicked.connect(self._on_choose_workspace)

        move_button = QPushButton("Move")
        move_button.clicked.connect(self._on_move_files)

        copy_button = QPushButton("Copy")
        copy_button.clicked.connect(self._on_copy_files)

        open_folder_button = QPushButton("Open Folder")
        open_folder_button.clicked.connect(self._on_open_folder)

        open_file_button = QPushButton("Open File")
        open_file_button.clicked.connect(self._on_open_file)

        toolbar.addWidget(self.search_input)
        toolbar.addWidget(self.view_mode)
        toolbar.addWidget(self.layout_mode)
        toolbar.addWidget(self.type_filter)
        toolbar.addWidget(self.sort_filter)
        toolbar.addWidget(workspace_button)
        toolbar.addWidget(scan_button)
        toolbar.addWidget(delete_button)
        toolbar.addWidget(move_button)
        toolbar.addWidget(copy_button)
        toolbar.addWidget(open_folder_button)
        toolbar.addWidget(open_file_button)

        splitter = QSplitter()
        self.tag_panel = TagPanel()
        self.browser_view = FileBrowserView()
        self.detail_panel = DetailPanel()
        splitter.addWidget(self.tag_panel)
        splitter.addWidget(self.browser_view)
        splitter.addWidget(self.detail_panel)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 0)
        splitter.setCollapsible(2, False)

        self.browser_view.file_selected.connect(self._on_file_selected)
        self.browser_view.selection_changed.connect(self._on_selection_count)
        self.tag_panel.add_button.clicked.connect(self._on_add_tag)
        self.tag_panel.delete_button.clicked.connect(self._on_delete_tag)
        self.tag_panel.apply_button.clicked.connect(self._on_apply_tags)
        self.tag_panel.remove_button.clicked.connect(self._on_remove_tags)
        self.tag_panel.filter_button.clicked.connect(self._on_tag_filter_clicked)
        self.tag_panel.clear_filter_button.clicked.connect(self._on_clear_filter)

        self.search_input.textChanged.connect(self._on_search_text_changed)

        self.setCentralWidget(splitter)
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress)

        self.selection_label = QLabel("Selected files: 0")
        self.status_bar.addPermanentWidget(self.selection_label)

        self._load_initial_files()
        self._load_tags()

    def _load_initial_files(self) -> None:
        self._apply_filters()

    def _load_tags(self) -> None:
        tags = self.controller.list_tags()
        self.tag_panel.set_tags(tags)

    def _on_scan(self) -> None:
        if not self.active_workspace:
            QMessageBox.warning(self, "Workspace", "Set MYTAGS_WORKSPACE first.")
            return

        root = self.active_workspace
        if self._scan_thread is not None and self._scan_thread.isRunning():
            return

        self.statusBar().showMessage("Scanning...")
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
            types=types,
            sort_by=sort_by if sort_by else None,
            sort_desc=sort_desc,
        )
        results = self.controller.search(query)
        self.browser_view.set_search_results(results, root=self.active_workspace)
        self.detail_panel.set_file(None)
        self.selection_label.setText("Selected files: 0")

    def _on_search_text_changed(self, text: str) -> None:
        if not text:
            self._apply_filters()

    def _on_filter_changed(self) -> None:
        self._apply_filters()

    def _on_view_mode_changed(self) -> None:
        mode = self.view_mode.currentData()
        if mode:
            self.browser_view.set_view_mode(mode)

    def _on_layout_mode_changed(self) -> None:
        mode = self.layout_mode.currentData()
        if mode:
            self.browser_view.set_layout_mode(mode)

    def _apply_filters(self) -> None:
        text = self.search_input.text().strip()
        types = self._selected_types()
        sort_by, sort_desc = self._selected_sort()
        query = SearchQuery(
            text=text if text else None,
            types=types,
            sort_by=sort_by if sort_by else None,
            sort_desc=sort_desc,
        )
        results = self.controller.search(query)
        self.browser_view.set_search_results(results, root=self.active_workspace)
        self.detail_panel.set_file(None)
        self.selection_label.setText("Selected files: 0")

    def _selected_types(self) -> tuple[str, ...]:
        value = self.type_filter.currentData()
        if not value:
            return ()
        return (value,)

    def _selected_sort(self) -> tuple[str | None, bool]:
        value = self.sort_filter.currentData()
        if not value:
            return None, False
        return value

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
            types=types,
            sort_by=sort_by if sort_by else None,
            sort_desc=sort_desc,
        )
        results = self.controller.search(query)
        self.browser_view.set_search_results(results, root=self.active_workspace)
        self.detail_panel.set_file(None)

    def _on_clear_filter(self) -> None:
        self.search_input.clear()
        self.type_filter.setCurrentIndex(0)
        self.sort_filter.setCurrentIndex(0)
        self.view_mode.setCurrentIndex(0)
        self.layout_mode.setCurrentIndex(0)
        self._apply_filters()

    def _on_apply_tags(self) -> None:
        file_ids = self.browser_view.selected_file_ids()
        if not file_ids:
            return
        tag_ids = self.tag_panel.selected_tag_ids()
        for file_id in file_ids:
            self.controller.replace_tags(file_id, tag_ids)
        self._on_file_selected(file_ids[0])

    def _on_remove_tags(self) -> None:
        file_ids = self.browser_view.selected_file_ids()
        if not file_ids:
            return
        tag_ids = self.tag_panel.selected_tag_ids()
        for file_id in file_ids:
            self.controller.remove_tags(file_id, tag_ids)
        self._on_file_selected(file_ids[0])

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
        self.selection_label.setText("Selected files: 0")

    def _on_choose_workspace(self) -> None:
        selected = QFileDialog.getExistingDirectory(self, "Select Workspace")
        if not selected:
            return
        self.active_workspace = Path(selected)
        self.statusBar().showMessage(f"Workspace: {self.active_workspace}")
        self._restart_watch()

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
        self.selection_label.setText("Selected files: 0")
        if errors:
            QMessageBox.warning(self, "Move", "\n".join(errors))
        else:
            self.statusBar().showMessage(f"Moved {moved} files")

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
        self.selection_label.setText("Selected files: 0")
        if errors:
            QMessageBox.warning(self, "Copy", "\n".join(errors))
        else:
            self.statusBar().showMessage(f"Copied {copied} files")

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
        self.selection_label.setText(f"Selected files: {count}")

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
        self.statusBar().showMessage(f"Scanning... {count} files")

    def _on_scan_finished(self, count: int) -> None:
        self.progress.setRange(0, 1)
        self.progress.setValue(1)
        self.progress.setVisible(False)
        self.statusBar().showMessage(f"Scan complete: {count} files")
        self._load_initial_files()
        self.detail_panel.set_file(None)
        self._restart_watch()

    def closeEvent(self, event) -> None:
        self._watch_service.stop()
        super().closeEvent(event)

    def _on_scan_failed(self, message: str) -> None:
        self.progress.setVisible(False)
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
