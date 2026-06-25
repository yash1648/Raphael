"""update task model with description, updated_at, integer priority

Revision ID: b8c2d3e4f5g6
Revises: a5fc1c66dc24
Create Date: 2026-06-26 02:30:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b8c2d3e4f5g6"
down_revision: Union[str, None] = "a5fc1c66dc24"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("tasks") as batch_op:
        batch_op.add_column(sa.Column("description", sa.Text(), server_default="", nullable=False))
        batch_op.add_column(sa.Column("updated_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False))
        batch_op.alter_column("priority", type_=sa.Integer(), existing_type=sa.String(), nullable=False, server_default="0")
        batch_op.alter_column("status", type_=sa.String(), existing_type=sa.String(), nullable=False, server_default="todo")


def downgrade() -> None:
    with op.batch_alter_table("tasks") as batch_op:
        batch_op.drop_column("updated_at")
        batch_op.drop_column("description")
        batch_op.alter_column("priority", type_=sa.String(), existing_type=sa.Integer(), nullable=False, server_default="medium")
        batch_op.alter_column("status", type_=sa.String(), existing_type=sa.String(), nullable=False, server_default="pending")
