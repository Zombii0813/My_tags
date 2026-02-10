from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class FileCard(QWidget):
    def __init__(self, title: str) -> None:
        super().__init__()
        layout = QVBoxLayout()
        layout.addWidget(QLabel(title))
        self.setLayout(layout)
