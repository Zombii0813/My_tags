"""
Modern, sleek stylesheets for the application.
Provides minimalist and futuristic themes.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtWidgets import QApplication

# Theme directory
THEMES_DIR = Path(__file__).parent / "themes"
DEFAULT_THEME = "light"


def load_theme(theme_name: str) -> str:
    """
    Load a theme stylesheet from file.
    
    Args:
        theme_name: Name of the theme (e.g., 'light', 'dark')
        
    Returns:
        Stylesheet content as string
    """
    theme_file = THEMES_DIR / f"{theme_name}.qss"
    
    if not theme_file.exists():
        # Fallback to default theme
        theme_file = THEMES_DIR / f"{DEFAULT_THEME}.qss"
    
    if theme_file.exists():
        return theme_file.read_text(encoding='utf-8')
    
    return ""


def apply_theme(app: QApplication, theme_name: str) -> None:
    """
    Apply a theme to the application.
    
    Args:
        app: QApplication instance
        theme_name: Name of the theme to apply
    """
    stylesheet = load_theme(theme_name)
    if stylesheet:
        app.setStyleSheet(stylesheet)


def get_available_themes() -> list[str]:
    """
    Get list of available theme names.
    
    Returns:
        List of theme names (without .qss extension)
    """
    if not THEMES_DIR.exists():
        return [DEFAULT_THEME]
    
    themes = []
    for file in THEMES_DIR.glob("*.qss"):
        themes.append(file.stem)
    
    return sorted(themes) if themes else [DEFAULT_THEME]


def get_stylesheet(theme: str) -> str:
    """
    Get stylesheet for the specified theme.
    
    Args:
        theme: Theme name ('light', 'dark')
        
    Returns:
        Stylesheet content
    """
    return load_theme(theme)


def get_available_themes_list() -> list[str]:
    """
    Get list of available theme names.
    
    Returns:
        List of theme names
    """
    return get_available_themes()


# Re-export main functions for convenience
__all__ = [
    "load_theme",
    "apply_theme",
    "get_available_themes",
    "DEFAULT_THEME",
    "get_stylesheet",
    "get_available_themes_list",
]
