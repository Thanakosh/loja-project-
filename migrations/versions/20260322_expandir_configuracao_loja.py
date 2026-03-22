"""expande configuracao da loja com dados cadastrais

Revision ID: 20260322_expandir_configuracao_loja
Revises: 20260321_configuracao_loja
Create Date: 2026-03-22
"""

from alembic import op
import sqlalchemy as sa


revision = "20260322_expandir_configuracao_loja"
down_revision = "20260321_configuracao_loja"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("configuracao_loja", sa.Column("cnpj", sa.String(length=14), nullable=True))
    op.add_column("configuracao_loja", sa.Column("razao_social", sa.String(length=160), nullable=True))
    op.add_column("configuracao_loja", sa.Column("nome_fantasia", sa.String(length=160), nullable=True))
    op.add_column("configuracao_loja", sa.Column("logradouro", sa.String(length=160), nullable=True))
    op.add_column("configuracao_loja", sa.Column("numero", sa.String(length=20), nullable=True))
    op.add_column("configuracao_loja", sa.Column("bairro", sa.String(length=100), nullable=True))
    op.add_column("configuracao_loja", sa.Column("municipio", sa.String(length=100), nullable=True))
    op.add_column("configuracao_loja", sa.Column("porte", sa.String(length=8), nullable=True))
    op.add_column("configuracao_loja", sa.Column("inscricao_estadual", sa.String(length=20), nullable=True))
    op.add_column("configuracao_loja", sa.Column("inscricao_municipal", sa.String(length=20), nullable=True))
    op.add_column("configuracao_loja", sa.Column("cep", sa.String(length=8), nullable=True))
    op.add_column("configuracao_loja", sa.Column("pais", sa.String(length=80), nullable=True))
    op.add_column("configuracao_loja", sa.Column("fone", sa.String(length=20), nullable=True))
    op.add_column("configuracao_loja", sa.Column("email", sa.String(length=160), nullable=True))
    op.add_column("configuracao_loja", sa.Column("cnae", sa.String(length=20), nullable=True))
    op.drop_column("configuracao_loja", "aliquota_impostos_default")
    op.drop_column("configuracao_loja", "margem_minima_percentual")


def downgrade() -> None:
    op.add_column("configuracao_loja", sa.Column("margem_minima_percentual", sa.Float(), nullable=False, server_default="0.05"))
    op.add_column("configuracao_loja", sa.Column("aliquota_impostos_default", sa.Float(), nullable=True))
    op.drop_column("configuracao_loja", "cnae")
    op.drop_column("configuracao_loja", "email")
    op.drop_column("configuracao_loja", "fone")
    op.drop_column("configuracao_loja", "pais")
    op.drop_column("configuracao_loja", "cep")
    op.drop_column("configuracao_loja", "inscricao_municipal")
    op.drop_column("configuracao_loja", "inscricao_estadual")
    op.drop_column("configuracao_loja", "porte")
    op.drop_column("configuracao_loja", "municipio")
    op.drop_column("configuracao_loja", "bairro")
    op.drop_column("configuracao_loja", "numero")
    op.drop_column("configuracao_loja", "logradouro")
    op.drop_column("configuracao_loja", "nome_fantasia")
    op.drop_column("configuracao_loja", "razao_social")
    op.drop_column("configuracao_loja", "cnpj")
