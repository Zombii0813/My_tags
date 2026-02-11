from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib
import os
import shutil
import subprocess

from PIL import Image
from PySide6.QtCore import QRunnable, QThreadPool
from PySide6.QtGui import QPixmap, QPixmapCache

from app.utils.windows_thumbnails import load_shell_thumbnail


@dataclass
class ThumbnailService:
    thumbs_dir: Path

    def __post_init__(self) -> None:
        QPixmapCache.setCacheLimit(128 * 1024)
        self._thread_pool = QThreadPool.globalInstance()
        self._preheat_token = 0

    def _ensure_dir(self) -> None:
        self.thumbs_dir.mkdir(parents=True, exist_ok=True)

    def _cache_key(self, source: Path, kind: str, size: tuple[int, int]) -> str:
        stat = source.stat()
        digest = hashlib.sha1(str(source).encode("utf-8")).hexdigest()
        stamp = int(stat.st_mtime)
        return f"{kind}:{digest}:{stamp}:{size[0]}x{size[1]}"

    def _cache_path(self, cache_key: str) -> Path:
        digest = hashlib.sha1(cache_key.encode("utf-8")).hexdigest()
        return self.thumbs_dir / digest[:2] / digest[2:4] / f"{digest}.webp"

    def _load_cached_pixmap(self, cache_key: str, path: Path) -> QPixmap | None:
        cached = QPixmapCache.find(cache_key)
        if cached is not None and not cached.isNull():
            return cached
        if not path.exists():
            return None
        pixmap = QPixmap(str(path))
        if pixmap.isNull():
            return None
        QPixmapCache.insert(cache_key, pixmap)
        return pixmap

    def _ffmpeg_bin(self) -> str | None:
        ffmpeg_path = os.getenv("MYTAGS_FFMPEG") or os.getenv("FFMPEG_PATH")
        return ffmpeg_path or shutil.which("ffmpeg")

    def _ensure_disk_image(self, source: Path, size: tuple[int, int]) -> Path | None:
        cache_key = self._cache_key(source, "image", size)
        target = self._cache_path(cache_key)
        if target.exists():
            return target
        shell_image = load_shell_thumbnail(source, size)
        self._ensure_dir()
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            if shell_image is not None:
                shell_image.thumbnail(size)
                shell_image.save(target, "WEBP", quality=80, method=6)
            else:
                with Image.open(source) as image:
                    image.thumbnail(size)
                    image.save(target, "WEBP", quality=80, method=6)
        except Exception:
            return None
        return target if target.exists() else None

    def _ensure_disk_video(self, source: Path, size: tuple[int, int]) -> Path | None:
        cache_key = self._cache_key(source, "video", size)
        target = self._cache_path(cache_key)
        if target.exists():
            return target
        shell_image = load_shell_thumbnail(source, size)
        if shell_image is not None:
            self._ensure_dir()
            target.parent.mkdir(parents=True, exist_ok=True)
            try:
                shell_image.thumbnail(size)
                shell_image.save(target, "WEBP", quality=80, method=6)
            except Exception:
                return None
            return target if target.exists() else None
        ffmpeg_bin = self._ffmpeg_bin()
        if not ffmpeg_bin:
            return None
        self._ensure_dir()
        target.parent.mkdir(parents=True, exist_ok=True)
        command = [
            ffmpeg_bin,
            "-y",
            "-ss",
            "00:00:01",
            "-i",
            str(source),
            "-vframes",
            "1",
            "-vf",
            f"scale={size[0]}:{size[1]}:force_original_aspect_ratio=decrease",
            "-q:v",
            "3",
            str(target),
        ]
        try:
            subprocess.run(
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
            )
        except Exception:
            return None
        return target if target.exists() else None

    def _ensure_disk_shell(self, source: Path, size: tuple[int, int]) -> Path | None:
        cache_key = self._cache_key(source, "shell", size)
        target = self._cache_path(cache_key)
        if target.exists():
            return target
        shell_image = load_shell_thumbnail(source, size)
        if shell_image is None:
            return None
        self._ensure_dir()
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            shell_image.thumbnail(size)
            shell_image.save(target, "WEBP", quality=80, method=6)
        except Exception:
            return None
        return target if target.exists() else None

    def generate_image_thumbnail(self, source: Path, size: tuple[int, int]) -> QPixmap | None:
        cache_key = self._cache_key(source, "image", size)
        target = self._cache_path(cache_key)
        cached = self._load_cached_pixmap(cache_key, target)
        if cached is not None:
            return cached
        created = self._ensure_disk_image(source, size)
        if created is None:
            return None
        return self._load_cached_pixmap(cache_key, target)

    def generate_video_thumbnail(self, source: Path, size: tuple[int, int]) -> QPixmap | None:
        cache_key = self._cache_key(source, "video", size)
        target = self._cache_path(cache_key)
        cached = self._load_cached_pixmap(cache_key, target)
        if cached is not None:
            return cached
        created = self._ensure_disk_video(source, size)
        if created is None:
            return None
        return self._load_cached_pixmap(cache_key, target)

    def generate_shell_thumbnail(self, source: Path, size: tuple[int, int]) -> QPixmap | None:
        cache_key = self._cache_key(source, "shell", size)
        target = self._cache_path(cache_key)
        cached = self._load_cached_pixmap(cache_key, target)
        if cached is not None:
            return cached
        created = self._ensure_disk_shell(source, size)
        if created is None:
            return None
        return self._load_cached_pixmap(cache_key, target)

    def preheat_disk_thumbnails(
        self,
        items: list[tuple[Path, str]],
        size: tuple[int, int],
    ) -> None:
        if not items:
            return
        self._preheat_token += 1
        token = self._preheat_token
        self._thread_pool.start(_PreheatTask(self, items, size, token))


class _PreheatTask(QRunnable):
    def __init__(
        self,
        service: ThumbnailService,
        items: list[tuple[Path, str]],
        size: tuple[int, int],
        token: int,
    ) -> None:
        super().__init__()
        self._service = service
        self._items = items
        self._size = size
        self._token = token

    def run(self) -> None:
        for path, kind in self._items:
            if self._service._preheat_token != self._token:
                return
            if not path.exists():
                continue
            if kind == "image":
                self._service._ensure_disk_image(path, self._size)
            elif kind == "video":
                self._service._ensure_disk_video(path, self._size)
            elif kind == "shell":
                self._service._ensure_disk_shell(path, self._size)
