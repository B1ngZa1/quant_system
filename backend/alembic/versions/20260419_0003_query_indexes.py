"""composite indexes for list queries and realtime freshness

Revision ID: 20260419_0003
Revises: 20260418_0002
Create Date: 2026-04-19
"""

from alembic import op

revision = "20260419_0003"
down_revision = "20260418_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    try:
        op.create_index(
            "ix_strategies_user_id_updated_at",
            "strategies",
            ["user_id", "updated_at"],
            unique=False,
        )
    except Exception:
        pass
    try:
        op.create_index(
            "ix_backtests_user_id_created_at",
            "backtests",
            ["user_id", "created_at"],
            unique=False,
        )
    except Exception:
        pass
    try:
        op.create_index(
            "ix_backtests_user_id_strategy_id",
            "backtests",
            ["user_id", "strategy_id"],
            unique=False,
        )
    except Exception:
        pass
    try:
        op.create_index(
            "ix_trades_user_id_created_at",
            "trades",
            ["user_id", "created_at"],
            unique=False,
        )
    except Exception:
        pass
    try:
        op.create_index(
            "ix_stock_realtime_update_time",
            "stock_realtime",
            ["update_time"],
            unique=False,
        )
    except Exception:
        pass


def downgrade() -> None:
    op.drop_index("ix_stock_realtime_update_time", table_name="stock_realtime")
    op.drop_index("ix_trades_user_id_created_at", table_name="trades")
    op.drop_index("ix_backtests_user_id_strategy_id", table_name="backtests")
    op.drop_index("ix_backtests_user_id_created_at", table_name="backtests")
    op.drop_index("ix_strategies_user_id_updated_at", table_name="strategies")
