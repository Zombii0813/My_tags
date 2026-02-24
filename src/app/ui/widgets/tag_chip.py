"""
Modern, colorful tag chip widget with animations and sleek design.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, Property, QPoint, QRect
from PySide6.QtGui import QColor, QPainter, QPainterPath, QFont, QFontMetrics
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QLayout, QLayoutItem
)


# Simple FlowLayout implementation for tag wrapping
class FlowLayout(QLayout):
    """Flow layout that wraps widgets to next line when overflowing."""

    def __init__(self, parent=None, margin=0, spacing=-1):
        super().__init__(parent)
        if parent is not None:
            self.setContentsMargins(margin, margin, margin, margin)
        self.setSpacing(spacing)
        self._items: list[QLayoutItem] = []

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item: QLayoutItem):
        self._items.append(item)

    def count(self) -> int:
        return len(self._items)

    def itemAt(self, index: int) -> QLayoutItem | None:
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index: int) -> QLayoutItem | None:
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def expandingDirections(self) -> Qt.Orientations:
        return Qt.Orientation(0)

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, width: int) -> int:
        return self._doLayout(QRect(0, 0, width, 0), True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._doLayout(rect, False)

    def sizeHint(self) -> QSize:
        return self.minimumSize()

    def minimumSize(self) -> QSize:
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        margin = self.contentsMargins()
        size += QSize(margin.left() + margin.right(), margin.top() + margin.bottom())
        return size

    def _doLayout(self, rect, test_only: bool) -> int:
        x = rect.x()
        y = rect.y()
        line_height = 0
        
        for item in self._items:
            widget = item.widget()
            space_x = self.spacing()
            space_y = self.spacing()
            
            next_x = x + item.sizeHint().width() + space_x
            if next_x - space_x > rect.right() and line_height > 0:
                x = rect.x()
                y = y + line_height + space_y
                next_x = x + item.sizeHint().width() + space_x
                line_height = 0

            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))

            x = next_x
            line_height = max(line_height, item.sizeHint().height())

        return y + line_height - rect.y()


class TagChip(QWidget):
    """
    A modern, colorful tag chip with hover effects and smooth animations.
    
    Features:
    - Rounded pill-shaped design
    - Gradient backgrounds based on tag color
    - Hover animation with slight scale effect
    - Optional close button
    - Customizable colors
    """

    # Predefined color schemes for tags
    COLOR_SCHEMES = {
        "blue":   ("#3b82f6", "#dbeafe", "#2563eb"),
        "green":  ("#10b981", "#d1fae5", "#059669"),
        "red":    ("#ef4444", "#fee2e2", "#dc2626"),
        "yellow": ("#f59e0b", "#fef3c7", "#d97706"),
        "purple": ("#8b5cf6", "#ede9fe", "#7c3aed"),
        "pink":   ("#ec4899", "#fce7f3", "#db2777"),
        "cyan":   ("#06b6d4", "#cffafe", "#0891b2"),
        "orange": ("#f97316", "#ffedd5", "#ea580c"),
        "indigo": ("#6366f1", "#e0e7ff", "#4f46e5"),
        "teal":   ("#14b8a6", "#ccfbf1", "#0d9488"),
        "gray":   ("#6b7280", "#f3f4f6", "#4b5563"),
    }

    def __init__(
        self,
        name: str,
        color: str = "blue",
        removable: bool = False,
        parent=None,
    ):
        super().__init__(parent)
        self._name = name
        self._color_key = color if color in self.COLOR_SCHEMES else "blue"
        self._removable = removable
        self._hovered = False
        self._scale = 1.0
        self._selected = False

        self._setup_ui()
        self._setup_animations()
        self.setFixedHeight(28)
        self.setCursor(Qt.PointingHandCursor)

    def _setup_ui(self):
        """Setup the widget layout."""
        self.setAttribute(Qt.WA_StyledBackground, True)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 4, 12, 4)
        layout.setSpacing(6)

        self.label = QLabel(self._name)
        self.label.setStyleSheet("""
            QLabel {
                background: transparent;
                border: none;
                font-size: 12px;
                font-weight: 500;
            }
        """)
        layout.addWidget(self.label)

        if self._removable:
            self.close_btn = QLabel("×")
            self.close_btn.setStyleSheet("""
                QLabel {
                    background: transparent;
                    border: none;
                    font-size: 16px;
                    font-weight: 300;
                }
            """)
            layout.addWidget(self.close_btn)

    def _setup_animations(self):
        """Setup hover animations."""
        self._scale_animation = QPropertyAnimation(self, b"scale_factor")
        self._scale_animation.setDuration(150)
        self._scale_animation.setEasingCurve(QEasingCurve.OutCubic)

    def get_scale_factor(self):
        return self._scale

    def set_scale_factor(self, value):
        self._scale = value
        self.update()

    scale_factor = Property(float, get_scale_factor, set_scale_factor)

    def enterEvent(self, event):
        """Handle mouse enter."""
        self._hovered = True
        self._scale_animation.stop()
        self._scale_animation.setStartValue(self._scale)
        self._scale_animation.setEndValue(1.05)
        self._scale_animation.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Handle mouse leave."""
        self._hovered = False
        self._scale_animation.stop()
        self._scale_animation.setStartValue(self._scale)
        self._scale_animation.setEndValue(1.0)
        self._scale_animation.start()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        """Handle mouse press."""
        if self._removable and event.button() == Qt.LeftButton:
            # Check if close button was clicked
            if hasattr(self, 'close_btn'):
                close_rect = self.close_btn.geometry()
                if close_rect.contains(event.pos()):
                    self.deleteLater()
                    return
        super().mousePressEvent(event)

    def paintEvent(self, event):
        """Custom paint with rounded background."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Get color scheme
        primary, bg, border = self.COLOR_SCHEMES[self._color_key]

        # Adjust colors based on state
        if self._selected:
            bg_color = QColor(primary)
            text_color = QColor("#ffffff")
        elif self._hovered:
            bg_color = QColor(bg).darker(105)
            text_color = QColor(primary).darker(120)
        else:
            bg_color = QColor(bg)
            text_color = QColor(primary)

        # Apply scale transformation
        painter.translate(self.width() / 2, self.height() / 2)
        painter.scale(self._scale, self._scale)
        painter.translate(-self.width() / 2, -self.height() / 2)

        # Draw rounded rectangle background
        path = QPainterPath()
        rect = self.rect().adjusted(1, 1, -1, -1)
        path.addRoundedRect(rect, 14, 14)
        
        painter.fillPath(path, bg_color)

        # Draw border for selected state
        if self._selected:
            painter.setPen(QColor(border))
            painter.drawPath(path)

        # Update label color
        self.label.setStyleSheet(f"""
            QLabel {{
                background: transparent;
                border: none;
                font-size: 12px;
                font-weight: 500;
                color: {text_color.name()};
            }}
        """)

        if hasattr(self, 'close_btn'):
            self.close_btn.setStyleSheet(f"""
                QLabel {{
                    background: transparent;
                    border: none;
                    font-size: 16px;
                    font-weight: 300;
                    color: {text_color.name()};
                }}
            """)

        painter.end()

    def set_selected(self, selected: bool):
        """Set the selected state."""
        self._selected = selected
        self.update()

    def is_selected(self) -> bool:
        """Get the selected state."""
        return self._selected

    def get_name(self) -> str:
        """Get the tag name."""
        return self._name

    def set_color(self, color: str):
        """Set the tag color scheme."""
        if color in self.COLOR_SCHEMES:
            self._color_key = color
            self.update()

    def sizeHint(self) -> QSize:
        """Calculate optimal size based on text."""
        font = QFont()
        font.setPointSize(11)
        font.setWeight(QFont.Medium)
        metrics = QFontMetrics(font)
        text_width = metrics.horizontalAdvance(self._name)
        width = text_width + 24  # padding
        if self._removable:
            width += 20  # close button space
        return QSize(width, 28)


class TagChipContainer(QWidget):
    """
    A container widget for organizing multiple tag chips.
    Provides wrapping and spacing between chips.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._chips: list[TagChip] = []
        self._setup_ui()

    def _setup_ui(self):
        """Setup the container layout."""
        # Use flow layout for wrapping
        self.layout = FlowLayout(self)
        self.layout.setSpacing(8)
        self.layout.setContentsMargins(0, 0, 0, 0)

    def add_chip(self, name: str, color: str = "blue", removable: bool = False) -> TagChip:
        """Add a new tag chip."""
        chip = TagChip(name, color, removable, self)
        self._chips.append(chip)
        self.layout.addWidget(chip)
        return chip

    def remove_chip(self, chip: TagChip):
        """Remove a tag chip."""
        if chip in self._chips:
            self._chips.remove(chip)
            chip.deleteLater()

    def clear(self):
        """Remove all chips."""
        for chip in self._chips:
            chip.deleteLater()
        self._chips.clear()

    def get_selected_chips(self) -> list[TagChip]:
        """Get all selected chips."""
        return [chip for chip in self._chips if chip.is_selected()]
