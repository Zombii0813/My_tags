from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TagSpec:
    name: str
    color: str | None = None
    description: str | None = None
