"""Refatoracao do sistema de estoque com transacoes.

Revision ID: refactor_estoque_v2
Revises: 5065442b792a
Create Date: 2026-02-14
"""

from alembic import op
import sqlalchemy as sa


revision = "refactor_estoque_v2"
down_revision = "5065442b792a"
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


def _ensure_legacy_core_tables() -> None:
    if not _has_table("user"):
        op.create_table(
            "user",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("email", sa.String(), nullable=False),
            sa.Column("hashed_password", sa.String(), nullable=False),
            sa.Column("full_name", sa.String(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=True, server_default=sa.true()),
            sa.Column("is_superuser", sa.Boolean(), nullable=True, server_default=sa.false()),
            sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("email", name="uq_user_email"),
        )

    if not _has_table("produto"):
        op.create_table(
            "produto",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("nome", sa.String(), nullable=False),
            sa.Column("descricao", sa.String(), nullable=True),
            sa.Column("fornecedor", sa.String(), nullable=False),
            sa.Column("preco_unitario", sa.Float(), nullable=False),
            sa.Column("preco_liquido", sa.Float(), nullable=False),
            sa.Column("codigo_ncm", sa.String(), nullable=True),
            sa.Column("unidade", sa.String(), nullable=True),
            sa.Column("data_emissao", sa.Date(), nullable=True),
            sa.Column("numero_nota", sa.String(), nullable=True),
            sa.Column("cnpj_fornecedor", sa.String(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )

    if not _has_table("cliente"):
        op.create_table(
            "cliente",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("codigo_legado", sa.Integer(), nullable=False),
            sa.Column("nome", sa.String(length=60), nullable=False),
            sa.Column("cpf_cnpj", sa.String(length=20), nullable=True),
            sa.Column("endereco", sa.String(length=80), nullable=True),
            sa.Column("cidade", sa.String(length=30), nullable=True),
            sa.Column("uf", sa.String(length=2), nullable=True),
            sa.Column("cep", sa.String(length=10), nullable=True),
            sa.Column("telefone", sa.String(length=20), nullable=True),
            sa.Column("inscricao_estadual", sa.String(length=20), nullable=True),
            sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("codigo_legado", name="uq_cliente_codigo_legado"),
        )

    if not _has_table("venda"):
        op.create_table(
            "venda",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("numero_legado", sa.Integer(), nullable=False),
            sa.Column("data", sa.Date(), nullable=False),
            sa.Column("hora", sa.String(length=5), nullable=True),
            sa.Column("cliente_id", sa.Integer(), nullable=True),
            sa.Column("vendedor", sa.String(length=10), nullable=True),
            sa.Column("total", sa.Float(), nullable=True, server_default="0"),
            sa.Column("desconto", sa.Float(), nullable=True, server_default="0"),
            sa.Column("forma_pagamento", sa.Integer(), nullable=True),
            sa.Column("fatura", sa.String(length=10), nullable=True),
            sa.Column("situacao", sa.Integer(), nullable=True, server_default="0"),
            sa.Column("cancelada", sa.Boolean(), nullable=True, server_default=sa.false()),
            sa.Column("cupom", sa.Integer(), nullable=True, server_default="0"),
            sa.Column("observacao", sa.String(length=120), nullable=True),
            sa.Column("entrega", sa.String(length=80), nullable=True),
            sa.Column("entrega_data", sa.Date(), nullable=True),
            sa.ForeignKeyConstraint(["cliente_id"], ["cliente.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    if not _has_table("venda_item"):
        op.create_table(
            "venda_item",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("venda_id", sa.Integer(), nullable=False),
            sa.Column("produto_id", sa.Integer(), nullable=True),
            sa.Column("codigo_legado", sa.Integer(), nullable=True),
            sa.Column("nome_produto", sa.String(length=50), nullable=True),
            sa.Column("codigo_barras", sa.String(length=13), nullable=True),
            sa.Column("unidade", sa.String(length=2), nullable=True),
            sa.Column("quantidade", sa.Float(), nullable=True, server_default="0"),
            sa.Column("preco_unitario", sa.Float(), nullable=True, server_default="0"),
            sa.Column("preco_total", sa.Float(), nullable=True, server_default="0"),
            sa.Column("custo", sa.Float(), nullable=True, server_default="0"),
            sa.Column("desconto", sa.Float(), nullable=True, server_default="0"),
            sa.Column("marca", sa.String(length=15), nullable=True),
            sa.Column("grupo", sa.Integer(), nullable=True, server_default="0"),
            sa.ForeignKeyConstraint(["produto_id"], ["produto.id"]),
            sa.ForeignKeyConstraint(["venda_id"], ["venda.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    if not _has_table("conta_receber"):
        op.create_table(
            "conta_receber",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("cliente_id", sa.Integer(), nullable=True),
            sa.Column("documento", sa.Integer(), nullable=True),
            sa.Column("parcela", sa.Integer(), nullable=True),
            sa.Column("vendedor", sa.String(length=15), nullable=True),
            sa.Column("fatura", sa.String(length=10), nullable=True),
            sa.Column("data_emissao", sa.Date(), nullable=True),
            sa.Column("data_vencimento", sa.Date(), nullable=True),
            sa.Column("data_pagamento", sa.Date(), nullable=True),
            sa.Column("valor", sa.Float(), nullable=True, server_default="0"),
            sa.Column("desconto", sa.Float(), nullable=True, server_default="0"),
            sa.Column("juros", sa.Float(), nullable=True, server_default="0"),
            sa.Column("valor_pago", sa.Float(), nullable=True, server_default="0"),
            sa.Column("historico", sa.String(length=40), nullable=True),
            sa.Column("cheque", sa.String(length=10), nullable=True),
            sa.Column("cobranca", sa.String(length=15), nullable=True),
            sa.ForeignKeyConstraint(["cliente_id"], ["cliente.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    if not _has_table("nota_fiscal"):
        op.create_table(
            "nota_fiscal",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("numero_legado", sa.Integer(), nullable=False),
            sa.Column("chave_acesso", sa.String(length=44), nullable=True),
            sa.Column("serie", sa.String(length=3), nullable=True),
            sa.Column("data_emissao", sa.Date(), nullable=True),
            sa.Column("hora_emissao", sa.String(length=8), nullable=True),
            sa.Column("data_saida", sa.Date(), nullable=True),
            sa.Column("hora_saida", sa.String(length=8), nullable=True),
            sa.Column("situacao", sa.Integer(), nullable=True, server_default="0"),
            sa.Column("entrada_saida", sa.String(length=1), nullable=True),
            sa.Column("cfop", sa.String(length=5), nullable=True),
            sa.Column("cfop_descricao", sa.String(length=50), nullable=True),
            sa.Column("cliente_id", sa.Integer(), nullable=True),
            sa.Column("protocolo", sa.String(length=15), nullable=True),
            sa.Column("data_protocolo", sa.String(length=20), nullable=True),
            sa.Column("protocolo_cancelamento", sa.String(length=20), nullable=True),
            sa.Column("data_cancelamento", sa.Date(), nullable=True),
            sa.Column("valor_produtos", sa.Float(), nullable=True, server_default="0"),
            sa.Column("valor_total", sa.Float(), nullable=True, server_default="0"),
            sa.Column("valor_desconto", sa.Float(), nullable=True, server_default="0"),
            sa.Column("valor_frete", sa.Float(), nullable=True, server_default="0"),
            sa.Column("valor_icms", sa.Float(), nullable=True, server_default="0"),
            sa.Column("base_icms", sa.Float(), nullable=True, server_default="0"),
            sa.Column("base_substituicao", sa.Float(), nullable=True, server_default="0"),
            sa.Column("valor_substituicao", sa.Float(), nullable=True, server_default="0"),
            sa.Column("valor_ipi", sa.Float(), nullable=True, server_default="0"),
            sa.Column("valor_seguro", sa.Float(), nullable=True, server_default="0"),
            sa.Column("valor_outras", sa.Float(), nullable=True, server_default="0"),
            sa.Column("observacao", sa.String(length=80), nullable=True),
            sa.ForeignKeyConstraint(["cliente_id"], ["cliente.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    if not _has_table("nota_fiscal_item"):
        op.create_table(
            "nota_fiscal_item",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("nota_fiscal_id", sa.Integer(), nullable=False),
            sa.Column("produto_id", sa.Integer(), nullable=True),
            sa.Column("codigo_legado", sa.Integer(), nullable=True),
            sa.Column("nome_produto", sa.String(length=50), nullable=True),
            sa.Column("unidade", sa.String(length=2), nullable=True),
            sa.Column("quantidade", sa.Float(), nullable=True, server_default="0"),
            sa.Column("preco_unitario", sa.Float(), nullable=True, server_default="0"),
            sa.Column("preco_total", sa.Float(), nullable=True, server_default="0"),
            sa.Column("icms", sa.Float(), nullable=True, server_default="0"),
            sa.Column("ipi", sa.Float(), nullable=True, server_default="0"),
            sa.Column("cfop", sa.String(length=5), nullable=True),
            sa.Column("cst", sa.String(length=3), nullable=True),
            sa.Column("ncm", sa.String(length=8), nullable=True),
            sa.Column("codigo_barras", sa.String(length=13), nullable=True),
            sa.Column("pis", sa.Float(), nullable=True, server_default="0"),
            sa.Column("cofins", sa.Float(), nullable=True, server_default="0"),
            sa.Column("cest", sa.String(length=7), nullable=True),
            sa.Column("pedido", sa.String(length=10), nullable=True),
            sa.ForeignKeyConstraint(["nota_fiscal_id"], ["nota_fiscal.id"]),
            sa.ForeignKeyConstraint(["produto_id"], ["produto.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    if not _has_table("refresh_token"):
        op.create_table(
            "refresh_token",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("token_hash", sa.String(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
            sa.Column("replaced_by", sa.String(), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("token_hash", name="uq_refresh_token_token_hash"),
        )

    if not _has_table("movimentacao_estoque"):
        op.create_table(
            "movimentacao_estoque",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("data", sa.Date(), nullable=False),
            sa.Column("hora", sa.String(length=5), nullable=True),
            sa.Column("operador", sa.String(length=10), nullable=True),
            sa.Column("produto_id", sa.Integer(), nullable=True),
            sa.Column("codigo_legado", sa.Integer(), nullable=True),
            sa.Column("nome_produto", sa.String(length=50), nullable=True),
            sa.Column("unidade", sa.String(length=2), nullable=True),
            sa.Column("saldo_anterior", sa.Float(), nullable=True, server_default="0"),
            sa.Column("entrada", sa.Float(), nullable=True, server_default="0"),
            sa.Column("saida", sa.Float(), nullable=True, server_default="0"),
            sa.Column("saldo_final", sa.Float(), nullable=True, server_default="0"),
            sa.Column("documento", sa.Integer(), nullable=True),
            sa.Column("historico", sa.String(length=50), nullable=True),
            sa.ForeignKeyConstraint(["produto_id"], ["produto.id"]),
            sa.PrimaryKeyConstraint("id"),
        )


def upgrade():
    _ensure_legacy_core_tables()

    if not _has_table("transacao_estoque"):
        op.create_table(
            "transacao_estoque",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("produto_id", sa.Integer(), nullable=False),
            sa.Column(
                "tipo",
                sa.Enum("ENTRADA", "SAIDA", "AJUSTE", "DEVOLUCAO", name="tipotransacao"),
                nullable=False,
            ),
            sa.Column("quantidade", sa.Integer(), nullable=False),
            sa.Column("motivo", sa.String(), nullable=True),
            sa.Column("usuario_id", sa.Integer(), nullable=True),
            sa.Column(
                "data_transacao",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
            sa.ForeignKeyConstraint(["produto_id"], ["produto.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["usuario_id"], ["user.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
        )

    transacao_indexes = _get_indexes("transacao_estoque")
    if "ix_transacao_estoque_id" not in transacao_indexes:
        op.create_index("ix_transacao_estoque_id", "transacao_estoque", ["id"])
    if "ix_transacao_estoque_produto_id" not in transacao_indexes:
        op.create_index(
            "ix_transacao_estoque_produto_id",
            "transacao_estoque",
            ["produto_id"],
        )
    if "ix_transacao_estoque_data" not in transacao_indexes:
        op.create_index("ix_transacao_estoque_data", "transacao_estoque", ["data_transacao"])

    produto_columns = _get_columns("produto")
    if "ativo" not in produto_columns:
        op.add_column(
            "produto",
            sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.true()),
        )
    if "estoque_minimo" not in produto_columns:
        op.add_column(
            "produto",
            sa.Column("estoque_minimo", sa.Integer(), nullable=False, server_default="0"),
        )

    produto_indexes = _get_indexes("produto")
    if "ix_produto_nome" not in produto_indexes:
        op.create_index("ix_produto_nome", "produto", ["nome"])
    if "ix_produto_codigo_ncm" not in produto_indexes:
        op.create_index("ix_produto_codigo_ncm", "produto", ["codigo_ncm"])


def downgrade():
    produto_indexes = _get_indexes("produto")
    if "ix_produto_codigo_ncm" in produto_indexes:
        op.drop_index("ix_produto_codigo_ncm", table_name="produto")
    if "ix_produto_nome" in produto_indexes:
        op.drop_index("ix_produto_nome", table_name="produto")

    produto_columns = _get_columns("produto")
    if "estoque_minimo" in produto_columns:
        op.drop_column("produto", "estoque_minimo")
    if "ativo" in produto_columns:
        op.drop_column("produto", "ativo")

    transacao_indexes = _get_indexes("transacao_estoque")
    if "ix_transacao_estoque_data" in transacao_indexes:
        op.drop_index("ix_transacao_estoque_data", table_name="transacao_estoque")
    if "ix_transacao_estoque_produto_id" in transacao_indexes:
        op.drop_index("ix_transacao_estoque_produto_id", table_name="transacao_estoque")
    if "ix_transacao_estoque_id" in transacao_indexes:
        op.drop_index("ix_transacao_estoque_id", table_name="transacao_estoque")
    if _has_table("transacao_estoque"):
        op.drop_table("transacao_estoque")

    op.execute("DROP TYPE IF EXISTS tipotransacao")
