from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil

from ..config import AppConfig
from ..core.search import SearchQuery
from ..core.tag_manager import TagSpec
from ..db.repo import Repo
from ..db.session import get_session
from ..services.scan_service import ScanService


@dataclass
class AppController:
    config: AppConfig

    @staticmethod
    def _within_workspace(path: Path, workspace_root: Path | None) -> bool:
        if workspace_root is None:
            return True
        try:
            path.resolve().relative_to(workspace_root.resolve())
            return True
        except ValueError:
            return False

    def scan_workspace(self, root: Path, on_progress=None) -> int:
        session = get_session()
        try:
            service = ScanService(session)
            count = service.scan_workspace(root, on_progress=on_progress)
            session.commit()
            return count
        finally:
            session.close()

    def list_files(self, limit: int | None = None):
        session = get_session()
        try:
            repo = Repo(session)
            return repo.list_files(limit=limit)
        finally:
            session.close()

    def get_file(self, file_id: int):
        session = get_session()
        try:
            repo = Repo(session)
            return repo.get_file_by_id(file_id)
        finally:
            session.close()

    def search(self, query: SearchQuery, limit: int | None = None):
        session = get_session()
        try:
            repo = Repo(session)
            return repo.search(query, limit=limit)
        finally:
            session.close()

    def list_tags(self):
        session = get_session()
        try:
            repo = Repo(session)
            return repo.list_tags()
        finally:
            session.close()

    def create_tag(self, name: str):
        session = get_session()
        try:
            repo = Repo(session)
            tag = repo.get_or_create_tag(TagSpec(name=name))
            session.commit()
            return tag
        finally:
            session.close()

    def delete_tag(self, tag_id: int) -> None:
        session = get_session()
        try:
            repo = Repo(session)
            repo.delete_tag(tag_id)
            session.commit()
        finally:
            session.close()

    def attach_tags(self, file_id: int, tag_ids: list[int]) -> None:
        session = get_session()
        try:
            repo = Repo(session)
            file_row = repo.get_file_by_id(file_id)
            if file_row is None:
                return
            tags = repo.get_tags_by_ids(tag_ids)
            repo.attach_tags(file_row, tags)
            session.commit()
        finally:
            session.close()

    def tags_for_file(self, file_id: int):
        session = get_session()
        try:
            repo = Repo(session)
            return repo.get_tags_for_file(file_id)
        finally:
            session.close()

    def replace_tags(self, file_id: int, tag_ids: list[int]) -> None:
        session = get_session()
        try:
            repo = Repo(session)
            file_row = repo.get_file_by_id(file_id)
            if file_row is None:
                return
            tags = repo.get_tags_by_ids(tag_ids)
            repo.replace_tags(file_row, tags)
            session.commit()
        finally:
            session.close()

    def remove_tags(self, file_id: int, tag_ids: list[int]) -> None:
        session = get_session()
        try:
            repo = Repo(session)
            file_row = repo.get_file_by_id(file_id)
            if file_row is None:
                return
            tags = repo.get_tags_by_ids(tag_ids)
            repo.remove_tags_from_file(file_row, tags)
            session.commit()
        finally:
            session.close()

    def delete_files(self, file_ids: list[int]) -> None:
        session = get_session()
        try:
            repo = Repo(session)
            repo.delete_files(file_ids)
            session.commit()
        finally:
            session.close()

    def move_files(
        self, file_ids: list[int], destination: Path, workspace_root: Path | None = None
    ) -> tuple[int, list[str]]:
        session = get_session()
        errors: list[str] = []
        moved = 0
        try:
            repo = Repo(session)
            files = repo.get_files_by_ids(file_ids)
            used_targets: set[str] = set()
            from ..core.indexer import build_file_meta

            for file_row in files:
                try:
                    source = Path(str(file_row.path))
                    target = destination / source.name
                    if str(target) in used_targets or target.exists():
                        target = destination / f"{source.stem}_{file_row.id}{source.suffix}"
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(source), str(target))
                    if self._within_workspace(target, workspace_root):
                        meta = build_file_meta(target)
                        repo.update_file_meta(file_row, meta)
                    else:
                        if file_row.id is not None:
                            repo.delete_files([int(file_row.id)])
                    moved += 1
                    used_targets.add(str(target))
                except Exception as exc:
                    errors.append(f"{file_row.path}: {exc}")
            session.commit()
        finally:
            session.close()
        return moved, errors

    def copy_files(
        self, file_ids: list[int], destination: Path, workspace_root: Path | None = None
    ) -> tuple[int, list[str]]:
        session = get_session()
        errors: list[str] = []
        copied = 0
        try:
            repo = Repo(session)
            files = repo.get_files_by_ids(file_ids)
            used_targets: set[str] = set()
            for file_row in files:
                try:
                    source = Path(str(file_row.path))
                    target = destination / source.name
                    if str(target) in used_targets or target.exists():
                        target = destination / f"{source.stem}_{file_row.id}{source.suffix}"
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(str(source), str(target))
                    if self._within_workspace(target, workspace_root):
                        from ..core.indexer import build_file_meta

                        meta = build_file_meta(target)
                        repo.upsert_file(meta)
                    copied += 1
                    used_targets.add(str(target))
                except Exception as exc:
                    errors.append(f"{file_row.path}: {exc}")
            session.commit()
        finally:
            session.close()
        return copied, errors

    def handle_file_changed(self, path: Path) -> None:
        if not path.exists() or not path.is_file():
            return
        session = get_session()
        try:
            repo = Repo(session)
            from ..core.indexer import build_file_meta

            meta = build_file_meta(path)
            repo.upsert_file(meta)
            session.commit()
        finally:
            session.close()

    def handle_file_deleted(self, path: Path) -> None:
        session = get_session()
        try:
            repo = Repo(session)
            file_row = repo.get_file_by_path(str(path))
            if file_row and file_row.id is not None:
                repo.delete_files([int(file_row.id)])
                session.commit()
        finally:
            session.close()
