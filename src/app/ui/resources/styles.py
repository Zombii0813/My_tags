"""
Modern, sleek stylesheets for the application.
Provides minimalist and futuristic themes.
"""
from __future__ import annotations


class ThemeStyles:
    """Collection of modern theme stylesheets."""

    # Modern Light Theme - Clean & Minimalist
    LIGHT = """
    /* Main Window */
    QMainWindow {
        background-color: #f8fafc;
        color: #1e293b;
    }

    /* Menu Bar */
    QMenuBar {
        background: #ffffff;
        border-bottom: 1px solid #e2e8f0;
        padding: 4px 8px;
        font-size: 13px;
    }
    QMenuBar::item {
        background: transparent;
        padding: 4px 12px;
        border-radius: 4px;
    }
    QMenuBar::item:selected {
        background: #f1f5f9;
        color: #0f172a;
    }
    QMenuBar::item:pressed {
        background: #e2e8f0;
    }

    /* Menu */
    QMenu {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 6px;
    }
    QMenu::item {
        padding: 8px 24px 8px 12px;
        border-radius: 4px;
        font-size: 13px;
    }
    QMenu::item:selected {
        background: #eff6ff;
        color: #2563eb;
    }
    QMenu::separator {
        height: 1px;
        background: #e2e8f0;
        margin: 6px 12px;
    }

    /* Tool Bar */
    QToolBar {
        background: #ffffff;
        border: none;
        padding: 8px 12px;
        spacing: 8px;
        border-bottom: 1px solid #e2e8f0;
    }
    QToolBar::separator {
        width: 1px;
        height: 20px;
        background: #e2e8f0;
        margin: 0 4px;
    }

    /* Tool Button */
    QToolButton {
        background: transparent;
        border: 1px solid transparent;
        border-radius: 6px;
        padding: 6px;
        min-width: 28px;
        min-height: 28px;
    }
    QToolButton:hover {
        background: #f1f5f9;
        border-color: #e2e8f0;
    }
    QToolButton:pressed {
        background: #e2e8f0;
    }
    QToolButton:checked {
        background: #eff6ff;
        border-color: #3b82f6;
        color: #2563eb;
    }

    /* Line Edit (Search) */
    QLineEdit {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 8px 12px;
        font-size: 13px;
        min-height: 20px;
        selection-background-color: #3b82f6;
    }
    QLineEdit:focus {
        border-color: #3b82f6;
        background: #ffffff;
    }
    QLineEdit::placeholder {
        color: #94a3b8;
    }

    /* Push Button */
    QPushButton {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 6px 14px;
        font-size: 12px;
        font-weight: 500;
        color: #475569;
    }
    QPushButton:hover {
        background: #f1f5f9;
        border-color: #cbd5e1;
    }
    QPushButton:pressed {
        background: #e2e8f0;
    }
    QPushButton:default {
        background: #3b82f6;
        border-color: #3b82f6;
        color: #ffffff;
    }
    QPushButton:default:hover {
        background: #2563eb;
        border-color: #2563eb;
    }

    /* Primary Button (Blue) */
    QPushButton#primaryButton {
        background: #3b82f6;
        border-color: #3b82f6;
        color: #ffffff;
    }
    QPushButton#primaryButton:hover {
        background: #2563eb;
        border-color: #2563eb;
    }

    /* Danger Button (Red) */
    QPushButton#dangerButton {
        background: #ef4444;
        border-color: #ef4444;
        color: #ffffff;
    }
    QPushButton#dangerButton:hover {
        background: #dc2626;
        border-color: #dc2626;
    }

    /* Side Panel */
    #sidePanel {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 16px;
    }

    /* Tag Panel */
    #tagPanel {
        background: transparent;
    }

    /* Detail Panel */
    #detailPanel {
        background: transparent;
    }

    /* List Widget */
    QListWidget {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 4px;
        outline: none;
    }
    QListWidget::item {
        border-radius: 6px;
        padding: 8px 12px;
        margin: 2px 0;
        min-height: 24px;
    }
    QListWidget::item:selected {
        background: #eff6ff;
        color: #1e293b;
        border: 1px solid #bfdbfe;
    }
    QListWidget::item:hover {
        background: #f8fafc;
    }
    QListWidget::item:selected:hover {
        background: #dbeafe;
    }

    /* Tree Widget */
    QTreeWidget {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 4px;
        outline: none;
    }
    QTreeWidget::item {
        border-radius: 6px;
        padding: 6px 8px;
        margin: 1px 0;
        min-height: 20px;
    }
    QTreeWidget::item:selected {
        background: #eff6ff;
        color: #1e293b;
        border: 1px solid #bfdbfe;
    }
    QTreeWidget::item:hover {
        background: #f8fafc;
    }
    QTreeWidget::branch:has-children:!has-siblings:closed,
    QTreeWidget::branch:closed:has-children:has-siblings {
        image: none;
        border-image: none;
    }
    QTreeWidget::branch:open:has-children:!has-siblings,
    QTreeWidget::branch:open:has-children:has-siblings {
        image: none;
        border-image: none;
    }

    /* Status Bar */
    QStatusBar {
        background: #ffffff;
        border-top: 1px solid #e2e8f0;
        padding: 4px 12px;
        font-size: 12px;
        color: #64748b;
    }
    QStatusBar::item {
        border: none;
    }

    /* Progress Bar */
    QProgressBar {
        background: #e2e8f0;
        border: none;
        border-radius: 4px;
        height: 4px;
        text-align: center;
    }
    QProgressBar::chunk {
        background: #3b82f6;
        border-radius: 4px;
    }

    /* Check Box */
    QCheckBox {
        spacing: 8px;
        font-size: 12px;
        color: #475569;
    }
    QCheckBox::indicator {
        width: 16px;
        height: 16px;
        border: 1px solid #cbd5e1;
        border-radius: 4px;
        background: #ffffff;
    }
    QCheckBox::indicator:checked {
        background: #3b82f6;
        border-color: #3b82f6;
    }
    QCheckBox::indicator:hover {
        border-color: #94a3b8;
    }

    /* Splitter */
    QSplitter::handle {
        background: transparent;
    }
    QSplitter::handle:horizontal {
        width: 4px;
        margin: 0 2px;
    }
    QSplitter::handle:vertical {
        height: 4px;
        margin: 2px 0;
    }
    QSplitter::handle:hover {
        background: #cbd5e1;
    }

    /* Scroll Bar */
    QScrollBar:vertical {
        background: transparent;
        width: 8px;
        border-radius: 4px;
    }
    QScrollBar::handle:vertical {
        background: #cbd5e1;
        min-height: 24px;
        border-radius: 4px;
    }
    QScrollBar::handle:vertical:hover {
        background: #94a3b8;
    }
    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {
        height: 0px;
    }
    QScrollBar:horizontal {
        background: transparent;
        height: 8px;
        border-radius: 4px;
    }
    QScrollBar::handle:horizontal {
        background: #cbd5e1;
        min-width: 24px;
        border-radius: 4px;
    }
    QScrollBar::handle:horizontal:hover {
        background: #94a3b8;
    }
    QScrollBar::add-line:horizontal,
    QScrollBar::sub-line:horizontal {
        width: 0px;
    }

    /* Tooltip */
    QToolTip {
        background: #1e293b;
        color: #f8fafc;
        border: none;
        border-radius: 6px;
        padding: 6px 10px;
        font-size: 12px;
    }

    /* Dialog */
    QDialog {
        background: #f8fafc;
    }

    /* Input Dialog */
    QInputDialog {
        background: #f8fafc;
    }

    /* Message Box */
    QMessageBox {
        background: #f8fafc;
    }

    /* Label */
    QLabel {
        color: #1e293b;
        font-size: 13px;
    }
    QLabel#sectionTitle {
        font-size: 11px;
        font-weight: 600;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    """

    # Modern Dark Theme - Sleek & Futuristic
    DARK = """
    /* Main Window */
    QMainWindow {
        background-color: #0f172a;
        color: #f1f5f9;
    }

    /* Menu Bar */
    QMenuBar {
        background: #1e293b;
        border-bottom: 1px solid #334155;
        padding: 4px 8px;
        font-size: 13px;
        color: #cbd5e1;
    }
    QMenuBar::item {
        background: transparent;
        padding: 4px 12px;
        border-radius: 4px;
    }
    QMenuBar::item:selected {
        background: #334155;
        color: #f8fafc;
    }
    QMenuBar::item:pressed {
        background: #475569;
    }

    /* Menu */
    QMenu {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 6px;
    }
    QMenu::item {
        padding: 8px 24px 8px 12px;
        border-radius: 4px;
        font-size: 13px;
        color: #cbd5e1;
    }
    QMenu::item:selected {
        background: #3b82f6;
        color: #ffffff;
    }
    QMenu::separator {
        height: 1px;
        background: #334155;
        margin: 6px 12px;
    }

    /* Tool Bar */
    QToolBar {
        background: #1e293b;
        border: none;
        padding: 8px 12px;
        spacing: 8px;
        border-bottom: 1px solid #334155;
    }
    QToolBar::separator {
        width: 1px;
        height: 20px;
        background: #334155;
        margin: 0 4px;
    }

    /* Tool Button */
    QToolButton {
        background: transparent;
        border: 1px solid transparent;
        border-radius: 6px;
        padding: 6px;
        min-width: 28px;
        min-height: 28px;
        color: #94a3b8;
    }
    QToolButton:hover {
        background: #334155;
        border-color: #475569;
        color: #e2e8f0;
    }
    QToolButton:pressed {
        background: #475569;
    }
    QToolButton:checked {
        background: #3b82f6;
        border-color: #3b82f6;
        color: #ffffff;
    }
    QToolButton:checked:hover {
        background: #2563eb;
    }

    /* Line Edit (Search) */
    QLineEdit {
        background: #0f172a;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 8px 12px;
        font-size: 13px;
        min-height: 20px;
        color: #f1f5f9;
        selection-background-color: #3b82f6;
    }
    QLineEdit:focus {
        border-color: #3b82f6;
        background: #1e293b;
    }
    QLineEdit::placeholder {
        color: #64748b;
    }

    /* Push Button */
    QPushButton {
        background: #334155;
        border: 1px solid #475569;
        border-radius: 6px;
        padding: 6px 14px;
        font-size: 12px;
        font-weight: 500;
        color: #e2e8f0;
    }
    QPushButton:hover {
        background: #475569;
        border-color: #64748b;
    }
    QPushButton:pressed {
        background: #1e293b;
    }
    QPushButton:default {
        background: #3b82f6;
        border-color: #3b82f6;
        color: #ffffff;
    }
    QPushButton:default:hover {
        background: #2563eb;
        border-color: #2563eb;
    }

    /* Primary Button (Blue) */
    QPushButton#primaryButton {
        background: #3b82f6;
        border-color: #3b82f6;
        color: #ffffff;
    }
    QPushButton#primaryButton:hover {
        background: #2563eb;
        border-color: #2563eb;
    }

    /* Danger Button (Red) */
    QPushButton#dangerButton {
        background: #ef4444;
        border-color: #ef4444;
        color: #ffffff;
    }
    QPushButton#dangerButton:hover {
        background: #dc2626;
        border-color: #dc2626;
    }

    /* Side Panel */
    #sidePanel {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 16px;
    }

    /* Tag Panel */
    #tagPanel {
        background: transparent;
    }

    /* Detail Panel */
    #detailPanel {
        background: transparent;
    }

    /* List Widget */
    QListWidget {
        background: #0f172a;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 4px;
        outline: none;
    }
    QListWidget::item {
        border-radius: 6px;
        padding: 8px 12px;
        margin: 2px 0;
        min-height: 24px;
        color: #cbd5e1;
    }
    QListWidget::item:selected {
        background: #3b82f6;
        color: #ffffff;
        border: 1px solid #60a5fa;
    }
    QListWidget::item:hover {
        background: #1e293b;
    }
    QListWidget::item:selected:hover {
        background: #2563eb;
    }

    /* Tree Widget */
    QTreeWidget {
        background: #0f172a;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 4px;
        outline: none;
    }
    QTreeWidget::item {
        border-radius: 6px;
        padding: 6px 8px;
        margin: 1px 0;
        min-height: 20px;
        color: #cbd5e1;
    }
    QTreeWidget::item:selected {
        background: #3b82f6;
        color: #ffffff;
        border: 1px solid #60a5fa;
    }
    QTreeWidget::item:hover {
        background: #1e293b;
    }

    /* Status Bar */
    QStatusBar {
        background: #1e293b;
        border-top: 1px solid #334155;
        padding: 4px 12px;
        font-size: 12px;
        color: #94a3b8;
    }
    QStatusBar::item {
        border: none;
    }

    /* Progress Bar */
    QProgressBar {
        background: #334155;
        border: none;
        border-radius: 4px;
        height: 4px;
        text-align: center;
    }
    QProgressBar::chunk {
        background: #3b82f6;
        border-radius: 4px;
    }

    /* Check Box */
    QCheckBox {
        spacing: 8px;
        font-size: 12px;
        color: #cbd5e1;
    }
    QCheckBox::indicator {
        width: 16px;
        height: 16px;
        border: 1px solid #475569;
        border-radius: 4px;
        background: #0f172a;
    }
    QCheckBox::indicator:checked {
        background: #3b82f6;
        border-color: #3b82f6;
    }
    QCheckBox::indicator:hover {
        border-color: #64748b;
    }

    /* Splitter */
    QSplitter::handle {
        background: transparent;
    }
    QSplitter::handle:horizontal {
        width: 4px;
        margin: 0 2px;
    }
    QSplitter::handle:vertical {
        height: 4px;
        margin: 2px 0;
    }
    QSplitter::handle:hover {
        background: #475569;
    }

    /* Scroll Bar */
    QScrollBar:vertical {
        background: transparent;
        width: 8px;
        border-radius: 4px;
    }
    QScrollBar::handle:vertical {
        background: #475569;
        min-height: 24px;
        border-radius: 4px;
    }
    QScrollBar::handle:vertical:hover {
        background: #64748b;
    }
    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {
        height: 0px;
    }
    QScrollBar:horizontal {
        background: transparent;
        height: 8px;
        border-radius: 4px;
    }
    QScrollBar::handle:horizontal {
        background: #475569;
        min-width: 24px;
        border-radius: 4px;
    }
    QScrollBar::handle:horizontal:hover {
        background: #64748b;
    }
    QScrollBar::add-line:horizontal,
    QScrollBar::sub-line:horizontal {
        width: 0px;
    }

    /* Tooltip */
    QToolTip {
        background: #1e293b;
        color: #f8fafc;
        border: 1px solid #334155;
        border-radius: 6px;
        padding: 6px 10px;
        font-size: 12px;
    }

    /* Dialog */
    QDialog {
        background: #0f172a;
    }

    /* Input Dialog */
    QInputDialog {
        background: #0f172a;
    }

    /* Message Box */
    QMessageBox {
        background: #0f172a;
    }

    /* Label */
    QLabel {
        color: #f1f5f9;
        font-size: 13px;
    }
    QLabel#sectionTitle {
        font-size: 11px;
        font-weight: 600;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    """

    # Midnight Blue Theme - Deep & Elegant
    MIDNIGHT = """
    /* Main Window */
    QMainWindow {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
            stop:0 #0a0e1a, stop:1 #0f172a);
        color: #e2e8f0;
    }

    /* Menu Bar */
    QMenuBar {
        background: rgba(30, 41, 59, 0.8);
        border-bottom: 1px solid rgba(99, 102, 241, 0.3);
        padding: 4px 8px;
        font-size: 13px;
        color: #94a3b8;
    }
    QMenuBar::item {
        background: transparent;
        padding: 4px 12px;
        border-radius: 4px;
    }
    QMenuBar::item:selected {
        background: rgba(99, 102, 241, 0.2);
        color: #818cf8;
    }

    /* Menu */
    QMenu {
        background: #1e1b4b;
        border: 1px solid rgba(99, 102, 241, 0.4);
        border-radius: 8px;
        padding: 6px;
    }
    QMenu::item {
        padding: 8px 24px 8px 12px;
        border-radius: 4px;
        font-size: 13px;
        color: #c7d2fe;
    }
    QMenu::item:selected {
        background: linear-gradient(135deg, #6366f1, #8b5cf6);
        color: #ffffff;
    }
    QMenu::separator {
        height: 1px;
        background: rgba(99, 102, 241, 0.3);
        margin: 6px 12px;
    }

    /* Tool Bar */
    QToolBar {
        background: rgba(30, 41, 59, 0.6);
        border: none;
        padding: 8px 12px;
        spacing: 8px;
        border-bottom: 1px solid rgba(99, 102, 241, 0.2);
    }
    QToolBar::separator {
        width: 1px;
        height: 20px;
        background: rgba(99, 102, 241, 0.3);
        margin: 0 4px;
    }

    /* Tool Button */
    QToolButton {
        background: transparent;
        border: 1px solid transparent;
        border-radius: 8px;
        padding: 6px;
        min-width: 28px;
        min-height: 28px;
        color: #94a3b8;
    }
    QToolButton:hover {
        background: rgba(99, 102, 241, 0.15);
        border-color: rgba(99, 102, 241, 0.4);
        color: #818cf8;
    }
    QToolButton:pressed {
        background: rgba(99, 102, 241, 0.25);
    }
    QToolButton:checked {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 #6366f1, stop:1 #8b5cf6);
        border-color: transparent;
        color: #ffffff;
    }

    /* Line Edit (Search) */
    QLineEdit {
        background: rgba(15, 23, 42, 0.8);
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 10px;
        padding: 8px 14px;
        font-size: 13px;
        min-height: 20px;
        color: #e2e8f0;
        selection-background-color: #6366f1;
    }
    QLineEdit:focus {
        border-color: #6366f1;
        background: rgba(30, 41, 59, 0.9);
    }

    /* Push Button */
    QPushButton {
        background: rgba(30, 41, 59, 0.8);
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 8px;
        padding: 6px 14px;
        font-size: 12px;
        font-weight: 500;
        color: #c7d2fe;
    }
    QPushButton:hover {
        background: rgba(99, 102, 241, 0.15);
        border-color: rgba(99, 102, 241, 0.5);
    }
    QPushButton:pressed {
        background: rgba(99, 102, 241, 0.25);
    }
    QPushButton:default {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 #6366f1, stop:1 #8b5cf6);
        border-color: transparent;
        color: #ffffff;
    }

    /* Side Panel */
    #sidePanel {
        background: rgba(30, 41, 59, 0.6);
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: 12px;
        padding: 16px;
    }

    /* List Widget */
    QListWidget {
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: 10px;
        padding: 4px;
        outline: none;
    }
    QListWidget::item {
        border-radius: 8px;
        padding: 8px 12px;
        margin: 2px 0;
        min-height: 24px;
        color: #c7d2fe;
    }
    QListWidget::item:selected {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 rgba(99, 102, 241, 0.3), stop:1 rgba(139, 92, 246, 0.3));
        color: #ffffff;
        border: 1px solid rgba(99, 102, 241, 0.5);
    }
    QListWidget::item:hover {
        background: rgba(99, 102, 241, 0.1);
    }

    /* Tree Widget */
    QTreeWidget {
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: 10px;
        padding: 4px;
        outline: none;
    }
    QTreeWidget::item {
        border-radius: 6px;
        padding: 6px 8px;
        margin: 1px 0;
        min-height: 20px;
        color: #c7d2fe;
    }
    QTreeWidget::item:selected {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 rgba(99, 102, 241, 0.3), stop:1 rgba(139, 92, 246, 0.3));
        color: #ffffff;
        border: 1px solid rgba(99, 102, 241, 0.5);
    }

    /* Status Bar */
    QStatusBar {
        background: rgba(30, 41, 59, 0.8);
        border-top: 1px solid rgba(99, 102, 241, 0.2);
        padding: 4px 12px;
        font-size: 12px;
        color: #818cf8;
    }

    /* Progress Bar */
    QProgressBar {
        background: rgba(30, 41, 59, 0.8);
        border: none;
        border-radius: 4px;
        height: 4px;
    }
    QProgressBar::chunk {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #6366f1, stop:1 #8b5cf6);
        border-radius: 4px;
    }

    /* Check Box */
    QCheckBox {
        spacing: 8px;
        font-size: 12px;
        color: #c7d2fe;
    }
    QCheckBox::indicator {
        width: 16px;
        height: 16px;
        border: 1px solid rgba(99, 102, 241, 0.4);
        border-radius: 4px;
        background: rgba(15, 23, 42, 0.6);
    }
    QCheckBox::indicator:checked {
        background: #6366f1;
        border-color: #6366f1;
    }

    /* Splitter */
    QSplitter::handle:hover {
        background: rgba(99, 102, 241, 0.5);
    }

    /* Scroll Bar */
    QScrollBar::handle:vertical,
    QScrollBar::handle:horizontal {
        background: rgba(99, 102, 241, 0.3);
    }
    QScrollBar::handle:vertical:hover,
    QScrollBar::handle:horizontal:hover {
        background: rgba(99, 102, 241, 0.5);
    }

    /* Tooltip */
    QToolTip {
        background: #1e1b4b;
        color: #e2e8f0;
        border: 1px solid rgba(99, 102, 241, 0.4);
        border-radius: 6px;
        padding: 6px 10px;
    }

    /* Label */
    QLabel {
        color: #e2e8f0;
        font-size: 13px;
    }
    QLabel#sectionTitle {
        font-size: 11px;
        font-weight: 600;
        color: #818cf8;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    """


THEMES = {
    "light": ThemeStyles.LIGHT,
    "dark": ThemeStyles.DARK,
    "midnight": ThemeStyles.MIDNIGHT,
}


def get_stylesheet(theme: str) -> str:
    """Get stylesheet for the specified theme."""
    return THEMES.get(theme, ThemeStyles.LIGHT)


def get_available_themes() -> list[str]:
    """Get list of available theme names."""
    return list(THEMES.keys())
