"""convert other timeseries tables to hypertables

Revision ID: 20260506_0007
Revises: 20260506_0006
Create Date: 2026-05-06
"""

from alembic import op
import sqlalchemy as sa


revision = "20260506_0007"
down_revision = "20260506_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 仅针对 PostgreSQL
    bind = op.get_bind()
    if bind.engine.name != 'postgresql':
        return

    # 开启 TimescaleDB 插件（如果尚未开启）
    op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;")

    # 转换 index_data 表为 Hypertable
    try:
        # 移除原有的唯一约束
        op.drop_index('ix_index_data_symbol_date', table_name='index_data')
    except Exception:
        pass

    # 重新创建包含分区键的复合索引
    op.create_index('ix_index_data_symbol_date', 'index_data', ['symbol', 'trade_date'], unique=True)

    # 调整主键
    try:
        op.drop_constraint('index_data_pkey', 'index_data', type_='primary')
    except Exception:
        pass
    try:
        op.create_primary_key('index_data_pkey', 'index_data', ['id', 'trade_date'])
    except Exception:
        pass

    # 转换为 hypertable
    op.execute("SELECT create_hypertable('index_data', 'trade_date', if_not_exists => TRUE, migrate_data => TRUE);")

    # 转换 industry_data 表为 Hypertable
    try:
        op.drop_index('ix_industry_data_code_date', table_name='industry_data')
    except Exception:
        pass

    op.create_index('ix_industry_data_code_date', 'industry_data', ['industry_code', 'trade_date'], unique=True)

    try:
        op.drop_constraint('industry_data_pkey', 'industry_data', type_='primary')
    except Exception:
        pass
    try:
        op.create_primary_key('industry_data_pkey', 'industry_data', ['id', 'trade_date'])
    except Exception:
        pass

    op.execute("SELECT create_hypertable('industry_data', 'trade_date', if_not_exists => TRUE, migrate_data => TRUE);")

    # 转换 indicator_daily 表为 Hypertable
    try:
        op.drop_index('ix_indicator_daily_symbol_date', table_name='indicator_daily')
    except Exception:
        pass

    op.create_index('ix_indicator_daily_symbol_date', 'indicator_daily', ['symbol', 'trade_date'], unique=True)

    try:
        op.drop_constraint('indicator_daily_pkey', 'indicator_daily', type_='primary')
    except Exception:
        pass
    try:
        op.create_primary_key('indicator_daily_pkey', 'indicator_daily', ['id', 'trade_date'])
    except Exception:
        pass

    op.execute("SELECT create_hypertable('indicator_daily', 'trade_date', if_not_exists => TRUE, migrate_data => TRUE);")

    # 转换 fund_flow 表为 Hypertable
    try:
        op.drop_index('ix_fund_flow_symbol_date', table_name='fund_flow')
    except Exception:
        pass

    op.create_index('ix_fund_flow_symbol_date', 'fund_flow', ['symbol', 'trade_date'], unique=True)

    try:
        op.drop_constraint('fund_flow_pkey', 'fund_flow', type_='primary')
    except Exception:
        pass
    try:
        op.create_primary_key('fund_flow_pkey', 'fund_flow', ['id', 'trade_date'])
    except Exception:
        pass

    op.execute("SELECT create_hypertable('fund_flow', 'trade_date', if_not_exists => TRUE, migrate_data => TRUE);")

    # 转换 market_sentiment 表为 Hypertable
    try:
        op.drop_index('ix_market_sentiment_trade_date', table_name='market_sentiment')
    except Exception:
        pass

    op.create_index('ix_market_sentiment_trade_date', 'market_sentiment', ['trade_date'], unique=True)

    try:
        op.drop_constraint('market_sentiment_pkey', 'market_sentiment', type_='primary')
    except Exception:
        pass
    try:
        op.create_primary_key('market_sentiment_pkey', 'market_sentiment', ['id', 'trade_date'])
    except Exception:
        pass

    op.execute("SELECT create_hypertable('market_sentiment', 'trade_date', if_not_exists => TRUE, migrate_data => TRUE);")


def downgrade() -> None:
    # 仅针对 PostgreSQL
    bind = op.get_bind()
    if bind.engine.name != 'postgresql':
        return

    # 注意：TimescaleDB 不支持直接将 hypertable 转换回普通表
    # 这里只是移除 hypertable 相关的约束，实际的 hypertable 转换无法回滚
    # 如果需要回滚，需要手动处理

    # 恢复 market_sentiment 表的主键
    try:
        op.drop_constraint('market_sentiment_pkey', 'market_sentiment', type_='primary')
        op.create_primary_key('market_sentiment_pkey', 'market_sentiment', ['id'])
    except Exception:
        pass

    # 恢复 fund_flow 表的主键
    try:
        op.drop_constraint('fund_flow_pkey', 'fund_flow', type_='primary')
        op.create_primary_key('fund_flow_pkey', 'fund_flow', ['id'])
    except Exception:
        pass

    # 恢复 indicator_daily 表的主键
    try:
        op.drop_constraint('indicator_daily_pkey', 'indicator_daily', type_='primary')
        op.create_primary_key('indicator_daily_pkey', 'indicator_daily', ['id'])
    except Exception:
        pass

    # 恢复 industry_data 表的主键
    try:
        op.drop_constraint('industry_data_pkey', 'industry_data', type_='primary')
        op.create_primary_key('industry_data_pkey', 'industry_data', ['id'])
    except Exception:
        pass

    # 恢复 index_data 表的主键
    try:
        op.drop_constraint('index_data_pkey', 'index_data', type_='primary')
        op.create_primary_key('index_data_pkey', 'index_data', ['id'])
    except Exception:
        pass
