from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class SearchQuery:
    """搜索查询对象 - 支持多种搜索条件组合
    
    Attributes:
        text: 搜索文本，支持通配符和 FTS5 语法
        root: 限制搜索路径前缀
        types: 文件类型元组，如 ('image', 'video')
        tags: 标签名称元组
        match_all_tags: 是否要求匹配所有标签（默认 OR）
        sort_by: 排序字段 ('name', 'size', 'type', 'created_at', 'updated_at', 'modified_at')
        sort_desc: 是否降序
        use_fts: 是否使用 FTS5 全文搜索（优先级高于 LIKE）
    """
    text: str | None = None
    root: str | None = None
    types: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
    match_all_tags: bool = False
    sort_by: str | None = None
    sort_desc: bool = False
    use_fts: bool = True  # 默认启用 FTS5


@dataclass(frozen=True)
class SearchResult:
    """搜索结果对象"""
    file_id: int
    path: str
    name: str
    type: str


def empty_results() -> Iterable[SearchResult]:
    """返回空结果迭代器"""
    return []
