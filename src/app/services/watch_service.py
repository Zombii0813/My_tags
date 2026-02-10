from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


@dataclass
class WatchService:
    observer = None
    handler = None

    def start(
        self,
        root: Path,
        on_change: Callable[[Path], None] | None = None,
        on_delete: Callable[[Path], None] | None = None,
    ) -> None:
        if self.observer is None:
            self.observer = Observer()
        self.handler = _WatchHandler(on_change=on_change, on_delete=on_delete)
        observer = self.observer
        if observer is None:
            return
        observer.schedule(self.handler, str(root), recursive=True)
        observer.start()

    def stop(self) -> None:
        if self.observer is None:
            return
        self.observer.stop()
        self.observer.join()
        self.observer = None


class _WatchHandler(FileSystemEventHandler):
    def __init__(self, on_change=None, on_delete=None) -> None:
        super().__init__()
        self.on_change = on_change
        self.on_delete = on_delete

    def on_created(self, event) -> None:
        if event.is_directory:
            return
        if self.on_change:
            self.on_change(Path(event.src_path))

    def on_modified(self, event) -> None:
        if event.is_directory:
            return
        if self.on_change:
            self.on_change(Path(event.src_path))

    def on_moved(self, event) -> None:
        if event.is_directory:
            return
        if self.on_change:
            self.on_change(Path(event.dest_path))

    def on_deleted(self, event) -> None:
        if event.is_directory:
            return
        if self.on_delete:
            self.on_delete(Path(event.src_path))
