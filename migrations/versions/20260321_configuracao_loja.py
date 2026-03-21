"""cria tabela de configuracao da loja

Revision ID: 20260321_configuracao_loja
Revises: 20260308_adiciona_campos_feedback_fiscal
Create Date: 2026-03-21
"""

from alembic import op
import sqlalchemy as sa


revision = "20260321_configuracao_loja"
down_revision = "20260308_adiciona_campos_feedback_fiscal"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "configuracao_loja",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("regime_tributario", sa.String(length=32), nullable=False, server_default="simples_nacional"),
        sa.Column("uf", sa.String(length=2), nullable=False, server_default="SP"),
        sa.Column("margem_minima_percentual", sa.Float(), nullable=False, server_default="0.05"),
        sa.Column("aliquota_impostos_default", sa.Float(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.execute(
        """
        INSERT INTO configuracao_loja (
            regime_tributario,
            uf,
            margem_minima_percentual,
            aliquota_impostos_default
        ) VALUES ('simples_nacional', 'SP', 0.05, NULL)
        """
    )


def downgrade() -> None:
    op.drop_table("configuracao_loja")
