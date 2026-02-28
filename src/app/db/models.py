from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Index, Integer, Text
from sqlalchemy.orm import relationship

from .session import Base


class File(Base):
    """文件模型 - 存储文件元数据"""

    __tablename__ = "files"

    id = Column(Integer, primary_key=True)
    path = Column(Text, unique=True, nullable=False)
    name = Column(Text, nullable=False)
    ext = Column(Text, nullable=True)
    size = Column(Integer, nullable=False, default=0)
    type = Column(Text, nullable=False)
    hash = Column(Text, nullable=True)
    modified_at = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    tags = relationship("Tag", secondary="file_tags", back_populates="files")

    # 数据库索引优化 - 提升常用查询字段的检索性能
    __table_args__ = (
        Index("idx_files_type", "type"),  # 按文件类型筛选
        Index("idx_files_name", "name"),  # 按文件名搜索
        Index("idx_files_path", "path"),  # 按路径查找
        Index("idx_files_modified_at", "modified_at"),  # 按修改时间排序
    )


class Tag(Base):
    """标签模型 - 存储标签信息"""

    __tablename__ = "tags"

    id = Column(Integer, primary_key=True)
    name = Column(Text, unique=True, nullable=False)
    color = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    files = relationship("File", secondary="file_tags", back_populates="tags")


class FileTag(Base):
    """文件-标签关联表 - 多对多关系"""

    __tablename__ = "file_tags"

    file_id = Column(Integer, ForeignKey("files.id"), primary_key=True)
    tag_id = Column(Integer, ForeignKey("tags.id"), primary_key=True)

    # 索引优化 - 加速标签关联查询
    __table_args__ = (
        Index("idx_file_tags_tag_id", "tag_id"),
        Index("idx_file_tags_file_id", "file_id"),
    )


class FileSearch(Base):
    """FTS5 全文搜索虚拟表 - 用于高性能文件名搜索
    
    使用 SQLite FTS5 扩展提供全文搜索能力，支持：
    - 前缀搜索: name:'report*'
    - 短语搜索: name:'"annual report"'
    - 布尔搜索: name:'report AND 2024'
    
    注意：FTS 表的同步由数据库触发器自动维护，不需要 ORM 干预。
    """

    __tablename__ = "files_fts"

    # FTS5 虚拟表通过 raw SQL 创建，这里仅用于 ORM 映射
    rowid = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
