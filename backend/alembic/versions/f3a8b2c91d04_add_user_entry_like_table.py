"""add user_entry_like table

Revision ID: f3a8b2c91d04
Revises: d1ca8a5c4aa1
Create Date: 2026-05-26 10:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f3a8b2c91d04"
down_revision: Union[str, None] = "d1ca8a5c4aa1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_entry_like",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("entry_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["entry_id"], ["entry.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("user_id", "entry_id"),
    )


def downgrade() -> None:
    op.drop_table("user_entry_like")
