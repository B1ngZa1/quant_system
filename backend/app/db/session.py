"""数据库会话管理"""
from typing import AsyncGenerator

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.core.logging import log

# 创建异步引擎
db_type = (settings.DATABASE_TYPE or "").strip().lower()
if db_type not in {"postgres", "mysql", "sqlite"}:
    log.warning(f"未知 DATABASE_TYPE={settings.DATABASE_TYPE}，将按 DEBUG 兜底选择数据库")
    db_type = "sqlite" if settings.DEBUG else "postgres"

if db_type == "sqlite":
    database_url = settings.SQLITE_URL
elif db_type == "postgres":
    database_url = settings.postgres_url
else:
    database_url = settings.mysql_url

engine_kwargs = {"echo": settings.DEBUG}
if database_url.startswith("sqlite"):
    engine_kwargs["poolclass"] = NullPool
else:
    pool_size = settings.POSTGRES_POOL_SIZE if db_type == "postgres" else settings.MYSQL_POOL_SIZE
    max_overflow = settings.POSTGRES_MAX_OVERFLOW if db_type == "postgres" else settings.MYSQL_MAX_OVERFLOW
    engine_kwargs.update(
        {
            "pool_size": pool_size,
            "max_overflow": max_overflow,
            "pool_pre_ping": True,
            "pool_recycle": 3600,
            "pool_timeout": 30,
            "pool_use_lifo": True,  # 使用LIFO提高缓存命中率
        }
    )

engine = create_async_engine(database_url, **engine_kwargs)

# SQLite 性能优化：WAL 模式 + 同步级别 + 外键约束
if database_url.startswith("sqlite"):

    @event.listens_for(engine.sync_engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA cache_size=-64000")  # 64MB
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.execute("PRAGMA mmap_size=268435456")  # 256MB
        cursor.close()

# 创建异步会话工厂
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            log.error(f"数据库操作错误: {e}")
            raise
        finally:
            await session.close()


async def init_db():
    """初始化数据库"""
    from app.db.base import Base
    # 确保所有模型被导入并注册到 Base.metadata，
    # 否则 create_all 可能不会创建 users 等业务表，导致登录/注册报错。
    import app.models  # noqa: F401
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    log.info("数据库初始化完成")


async def close_db():
    """关闭数据库连接"""
    await engine.dispose()
    log.info("数据库连接已关闭")
