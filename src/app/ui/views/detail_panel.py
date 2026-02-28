"""
Modern, sleek detail panel with preview and file information.
"""
from __future__ import annotations

from pathlib import Path
from datetime import datetime

from PySide6.QtCore import Qt, QSize, QTimer, Signal
from PySide6.QtGui import QPixmap, QFont, QColor, QPainter
from PySide6.QtWidgets import (
    QLabel, QSizePolicy, QVBoxLayout, QWidget,
    QHBoxLayout, QFrame, QScrollArea, QGridLayout
)


class PreviewWidget(QWidget):
    """Custom widget to display a centered pixmap."""
    
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._pixmap: QPixmap | None = None
        self._text: str = "No preview"
        self.setMinimumSize(200, 180)
        # 使用 Expanding 策略让预览图自适应容器
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
    def setPixmap(self, pixmap: QPixmap | None) -> None:
        self._pixmap = pixmap
        self.update()
        
    def setText(self, text: str) -> None:
        self._text = text
        self._pixmap = None
        self.update()
        
    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        if self._pixmap is not None and not self._pixmap.isNull():
            # 按原比例缩放图片，使其在区域内最大化显示
            available_width = self.width()
            available_height = self.height()
            
            # 计算缩放后的尺寸，保持比例
            scaled = self._pixmap.scaled(
                available_width,
                available_height,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            # Calculate centered position
            x = (available_width - scaled.width()) // 2
            y = (available_height - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)
        else:
            # 填充背景
            painter.fillRect(self.rect(), QColor("#f8fafc"))
            # Draw text in center
            painter.setPen(QColor("#64748b"))
            font = QFont()
            font.setPointSize(32)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignCenter, self._text)
        
        painter.end()

from ...config import load_config
from ...db.models import File
from ...services.thumbnail_service import ThumbnailService
from ..widgets.tag_chip import TagChip, TagChipContainer


