"""
Modern SVG-style icons for the application.
Using QPainter to draw modern, minimalist icons.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, QSize, QRectF, QPoint, QPointF
from PySide6.QtGui import QPainter, QColor, QPixmap, QIcon, QPen, QBrush, QFont
from PySide6.QtWidgets import QStyle, QApplication


class IconBuilder:
    """Build modern, minimalist icons with consistent style."""

    ICON_SIZE = 20
    STROKE_WIDTH = 1.5
    CORNER_RADIUS = 2

    def __init__(self, color: str = "#5a677a", size: int = ICON_SIZE):
        self.color = QColor(color)
        self.size = size
        self.half_size = size / 2

    def build(self, draw_func) -> QIcon:
        """Build an icon using the provided draw function."""
        pixmap = QPixmap(self.size, self.size)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(self.color, self.STROKE_WIDTH, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        
        draw_func(painter, self.size)
        
        painter.end()
        return QIcon(pixmap)

    def search(self) -> QIcon:
        """Search/magnifying glass icon."""
        def draw(p, size):
            center = int(size / 2 - 1)
            radius = int(size / 3)
            p.drawEllipse(int(center - radius + 2), int(center - radius), int(radius * 1.6), int(radius * 1.6))
            p.drawLine(int(center + radius - 2), int(center + radius - 4), int(size - 4), int(size - 4))
        return self.build(draw)

    def list_view(self) -> QIcon:
        """List view icon with horizontal lines."""
        def draw(p, size):
            margin = 4
            spacing = 4
            for i in range(4):
                y = margin + i * spacing
                p.drawLine(margin, y, size - margin, y)
        return self.build(draw)

    def grid_view(self) -> QIcon:
        """Grid view icon with squares."""
        def draw(p, size):
            margin = 3
            cell = (size - margin * 2 - 1) // 2
            for row in range(2):
                for col in range(2):
                    x = margin + col * (cell + 1)
                    y = margin + row * (cell + 1)
                    p.drawRect(x, y, cell, cell)
        return self.build(draw)

    def folder(self) -> QIcon:
        """Folder icon."""
        def draw(p, size):
            margin = 3
            folder_width = size - margin * 2
            folder_height = size - margin * 2 - 3
            tab_width = folder_width // 3
            
            # Tab
            p.drawLine(margin, margin + 3, margin + tab_width, margin + 3)
            p.drawLine(margin + tab_width, margin + 3, margin + tab_width + 3, margin)
            
            # Body
            p.drawRoundedRect(margin, margin + 3, folder_width, folder_height, 2, 2)
        return self.build(draw)

    def home(self) -> QIcon:
        """Home icon."""
        def draw(p, size):
            margin = 3
            center = size // 2
            roof_height = size // 3
            
            # Roof
            p.drawLine(margin + 2, margin + roof_height, center, margin)
            p.drawLine(center, margin, size - margin - 2, margin + roof_height)
            
            # Walls
            p.drawLine(margin + 4, margin + roof_height, margin + 4, size - margin - 1)
            p.drawLine(size - margin - 4, margin + roof_height, size - margin - 4, size - margin - 1)
            
            # Floor
            p.drawLine(margin + 4, size - margin - 1, size - margin - 4, size - margin - 1)
            
            # Door
            door_width = 6
            p.drawLine(center - door_width//2, size - margin - 1, center - door_width//2, size - margin - 6)
            p.drawLine(center + door_width//2, size - margin - 1, center + door_width//2, size - margin - 6)
            p.drawLine(center - door_width//2, size - margin - 6, center + door_width//2, size - margin - 6)
        return self.build(draw)

    def image(self) -> QIcon:
        """Image/picture icon."""
        def draw(p, size):
            margin = 3
            rect = size - margin * 2
            
            # Frame
            p.drawRoundedRect(margin, margin, rect, rect, 2, 2)
            
            # Mountains
            p.drawLine(margin + 2, size - margin - 3, margin + 6, size - margin - 7)
            p.drawLine(margin + 6, size - margin - 7, margin + 10, size - margin - 4)
            p.drawLine(margin + 10, size - margin - 4, margin + 14, size - margin - 8)
            
            # Sun
            sun_x = size - margin - 5
            sun_y = margin + 5
            p.drawEllipse(sun_x - 2, sun_y - 2, 4, 4)
        return self.build(draw)

    def video(self) -> QIcon:
        """Video/play icon."""
        def draw(p, size):
            margin = 3
            rect = size - margin * 2
            
            # Frame
            p.drawRoundedRect(margin, margin, rect, rect, 2, 2)
            
            # Play triangle
            center_x = size // 2
            center_y = size // 2
            triangle_size = 5
            x1 = int(center_x - triangle_size // 2)
            y1 = int(center_y - triangle_size)
            x2 = int(center_x - triangle_size // 2)
            y2 = int(center_y + triangle_size)
            x3 = int(center_x + triangle_size)
            y3 = int(center_y)
            p.drawLine(x1, y1, x2, y2)
            p.drawLine(x2, y2, x3, y3)
            p.drawLine(x3, y3, x1, y1)
        return self.build(draw)

    def document(self) -> QIcon:
        """Document/file icon."""
        def draw(p, size):
            margin = 3
            width = size - margin * 2 - 2
            height = size - margin * 2
            fold = 5
            
            # Page
            p.drawLine(margin, margin, margin + width - fold, margin)
            p.drawLine(margin + width - fold, margin, margin + width, margin + fold)
            p.drawLine(margin + width, margin + fold, margin + width, size - margin)
            p.drawLine(margin + width, size - margin, margin, size - margin)
            p.drawLine(margin, size - margin, margin, margin)
            
            # Fold line
            p.drawLine(margin + width - fold, margin, margin + width - fold, margin + fold)
            p.drawLine(margin + width - fold, margin + fold, margin + width, margin + fold)
            
            # Lines
            line_y1 = margin + 7
            line_y2 = margin + 11
            line_y3 = margin + 15
            p.drawLine(margin + 3, line_y1, margin + width - 3, line_y1)
            p.drawLine(margin + 3, line_y2, margin + width - 3, line_y2)
            p.drawLine(margin + 3, line_y3, margin + width - 6, line_y3)
        return self.build(draw)

    def audio(self) -> QIcon:
        """Audio/volume icon."""
        def draw(p, size):
            margin = 3
            speaker_x = margin + 3
            speaker_width = 6
            
            # Speaker cone
            p.drawLine(speaker_x, margin + 5, speaker_x + 2, margin + 3)
            p.drawLine(speaker_x + 2, margin + 3, speaker_x + speaker_width, margin)
            p.drawLine(speaker_x + speaker_width, margin, speaker_x + speaker_width, size - margin)
            p.drawLine(speaker_x + speaker_width, size - margin, speaker_x + 2, size - margin - 3)
            p.drawLine(speaker_x + 2, size - margin - 3, speaker_x, margin + 5)
            
            # Sound waves
            wave1_x = speaker_x + speaker_width + 2
            p.drawArc(wave1_x, margin + 3, 6, size - margin * 2 - 3, 0, 90 * 16)
            p.drawArc(wave1_x, margin + 3, 6, size - margin * 2 - 3, 0, -90 * 16)
        return self.build(draw)

    def more(self) -> QIcon:
        """More/dots icon."""
        def draw(p, size):
            margin = 3
            dot_y = size // 2
            spacing = 5
            center_x = size // 2
            
            for i in range(-1, 2):
                x = center_x + i * spacing
                p.drawEllipse(x - 1, dot_y - 1, 3, 3)
        return self.build(draw)

    def arrow_up(self) -> QIcon:
        """Arrow up icon."""
        def draw(p, size):
            center_x = size // 2
            margin = 4
            head_y = margin + 4
            
            p.drawLine(center_x, head_y, center_x, size - margin)
            p.drawLine(center_x, head_y, center_x - 4, head_y + 4)
            p.drawLine(center_x, head_y, center_x + 4, head_y + 4)
        return self.build(draw)

    def arrow_down(self) -> QIcon:
        """Arrow down icon."""
        def draw(p, size):
            center_x = size // 2
            margin = 4
            head_y = size - margin - 4
            
            p.drawLine(center_x, margin, center_x, head_y)
            p.drawLine(center_x, head_y, center_x - 4, head_y - 4)
            p.drawLine(center_x, head_y, center_x + 4, head_y - 4)
        return self.build(draw)

    def clock(self) -> QIcon:
        """Clock/time icon."""
        def draw(p, size):
            margin = 3
            rect = size - margin * 2
            
            p.drawEllipse(margin, margin, rect, rect)
            center = size // 2
            p.drawLine(center, center, center, margin + 5)
            p.drawLine(center, center, center + 4, center + 2)
        return self.build(draw)

    def trash(self) -> QIcon:
        """Trash/delete icon."""
        def draw(p, size):
            margin = 3
            width = size - margin * 2 - 2
            height = size - margin * 2 - 2
            
            # Lid
            p.drawLine(margin + 3, margin + 2, size - margin - 3, margin + 2)
            p.drawLine(margin + 5, margin + 2, margin + 5, margin)
            p.drawLine(size - margin - 5, margin + 2, size - margin - 5, margin)
            
            # Body
            p.drawRoundedRect(margin + 1, margin + 3, width, height, 2, 2)
            
            # Lines
            line_x1 = margin + 5
            line_x2 = size // 2
            line_x3 = size - margin - 5
            for x in [line_x1, line_x2, line_x3]:
                p.drawLine(x, margin + 6, x, size - margin - 3)
        return self.build(draw)

    def tag(self) -> QIcon:
        """Tag/label icon."""
        def draw(p, size):
            margin = 3
            
            # Tag shape using QPoint
            points = [
                QPoint(margin + 3, margin),
                QPoint(size - margin, margin),
                QPoint(size - margin, size - margin - 3),
                QPoint(margin + 3, size - margin),
                QPoint(margin, size - margin - 3),
                QPoint(margin, margin + 3),
            ]
            for i in range(len(points)):
                p.drawLine(points[i], points[(i+1) % len(points)])
            
            # Hole
            p.drawEllipse(margin + 3, size//2 - 1, 3, 3)
        return self.build(draw)

    def plus(self) -> QIcon:
        """Plus/add icon."""
        def draw(p, size):
            center = size // 2
            margin = 4
            
            p.drawLine(center, margin, center, size - margin)
            p.drawLine(margin, center, size - margin, center)
        return self.build(draw)

    def minus(self) -> QIcon:
        """Minus/remove icon."""
        def draw(p, size):
            center = size // 2
            margin = 4
            
            p.drawLine(margin, center, size - margin, center)
        return self.build(draw)

    def filter(self) -> QIcon:
        """Filter/funnel icon."""
        def draw(p, size):
            margin = 3
            top_width = size - margin * 2
            bottom_width = top_width // 2
            
            # Funnel shape
            p.drawLine(margin, margin, size - margin, margin)
            left_x = margin + (top_width - bottom_width)//2
            right_x = size - margin - (top_width - bottom_width)//2
            bottom_y = size - margin - 4
            p.drawLine(margin, margin, left_x, bottom_y)
            p.drawLine(size - margin, margin, right_x, bottom_y)
            p.drawLine(left_x, bottom_y, right_x, bottom_y)
        return self.build(draw)

    def refresh(self) -> QIcon:
        """Refresh/reload icon."""
        def draw(p, size):
            margin = 3
            center = size // 2
            radius = size // 2 - margin - 1
            
            # Arc (most of circle)
            p.drawArc(margin, margin, size - margin * 2, size - margin * 2, 45 * 16, 270 * 16)
            
            # Arrow head
            arrow_x = center + radius - 2
            arrow_y = margin + 4
            p.drawLine(arrow_x, arrow_y, arrow_x + 3, arrow_y + 3)
            p.drawLine(arrow_x, arrow_y, arrow_x - 2, arrow_y + 3)
        return self.build(draw)

    def clear(self) -> QIcon:
        """Clear/x icon."""
        def draw(p, size):
            margin = 4
            
            p.drawLine(margin, margin, size - margin, size - margin)
            p.drawLine(margin, size - margin, size - margin, margin)
        return self.build(draw)


class IconProvider:
    """Provides themed icons for the application."""

    def __init__(self, theme: str = "light"):
        self.theme = theme
        self._update_color()

    def _update_color(self):
        if self.theme == "dark":
            self.color = "#a0aec0"
            self.hover_color = "#63b3ed"
            self.active_color = "#4299e1"
        else:
            self.color = "#5a677a"
            self.hover_color = "#3182ce"
            self.active_color = "#2b6cb0"

    def set_theme(self, theme: str):
        self.theme = theme
        self._update_color()

    def get_icon(self, name: str, state: str = "normal") -> QIcon:
        """Get an icon by name."""
        color = self.color
        if state == "hover":
            color = self.hover_color
        elif state == "active":
            color = self.active_color

        builder = IconBuilder(color)
        icon_map = {
            "search": builder.search,
            "list": builder.list_view,
            "grid": builder.grid_view,
            "folder": builder.folder,
            "home": builder.home,
            "image": builder.image,
            "video": builder.video,
            "document": builder.document,
            "audio": builder.audio,
            "more": builder.more,
            "arrow_up": builder.arrow_up,
            "arrow_down": builder.arrow_down,
            "clock": builder.clock,
            "trash": builder.trash,
            "tag": builder.tag,
            "plus": builder.plus,
            "minus": builder.minus,
            "filter": builder.filter,
            "refresh": builder.refresh,
            "clear": builder.clear,
        }
        
        if name in icon_map:
            return icon_map[name]()
        return QIcon()


# Global icon provider instance
_icon_provider = IconProvider()


def get_icon(name: str, state: str = "normal") -> QIcon:
    """Get an icon from the global provider."""
    return _icon_provider.get_icon(name, state)


def set_theme(theme: str):
    """Set the global icon theme."""
    _icon_provider.set_theme(theme)
