"""add refresh token to auth_sessions

Revision ID: 0005
Revises: 0004
Create Date: 2026-10-28 09:42:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("auth_sessions", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("refresh_token_hash", sa.String(length=64), nullable=True)
        )
        batch_op.create_unique_constraint(
            batch_op.f("uq_auth_sessions_refresh_token_hash"), ["refresh_token_hash"]
        )


def downgrade() -> None:
    with op.batch_alter_table("auth_sessions", schema=None) as batch_op:
        batch_op.drop_constraint(
            batch_op.f("uq_auth_sessions_refresh_token_hash"), type_="unique"
        )
        batch_op.drop_column("refresh_token_hash")
