"""adiciona movimentacao de caixa

Revision ID: 20260330_movimentacao_caixa
Revises: 20260326_caixa_usuario_fechamento
Create Date: 2026-03-30 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260330_movimentacao_caixa"
down_revision = "20260326_caixa_usuario_fechamento"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "movimentacao_caixa",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("caixa_id", sa.Integer(), nullable=False),
        sa.Column("tipo", sa.String(length=20), nullable=False),
        sa.Column("valor", sa.Float(), nullable=False),
        sa.Column("motivo", sa.String(length=120), nullable=False),
        sa.Column("observacao", sa.String(length=255), nullable=True),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(["caixa_id"], ["caixa_diario.id"]),
        sa.ForeignKeyConstraint(["usuario_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_movimentacao_caixa_caixa_id", "movimentacao_caixa", ["caixa_id"])
    op.create_index("ix_movimentacao_caixa_tipo", "movimentacao_caixa", ["tipo"])
    op.create_index("ix_movimentacao_caixa_usuario_id", "movimentacao_caixa", ["usuario_id"])
    op.create_index("ix_movimentacao_caixa_created_at", "movimentacao_caixa", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_movimentacao_caixa_created_at", table_name="movimentacao_caixa")
    op.drop_index("ix_movimentacao_caixa_usuario_id", table_name="movimentacao_caixa")
    op.drop_index("ix_movimentacao_caixa_tipo", table_name="movimentacao_caixa")
    op.drop_index("ix_movimentacao_caixa_caixa_id", table_name="movimentacao_caixa")
    op.drop_table("movimentacao_caixa")
