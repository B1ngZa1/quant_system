"""数据库会话管理 — PostgreSQL 专用"""
from typing import AsyncGenerator

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import Pool

from app.core.config import settings
from app.core.logging import log

# 创建异步引擎 (PostgreSQL)
engine = create_async_engine(
    settings.postgres_url,
    echo=settings.DEBUG,
    pool_size=settings.POSTGRES_POOL_SIZE,
    max_overflow=settings.POSTGRES_MAX_OVERFLOW,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_timeout=30,
    pool_use_lifo=True,
)


# 连接池诊断事件
@event.listens_for(Pool, "connect")
def _on_connect(dbapi_conn, connection_record):
    connection_record.info["connect_time"] = __import__("time").time()


@event.listens_for(Pool, "checkout")
def _on_checkout(dbapi_conn, connection_record, connection_proxy):
    connect_time = connection_record.info.get("connect_time", 0)
    idle_sec = __import__("time").time() - connect_time if connect_time else 0
    if idle_sec > 300:
        log.debug(f"连接池: 取出闲置 {idle_sec:.0f}s 的连接")


@event.listens_for(Pool, "checkin")
def _on_checkin(dbapi_conn, connection_record):
    connection_record.info["connect_time"] = __import__("time").time()


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


async def check_db_health() -> dict:
    """检查 PostgreSQL 连接健康状态。

    Returns
    -------
    dict : 包含 status, latency_ms, pool_size, checked_out, overflow
    """
    import time
    start = time.monotonic()
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            result.scalar()
        latency = round((time.monotonic() - start) * 1000, 1)
        pool = engine.pool
        return {
            "status": "healthy",
            "latency_ms": latency,
            "pool_size": pool.size(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "checkedin": pool.checkedin(),
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
        }


async def init_db():
    """初始化数据库"""
    from app.db.base import Base
    # 确保所有模型被导入并注册到 Base.metadata，
    # 否则 create_all 可能不会创建 users 等业务表，导致登录/注册报错。
    import app.models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    log.info("数据库初始化完成 (PostgreSQL)")


async def close_db():
    """关闭数据库连接"""
    await engine.dispose()
    log.info("数据库连接已关闭")
