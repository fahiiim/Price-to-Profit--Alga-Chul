"""password hashes and registration OTP

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-17 12:40:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # SQLite refuses NOT NULL columns without a default when the table
    # already has rows (accounts created before passwords existed).
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "password_hash",
                sa.String(length=255),
                nullable=False,
                server_default="invalid",
            )
        )
        batch_op.add_column(
            sa.Column("email_verified_at", sa.DateTime(), nullable=True)
        )
        batch_op.add_column(sa.Column("otp_hash", sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column("otp_expires_at", sa.DateTime(), nullable=True))
        batch_op.add_column(
            sa.Column("otp_attempts", sa.Integer(), nullable=False, server_default="0")
        )


def downgrade() -> None:
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("otp_attempts")
        batch_op.drop_column("otp_expires_at")
        batch_op.drop_column("otp_hash")
        batch_op.drop_column("email_verified_at")
        batch_op.drop_column("password_hash")
