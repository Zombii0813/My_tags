from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from ..core.indexer import FileMeta
from ..core.search import SearchQuery, SearchResult
from ..core.tag_manager import TagSpec
from .models import File, FileTag, Tag


@dataclass
class Repo:
    session: Session

    def upsert_file(self, meta: FileMeta, existing_id: int | None = None) -> File:
        existing = None
        if existing_id is not None:
            existing = self.session.execute(
                select(File).where(File.id == existing_id)
            ).scalar_one_or_none()
        if existing is None:
            existing = self.session.execute(
                select(File).where(File.path == str(meta.path))
            ).scalar_one_or_none()

        if existing is None:
            file_row = File(
                path=str(meta.path),
                name=meta.name,
                ext=meta.ext,
                size=meta.size,
                type=meta.type,
                hash=meta.sha256,
                modified_at=meta.modified_at,
            )
            self.session.add(file_row)
            return file_row

        existing.name = meta.name  # type: ignore[assignment]
        existing.ext = meta.ext  # type: ignore[assignment]
        existing.size = meta.size  # type: ignore[assignment]
        existing.type = meta.type  # type: ignore[assignment]
        existing.hash = meta.sha256  # type: ignore[assignment]
        existing.modified_at = meta.modified_at  # type: ignore[assignment]
        existing.updated_at = datetime.utcnow()  # type: ignore[assignment]
        return existing

    def list_file_paths(self) -> list[tuple[int, str]]:
        stmt = select(File.id, File.path)
        return [
            (int(file_id), str(path))
            for file_id, path in self.session.execute(stmt).all()
            if file_id is not None
        ]

    def update_file_meta(self, file_row: File, meta: FileMeta) -> None:
        file_row.path = str(meta.path)  # type: ignore[assignment]
        file_row.name = meta.name  # type: ignore[assignment]
        file_row.ext = meta.ext  # type: ignore[assignment]
        file_row.size = meta.size  # type: ignore[assignment]
        file_row.type = meta.type  # type: ignore[assignment]
        file_row.hash = meta.sha256  # type: ignore[assignment]
        file_row.modified_at = meta.modified_at  # type: ignore[assignment]
        file_row.updated_at = datetime.utcnow()  # type: ignore[assignment]

    def list_tags(self) -> list[Tag]:
        return list(self.session.execute(select(Tag)).scalars())

    def get_tag_by_name(self, name: str) -> Tag | None:
        return self.session.execute(select(Tag).where(Tag.name == name)).scalar_one_or_none()

    def create_tag(self, spec: TagSpec) -> Tag:
        tag = Tag(name=spec.name, color=spec.color, description=spec.description)
        self.session.add(tag)
        return tag

    def get_or_create_tag(self, spec: TagSpec) -> Tag:
        existing = self.get_tag_by_name(spec.name)
        if existing is not None:
            return existing
        return self.create_tag(spec)

    def get_file_by_path(self, path: str) -> File | None:
        return self.session.execute(select(File).where(File.path == path)).scalar_one_or_none()

    def get_file_by_id(self, file_id: int) -> File | None:
        return self.session.execute(select(File).where(File.id == file_id)).scalar_one_or_none()

    def get_tags_for_file(self, file_id: int) -> list[Tag]:
        stmt = (
            select(Tag)
            .join(FileTag, FileTag.tag_id == Tag.id)
            .where(FileTag.file_id == file_id)
        )
        return list(self.session.execute(stmt).scalars())

    def get_tags_by_ids(self, tag_ids: Iterable[int]) -> list[Tag]:
        tag_ids = list(tag_ids)
        if not tag_ids:
            return []
        stmt = select(Tag).where(Tag.id.in_(tag_ids))
        return list(self.session.execute(stmt).scalars())

    def get_files_by_ids(self, file_ids: Iterable[int]) -> list[File]:
        file_ids = [int(file_id) for file_id in file_ids]
        if not file_ids:
            return []
        stmt = select(File).where(File.id.in_(file_ids))
        return list(self.session.execute(stmt).scalars())

    def list_files(self, limit: int | None = None) -> list[File]:
        query = select(File)
        if limit is not None:
            query = query.limit(limit)
        return list(self.session.execute(query).scalars())

    def attach_tags(self, file_row: File, tags: Iterable[Tag]) -> None:
        existing = {tag.id for tag in file_row.tags}
        for tag in tags:
            if tag.id not in existing:
                file_row.tags.append(tag)

    def detach_all_tags(self, file_row: File) -> None:
        file_row.tags.clear()

    def replace_tags(self, file_row: File, tags: Iterable[Tag]) -> None:
        file_row.tags = list(tags)

    def remove_tag_from_file(self, file_row: File, tag: Tag) -> None:
        if tag in file_row.tags:
            file_row.tags.remove(tag)

    def remove_tags_from_file(self, file_row: File, tags: Iterable[Tag]) -> None:
        for tag in tags:
            if tag in file_row.tags:
                file_row.tags.remove(tag)

    def delete_tag(self, tag_id: int) -> None:
        self.session.execute(delete(FileTag).where(FileTag.tag_id == tag_id))
        tag = self.session.execute(select(Tag).where(Tag.id == tag_id)).scalar_one_or_none()
        if tag is not None:
            self.session.delete(tag)

    def delete_files(self, file_ids: Iterable[int]) -> None:
        file_ids = list(file_ids)
        if not file_ids:
            return
        self.session.execute(delete(FileTag).where(FileTag.file_id.in_(file_ids)))
        self.session.execute(delete(File).where(File.id.in_(file_ids)))

    def search(self, query: SearchQuery, limit: int | None = None) -> list[SearchResult]:
        stmt = select(File)

        if query.text:
            term = f"%{query.text}%"
            stmt = stmt.where(File.name.ilike(term))

        if query.types:
            stmt = stmt.where(File.type.in_(query.types))

        if query.tags:
            stmt = stmt.join(FileTag, FileTag.file_id == File.id).join(
                Tag, Tag.id == FileTag.tag_id
            )
            stmt = stmt.where(Tag.name.in_(query.tags))
            if query.match_all_tags:
                stmt = stmt.group_by(File.id).having(
                    func.count(func.distinct(Tag.name)) == len(query.tags)
                )
            else:
                stmt = stmt.distinct()

        if query.sort_by:
            sort_map = {
                "name": File.name,
                "size": File.size,
                "type": File.type,
                "created_at": File.created_at,
                "updated_at": File.updated_at,
                "modified_at": File.modified_at,
            }
            column = sort_map.get(query.sort_by)
            if column is not None:
                stmt = stmt.order_by(column.desc() if query.sort_desc else column.asc())

        if limit is not None:
            stmt = stmt.limit(limit)

        rows = self.session.execute(stmt).scalars().all()
        results: list[SearchResult] = []
        for row in rows:
            results.append(
                SearchResult(
                    file_id=row.id,  # type: ignore[arg-type]
                    path=row.path,  # type: ignore[arg-type]
                    name=row.name,  # type: ignore[arg-type]
                    type=row.type,  # type: ignore[arg-type]
                )
            )
        return results
