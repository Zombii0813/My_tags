from __future__ import annotations

from pathlib import Path
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session, declarative_base, sessionmaker
from sqlalchemy.pool import QueuePool

Base = declarative_base()
SessionLocal = sessionmaker(autoflush=False, autocommit=False)
_engine = None
_engine_path: Path | None = None

# 连接池配置常量
POOL_SIZE = 5              # 连接池保持的连接数
MAX_OVERFLOW = 10          # 连接池最大溢出连接数
POOL_TIMEOUT = 30          # 获取连接超时时间（秒）
POOL_RECYCLE = 3600        # 连接回收时间（秒），防止连接过期
BATCH_SIZE = 500           # 批量操作默认批次大小


def init_db(db_path: Path) -> None:
    """初始化数据库连接和表结构
    
    Args:
        db_path: SQLite 数据库文件路径
    """
    global _engine, _engine_path
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    if _engine is None or _engine_path != db_path:
        # 创建带连接池的引擎
        # 使用 QueuePool 实现连接复用，减少连接开销
        _engine = create_engine(
            f"sqlite:///{db_path}",
            connect_args={"check_same_thread": False},
            poolclass=QueuePool,
            pool_size=POOL_SIZE,
            max_overflow=MAX_OVERFLOW,
            pool_timeout=POOL_TIMEOUT,
            pool_recycle=POOL_RECYCLE,
            pool_pre_ping=True,  # 连接前 ping 检测，自动回收失效连接
        )
        SessionLocal.configure(bind=_engine)
        Base.metadata.create_all(bind=_engine)
        _ensure_schema()
        _init_fts5()
        _engine_path = db_path


def _ensure_schema() -> None:
    """确保数据库 schema 兼容性
    
    检查并添加缺失的列（如 modified_at），用于数据库升级。
    """
    session = SessionLocal()
    try:
        connection = session.connection()
        connection.execute(text("ALTER TABLE files ADD COLUMN modified_at FLOAT"))
        session.commit()
    except Exception:
        session.rollback()
    finally:
        session.close()


def _init_fts5() -> None:
    """初始化 FTS5 全文搜索虚拟表
    
    创建与 files 表同步的虚拟表 files_fts，使用 FTS5 扩展
    提供高性能全文搜索能力。
    """
    session = SessionLocal()
    try:
        connection = session.connection()
        
        # 检查 FTS5 扩展是否可用
        try:
            connection.execute(text("SELECT fts5('test')"))
        except Exception:
            # FTS5 不可用，跳过创建
            return
        
        # 创建 FTS5 虚拟表
        connection.execute(text("""
            CREATE VIRTUAL TABLE IF NOT EXISTS files_fts USING fts5(
                name,
                content='files',
                content_rowid='id'
            )
        """))
        
        # 创建触发器保持 FTS 表与 files 表同步
        # 插入触发器
        connection.execute(text("""
            CREATE TRIGGER IF NOT EXISTS files_ai AFTER INSERT ON files BEGIN
                INSERT INTO files_fts(rowid, name) VALUES (new.id, new.name);
            END
        """))
        
        # 删除触发器
        connection.execute(text("""
            CREATE TRIGGER IF NOT EXISTS files_ad AFTER DELETE ON files BEGIN
                INSERT INTO files_fts(files_fts, rowid, name) VALUES ('delete', old.id, old.name);
            END
        """))
        
        # 更新触发器
        connection.execute(text("""
            CREATE TRIGGER IF NOT EXISTS files_au AFTER UPDATE ON files BEGIN
                INSERT INTO files_fts(files_fts, rowid, name) VALUES ('delete', old.id, old.name);
                INSERT INTO files_fts(rowid, name) VALUES (new.id, new.name);
            END
        """))
        
        session.commit()
    except Exception:
        session.rollback()
    finally:
        session.close()


def get_session() -> Session:
    """获取数据库会话
    
    Returns:
        新的数据库 Session 对象
    """
    return SessionLocal()


def get_session_context():
    """获取会话上下文管理器
    
    使用示例:
        with get_session_context() as session:
            repo = Repo(session)
            repo.create_file(...)
    
    Returns:
        上下文管理器，自动处理 commit/rollback
    """
    return SessionContext()


class SessionContext:
    """会话上下文管理器 - 自动管理事务"""
    
    def __enter__(self) -> Session:
        self.session = SessionLocal()
        return self.session
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.session.commit()
        else:
            self.session.rollback()
        self.session.close()


def rebuild_fts_index() -> None:
    """重建 FTS 全文搜索索引
    
    当 FTS 表数据不一致时调用，会清空并重新构建索引。
    """
    session = SessionLocal()
    try:
        connection = session.connection()
        # 重建索引
        connection.execute(text("INSERT INTO files_fts(files_fts) VALUES ('rebuild')"))
        session.commit()
    except Exception:
        session.rollback()
    finally:
        session.close()
