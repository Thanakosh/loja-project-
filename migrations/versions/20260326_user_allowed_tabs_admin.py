"""adiciona permissoes por aba em usuarios

Revision ID: 20260326_user_allowed_tabs_admin
Revises: 20260322_expandir_configuracao_loja
Create Date: 2026-03-26 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260326_user_allowed_tabs_admin"
down_revision = "20260322_expandir_configuracao_loja"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "user",
        sa.Column("allowed_tabs", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
    )


def downgrade() -> None:
    op.drop_column("user", "allowed_tabs")
