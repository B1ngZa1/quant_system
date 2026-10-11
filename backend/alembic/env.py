"""Alembic 环境配置 — PostgreSQL 专用"""
import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# 导入应用配置和模型
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.db.base import Base
from app.models import *  # 导入所有模型

# this is the Alembic Config object
config = context.config

# 设置数据库URL：优先环境变量，其次使用 PostgreSQL
database_url = os.getenv("DATABASE_URL") or settings.sync_postgres_url
config.set_main_option("sqlalchemy.url", database_url)

# 解释配置文件中的Python日志配置
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 添加模型的MetaData对象
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """在离线模式下运行迁移"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """在在线模式下运行迁移"""
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = database_url

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        do_run_migrations(connection)


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
