"""Adiciona codigo_barras em produto, observacoes de cliente e snapshot de autorizacao na venda

Revision ID: 20260303_pdv_barcode_autorizacao_pdf
Revises: 20260303_caixa_diario
Create Date: 2026-03-03
"""

from alembic import op
import sqlalchemy as sa


revision = "20260303_pdv_barcode_autorizacao_pdf"
down_revision = "20260303_caixa_diario"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("produto", sa.Column("codigo_barras", sa.String(length=32), nullable=True))
    op.create_index("ix_produto_codigo_barras", "produto", ["codigo_barras"], unique=True)

    op.add_column("cliente", sa.Column("email", sa.String(length=120), nullable=True))
    op.add_column("cliente", sa.Column("observacao", sa.String(length=255), nullable=True))
    op.add_column("cliente", sa.Column("historico_observacoes", sa.Text(), nullable=True))

    op.add_column("venda", sa.Column("autorizacao_terceiro_nome", sa.String(length=120), nullable=True))
    op.add_column("venda", sa.Column("autorizacao_terceiro_documento", sa.String(length=30), nullable=True))
    op.add_column("venda", sa.Column("autorizacao_terceiro_observacao", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("venda", "autorizacao_terceiro_observacao")
    op.drop_column("venda", "autorizacao_terceiro_documento")
    op.drop_column("venda", "autorizacao_terceiro_nome")

    op.drop_column("cliente", "historico_observacoes")
    op.drop_column("cliente", "observacao")
    op.drop_column("cliente", "email")

    op.drop_index("ix_produto_codigo_barras", table_name="produto")
    op.drop_column("produto", "codigo_barras")
