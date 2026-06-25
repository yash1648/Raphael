"""add goal, actions_taken, unresolved_items to sessions

Revision ID: c7d8e9f0a1b2
Revises: b8c2d3e4f5g6
Create Date: 2026-06-26 02:45:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c7d8e9f0a1b2"
down_revision: Union[str, None] = "b8c2d3e4f5g6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("sessions") as batch_op:
        batch_op.add_column(sa.Column("goal", sa.Text(), server_default="", nullable=False))
        batch_op.add_column(sa.Column("actions_taken", sa.Text(), server_default="", nullable=False))
        batch_op.add_column(sa.Column("unresolved_items", sa.Text(), server_default="", nullable=False))


def downgrade() -> None:
    with op.batch_alter_table("sessions") as batch_op:
        batch_op.drop_column("unresolved_items")
        batch_op.drop_column("actions_taken")
        batch_op.drop_column("goal")
