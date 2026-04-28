"""add kline sync state and hypertable

Revision ID: 20260427_0004
Revises: 20260419_0003
Create Date: 2026-04-27
"""

from alembic import op
import sqlalchemy as sa


revision = "20260427_0004"
down_revision = "20260419_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 0. 补充缺失的表结构修改 (股票表预加载字段、指标表、配置表)
    op.create_table(
        'preload_config',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('markets_csv', sa.String(length=64), nullable=True),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='1'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'indicator_daily',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('trade_date', sa.Date(), nullable=False),
        sa.Column('ma5', sa.Numeric(precision=20, scale=4), nullable=True),
        sa.Column('ma10', sa.Numeric(precision=20, scale=4), nullable=True),
        sa.Column('ma20', sa.Numeric(precision=20, scale=4), nullable=True),
        sa.Column('ma60', sa.Numeric(precision=20, scale=4), nullable=True),
        sa.Column('macd_dif', sa.Numeric(precision=20, scale=4), nullable=True),
        sa.Column('macd_dea', sa.Numeric(precision=20, scale=4), nullable=True),
        sa.Column('macd_hist', sa.Numeric(precision=20, scale=4), nullable=True),
        sa.Column('rsi6', sa.Numeric(precision=20, scale=4), nullable=True),
        sa.Column('rsi12', sa.Numeric(precision=20, scale=4), nullable=True),
        sa.Column('rsi24', sa.Numeric(precision=20, scale=4), nullable=True),
        sa.Column('boll_upper', sa.Numeric(precision=20, scale=4), nullable=True),
        sa.Column('boll_mid', sa.Numeric(precision=20, scale=4), nullable=True),
        sa.Column('boll_lower', sa.Numeric(precision=20, scale=4), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_indicator_daily_symbol_date', 'indicator_daily', ['symbol', 'trade_date'], unique=True)

    op.add_column('stock_basics', sa.Column('board', sa.String(length=16), nullable=True))
    op.add_column('stock_basics', sa.Column('delisted', sa.Boolean(), nullable=False, server_default='0'))
    op.add_column('stock_basics', sa.Column('enabled_for_preload', sa.Boolean(), nullable=False, server_default='1'))
    op.add_column('stock_basics', sa.Column('last_refreshed_at', sa.DateTime(), nullable=True))

    op.add_column('strategies', sa.Column('built_in', sa.Boolean(), nullable=False, server_default='0'))

    # 1. 创建 kline_sync_state 表
    op.create_table(
        'kline_sync_state',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('market', sa.String(length=10), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('period', sa.String(length=16), nullable=False),
        sa.Column('last_synced_ts', sa.DateTime(), nullable=True),
        sa.Column('last_attempt_ts', sa.DateTime(), nullable=True),
        sa.Column('last_error', sa.String(length=512), nullable=True),
        sa.Column('consecutive_failures', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('rows_total', sa.BigInteger(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_kline_sync_state_attempt', 'kline_sync_state', ['last_attempt_ts'], unique=False)
    op.create_index('ix_kline_sync_state_market_symbol_period', 'kline_sync_state', ['market', 'symbol', 'period'], unique=True)

    # 2. 将 stock_data 改造为 Hypertable (仅针对 PostgreSQL)
    bind = op.get_bind()
    if bind.engine.name == 'postgresql':
        # TimescaleDB 要求分区键(trade_date)必须是唯一约束/主键的一部分。
        # 移除原有的唯一约束
        try:
            op.drop_index('ix_stock_data_symbol_date', table_name='stock_data')
        except Exception:
            pass
        
        # 重新创建包含分区键的复合索引
        op.create_index('ix_stock_data_symbol_date', 'stock_data', ['symbol', 'trade_date'], unique=True)

        # 调整主键（如果当前是由 id 组成，需要删除并重建包含 trade_date 的联合主键）
        # 这里为了简化，我们仅要求 create_hypertable 可以执行，并在创建时跳过默认约束检查。
        # 注意: 转换为 hypertable 时，表可能为空。如果是新创建的数据库，表可能刚刚被 init_schema 创建。
        
        # 开启 TimescaleDB 插件（如果尚未开启）
        op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;")
        
        # 为了能够成为超表，需要去掉 id 上的主键约束，改为复合主键
        try:
            op.drop_constraint('stock_data_pkey', 'stock_data', type_='primary')
        except Exception:
            pass
        try:
            op.create_primary_key('stock_data_pkey', 'stock_data', ['id', 'trade_date'])
        except Exception:
            pass

        # 转换为 hypertable
        op.execute("SELECT create_hypertable('stock_data', 'trade_date', if_not_exists => TRUE, migrate_data => TRUE);")


def downgrade() -> None:
    # 回退 kline_sync_state
    op.drop_index('ix_kline_sync_state_market_symbol_period', table_name='kline_sync_state')
    op.drop_index('ix_kline_sync_state_attempt', table_name='kline_sync_state')
    op.drop_table('kline_sync_state')
    
    op.drop_column('strategies', 'built_in')
    op.drop_column('stock_basics', 'last_refreshed_at')
    op.drop_column('stock_basics', 'enabled_for_preload')
    op.drop_column('stock_basics', 'delisted')
    op.drop_column('stock_basics', 'board')

    op.drop_index('ix_indicator_daily_symbol_date', table_name='indicator_daily')
    op.drop_table('indicator_daily')
    op.drop_table('preload_config')

    # 恢复主键（忽略 hypertable 还原，因为不支持自动 reverse create_hypertable）
    bind = op.get_bind()
    if bind.engine.name == 'postgresql':
        try:
            op.drop_constraint('stock_data_pkey', 'stock_data', type_='primary')
            op.create_primary_key('stock_data_pkey', 'stock_data', ['id'])
        except Exception:
            pass
