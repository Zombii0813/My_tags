from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
from typing import Iterable

from ..utils.file_types import classify_file
from ..utils.hashing import sha256_file


@dataclass(frozen=True)
class FileMeta:
    path: Path
    name: str
    ext: str | None
    size: int
    type: str
    sha256: str | None
    modified_at: float | None


def build_file_meta(path: Path, include_hash: bool = False) -> FileMeta:
    stat = path.stat()
    ext = path.suffix.lower().lstrip(".") if path.suffix else None
    return FileMeta(
        path=path,
        name=path.name,
        ext=ext,
        size=stat.st_size,
        type=classify_file(path),
        sha256=sha256_file(path) if include_hash else None,
        modified_at=stat.st_mtime,
    )


def build_file_meta_from_entry(
    entry: os.DirEntry, include_hash: bool = False
) -> FileMeta:
    stat = entry.stat()
    path = Path(entry.path)
    ext = path.suffix.lower().lstrip(".") if path.suffix else None
    return FileMeta(
        path=path,
        name=entry.name,
        ext=ext,
        size=stat.st_size,
        type=classify_file(path),
        sha256=sha256_file(path) if include_hash else None,
        modified_at=stat.st_mtime,
    )


def iter_files(root: Path) -> Iterable[Path]:
    stack = [root]
    while stack:
        current = stack.pop()
        try:
            with os.scandir(current) as entries:
                for entry in entries:
                    if entry.is_dir(follow_symlinks=False):
                        stack.append(Path(entry.path))
                    elif entry.is_file(follow_symlinks=False):
                        yield Path(entry.path)
        except OSError:
            continue


def iter_file_entries(root: Path) -> Iterable[os.DirEntry]:
    stack = [root]
    while stack:
        current = stack.pop()
        try:
            with os.scandir(current) as entries:
                for entry in entries:
                    if entry.is_dir(follow_symlinks=False):
                        stack.append(Path(entry.path))
                    elif entry.is_file(follow_symlinks=False):
                        yield entry
        except OSError:
            continue
