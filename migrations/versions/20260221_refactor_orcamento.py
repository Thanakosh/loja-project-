"""Refatora modulo de orcamentos com itens e conversao em venda.

Revision ID: 20260221_refactor_orcamento
Revises: 20260220_add_pdv_columns
Create Date: 2026-02-21
"""

from alembic import op
import sqlalchemy as sa


revision = "20260221_refactor_orcamento"
down_revision = "20260220_add_pdv_columns"
branch_labels = None
depends_on = None


def _inspector():
    return sa.inspect(op.get_bind())


def _has_table(table_name: str) -> bool:
    return _inspector().has_table(table_name)


def _get_columns(table_name: str) -> set[str]:
    if not _has_table(table_name):
        return set()
    return {column["name"] for column in _inspector().get_columns(table_name)}


def _get_indexes(table_name: str) -> set[str]:
    if not _has_table(table_name):
        return set()
    return {index["name"] for index in _inspector().get_indexes(table_name)}


def upgrade():
    # Se existir a tabela legada de orcamento, ela e preservada como backup.
    # Em banco vazio, a tabela pode simplesmente nao existir.
    if _has_table("orcamento") and "desconto" in _get_columns("orcamento") and not _has_table(
        "orcamento_backup"
    ):
        op.rename_table("orcamento", "orcamento_backup")

    if not _has_table("orcamento"):
        op.create_table(
            "orcamento",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("cliente_id", sa.Integer(), nullable=True),
            sa.Column("cliente_nome", sa.String(length=120), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.Column("desconto_geral", sa.Float(), nullable=True),
            sa.Column("observacao", sa.String(length=255), nullable=True),
            sa.Column("data_criacao", sa.DateTime(), nullable=False),
            sa.Column("data_validade", sa.Date(), nullable=True),
            sa.Column("venda_id", sa.Integer(), nullable=True),
            sa.Column("criado_por", sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(["cliente_id"], ["cliente.id"]),
            sa.ForeignKeyConstraint(["criado_por"], ["user.id"]),
            sa.ForeignKeyConstraint(["venda_id"], ["venda.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    orcamento_indexes = _get_indexes("orcamento")
    if op.f("ix_orcamento_cliente_id") not in orcamento_indexes:
        op.create_index(op.f("ix_orcamento_cliente_id"), "orcamento", ["cliente_id"], unique=False)

    if not _has_table("orcamento_item"):
        op.create_table(
            "orcamento_item",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("orcamento_id", sa.Integer(), nullable=False),
            sa.Column("produto_id", sa.Integer(), nullable=True),
            sa.Column("descricao", sa.String(length=120), nullable=False),
            sa.Column("quantidade", sa.Float(), nullable=False),
            sa.Column("preco_unitario", sa.Float(), nullable=False),
            sa.Column("desconto", sa.Float(), nullable=True),
            sa.Column("preco_total", sa.Float(), nullable=False),
            sa.ForeignKeyConstraint(["orcamento_id"], ["orcamento.id"]),
            sa.ForeignKeyConstraint(["produto_id"], ["produto.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    orcamento_item_indexes = _get_indexes("orcamento_item")
    if op.f("ix_orcamento_item_orcamento_id") not in orcamento_item_indexes:
        op.create_index(
            op.f("ix_orcamento_item_orcamento_id"),
            "orcamento_item",
            ["orcamento_id"],
            unique=False,
        )


def downgrade():
    orcamento_item_indexes = _get_indexes("orcamento_item")
    if op.f("ix_orcamento_item_orcamento_id") in orcamento_item_indexes:
        op.drop_index(op.f("ix_orcamento_item_orcamento_id"), table_name="orcamento_item")
    if _has_table("orcamento_item"):
        op.drop_table("orcamento_item")

    orcamento_indexes = _get_indexes("orcamento")
    if op.f("ix_orcamento_cliente_id") in orcamento_indexes:
        op.drop_index(op.f("ix_orcamento_cliente_id"), table_name="orcamento")
    if _has_table("orcamento"):
        op.drop_table("orcamento")

    if _has_table("orcamento_backup") and not _has_table("orcamento"):
        op.rename_table("orcamento_backup", "orcamento")
