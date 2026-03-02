"""Adiciona unidade_medida em produto e permite quantidade fracionada em estoque

Revision ID: 20260302_unidade_medida_produto
Revises: 20260302_add_categoria_produto
Create Date: 2026-03-02

"""

from alembic import op
import sqlalchemy as sa


revision = "20260302_unidade_medida_produto"
down_revision = "20260302_add_categoria_produto"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "produto",
        sa.Column("unidade_medida", sa.String(length=10), nullable=False, server_default="UN"),
    )

    op.execute("UPDATE produto SET unidade_medida = COALESCE(NULLIF(UPPER(unidade), ''), 'UN')")

    with op.batch_alter_table("transacao_estoque") as batch_op:
        batch_op.alter_column(
            "quantidade",
            existing_type=sa.Integer(),
            type_=sa.Float(),
            existing_nullable=False,
        )


def downgrade():
    with op.batch_alter_table("transacao_estoque") as batch_op:
        batch_op.alter_column(
            "quantidade",
            existing_type=sa.Float(),
            type_=sa.Integer(),
            existing_nullable=False,
        )

    op.drop_column("produto", "unidade_medida")
