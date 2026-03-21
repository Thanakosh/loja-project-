"""cria tabela configuracao_loja

Revision ID: 20260321_configuracao_loja
Revises: 20260308_adiciona_campos_feedback_fiscal
Create Date: 2026-03-21
"""

import sqlalchemy as sa
from alembic import op

revision = "20260321_configuracao_loja"
down_revision = "20260308_adiciona_campos_feedback_fiscal"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "configuracao_loja",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "regime_tributario",
            sa.String(20),
            nullable=False,
            server_default="simples_nacional",
            comment="simples_nacional | regime_normal",
        ),
        sa.Column(
            "uf",
            sa.String(2),
            nullable=False,
            server_default="SP",
            comment="Sigla do estado (ex: SP, RJ, MG)",
        ),
        sa.Column(
            "margem_minima_percentual",
            sa.Float(),
            nullable=False,
            server_default="0.05",
            comment="Margem mínima para cálculo de preço mínimo",
        ),
        sa.Column(
            "aliquota_impostos_default",
            sa.Float(),
            nullable=True,
            comment="Alíquota padrão de impostos",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("configuracao_loja")
