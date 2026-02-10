from __future__ import annotations

from PySide6.QtWidgets import QLabel, QHBoxLayout, QWidget


class TagChip(QWidget):
    def __init__(self, name: str) -> None:
        super().__init__()
        layout = QHBoxLayout()
        layout.addWidget(QLabel(name))
        self.setLayout(layout)
