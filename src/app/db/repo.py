from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from sqlalchemy import delete, func, select, text, update
from sqlalchemy.orm import Session

from ..core.indexer import FileMeta
from ..core.search import SearchQuery, SearchResult
from ..core.tag_manager import TagSpec
from .models import File, FileTag, FileSearch, Tag

# 批量操作默认批次大小
DEFAULT_BATCH_SIZE = 500


@dataclass
class Repo:
    """数据访问层 - 提供数据库操作的统一接口
    
    包含文件、标签的增删改查，以及批量操作和全文搜索功能。
    实现了优化指南 1.1 中建议的所有数据库优化：
    - 索引优化
    - FTS5 全文搜索
    - 批量操作支持
    """
    
    session: Session

    # ========== 文件操作 ==========

    def upsert_file(self, meta: FileMeta, existing_id: int | None = None) -> File:
        """插入或更新单个文件
        
        Args:
            meta: 文件元数据
            existing_id: 可选的文件 ID，如果提供则优先查找此 ID
        
        Returns:
            插入或更新后的 File 对象
        """
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

    def bulk_upsert_files(
        self, metas: Iterable[FileMeta], batch_size: int = DEFAULT_BATCH_SIZE
    ) -> list[File]:
        """批量插入或更新文件 - 优化大文件扫描性能
        
        扫描时批量插入/更新，设置合理批次大小(默认500条)，
        减少数据库往返次数，显著提升性能。
        
        Args:
            metas: 文件元数据迭代器
            batch_size: 每批处理的文件数量
        
        Returns:
            插入或更新后的 File 对象列表
        """
        results: list[File] = []
        batch: list[FileMeta] = []
        
        for meta in metas:
            batch.append(meta)
            if len(batch) >= batch_size:
                results.extend(self._process_batch(batch))
                batch.clear()
                # 每批次提交一次，控制事务大小
                self.session.commit()
        
        # 处理剩余批次
        if batch:
            results.extend(self._process_batch(batch))
            self.session.commit()
        
        return results

    def _process_batch(self, batch: list[FileMeta]) -> list[File]:
        """处理一批文件元数据 - 内部方法"""
        results: list[File] = []
        paths = [str(m.path) for m in batch]
        
        # 批量查询已存在的文件
        existing_files = {
            f.path: f
            for f in self.session.execute(
                select(File).where(File.path.in_(paths))
            ).scalars()
        }
        
        for meta in batch:
            path_str = str(meta.path)
            if path_str in existing_files:
                # 更新现有文件
                file_row = existing_files[path_str]
                file_row.name = meta.name  # type: ignore[assignment]
                file_row.ext = meta.ext  # type: ignore[assignment]
                file_row.size = meta.size  # type: ignore[assignment]
                file_row.type = meta.type  # type: ignore[assignment]
                file_row.hash = meta.sha256  # type: ignore[assignment]
                file_row.modified_at = meta.modified_at  # type: ignore[assignment]
                file_row.updated_at = datetime.utcnow()  # type: ignore[assignment]
            else:
                # 创建新文件
                file_row = File(
                    path=path_str,
                    name=meta.name,
                    ext=meta.ext,
                    size=meta.size,
                    type=meta.type,
                    hash=meta.sha256,
                    modified_at=meta.modified_at,
                )
                self.session.add(file_row)
            results.append(file_row)
        
        return results

    def list_file_paths(self) -> list[tuple[int, str]]:
        """获取所有文件 ID 和路径列表"""
        stmt = select(File.id, File.path)
        return [
            (int(file_id), str(path))
            for file_id, path in self.session.execute(stmt).all()
            if file_id is not None
        ]

    def update_file_meta(self, file_row: File, meta: FileMeta) -> None:
        """更新文件元数据"""
        file_row.path = str(meta.path)  # type: ignore[assignment]
        file_row.name = meta.name  # type: ignore[assignment]
        file_row.ext = meta.ext  # type: ignore[assignment]
        file_row.size = meta.size  # type: ignore[assignment]
        file_row.type = meta.type  # type: ignore[assignment]
        file_row.hash = meta.sha256  # type: ignore[assignment]
        file_row.modified_at = meta.modified_at  # type: ignore[assignment]
        file_row.updated_at = datetime.utcnow()  # type: ignore[assignment]

    def get_file_by_path(self, path: str) -> File | None:
        """通过路径获取文件"""
        return self.session.execute(select(File).where(File.path == path)).scalar_one_or_none()

    def get_file_by_id(self, file_id: int) -> File | None:
        """通过 ID 获取文件"""
        return self.session.execute(select(File).where(File.id == file_id)).scalar_one_or_none()

    def list_files(self, limit: int | None = None) -> list[File]:
        """获取文件列表"""
        query = select(File)
        if limit is not None:
            query = query.limit(limit)
        return list(self.session.execute(query).scalars())

    def delete_files(self, file_ids: Iterable[int]) -> None:
        """批量删除文件及其标签关联"""
        file_ids = list(file_ids)
        if not file_ids:
            return
        self.session.execute(delete(FileTag).where(FileTag.file_id.in_(file_ids)))
        self.session.execute(delete(File).where(File.id.in_(file_ids)))

    # ========== 标签操作 ==========

    def list_tags(self) -> list[Tag]:
        """获取所有标签列表"""
        return list(self.session.execute(select(Tag)).scalars())

    def get_tag_by_name(self, name: str) -> Tag | None:
        """通过名称获取标签"""
        return self.session.execute(select(Tag).where(Tag.name == name)).scalar_one_or_none()

    def create_tag(self, spec: TagSpec) -> Tag:
        """创建新标签"""
        tag = Tag(name=spec.name, color=spec.color, description=spec.description)
        self.session.add(tag)
        return tag

    def get_or_create_tag(self, spec: TagSpec) -> Tag:
        """获取或创建标签"""
        existing = self.get_tag_by_name(spec.name)
        if existing is not None:
            return existing
        return self.create_tag(spec)

    def bulk_create_tags(self, specs: Iterable[TagSpec]) -> list[Tag]:
        """批量创建标签
        
        自动去重已存在的标签，返回创建的标签列表。
        
        Args:
            specs: 标签规格迭代器
        
        Returns:
            创建的标签对象列表
        """
        spec_list = list(specs)
        names = [s.name for s in spec_list]
        
        # 查询已存在的标签
        existing = {
            t.name: t
            for t in self.session.execute(
                select(Tag).where(Tag.name.in_(names))
            ).scalars()
        }
        
        created: list[Tag] = []
        for spec in spec_list:
            if spec.name not in existing:
                tag = Tag(name=spec.name, color=spec.color, description=spec.description)
                self.session.add(tag)
                existing[spec.name] = tag
                created.append(tag)
        
        return created

    def get_tags_for_file(self, file_id: int) -> list[Tag]:
        """获取文件关联的所有标签"""
        stmt = (
            select(Tag)
            .join(FileTag, FileTag.tag_id == Tag.id)
            .where(FileTag.file_id == file_id)
        )
        return list(self.session.execute(stmt).scalars())

    def get_tags_by_ids(self, tag_ids: Iterable[int]) -> list[Tag]:
        """通过 ID 批量获取标签"""
        tag_ids = list(tag_ids)
        if not tag_ids:
            return []
        stmt = select(Tag).where(Tag.id.in_(tag_ids))
        return list(self.session.execute(stmt).scalars())

    def get_files_by_ids(self, file_ids: Iterable[int]) -> list[File]:
        """通过 ID 批量获取文件"""
        file_ids = [int(file_id) for file_id in file_ids]
        if not file_ids:
            return []
        stmt = select(File).where(File.id.in_(file_ids))
        return list(self.session.execute(stmt).scalars())

    def delete_tag(self, tag_id: int) -> None:
        """删除标签及其关联"""
        self.session.execute(delete(FileTag).where(FileTag.tag_id == tag_id))
        tag = self.session.execute(select(Tag).where(Tag.id == tag_id)).scalar_one_or_none()
        if tag is not None:
            self.session.delete(tag)

    # ========== 文件-标签关联操作 ==========

    def attach_tags(self, file_row: File, tags: Iterable[Tag]) -> None:
        """为文件添加标签（跳过已存在的）"""
        existing = {tag.id for tag in file_row.tags}
        for tag in tags:
            if tag.id not in existing:
                file_row.tags.append(tag)

    def attach_tags_to_files(
        self, file_ids: Iterable[int], tag_ids: Iterable[int], batch_size: int = DEFAULT_BATCH_SIZE
    ) -> None:
        """批量为多个文件添加标签
        
        Args:
            file_ids: 文件 ID 列表
            tag_ids: 标签 ID 列表
            batch_size: 批次大小
        """
        file_ids = list(file_ids)
        tag_ids = list(tag_ids)
        
        if not file_ids or not tag_ids:
            return
        
        # 获取已存在的关联，避免重复
        existing = {
            (ft.file_id, ft.tag_id)
            for ft in self.session.execute(
                select(FileTag).where(
                    FileTag.file_id.in_(file_ids),
                    FileTag.tag_id.in_(tag_ids),
                )
            ).scalars()
        }
        
        # 批量插入新关联
        new_associations: list[dict] = []
        for file_id in file_ids:
            for tag_id in tag_ids:
                if (file_id, tag_id) not in existing:
                    new_associations.append({"file_id": file_id, "tag_id": tag_id})
                    if len(new_associations) >= batch_size:
                        self.session.execute(FileTag.__table__.insert(), new_associations)
                        new_associations.clear()
        
        if new_associations:
            self.session.execute(FileTag.__table__.insert(), new_associations)

    def detach_all_tags(self, file_row: File) -> None:
        """移除文件的所有标签"""
        file_row.tags.clear()

    def replace_tags(self, file_row: File, tags: Iterable[Tag]) -> None:
        """替换文件的所有标签"""
        file_row.tags = list(tags)

    def remove_tag_from_file(self, file_row: File, tag: Tag) -> None:
        """从文件移除单个标签"""
        if tag in file_row.tags:
            file_row.tags.remove(tag)

    def remove_tags_from_file(self, file_row: File, tags: Iterable[Tag]) -> None:
        """从文件批量移除标签"""
        for tag in tags:
            if tag in file_row.tags:
                file_row.tags.remove(tag)

    # ========== 搜索功能 ==========

    def search(self, query: SearchQuery, limit: int | None = None) -> list[SearchResult]:
        """文件搜索 - 支持多种搜索条件
        
        Args:
            query: 搜索查询对象，包含文本、类型、标签等条件
            limit: 结果数量限制
        
        Returns:
            搜索结果列表
        """
        stmt = select(File)

        # 文本搜索：优先使用 FTS5，回退到 LIKE
        if query.text:
            if self._has_fts5():
                # 使用 FTS5 全文搜索
                fts_ids = self._fts_search(query.text, limit)
                if fts_ids:
                    stmt = stmt.where(File.id.in_(fts_ids))
                else:
                    # FTS 无结果，回退到 LIKE
                    term = f"%{query.text}%"
                    stmt = stmt.where(File.name.ilike(term))
            else:
                # 无 FTS5，使用 LIKE
                term = f"%{query.text}%"
                stmt = stmt.where(File.name.ilike(term))

        # 路径前缀过滤
        if query.root:
            root = query.root.rstrip("/\\") + "%"
            stmt = stmt.where(File.path.like(root))

        # 文件类型过滤
        if query.types:
            stmt = stmt.where(File.type.in_(query.types))

        # 标签过滤
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

        # 排序
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

    def search_by_fts(self, text: str, limit: int | None = None) -> list[SearchResult]:
        """使用 FTS5 全文搜索文件名
        
        支持 FTS5 查询语法：
        - 前缀搜索: report* 
        - 短语搜索: "annual report"
        - 布尔搜索: report AND 2024
        - 排除搜索: report NOT draft
        
        Args:
            text: FTS5 查询文本
            limit: 结果数量限制
        
        Returns:
            搜索结果列表
        """
        file_ids = self._fts_search(text, limit)
        if not file_ids:
            return []
        
        # 按 FTS 结果顺序获取文件
        files = {f.id: f for f in self.get_files_by_ids(file_ids)}
        results: list[SearchResult] = []
        for fid in file_ids:
            if fid in files:
                f = files[fid]
                results.append(
                    SearchResult(
                        file_id=f.id,  # type: ignore[arg-type]
                        path=f.path,  # type: ignore[arg-type]
                        name=f.name,  # type: ignore[arg-type]
                        type=f.type,  # type: ignore[arg-type]
                    )
                )
        return results

    def _fts_search(self, text: str, limit: int | None = None) -> list[int]:
        """内部 FTS5 搜索方法 - 返回文件 ID 列表
        
        Args:
            text: 搜索文本
            limit: 结果数量限制
        
        Returns:
            匹配的文件 ID 列表
        """
        if not self._has_fts5():
            return []
        
        # 转义特殊字符，防止查询错误
        escaped = text.replace("'", "''")
        
        sql = "SELECT rowid FROM files_fts WHERE files_fts MATCH :text ORDER BY rank"
        params: dict[str, object] = {"text": escaped}
        if limit is not None:
            sql += " LIMIT :limit"
            params["limit"] = limit
        
        result = self.session.execute(text(sql), params)
        return [row[0] for row in result]

    def _has_fts5(self) -> bool:
        """检查 FTS5 扩展是否可用"""
        try:
            self.session.execute(text("SELECT 1 FROM files_fts LIMIT 1"))
            return True
        except Exception:
            return False
