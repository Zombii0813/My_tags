from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib
import os
import shutil
import subprocess
from typing import Literal

from PIL import Image
from PySide6.QtCore import QRunnable, QThreadPool, QRect, QTimer
from PySide6.QtGui import QPixmap, QPixmapCache, QGuiApplication
from PySide6.QtWidgets import QListWidget, QListWidgetItem

from ..utils.windows_thumbnails import load_shell_thumbnail


# 缩略图配置常量
DEFAULT_QUALITY = 80          # 默认 WebP 质量
JPEG_FALLBACK_QUALITY = 85    # JPEG 回退质量
BUFFER_ITEMS = 10             # 上下缓冲区项目数
PRELOAD_DELAY_MS = 100        # 预加载延迟（防抖）
MAX_PRELOAD_WORKERS = 4       # 最大并发预加载线程数


@dataclass
class ThumbnailSize:
    """缩略图尺寸配置 - 支持 1x/2x 版本"""
    logical_size: tuple[int, int]   # 逻辑尺寸（CSS像素）
    scale_factor: float = 1.0       # 设备像素比
    
    @property
    def physical_size(self) -> tuple[int, int]:
        """物理尺寸（实际像素）- 用于高分屏"""
        return (
            int(self.logical_size[0] * self.scale_factor),
            int(self.logical_size[1] * self.scale_factor),
        )
    
    @property
    def size_key(self) -> str:
        """尺寸缓存键"""
        return f"{self.logical_size[0]}x{self.logical_size[1]}@{self.scale_factor:.1f}x"


@dataclass
class ViewportRange:
    """可视区域范围"""
    first_visible: int
    last_visible: int
    total_items: int
    
    @property
    def visible_count(self) -> int:
        return self.last_visible - self.first_visible + 1
    
    def with_buffer(self, buffer_size: int) -> "ViewportRange":
        """扩展缓冲区范围"""
        return ViewportRange(
            first_visible=max(0, self.first_visible - buffer_size),
            last_visible=min(self.total_items - 1, self.last_visible + buffer_size),
            total_items=self.total_items,
        )


def get_device_pixel_ratio() -> float:
    """获取设备像素比（DPR）
    
    Returns:
        设备像素比，普通屏为 1.0，Retina/高分屏为 2.0 或更高
    """
    app = QGuiApplication.instance()
    if app is not None:
        # 获取主屏幕的 DPR
        screens = app.screens()
        if screens:
            return screens[0].devicePixelRatio()
    return 1.0


def calculate_dynamic_quality(size: tuple[int, int], original_size: tuple[int, int] | None = None) -> int:
    """根据显示尺寸动态计算压缩质量
    
    原理：
    - 小尺寸缩略图可以使用更低质量（人眼难以察觉）
    - 大尺寸预览需要更高质量保持清晰度
    
    Args:
        size: 目标缩略图尺寸
        original_size: 原始图片尺寸（可选）
    
    Returns:
        推荐的质量值 (50-95)
    """
    max_dimension = max(size)
    
    if max_dimension <= 64:
        # 极小图标：质量可以很低
        return 60
    elif max_dimension <= 100:
        # 小图标
        return 70
    elif max_dimension <= 200:
        # 中等缩略图
        return 80
    elif max_dimension <= 400:
        # 大缩略图
        return 85
    else:
        # 预览尺寸
        return 90


class ThumbnailFormat:
    """缩略图格式管理 - WebP 优先，JPEG 回退"""
    
    _webp_supported: bool | None = None
    
    @classmethod
    def is_webp_supported(cls) -> bool:
        """检测系统是否支持 WebP"""
        if cls._webp_supported is not None:
            return cls._webp_supported
        
        try:
            # 尝试创建一个 WebP 图片
            test_img = Image.new('RGB', (10, 10), color='red')
            from io import BytesIO
            buffer = BytesIO()
            test_img.save(buffer, 'WEBP')
            cls._webp_supported = True
        except Exception:
            cls._webp_supported = False
        
        return cls._webp_supported
    
    @classmethod
    def get_extension(cls) -> Literal[".webp", ".jpg"]:
        """获取推荐的文件扩展名"""
        return ".webp" if cls.is_webp_supported() else ".jpg"
    
    @classmethod
    def get_save_kwargs(cls, quality: int, size: tuple[int, int]) -> dict:
        """获取保存参数
        
        Args:
            quality: 质量值
            size: 目标尺寸
        
        Returns:
            PIL Image.save() 的参数字典
        """
        if cls.is_webp_supported():
            return {
                "format": "WEBP",
                "quality": quality,
                "method": 6,  # 压缩方法 (0-6)，越高压缩率越好但越慢
            }
        else:
            # JPEG 回退
            # 根据尺寸调整 JPEG 质量
            adjusted_quality = min(quality + 5, 95)  # JPEG 需要稍高质量补偿
            return {
                "format": "JPEG",
                "quality": adjusted_quality,
                "optimize": True,
                "progressive": True,
            }


