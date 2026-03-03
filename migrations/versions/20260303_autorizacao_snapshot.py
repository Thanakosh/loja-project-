"""Adiciona historico de autorizacoes em cliente e snapshot de autorizacao em contas a receber

Revision ID: 20260303_autorizacao_snapshot
Revises: 20260303_politica_desconto
Create Date: 2026-03-03
"""

from alembic import op
import sqlalchemy as sa


revision = "20260303_autorizacao_snapshot"
down_revision = "20260303_politica_desconto"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("cliente", sa.Column("historico_autorizacoes", sa.Text(), nullable=True))
    op.add_column("conta_receber", sa.Column("autorizacao_nome", sa.String(length=120), nullable=True))
    op.add_column("conta_receber", sa.Column("autorizacao_documento", sa.String(length=30), nullable=True))
    op.add_column("conta_receber", sa.Column("autorizacao_observacao", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("conta_receber", "autorizacao_observacao")
    op.drop_column("conta_receber", "autorizacao_documento")
    op.drop_column("conta_receber", "autorizacao_nome")
    op.drop_column("cliente", "historico_autorizacoes")
