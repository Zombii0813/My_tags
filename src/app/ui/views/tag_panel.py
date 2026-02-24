"""
Modern, sleek tag panel with improved UX.
"""
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
    QLabel,
    QFrame,
    QLineEdit,
)

from ...db.models import Tag
from ..widgets.tag_chip import TagChip


class TagPanel(QWidget):
    """
    Modern tag panel with search and management features.
    
    Features:
    - Search/filter tags
    - Modern tag list with color indicators
    - Action buttons with icons
    - Clean, organized layout
    """

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("tagPanel")
        self._tags: list[Tag] = []
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the modern tag panel UI."""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Search/filter
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Filter tags...")
        self.search_input.textChanged.connect(self._on_search_changed)
        layout.addWidget(self.search_input)

        # Tag list with modern styling
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.list_widget.setSpacing(4)
        self.list_widget.setStyleSheet("""
            QListWidget {
                background: transparent;
                border: none;
            }
            QListWidget::item {
                border-radius: 6px;
                padding: 8px 10px;
                margin: 2px 0;
                min-height: 20px;
            }
            QListWidget::item:selected {
                background: #eff6ff;
                color: #1e293b;
                border: 1px solid #bfdbfe;
            }
            QListWidget::item:hover {
                background: #f8fafc;
            }
        """)
        layout.addWidget(self.list_widget, 1)

        # Actions section
        actions_frame = QFrame()
        actions_frame.setObjectName("actionsFrame")
        actions_layout = QVBoxLayout(actions_frame)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(8)

        # Tag management buttons
        row1_layout = QHBoxLayout()
        row1_layout.setSpacing(6)
        
        self.add_button = QPushButton("➕ Add")
        self.add_button.setObjectName("primaryButton")
        self.add_button.setToolTip("Add new tag")
        
        self.delete_button = QPushButton("🗑️ Delete")
        self.delete_button.setObjectName("dangerButton")
        self.delete_button.setToolTip("Delete selected tags")
        
        row1_layout.addWidget(self.add_button)
        row1_layout.addWidget(self.delete_button)
        actions_layout.addLayout(row1_layout)

        # File-tag action buttons
        row2_layout = QHBoxLayout()
        row2_layout.setSpacing(6)
        
        self.apply_button = QPushButton("✓ Apply")
        self.apply_button.setToolTip("Apply selected tags to selected files")
        
        self.remove_button = QPushButton("✕ Remove")
        self.remove_button.setToolTip("Remove selected tags from selected files")
        
        row2_layout.addWidget(self.apply_button)
        row2_layout.addWidget(self.remove_button)
        actions_layout.addLayout(row2_layout)

        # Filter actions
        row3_layout = QHBoxLayout()
        row3_layout.setSpacing(6)
        
        self.filter_button = QPushButton("🔍 Filter")
        self.filter_button.setToolTip("Filter files by selected tags")
        
        self.clear_filter_button = QPushButton("✕ Clear")
        self.clear_filter_button.setToolTip("Clear all filters")
        
        row3_layout.addWidget(self.filter_button)
        row3_layout.addWidget(self.clear_filter_button)
        actions_layout.addLayout(row3_layout)

        # Match mode checkbox
        self.match_all_checkbox = QCheckBox("Match all selected tags")
        self.match_all_checkbox.setChecked(True)
        self.match_all_checkbox.setToolTip("Require all selected tags (AND) vs any (OR)")
        actions_layout.addWidget(self.match_all_checkbox)

        layout.addWidget(actions_frame)
        self.setLayout(layout)

    def _on_search_changed(self, text: str) -> None:
        """Filter tags based on search text."""
        text = text.lower()
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item:
                tag_name = item.data(Qt.UserRole + 1) or item.text()
                item.setHidden(text not in str(tag_name).lower())

    def set_tags(self, tags: list[Tag]) -> None:
        """Set the list of tags to display."""
        self._tags = tags
        self.list_widget.clear()

        for tag in tags:
            item = QListWidgetItem(f"🏷️ {tag.name}")
            item.setData(Qt.UserRole, tag.id)
            item.setData(Qt.UserRole + 1, tag.name)
            item.setToolTip(f"Tag: {tag.name}")
            self.list_widget.addItem(item)

    def selected_tag_ids(self) -> list[int]:
        """Get IDs of selected tags."""
        ids: list[int] = []
        for item in self.list_widget.selectedItems():
            tag_id = item.data(Qt.UserRole)
            if isinstance(tag_id, int):
                ids.append(tag_id)
        return ids

    def selected_tag_names(self) -> list[str]:
        """Get names of selected tags."""
        names = []
        for item in self.list_widget.selectedItems():
            name = item.data(Qt.UserRole + 1)
            if isinstance(name, str) and name:
                names.append(name)
                continue
            text = item.text()
            if text.startswith("🏷️ "):
                text = text[4:]
            names.append(text)
        return names

    def match_all_tags(self) -> bool:
        """Get the match mode."""
        return self.match_all_checkbox.isChecked()

    def clear_search(self) -> None:
        """Clear the search input."""
        self.search_input.clear()
