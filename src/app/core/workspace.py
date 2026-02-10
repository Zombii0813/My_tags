from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Workspace:
    root: Path

    def normalize(self) -> "Workspace":
        return Workspace(root=self.root.expanduser().resolve())
