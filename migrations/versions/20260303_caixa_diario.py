"""caixa_diario

Revision ID: 20260303_caixa_diario
Revises: 20260302_unidade_medida_produto
Create Date: 2026-03-03
"""
from alembic import op
import sqlalchemy as sa

revision = "20260303_caixa_diario"
down_revision = "20260302_unidade_medida_produto"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "caixa_diario",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("data_abertura", sa.DateTime(), nullable=False),
        sa.Column("data_fechamento", sa.DateTime(), nullable=True),
        sa.Column("valor_abertura", sa.Float(), nullable=False),
        sa.Column("valor_fechamento", sa.Float(), nullable=True),
        sa.Column("status", sa.String(length=10), nullable=False),
        sa.Column("observacao", sa.String(length=255), nullable=True),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["usuario_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_caixa_diario_data_abertura", "caixa_diario", ["data_abertura"])
    op.create_index("ix_caixa_diario_status", "caixa_diario", ["status"])
    op.create_index("ix_caixa_diario_usuario_id", "caixa_diario", ["usuario_id"])

    op.add_column("venda", sa.Column("caixa_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_venda_caixa_id", "venda", "caixa_diario", ["caixa_id"], ["id"]
    )
    op.create_index("ix_venda_caixa_id", "venda", ["caixa_id"])


def downgrade() -> None:
    op.drop_index("ix_venda_caixa_id", table_name="venda")
    op.drop_constraint("fk_venda_caixa_id", "venda", type_="foreignkey")
    op.drop_column("venda", "caixa_id")

    op.drop_index("ix_caixa_diario_usuario_id", table_name="caixa_diario")
    op.drop_index("ix_caixa_diario_status", table_name="caixa_diario")
    op.drop_index("ix_caixa_diario_data_abertura", table_name="caixa_diario")
    op.drop_table("caixa_diario")
