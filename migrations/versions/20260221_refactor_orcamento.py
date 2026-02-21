"""refatora módulo de orçamentos com itens e conversão em venda

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


def upgrade():
    # ATENÇÃO: A tabela original é renomeada para orcamento_backup.
    # Se houver dados na tabela antiga que precisem ser migrados para o novo formato,
    # execute manualmente após o upgrade:
    #
    #   INSERT INTO orcamento (id, cliente_id, cliente_nome, status, desconto_geral,
    #       observacao, data_criacao, data_validade, criado_por)
    #   SELECT id, cliente_id, cliente_nome,
    #       COALESCE(status, 'aberto'), COALESCE(desconto, 0.0),
    #       observacao, data_criacao, data_validade, NULL
    #   FROM orcamento_backup;
    #
    # Após validar os dados migrados, a tabela orcamento_backup pode ser removida:
    #   DROP TABLE orcamento_backup;
    op.rename_table("orcamento", "orcamento_backup")

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
    op.create_index(op.f("ix_orcamento_cliente_id"), "orcamento", ["cliente_id"], unique=False)

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
    op.create_index(op.f("ix_orcamento_item_orcamento_id"), "orcamento_item", ["orcamento_id"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_orcamento_item_orcamento_id"), table_name="orcamento_item")
    op.drop_table("orcamento_item")

    op.drop_index(op.f("ix_orcamento_cliente_id"), table_name="orcamento")
    op.drop_table("orcamento")

    op.rename_table("orcamento_backup", "orcamento")
