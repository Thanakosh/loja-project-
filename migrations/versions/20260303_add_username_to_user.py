"""add_username_to_user

Revision ID: 20260303_add_username_to_user
Revises: 20260302_precificacao_avancada
Create Date: 2026-03-03
"""
from alembic import op
import sqlalchemy as sa

revision = "20260303_add_username_to_user"
down_revision = "20260302_precificacao_avancada"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "user",
        sa.Column("username", sa.String(), nullable=True),
    )
    op.create_index(op.f("ix_user_username"), "user", ["username"], unique=True)


def downgrade():
    op.drop_index(op.f("ix_user_username"), table_name="user")
    op.drop_column("user", "username")
