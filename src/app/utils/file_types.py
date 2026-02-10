from __future__ import annotations

from pathlib import Path


_IMAGE = {"jpg", "jpeg", "png", "gif", "bmp", "webp", "tiff"}
_VIDEO = {"mp4", "mov", "mkv", "avi", "wmv"}
_DOC = {"pdf", "doc", "docx", "ppt", "pptx", "xls", "xlsx", "txt"}
_AUDIO = {"mp3", "wav", "flac", "aac"}


def classify_file(path: Path) -> str:
    ext = path.suffix.lower().lstrip(".")
    if ext in _IMAGE:
        return "image"
    if ext in _VIDEO:
        return "video"
    if ext in _DOC:
        return "doc"
    if ext in _AUDIO:
        return "audio"
    return "other"