class DetailPanel(QWidget):
    """
    Modern detail panel with file preview and metadata.
    
    Features:
    - Large file preview area
    - Clean metadata display
    - Tag chips for associated tags
    - Modern card-based layout
    """

    tag_remove_requested = Signal(int, str)  # file_id, tag_name

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("detailPanel")
        config = load_config()
        self._thumb_service = ThumbnailService(config.thumbs_dir)
        self._current_file: File | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the modern detail panel UI."""
        # Main scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        # Container widget
        container = QWidget()
        self.main_layout = QVBoxLayout(container)
        self.main_layout.setContentsMargins(12, 12, 12, 12)
        self.main_layout.setSpacing(12)
        self.main_layout.setAlignment(Qt.AlignTop)

        # Preview section
        self.preview_section = self._build_preview_section()
        self.main_layout.addWidget(self.preview_section)

        # File info section
        self.info_section = self._build_info_section()
        self.main_layout.addWidget(self.info_section)

        # Tags section
        self.tags_section = self._build_tags_section()
        self.main_layout.addWidget(self.tags_section)

        # Selection info
        self.selection_label = QLabel("")
        self.selection_label.setStyleSheet("""
            QLabel {
                color: #64748b;
                font-size: 12px;
                font-style: italic;
            }
        """)
        self.selection_label.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.selection_label)

        self.main_layout.addStretch()
        scroll.setWidget(container)

        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll)

    def _build_preview_section(self) -> QFrame:
        """Build the file preview section."""
        section = QFrame()
        section.setObjectName("previewSection")
        section.setStyleSheet("""
            QFrame#previewSection {
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
            }
        """)
        # 限制 section 的最大宽度，确保不超出板块
        section.setMaximumWidth(280)
        section.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        layout = QVBoxLayout(section)
        # 减小边距以减少留白
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setAlignment(Qt.AlignCenter)

        # Use custom preview widget for better centering
        self.preview_widget = PreviewWidget()
        # 增大预览图大小以填满框
        self.preview_widget.setMaximumSize(268, 240)
        self.preview_widget.setMinimumSize(200, 180)
        self.preview_widget.setFixedSize(268, 240)
        layout.addWidget(self.preview_widget, alignment=Qt.AlignCenter)

        return section

    def _build_info_section(self) -> QFrame:
        """Build the file info section."""
        section = QFrame()
        section.setObjectName("infoSection")
        section.setStyleSheet("""
            QFrame#infoSection {
                background: white;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
            }
        """)
        # 限制 section 的最大宽度
        section.setMaximumWidth(300)
        section.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        layout = QVBoxLayout(section)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # File name
        self.name_label = QLabel("Select a file")
        self.name_label.setWordWrap(True)
        self.name_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
        # 确保文本在板块宽度内换行
        self.name_label.setMinimumWidth(100)
        self.name_label.setMaximumWidth(300)
        # 允许长字符串在任意位置换行
        self.name_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.name_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: 600;
                color: #1e293b;
                line-height: 1.4;
            }
        """)
        layout.addWidget(self.name_label)

        # File path
        self.path_label = QLabel("")
        self.path_label.setWordWrap(True)
        self.path_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
        self.path_label.setMinimumWidth(100)
        self.path_label.setMaximumWidth(300)
        self.path_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.path_label.setStyleSheet("""
            QLabel {
                font-size: 11px;
                color: #64748b;
                line-height: 1.4;
            }
        """)
        layout.addWidget(self.path_label)

        # Metadata grid
        meta_frame = QFrame()
        meta_layout = QGridLayout(meta_frame)
        meta_layout.setContentsMargins(0, 0, 0, 0)
        meta_layout.setSpacing(8)
        meta_layout.setColumnStretch(1, 1)
        meta_layout.setColumnMinimumWidth(0, 50)

        # Type
        type_title = QLabel("Type")
        type_title.setStyleSheet(self._meta_title_style())
        self.type_value = QLabel("-")
        self.type_value.setStyleSheet(self._meta_value_style())
        self.type_value.setWordWrap(True)
        self.type_value.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.type_value.setMinimumWidth(50)
        meta_layout.addWidget(type_title, 0, 0, Qt.AlignTop)
        meta_layout.addWidget(self.type_value, 0, 1, Qt.AlignTop)

        # Size
        size_title = QLabel("Size")
        size_title.setStyleSheet(self._meta_title_style())
        self.size_value = QLabel("-")
        self.size_value.setStyleSheet(self._meta_value_style())
        self.size_value.setWordWrap(True)
        self.size_value.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.size_value.setMinimumWidth(50)
        meta_layout.addWidget(size_title, 1, 0, Qt.AlignTop)
        meta_layout.addWidget(self.size_value, 1, 1, Qt.AlignTop)

        # Modified
        modified_title = QLabel("Modified")
        modified_title.setStyleSheet(self._meta_title_style())
        self.modified_value = QLabel("-")
        self.modified_value.setStyleSheet(self._meta_value_style())
        self.modified_value.setWordWrap(True)
        self.modified_value.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.modified_value.setMinimumWidth(50)
        meta_layout.addWidget(modified_title, 2, 0, Qt.AlignTop)
        meta_layout.addWidget(self.modified_value, 2, 1, Qt.AlignTop)

        layout.addWidget(meta_frame)

        return section

    def _build_tags_section(self) -> QFrame:
        """Build the tags section."""
        section = QFrame()
        section.setObjectName("tagsSection")
        section.setStyleSheet("""
            QFrame#tagsSection {
                background: white;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
            }
        """)
        # 限制 section 的最大宽度
        section.setMaximumWidth(300)
        section.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        layout = QVBoxLayout(section)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Section title
        tags_title = QLabel("🏷️ Tags")
        tags_title.setStyleSheet("""
            QLabel {
                font-size: 12px;
                font-weight: 600;
                color: #64748b;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
        """)
        layout.addWidget(tags_title)

        # Tags container
        self.tags_container = TagChipContainer()
        self.tags_container.tag_removed.connect(self._on_tag_removed)
        layout.addWidget(self.tags_container)

        return section

    def _meta_title_style(self) -> str:
        return """
            QLabel {
                font-size: 11px;
                font-weight: 500;
                color: #94a3b8;
                min-width: 50px;
            }
        """

    def _meta_value_style(self) -> str:
        return """
            QLabel {
                font-size: 12px;
                color: #334155;
                font-weight: 500;
            }
        """

    def set_file(
        self, 
        file_row: File | None, 
        tags: list[str] | None = None, 
        selection_count: int = 1
    ) -> None:
        """Set the file to display details for."""
        if file_row is None:
            self._clear_display()
            if selection_count > 1:
                self.selection_label.setText(f"📁 {selection_count} files selected")
            else:
                self.selection_label.setText("Select a file to view details")
            return

        self._current_file = file_row
        self._update_display(file_row, tags or [])
        
        if selection_count > 1:
            self.selection_label.setText(f"📁 {selection_count} files selected")
        else:
            self.selection_label.setText("")

    def _clear_display(self) -> None:
        """Clear the display to default state."""
        self.name_label.setText("Select a file")
        self.path_label.setText("")
        self.type_value.setText("-")
        self.size_value.setText("-")
        self.modified_value.setText("-")
        self.preview_widget.setText("No preview")
        self.tags_container.clear()
        self._current_file = None

    def _update_display(self, file_row: File, tags: list[str]) -> None:
        """Update display with file information."""
        # Update basic info - 对长字符串进行特殊处理以便换行
        name = str(file_row.name)
        path = str(file_row.path)
        
        # 插入零宽空格 (\u200B) 帮助长字符串在任意位置换行
        self.name_label.setText(self._prepare_text_for_wrapping(name, max_chars=20))
        self.path_label.setText(self._prepare_text_for_wrapping(path, max_chars=25))
        
        self.type_value.setText(str(file_row.type).capitalize())
        self.size_value.setText(self._format_size(file_row.size))
        self.modified_value.setText(self._format_date(file_row.modified_at))

        # Update preview
        self._update_preview(file_row)

        # Update tags
        self.tags_container.clear()
        self._current_tags = tags  # Store current tags
        for tag in tags:
            self.tags_container.add_chip(tag, self._get_tag_color(tag), removable=True)

    def _update_preview(self, file_row: File) -> None:
        """Update the preview image."""
        file_type = str(file_row.type)
        file_path = Path(str(file_row.path))
        
        if not file_path.exists():
            self.preview_widget.setText("📄")
            return

        # Use widget size for thumbnail generation
        size = (self.preview_widget.width(), self.preview_widget.height())
        pixmap = None

        try:
            if file_type == "image":
                pixmap = self._thumb_service.generate_image_thumbnail(file_path, size)
            elif file_type == "video":
                pixmap = self._thumb_service.generate_video_thumbnail(file_path, size)
            else:
                pixmap = self._thumb_service.generate_shell_thumbnail(file_path, size)
        except Exception:
            pass

        if pixmap is None or pixmap.isNull():
            # Show file type icon
            icon_map = {
                "image": "🖼️",
                "video": "🎬",
                "audio": "🎵",
                "doc": "📄",
            }
            icon = icon_map.get(file_type, "📄")
            self.preview_widget.setText(icon)
        else:
            self.preview_widget.setPixmap(pixmap)

    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human readable format."""
        for unit in ["B", "KB", "MB", "GB"]:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"

    def _format_date(self, timestamp: float) -> str:
        """Format timestamp to readable date."""
        try:
            dt = datetime.fromtimestamp(timestamp)
            return dt.strftime("%Y-%m-%d %H:%M")
        except (ValueError, OSError):
            return "Unknown"

    def _get_tag_color(self, tag: str) -> str:
        """Get a consistent color for a tag."""
        colors = ["blue", "green", "red", "yellow", "purple",
                  "pink", "cyan", "orange", "indigo", "teal"]
        # Use hash of tag name to get consistent color
        color_index = hash(tag) % len(colors)
        return colors[color_index]

    def _prepare_text_for_wrapping(self, text: str, max_chars: int = 20) -> str:
        """
        在长字符串中插入零宽空格 (\u200B) 以帮助换行。
        这样可以避免超长单词导致布局超出边界。
        """
        if len(text) <= max_chars:
            return text
        
        # 在路径分隔符后插入零宽空格帮助换行
        text = text.replace('/', '/\u200B')
        text = text.replace('\\', '\\\u200B')
        
        # 对于超长单词（超过 max_chars 个字符无分隔符），强制分割
        result = []
        current = ""
        for char in text:
            if char == '\u200B':
                result.append(char)
                continue
            current += char
            if len(current) >= max_chars and char not in '\u200B':
                result.append(current)
                result.append('\u200B')  # 插入零宽空格允许换行
                current = ""
        result.append(current)
        
        return ''.join(result)

    def _on_tag_removed(self, tag_name: str) -> None:
        """Handle tag removal from the detail panel."""
        if self._current_file is not None and self._current_file.id is not None:
            # Emit signal to parent for tag removal
            self.tag_remove_requested.emit(int(self._current_file.id), tag_name)

    def resizeEvent(self, event) -> None:
        """Handle resize events to update preview size."""
        super().resizeEvent(event)
        # Re-update preview on resize to adjust image size
        if self._current_file is not None:
            # Use a small delay to avoid too many updates during resize
            QTimer.singleShot(50, lambda: self._update_preview(self._current_file))
