"""remove redundant MA columns from stock_data

Revision ID: 20260506_0005
Revises: 20260427_0004
Create Date: 2026-05-06
"""

from alembic import op
import sqlalchemy as sa


revision = "20260506_0005"
down_revision = "20260427_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 删除 stock_data 表中冗余的 MA 字段
    # 这些字段与 indicator_daily 表重复，统一由 indicator_daily 表管理
    op.drop_column('stock_data', 'ma5')
    op.drop_column('stock_data', 'ma10')
    op.drop_column('stock_data', 'ma20')
    op.drop_column('stock_data', 'ma60')


def downgrade() -> None:
    # 恢复 stock_data 表中的 MA 字段
    op.add_column('stock_data', sa.Column('ma5', sa.Numeric(precision=20, scale=4), nullable=True))
    op.add_column('stock_data', sa.Column('ma10', sa.Numeric(precision=20, scale=4), nullable=True))
    op.add_column('stock_data', sa.Column('ma20', sa.Numeric(precision=20, scale=4), nullable=True))
    op.add_column('stock_data', sa.Column('ma60', sa.Numeric(precision=20, scale=4), nullable=True))
