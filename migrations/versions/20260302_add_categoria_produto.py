"""Adiciona tabela categoria e vínculo de categoria em produto

Revision ID: 20260302_add_categoria_produto
Revises: 20260222_add_ncm_table
Create Date: 2026-03-02

"""

from alembic import op
import sqlalchemy as sa


revision = "20260302_add_categoria_produto"
down_revision = "20260222_add_ncm_table"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "categoria",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.ForeignKeyConstraint(["parent_id"], ["categoria.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_categoria_id"), "categoria", ["id"], unique=False)
    op.create_index(op.f("ix_categoria_nome"), "categoria", ["nome"], unique=False)
    op.create_index(op.f("ix_categoria_parent_id"), "categoria", ["parent_id"], unique=False)

    op.add_column("produto", sa.Column("categoria_id", sa.Integer(), nullable=True))
    op.create_index(op.f("ix_produto_categoria_id"), "produto", ["categoria_id"], unique=False)
    op.create_foreign_key(
        "fk_produto_categoria_id_categoria",
        "produto",
        "categoria",
        ["categoria_id"],
        ["id"],
    )


def downgrade():
    op.drop_constraint("fk_produto_categoria_id_categoria", "produto", type_="foreignkey")
    op.drop_index(op.f("ix_produto_categoria_id"), table_name="produto")
    op.drop_column("produto", "categoria_id")

    op.drop_index(op.f("ix_categoria_parent_id"), table_name="categoria")
    op.drop_index(op.f("ix_categoria_nome"), table_name="categoria")
    op.drop_index(op.f("ix_categoria_id"), table_name="categoria")
    op.drop_table("categoria")
