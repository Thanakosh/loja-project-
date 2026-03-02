"""Adiciona campos de precificação avançada em produto

Revision ID: 20260302_precificacao_avancada
Revises: 20260302_unidade_medida_produto
Create Date: 2026-03-02

"""

from alembic import op
import sqlalchemy as sa


revision = "20260302_precificacao_avancada"
down_revision = "20260302_unidade_medida_produto"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("produto", sa.Column("preco_custo", sa.Float(), nullable=True))
    op.add_column("produto", sa.Column("preco_varejo", sa.Float(), nullable=True))
    op.add_column("produto", sa.Column("preco_atacado", sa.Float(), nullable=True))
    op.add_column("produto", sa.Column("qtd_minima_atacado", sa.Float(), nullable=True))


def downgrade():
    op.drop_column("produto", "qtd_minima_atacado")
    op.drop_column("produto", "preco_atacado")
    op.drop_column("produto", "preco_varejo")
    op.drop_column("produto", "preco_custo")
