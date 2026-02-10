from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv


@dataclass(frozen=True)
class AppConfig:
    data_dir: Path
    db_path: Path
    thumbs_dir: Path
    default_workspace: Path | None


def _env_path(name: str) -> Path | None:
    value = os.getenv(name)
    if not value:
        return None
    return Path(value).expanduser().resolve()


def load_config() -> AppConfig:
    load_dotenv()
    base_dir = _env_path("MYTAGS_DATA_DIR")
    if base_dir is None:
        base_dir = Path.home() / ".mytags"

    db_path = _env_path("MYTAGS_DB_PATH")
    if db_path is None:
        db_path = base_dir / "mytags.db"

    thumbs_dir = _env_path("MYTAGS_THUMBS_DIR")
    if thumbs_dir is None:
        thumbs_dir = base_dir / "thumbs"

    default_workspace = _env_path("MYTAGS_WORKSPACE")

    return AppConfig(
        data_dir=base_dir,
        db_path=db_path,
        thumbs_dir=thumbs_dir,
        default_workspace=default_workspace,
    )
