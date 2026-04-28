"""add trade idempotency key

Revision ID: 20260418_0002
Revises: 20260417_0001
Create Date: 2026-04-18
"""

import sqlalchemy as sa
from alembic import op

revision = "20260418_0002"
down_revision = "20260417_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        try:
            op.add_column("trades", sa.Column("idempotency_key", sa.String(length=64), nullable=True))
        except Exception:
            pass
        try:
            op.create_index("ix_trades_idempotency_key", "trades", ["idempotency_key"], unique=False)
        except Exception:
            pass
        try:
            op.create_unique_constraint(
                "uq_trades_user_idempotency_key",
                "trades",
                ["user_id", "idempotency_key"],
            )
        except Exception:
            pass
    else:
        op.add_column("trades", sa.Column("idempotency_key", sa.String(length=64), nullable=True))
        op.create_index("ix_trades_idempotency_key", "trades", ["idempotency_key"], unique=False)
        op.create_unique_constraint(
            "uq_trades_user_idempotency_key",
            "trades",
            ["user_id", "idempotency_key"],
        )


def downgrade() -> None:
    op.drop_constraint("uq_trades_user_idempotency_key", "trades", type_="unique")
    op.drop_index("ix_trades_idempotency_key", table_name="trades")
    op.drop_column("trades", "idempotency_key")
