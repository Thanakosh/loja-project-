"""Cria tabela politica_desconto_produto para descontos progressivos por volume

Revision ID: 20260303_politica_desconto
Revises: 20260303_pdv_barcode_autorizacao_pdf
Create Date: 2026-03-03
"""

from alembic import op
import sqlalchemy as sa


revision = "20260303_politica_desconto"
down_revision = "20260303_pdv_barcode_autorizacao_pdf"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "politica_desconto_produto",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("produto_id", sa.Integer(), sa.ForeignKey("produto.id"), nullable=False, index=True),
        sa.Column("qtd_minima", sa.Float(), nullable=False, server_default="1"),
        sa.Column("desconto_maximo_percentual", sa.Float(), nullable=False),
        sa.Column("descricao", sa.String(length=120), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("politica_desconto_produto")
