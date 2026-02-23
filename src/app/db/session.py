from __future__ import annotations

from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, declarative_base, sessionmaker

Base = declarative_base()
SessionLocal = sessionmaker(autoflush=False, autocommit=False)
_engine = None
_engine_path: Path | None = None


def init_db(db_path: Path) -> None:
    global _engine, _engine_path
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if _engine is None or _engine_path != db_path:
        _engine = create_engine(
            f"sqlite:///{db_path}", connect_args={"check_same_thread": False}
        )
        SessionLocal.configure(bind=_engine)
        Base.metadata.create_all(bind=_engine)
        _ensure_schema()
        _engine_path = db_path


def _ensure_schema() -> None:
    session = SessionLocal()
    try:
        connection = session.connection()
        connection.execute(text("ALTER TABLE files ADD COLUMN modified_at FLOAT"))
        session.commit()
    except Exception:
        session.rollback()
    finally:
        session.close()


def get_session() -> Session:
    return SessionLocal()
