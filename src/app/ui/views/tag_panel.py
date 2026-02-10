from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.db.models import Tag


class TagPanel(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout()

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)

        row_one = QHBoxLayout()
        self.add_button = QPushButton("Add")
        self.delete_button = QPushButton("Delete")
        row_one.addWidget(self.add_button)
        row_one.addWidget(self.delete_button)

        row_two = QHBoxLayout()
        self.apply_button = QPushButton("Apply")
        self.remove_button = QPushButton("Remove")
        self.filter_button = QPushButton("Filter")
        self.clear_filter_button = QPushButton("Clear")
        self.match_all_checkbox = QCheckBox("Match All")
        self.match_all_checkbox.setChecked(True)
        row_two.addWidget(self.apply_button)
        row_two.addWidget(self.remove_button)
        row_two.addWidget(self.filter_button)
        row_two.addWidget(self.clear_filter_button)
        row_two.addWidget(self.match_all_checkbox)

        layout.addLayout(row_one)
        layout.addLayout(row_two)
        layout.addWidget(self.list_widget)
        self.setLayout(layout)

    def set_tags(self, tags: list[Tag]) -> None:
        self.list_widget.clear()
        for tag in tags:
            item = QListWidgetItem(tag.name)
            item.setData(Qt.UserRole, tag.id)
            self.list_widget.addItem(item)

    def selected_tag_ids(self) -> list[int]:
        ids: list[int] = []
        for item in self.list_widget.selectedItems():
            tag_id = item.data(Qt.UserRole)
            if isinstance(tag_id, int):
                ids.append(tag_id)
        return ids

    def selected_tag_names(self) -> list[str]:
        return [item.text() for item in self.list_widget.selectedItems()]

    def match_all_tags(self) -> bool:
        return self.match_all_checkbox.isChecked()
