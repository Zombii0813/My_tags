from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib
import os
import shutil
import subprocess

from PIL import Image


@dataclass
class ThumbnailService:
    thumbs_dir: Path

    def _ensure_dir(self) -> None:
        self.thumbs_dir.mkdir(parents=True, exist_ok=True)

    def _cache_path(self, source: Path, kind: str) -> Path:
        stat = source.stat()
        digest = hashlib.sha1(str(source).encode("utf-8")).hexdigest()
        stamp = int(stat.st_mtime)
        return self.thumbs_dir / f"{kind}_{digest}_{stamp}.jpg"

    def generate_image_thumbnail(self, source: Path, size: tuple[int, int]) -> Path:
        self._ensure_dir()
        target = self._cache_path(source, "image")
        if target.exists():
            return target
        with Image.open(source) as image:
            image.thumbnail(size)
            image.save(target, "JPEG")
        return target

    def generate_video_thumbnail(self, source: Path, size: tuple[int, int]) -> Path | None:
        ffmpeg_path = os.getenv("MYTAGS_FFMPEG") or os.getenv("FFMPEG_PATH")
        ffmpeg_bin = ffmpeg_path or shutil.which("ffmpeg")
        if not ffmpeg_bin:
            return None
        self._ensure_dir()
        target = self._cache_path(source, "video")
        if target.exists():
            return target
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
