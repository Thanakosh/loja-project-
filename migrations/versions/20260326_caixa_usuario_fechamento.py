"""adiciona usuario de fechamento ao caixa diario

Revision ID: 20260326_caixa_usuario_fechamento
Revises: 20260326_user_allowed_tabs_admin
Create Date: 2026-03-26 00:00:00.000001
"""

from alembic import op
import sqlalchemy as sa


revision = "20260326_caixa_usuario_fechamento"
down_revision = "20260326_user_allowed_tabs_admin"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("caixa_diario", sa.Column("usuario_fechamento_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_caixa_diario_usuario_fechamento_id",
        "caixa_diario",
        "user",
        ["usuario_fechamento_id"],
        ["id"],
    )
    op.create_index(
        "ix_caixa_diario_usuario_fechamento_id",
        "caixa_diario",
        ["usuario_fechamento_id"],
    )
    op.execute(
        """
        UPDATE caixa_diario
        SET usuario_fechamento_id = usuario_id
        WHERE status = 'fechado' AND usuario_fechamento_id IS NULL
        """
    )


def downgrade() -> None:
    op.drop_index("ix_caixa_diario_usuario_fechamento_id", table_name="caixa_diario")
    op.drop_constraint("fk_caixa_diario_usuario_fechamento_id", "caixa_diario", type_="foreignkey")
    op.drop_column("caixa_diario", "usuario_fechamento_id")
