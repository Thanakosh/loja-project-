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
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    dialect = bind.dialect.name

    if not inspector.has_table("categoria"):
        op.create_table(
            "categoria",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("nome", sa.String(), nullable=False),
            sa.Column("parent_id", sa.Integer(), nullable=True),
            sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.ForeignKeyConstraint(["parent_id"], ["categoria.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
        )

    categoria_indexes = {index["name"] for index in inspector.get_indexes("categoria")}
    if op.f("ix_categoria_id") not in categoria_indexes:
        op.create_index(op.f("ix_categoria_id"), "categoria", ["id"], unique=False)
    if op.f("ix_categoria_nome") not in categoria_indexes:
        op.create_index(op.f("ix_categoria_nome"), "categoria", ["nome"], unique=False)
    if op.f("ix_categoria_parent_id") not in categoria_indexes:
        op.create_index(op.f("ix_categoria_parent_id"), "categoria", ["parent_id"], unique=False)

    produto_columns = {column["name"] for column in inspector.get_columns("produto")}
    if "categoria_id" not in produto_columns:
        op.add_column("produto", sa.Column("categoria_id", sa.Integer(), nullable=True))

    produto_indexes = {index["name"] for index in inspector.get_indexes("produto")}
    if op.f("ix_produto_categoria_id") not in produto_indexes:
        op.create_index(op.f("ix_produto_categoria_id"), "produto", ["categoria_id"], unique=False)

    foreign_keys = {fk.get("name") for fk in inspector.get_foreign_keys("produto")}
    if "fk_produto_categoria_id_categoria" not in foreign_keys:
        if dialect == "sqlite":
            with op.batch_alter_table("produto") as batch_op:
                batch_op.create_foreign_key(
                    "fk_produto_categoria_id_categoria",
                    "categoria",
                    ["categoria_id"],
                    ["id"],
                )
        else:
            op.create_foreign_key(
                "fk_produto_categoria_id_categoria",
                "produto",
                "categoria",
                ["categoria_id"],
                ["id"],
            )


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    dialect = bind.dialect.name

    if inspector.has_table("produto"):
        foreign_keys = {fk.get("name") for fk in inspector.get_foreign_keys("produto")}
        if "fk_produto_categoria_id_categoria" in foreign_keys:
            if dialect == "sqlite":
                with op.batch_alter_table("produto") as batch_op:
                    batch_op.drop_constraint("fk_produto_categoria_id_categoria", type_="foreignkey")
            else:
                op.drop_constraint("fk_produto_categoria_id_categoria", "produto", type_="foreignkey")

        produto_indexes = {index["name"] for index in inspector.get_indexes("produto")}
        if op.f("ix_produto_categoria_id") in produto_indexes:
            op.drop_index(op.f("ix_produto_categoria_id"), table_name="produto")

        produto_columns = {column["name"] for column in inspector.get_columns("produto")}
        if "categoria_id" in produto_columns:
            op.drop_column("produto", "categoria_id")

    if inspector.has_table("categoria"):
        categoria_indexes = {index["name"] for index in inspector.get_indexes("categoria")}
        if op.f("ix_categoria_parent_id") in categoria_indexes:
            op.drop_index(op.f("ix_categoria_parent_id"), table_name="categoria")
        if op.f("ix_categoria_nome") in categoria_indexes:
            op.drop_index(op.f("ix_categoria_nome"), table_name="categoria")
        if op.f("ix_categoria_id") in categoria_indexes:
            op.drop_index(op.f("ix_categoria_id"), table_name="categoria")

        op.drop_table("categoria")
