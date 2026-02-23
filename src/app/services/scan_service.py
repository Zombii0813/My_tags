from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from sqlalchemy.orm import Session

from ..core.indexer import build_file_meta_from_entry, iter_file_entries
from ..db.repo import Repo


@dataclass
class ScanService:
    session: Session

    def scan_workspace(
        self, root: Path, on_progress: Callable[[int], None] | None = None
    ) -> int:
        repo = Repo(self.session)
        paths_seen: set[str] = set()
        count = 0
        root_path = root.resolve()
        path_to_id = {
            path: file_id
            for file_id, path in repo.list_file_paths()
            if self._is_under_root(path, root_path)
        }
        batch_size = 500
        for entry in iter_file_entries(root):
            path_str = entry.path
            existing_id = path_to_id.get(path_str)
            meta = build_file_meta_from_entry(entry)
            file_row = repo.upsert_file(meta, existing_id=existing_id)
            paths_seen.add(path_str)
            count += 1
            if on_progress:
                on_progress(count)
            if count % batch_size == 0:
                self.session.commit()

        stale_ids = []
        for file_id, path in repo.list_file_paths():
            if not self._is_under_root(path, root_path):
                continue
            if path not in paths_seen:
                stale_ids.append(int(file_id))
        if stale_ids:
            repo.delete_files(stale_ids)
        self.session.commit()
        return count

    @staticmethod
    def _is_under_root(path_value: str, root: Path) -> bool:
        try:
            Path(path_value).resolve().relative_to(root)
            return True
        except Exception:
            return False
