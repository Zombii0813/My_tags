from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel, QSizePolicy, QVBoxLayout, QWidget

from ...config import load_config
from ...db.models import File
from ...services.thumbnail_service import ThumbnailService


class DetailPanel(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("detailPanel")
        config = load_config()
        self._thumb_service = ThumbnailService(config.thumbs_dir)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout()
        self.title_label = QLabel("Details")
        self.path_label = QLabel("")
        self.meta_label = QLabel("")
        self.tags_label = QLabel("")
        self.selection_label = QLabel("")
        self.preview_label = QLabel("")
        self.setMinimumWidth(280)
        self.setMinimumHeight(220)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.title_label.setWordWrap(True)
        self.path_label.setWordWrap(True)
        self.meta_label.setWordWrap(True)
        self.tags_label.setWordWrap(True)
        self.selection_label.setWordWrap(True)
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setFixedSize(260, 260)
        layout.addWidget(self.title_label)
        layout.addWidget(self.path_label)
        layout.addWidget(self.meta_label)
        layout.addWidget(self.tags_label)
        layout.addWidget(self.selection_label)
        layout.addWidget(self.preview_label)
        self.setLayout(layout)

    def set_file(self, file_row: File | None, tags=None, selection_count: int = 1) -> None:
        if file_row is None:
            self.title_label.setText("Details")
            self.path_label.setText("")
            self.meta_label.setText("")
            self.tags_label.setText("")
            self.selection_label.setText("")
            self.preview_label.setPixmap(QPixmap())
            self.preview_label.setText("")
            return
        self.title_label.setText(str(file_row.name))
        self.path_label.setText(str(file_row.path))
        self.meta_label.setText(f"{file_row.type} | {file_row.size} bytes")
        if tags:
            self.tags_label.setText("Tags: " + ", ".join([str(tag) for tag in tags]))
        else:
            self.tags_label.setText("Tags: (none)")
        self.selection_label.setText(f"Selected files: {selection_count}")
        self._set_preview(file_row)

    def _set_preview(self, file_row: File) -> None:
        file_type = str(file_row.type)
        file_path = Path(str(file_row.path))
        if not file_path.exists():
            self.preview_label.setPixmap(QPixmap())
            self.preview_label.setText("No preview")
            return
        pixmap = None
        size = (self.preview_label.width(), self.preview_label.height())
        if file_type == "image":
            pixmap = self._thumb_service.generate_image_thumbnail(file_path, size)
        elif file_type == "video":
            pixmap = self._thumb_service.generate_video_thumbnail(file_path, size)
        else:
            pixmap = self._thumb_service.generate_shell_thumbnail(file_path, size)
        if pixmap is None or pixmap.isNull():
            self.preview_label.setPixmap(QPixmap())
            self.preview_label.setText("No preview")
            return
        scaled = pixmap.scaled(
            self.preview_label.width(),
            self.preview_label.height(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self.preview_label.setText("")
        self.preview_label.setPixmap(scaled)
