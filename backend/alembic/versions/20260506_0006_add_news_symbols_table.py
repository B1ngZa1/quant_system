"""add news_symbols table for efficient symbol-based news queries

Revision ID: 20260506_0006
Revises: 20260506_0005
Create Date: 2026-05-06
"""

from alembic import op
import sqlalchemy as sa


revision = "20260506_0006"
down_revision = "20260506_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 创建 news_symbols 关联表
    op.create_table(
        'news_symbols',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('news_id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    # 创建索引
    op.create_index('ix_news_symbols_news_id_symbol', 'news_symbols', ['news_id', 'symbol'], unique=True)
    op.create_index('ix_news_symbols_symbol', 'news_symbols', ['symbol'], unique=False)


def downgrade() -> None:
    # 删除索引和表
    op.drop_index('ix_news_symbols_symbol', table_name='news_symbols')
    op.drop_index('ix_news_symbols_news_id_symbol', table_name='news_symbols')
    op.drop_table('news_symbols')
