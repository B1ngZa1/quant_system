"""initial schema

Revision ID: 20260417_0001
Revises:
Create Date: 2026-04-17 23:03:00
"""

from alembic import op

revision = "20260417_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create all ORM tables in first migration."""
    from app.db.base import Base
    from app import models  # noqa: F401

    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    """Drop all ORM tables in reverse dependency order."""
    from app.db.base import Base
    from app import models  # noqa: F401

    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
