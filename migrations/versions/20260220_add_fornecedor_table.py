"""adiciona tabela fornecedor e relacionamento opcional em produto

Revision ID: 20260220_add_fornecedor_table
Revises: refactor_estoque_v2
Create Date: 2026-02-20

"""

from alembic import op
import sqlalchemy as sa


revision = "20260220_add_fornecedor_table"
down_revision = "refactor_estoque_v2"
branch_labels = None
depends_on = "refactor_estoque_v2"


def upgrade():
    op.create_table(
        "fornecedor",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("razao_social", sa.String(length=120), nullable=False),
        sa.Column("nome_fantasia", sa.String(length=80), nullable=True),
        sa.Column("cnpj", sa.String(length=18), nullable=False),
        sa.Column("telefone", sa.String(length=20), nullable=True),
        sa.Column("email", sa.String(length=120), nullable=True),
        sa.Column("endereco", sa.String(length=120), nullable=True),
        sa.Column("cidade", sa.String(length=60), nullable=True),
        sa.Column("uf", sa.String(length=2), nullable=True),
        sa.Column("cep", sa.String(length=10), nullable=True),
        sa.Column("prazo_pagamento_dias", sa.Integer(), nullable=True, server_default="30"),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("criado_em", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("atualizado_em", sa.DateTime(), nullable=True, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_fornecedor_id", "fornecedor", ["id"], unique=False)
    op.create_index("ix_fornecedor_razao_social", "fornecedor", ["razao_social"], unique=False)
    op.create_index("ix_fornecedor_cnpj", "fornecedor", ["cnpj"], unique=True)

    op.add_column("produto", sa.Column("fornecedor_id", sa.Integer(), nullable=True))
    op.create_index("ix_produto_fornecedor_id", "produto", ["fornecedor_id"], unique=False)
    op.create_foreign_key(
        "fk_produto_fornecedor_id_fornecedor",
        "produto",
        "fornecedor",
        ["fornecedor_id"],
        ["id"],
    )


def downgrade():
    op.drop_constraint("fk_produto_fornecedor_id_fornecedor", "produto", type_="foreignkey")
    op.drop_index("ix_produto_fornecedor_id", table_name="produto")
    op.drop_column("produto", "fornecedor_id")

    op.drop_index("ix_fornecedor_cnpj", table_name="fornecedor")
    op.drop_index("ix_fornecedor_razao_social", table_name="fornecedor")
    op.drop_index("ix_fornecedor_id", table_name="fornecedor")
    op.drop_table("fornecedor")
