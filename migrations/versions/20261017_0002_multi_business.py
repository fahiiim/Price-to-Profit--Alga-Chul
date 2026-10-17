"""multi-tenant businesses, tagline and per-business document numbers

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-17 11:20:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("business_profiles", schema=None) as batch_op:
        batch_op.add_column(sa.Column("tagline", sa.String(length=160), nullable=True))

    with op.batch_alter_table("activity_log", schema=None) as batch_op:
        batch_op.add_column(sa.Column("business_id", sa.Integer(), nullable=True))
        batch_op.create_index(
            batch_op.f("ix_activity_log_business_id"), ["business_id"], unique=False
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_activity_log_business_id_business_profiles"),
            "business_profiles",
            ["business_id"],
            ["id"],
            ondelete="CASCADE",
        )

    with op.batch_alter_table("quotes", schema=None) as batch_op:
        batch_op.drop_constraint(op.f("uq_quotes_number"), type_="unique")
        batch_op.create_unique_constraint(
            "uq_quotes_business_id_number", ["business_id", "number"]
        )

    with op.batch_alter_table("invoices", schema=None) as batch_op:
        batch_op.drop_constraint(op.f("uq_invoices_number"), type_="unique")
        batch_op.create_unique_constraint(
            "uq_invoices_business_id_number", ["business_id", "number"]
        )


def downgrade() -> None:
    with op.batch_alter_table("invoices", schema=None) as batch_op:
        batch_op.drop_constraint("uq_invoices_business_id_number", type_="unique")
        batch_op.create_unique_constraint("uq_invoices_number", ["number"])

    with op.batch_alter_table("quotes", schema=None) as batch_op:
        batch_op.drop_constraint("uq_quotes_business_id_number", type_="unique")
        batch_op.create_unique_constraint("uq_quotes_number", ["number"])

    with op.batch_alter_table("activity_log", schema=None) as batch_op:
        batch_op.drop_constraint(
            batch_op.f("fk_activity_log_business_id_business_profiles"),
            type_="foreignkey",
        )
        batch_op.drop_index(batch_op.f("ix_activity_log_business_id"))
        batch_op.drop_column("business_id")

    with op.batch_alter_table("business_profiles", schema=None) as batch_op:
        batch_op.drop_column("tagline")
