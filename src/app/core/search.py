from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class SearchQuery:
    text: str | None = None
    types: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
    match_all_tags: bool = False
    sort_by: str | None = None
    sort_desc: bool = False


@dataclass(frozen=True)
class SearchResult:
    file_id: int
    path: str
    name: str
    type: str


def empty_results() -> Iterable[SearchResult]:
    return []
