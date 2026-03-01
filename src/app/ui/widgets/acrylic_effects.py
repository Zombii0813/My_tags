"""
Acrylic/Glassmorphism effects for modern UI.
Provides blur and transparency effects for panels and dialogs.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, QTimer, QPoint, QRect
from PySide6.QtWidgets import (
    QWidget, QGraphicsBlurEffect, QGraphicsDropShadowEffect,
    QVBoxLayout, QHBoxLayout, QLabel, QFrame
)
from PySide6.QtGui import QColor, QPainter, QBrush, QPen, QFont


class AcrylicPanel(QFrame):
    """
    A panel with acrylic/glassmorphism effect.
    
    Features:
    - Semi-transparent background
    - Optional blur effect
    - Smooth shadow
    - Modern rounded corners (12px radius)
    """
    
    def __init__(
        self,
        parent: QWidget | None = None,
        blur_radius: int = 20,
        opacity: float = 0.85,
        bg_color: str = "#ffffff",
        enable_blur: bool = False
    ):
        super().__init__(parent)
        self._blur_radius = blur_radius
        self._opacity = opacity
        self._bg_color = bg_color
        self._enable_blur = enable_blur
        
        self._setup_ui()
        self._setup_effects()
        
    def _setup_ui(self):
        """Setup the panel UI."""
        self.setObjectName("acrylicPanel")
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_StyledBackground, False)
        
        # Set fixed corner radius
        self.setStyleSheet(f"""
            QFrame#acrylicPanel {{
                background-color: transparent;
                border-radius: 12px;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }}
        """)
        
    def _setup_effects(self):
        """Setup visual effects."""
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)
        
    def paintEvent(self, event):
        """Custom paint with acrylic effect."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Create semi-transparent background
        bg = QColor(self._bg_color)
        bg.setAlphaF(self._opacity)
        
        # Draw rounded rect background
        rect = self.rect().adjusted(1, 1, -1, -1)
        painter.fillRect(rect, bg)
        
        # Draw subtle border
        pen = QPen(QColor(255, 255, 255, 60))
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawRoundedRect(rect, 12, 12)
        
        painter.end()


class GlassCard(QFrame):
    """
    A card component with glassmorphism effect.
    
    Features:
    - Glass-like transparency
    - Smooth rounded corners
    - Soft shadow
    - Hover lift effect
    """
    
    def __init__(
        self,
        parent: QWidget | None = None,
        elevation: int = 1,  # 0-3, higher = more shadow
        hover_lift: bool = True
    ):
        super().__init__(parent)
        self._elevation = elevation
        self._hover_lift = hover_lift
        self._is_hovered = False
        self._shadow_effect: QGraphicsDropShadowEffect | None = None
        
        self._setup_ui()
        self._setup_shadow()
        
    def _setup_ui(self):
        """Setup the card UI."""
        self.setObjectName("glassCard")
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        
        # Base styles for glass effect
        self.setStyleSheet("""
            QFrame#glassCard {
                background-color: rgba(255, 255, 255, 0.9);
                border-radius: 12px;
                border: 1px solid rgba(0, 0, 0, 0.05);
            }
        """)
        
    def _setup_shadow(self):
        """Setup shadow based on elevation."""
        shadow = QGraphicsDropShadowEffect(self)
        
        # Shadow parameters based on elevation
        shadows = {
            0: (0, 0, QColor(0, 0, 0, 0)),
            1: (0, 2, QColor(0, 0, 0, 30)),
            2: (0, 4, QColor(0, 0, 0, 40)),
            3: (0, 8, QColor(0, 0, 0, 50)),
        }
        
        offset_x, offset_y, color = shadows.get(self._elevation, shadows[1])
        
        shadow.setBlurRadius(20)
        shadow.setColor(color)
        shadow.setOffset(offset_x, offset_y)
        
        self._shadow_effect = shadow
        self.setGraphicsEffect(shadow)
        
    def enterEvent(self, event):
        """Handle hover enter."""
        if self._hover_lift and self._shadow_effect:
            self._is_hovered = True
            # Lift effect - increase shadow
            self._shadow_effect.setBlurRadius(30)
            self._shadow_effect.setOffset(0, 6)
            self._shadow_effect.setColor(QColor(0, 0, 0, 60))
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        """Handle hover leave."""
        if self._hover_lift and self._shadow_effect:
            self._is_hovered = False
            # Reset shadow
            self._setup_shadow()
        super().leaveEvent(event)


class ModernSidePanel(QFrame):
    """
    Modern side panel with acrylic effect and consistent styling.
    
    Features:
    - 12px border radius
    - Soft shadow
    - Semi-transparent background
    - Consistent padding
    """
    
    def __init__(self, parent: QWidget | None = None, theme: str = "light"):
        super().__init__(parent)
        self._theme = theme
        self._setup_ui()
        self._setup_shadow()
        
    def set_theme(self, theme: str) -> None:
        """Set the panel theme and update styling."""
        self._theme = theme
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the panel UI."""
        self.setObjectName("sidePanel")
        
        # Theme-based styling
        if self._theme == "dark":
            bg_color = "rgba(30, 41, 59, 0.85)"
            border_color = "rgba(255, 255, 255, 0.1)"
        else:
            bg_color = "rgba(255, 255, 255, 0.95)"
            border_color = "rgba(0, 0, 0, 0.05)"
        
        self.setStyleSheet(f"""
            QFrame#sidePanel {{
                background-color: {bg_color};
                border-radius: 12px;
                border: 1px solid {border_color};
                padding: 2px;
            }}
        """)
        
    def _setup_shadow(self):
        """Setup shadow effect."""
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)


def create_card_widget(
    parent: QWidget | None = None,
    title: str | None = None,
    elevation: int = 1
) -> tuple[QFrame, QVBoxLayout]:
    """
    Create a modern card widget with shadow.
    
    Args:
        parent: Parent widget
        title: Optional card title
        elevation: Shadow elevation (0-3)
        
    Returns:
        Tuple of (card_widget, content_layout)
    """
    card = GlassCard(parent, elevation=elevation)
    layout = QVBoxLayout(card)
    layout.setContentsMargins(16, 16, 16, 16)
    layout.setSpacing(12)
    
    if title:
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 11px;
                font-weight: 600;
                color: #64748b;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
        """)
        layout.addWidget(title_label)
    
    content_layout = QVBoxLayout()
    content_layout.setSpacing(10)
    layout.addLayout(content_layout)
    
    return card, content_layout
