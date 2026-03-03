"""Adiciona campos de auditoria de desconto em venda_item

Revision ID: 20260303_desconto_auditoria
Revises: 20260303_autorizacao_snapshot
Create Date: 2026-03-03
"""

from alembic import op
import sqlalchemy as sa

revision = "20260303_desconto_auditoria"
down_revision = "20260303_autorizacao_snapshot"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("venda_item", sa.Column("desconto_motivo", sa.String(length=255), nullable=True))
    op.add_column("venda_item", sa.Column("desconto_autorizado_por", sa.String(length=120), nullable=True))


def downgrade() -> None:
    op.drop_column("venda_item", "desconto_autorizado_por")
    op.drop_column("venda_item", "desconto_motivo")