@dataclass
class ThumbnailService:
    """缩略图服务 - 优化版
    
    优化特性：
    1. 可视区域+缓冲区预加载
    2. 动态质量调整
    3. WebP/JPEG 自适应
    4. Retina/高分屏支持
    """
    
    thumbs_dir: Path

    def __post_init__(self) -> None:
        # 内存缓存限制：128MB
        QPixmapCache.setCacheLimit(128 * 1024)
        
        # 线程池用于后台预加载
        self._thread_pool = QThreadPool()
        self._thread_pool.setMaxThreadCount(MAX_PRELOAD_WORKERS)
        
        # 预加载令牌（用于取消旧任务）
        self._preheat_token = 0
        
        # 防抖定时器
        self._preload_timer: QTimer | None = None
        
        # 当前预加载范围
        self._current_range: ViewportRange | None = None

    def _ensure_dir(self) -> None:
        self.thumbs_dir.mkdir(parents=True, exist_ok=True)

    def _cache_key(self, source: Path, kind: str, size: ThumbnailSize) -> str:
        """生成缓存键 - 包含 DPR 信息"""
        stat = source.stat()
        digest = hashlib.sha1(str(source).encode("utf-8")).hexdigest()
        stamp = int(stat.st_mtime)
        return f"{kind}:{digest}:{stamp}:{size.size_key}"

    def _cache_path(self, cache_key: str) -> Path:
        """生成磁盘缓存路径"""
        digest = hashlib.sha1(cache_key.encode("utf-8")).hexdigest()
        ext = ThumbnailFormat.get_extension()
        return self.thumbs_dir / digest[:2] / digest[2:4] / f"{digest}{ext}"

    def _load_cached_pixmap(self, cache_key: str, path: Path) -> QPixmap | None:
        """从内存或磁盘加载缓存的缩略图"""
        # 先查内存缓存
        cached = QPixmapCache.find(cache_key)
        if cached is not None and not cached.isNull():
            return cached
        
        # 再查磁盘缓存
        if not path.exists():
            return None
        
        # 根据 DPR 加载合适尺寸的图片
        pixmap = QPixmap(str(path))
        if pixmap.isNull():
            return None
        
        # 存入内存缓存
        QPixmapCache.insert(cache_key, pixmap)
        return pixmap

    def _save_thumbnail(self, image: Image.Image, target: Path, size: tuple[int, int]) -> bool:
        """保存缩略图到磁盘 - 自动选择格式和质量"""
        try:
            self._ensure_dir()
            target.parent.mkdir(parents=True, exist_ok=True)
            
            # 动态计算质量
            quality = calculate_dynamic_quality(size)
            kwargs = ThumbnailFormat.get_save_kwargs(quality, size)
            
            # 调整尺寸（保持比例）
            image.thumbnail(size)
            
            # 保存
            image.save(target, **kwargs)
            return target.exists()
        except Exception:
            return False

    def _ensure_disk_image(self, source: Path, size: ThumbnailSize) -> Path | None:
        """确保图片缩略图已生成并返回缓存路径"""
        cache_key = self._cache_key(source, "image", size)
        target = self._cache_path(cache_key)
        
        if target.exists():
            return target
        
        # 优先使用系统 Shell 缩略图
        shell_image = load_shell_thumbnail(source, size.physical_size)
        
        try:
            if shell_image is not None:
                if self._save_thumbnail(shell_image, target, size.physical_size):
                    return target
            
            # 回退到 PIL 处理
            with Image.open(source) as image:
                # 处理 EXIF 旋转
                image = self._apply_exif_rotation(image)
                if self._save_thumbnail(image, target, size.physical_size):
                    return target
        except Exception:
            pass
        
        return None

    def _ensure_disk_video(self, source: Path, size: ThumbnailSize) -> Path | None:
        """确保视频缩略图已生成"""
        cache_key = self._cache_key(source, "video", size)
        target = self._cache_path(cache_key)
        
        if target.exists():
            return target
        
        # 优先使用系统 Shell 缩略图
        shell_image = load_shell_thumbnail(source, size.physical_size)
        if shell_image is not None:
            if self._save_thumbnail(shell_image, target, size.physical_size):
                return target
        
        # 回退到 ffmpeg
        ffmpeg_bin = self._ffmpeg_bin()
        if not ffmpeg_bin:
            return None
        
        # 先生成临时帧，再转换
        temp_frame = target.with_suffix(".jpg")
        command = [
            ffmpeg_bin,
            "-y",
            "-ss", "00:00:01",
            "-i", str(source),
            "-vframes", "1",
            "-vf", f"scale={size.physical_size[0]}:{size.physical_size[1]}:force_original_aspect_ratio=decrease",
            "-q:v", "3",
            str(temp_frame),
        ]
        
        try:
            subprocess.run(
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
            )
            
            if temp_frame.exists():
                with Image.open(temp_frame) as img:
                    if self._save_thumbnail(img, target, size.physical_size):
                        return target
        except Exception:
            pass
        finally:
            # 清理临时文件
            if temp_frame.exists():
                temp_frame.unlink(missing_ok=True)
        
        return None

    def _ensure_disk_shell(self, source: Path, size: ThumbnailSize) -> Path | None:
        """确保 Shell 缩略图已生成"""
        cache_key = self._cache_key(source, "shell", size)
        target = self._cache_path(cache_key)
        
        if target.exists():
            return target
        
        shell_image = load_shell_thumbnail(source, size.physical_size)
        if shell_image is None:
            return None
        
        if self._save_thumbnail(shell_image, target, size.physical_size):
            return target
        
        return None

    def _apply_exif_rotation(self, image: Image.Image) -> Image.Image:
        """应用 EXIF 旋转信息"""
        try:
            from PIL import ExifTags
            exif = image._getexif()
            if exif is not None:
                orientation = exif.get(ExifTags.Orientation)
                rotations = {
                    3: Image.ROTATE_180,
                    6: Image.ROTATE_270,
                    8: Image.ROTATE_90,
                }
                if orientation in rotations:
                    image = image.transpose(rotations[orientation])
        except Exception:
            pass
        return image

    def _ffmpeg_bin(self) -> str | None:
        """获取 ffmpeg 可执行文件路径"""
        ffmpeg_path = os.getenv("MYTAGS_FFMPEG") or os.getenv("FFMPEG_PATH")
        return ffmpeg_path or shutil.which("ffmpeg")

    def get_thumbnail_size(self, logical_size: tuple[int, int]) -> ThumbnailSize:
        """获取适合当前设备的缩略图尺寸"""
        dpr = get_device_pixel_ratio()
        return ThumbnailSize(logical_size=logical_size, scale_factor=dpr)

    def generate_image_thumbnail(
        self, source: Path, logical_size: tuple[int, int]
    ) -> QPixmap | None:
        """生成图片缩略图"""
        size = self.get_thumbnail_size(logical_size)
        cache_key = self._cache_key(source, "image", size)
        target = self._cache_path(cache_key)
        
        cached = self._load_cached_pixmap(cache_key, target)
        if cached is not None:
            return cached
        
        created = self._ensure_disk_image(source, size)
        if created is None:
            return None
        
        return self._load_cached_pixmap(cache_key, target)

    def generate_video_thumbnail(
        self, source: Path, logical_size: tuple[int, int]
    ) -> QPixmap | None:
        """生成视频缩略图"""
        size = self.get_thumbnail_size(logical_size)
        cache_key = self._cache_key(source, "video", size)
        target = self._cache_path(cache_key)
        
        cached = self._load_cached_pixmap(cache_key, target)
        if cached is not None:
            return cached
        
        created = self._ensure_disk_video(source, size)
        if created is None:
            return None
        
        return self._load_cached_pixmap(cache_key, target)

    def generate_shell_thumbnail(
        self, source: Path, logical_size: tuple[int, int]
    ) -> QPixmap | None:
        """生成 Shell 缩略图"""
        size = self.get_thumbnail_size(logical_size)
        cache_key = self._cache_key(source, "shell", size)
        target = self._cache_path(cache_key)
        
        cached = self._load_cached_pixmap(cache_key, target)
        if cached is not None:
            return cached
        
        created = self._ensure_disk_shell(source, size)
        if created is None:
            return None
        
        return self._load_cached_pixmap(cache_key, target)

    def calculate_viewport_range(self, widget: QListWidget) -> ViewportRange:
        """计算可视区域范围
        
        Args:
            widget: 文件列表控件
        
        Returns:
            可视区域范围，包含首尾索引和总数
        """
        if widget.count() == 0:
            return ViewportRange(0, 0, 0)
        
        # 获取滚动条位置
        scrollbar = widget.verticalScrollBar()
        viewport_height = widget.viewport().height()
        
        # 估算每个项目的高度（列表模式 vs 网格模式）
        if widget.viewMode() == QListWidget.IconMode:
            # 网格模式：估算每行高度
            item_height = widget.iconSize().height() + 20  # 图标 + 文字间距
            items_per_row = max(1, widget.viewport().width() // (widget.iconSize().width() + 10))
        else:
            # 列表模式
            item_height = widget.visualItemRect(widget.item(0)).height() if widget.count() > 0 else 20
            items_per_row = 1
        
        # 计算可见范围
        scroll_pos = scrollbar.value()
        first_visible = int(scroll_pos / item_height) * items_per_row
        visible_rows = int(viewport_height / item_height) + 1
        last_visible = min(
            first_visible + visible_rows * items_per_row - 1,
            widget.count() - 1,
        )
        
        return ViewportRange(
            first_visible=max(0, first_visible),
            last_visible=max(0, last_visible),
            total_items=widget.count(),
        )

    def preheat_visible_thumbnails(
        self,
        widget: QListWidget,
        items: list[dict],
        logical_size: tuple[int, int],
    ) -> None:
        """预加载可视区域+缓冲区的缩略图（智能防抖版）
        
        Args:
            widget: 文件列表控件
            items: 项目数据列表
            logical_size: 缩略图逻辑尺寸
        """
        if not items or widget.count() == 0:
            return
        
        # 计算新的可视区域
        viewport = self.calculate_viewport_range(widget)
        buffered = viewport.with_buffer(BUFFER_ITEMS)
        
        # 如果范围没有变化，跳过
        if (self._current_range is not None and 
            self._current_range.first_visible == buffered.first_visible and
            self._current_range.last_visible == buffered.last_visible):
            return
        
        self._current_range = buffered
        
        # 取消旧的预加载任务
        self._preheat_token += 1
        token = self._preheat_token
        
        # 防抖：延迟启动预加载
        if self._preload_timer is not None:
            self._preload_timer.stop()
        
        self._preload_timer = QTimer()
        self._preload_timer.setSingleShot(True)
        
        def do_preheat():
            self._start_preheat(items, buffered, logical_size, token)
        
        self._preload_timer.timeout.connect(do_preheat)
        self._preload_timer.start(PRELOAD_DELAY_MS)

    def _start_preheat(
        self,
        items: list[dict],
        range_: ViewportRange,
        logical_size: tuple[int, int],
        token: int,
    ) -> None:
        """启动预加载任务"""
        # 准备预加载列表
        preheat_items: list[tuple[Path, str]] = []
        size = self.get_thumbnail_size(logical_size)
        
        for i in range(range_.first_visible, range_.last_visible + 1):
            if i >= len(items):
                break
            
            item = items[i]
            path = Path(item.get("path", ""))
            file_type = item.get("type")
            
            if not path.exists():
                continue
            
            # 确定缩略图类型
            if file_type in {"image", "video"}:
                kind = str(file_type)
            else:
                kind = "shell"
            
            # 检查是否已缓存
            cache_key = self._cache_key(path, kind, size)
            cache_path = self._cache_path(cache_key)
            if not cache_path.exists():
                preheat_items.append((path, kind))
        
        # 分批提交到线程池
        if preheat_items:
            batch_size = max(1, len(preheat_items) // MAX_PRELOAD_WORKERS)
            for i in range(0, len(preheat_items), batch_size):
                batch = preheat_items[i:i + batch_size]
                self._thread_pool.start(
                    _PreheatTask(self, batch, logical_size, token)
                )


class _PreheatTask(QRunnable):
    """后台预加载任务"""
    
    def __init__(
        self,
        service: ThumbnailService,
        items: list[tuple[Path, str]],
        logical_size: tuple[int, int],
        token: int,
    ) -> None:
        super().__init__()
        self._service = service
        self._items = items
        self._logical_size = logical_size
        self._token = token

    def run(self) -> None:
        """执行预加载"""
        for path, kind in self._items:
            # 检查令牌是否过期（新任务已启动）
            if self._service._preheat_token != self._token:
                return
            
            if not path.exists():
                continue
            
            size = self._service.get_thumbnail_size(self._logical_size)
            
            try:
                if kind == "image":
                    self._service._ensure_disk_image(path, size)
                elif kind == "video":
                    self._service._ensure_disk_video(path, size)
                elif kind == "shell":
                    self._service._ensure_disk_shell(path, size)
            except Exception:
                # 预加载失败不抛出，避免阻塞
                pass
