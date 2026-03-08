"""Cria tabela fiscal_feedback para rastreabilidade de sugestões fiscais (TASK-033).

Revision ID: 20260303_fiscal_feedback
Revises: 20260303_produto_embedding
Create Date: 2026-03-03
"""

from alembic import op
import sqlalchemy as sa

revision = "20260303_fiscal_feedback"
down_revision = "20260303_produto_embedding"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "fiscal_feedback",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "origem_sugestao",
            sa.Enum(
                "validate_note",
                "suggest_price",
                "classify_ncm",
                "supplier_ranking",
                name="origem_sugestao_enum",
            ),
            nullable=False,
        ),
        sa.Column("versao_motor", sa.String(length=20), nullable=False),
        sa.Column(
            "decisao",
            sa.Enum("aceito", "rejeitado", "revisado", name="decisao_feedback_enum"),
            nullable=False,
        ),
        sa.Column("referencia_id", sa.String(length=80), nullable=True),
        sa.Column("observacao", sa.String(length=500), nullable=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_fiscal_feedback_origem_sugestao", "fiscal_feedback", ["origem_sugestao"])
    op.create_index("ix_fiscal_feedback_decisao", "fiscal_feedback", ["decisao"])
    op.create_index("ix_fiscal_feedback_user_id", "fiscal_feedback", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_fiscal_feedback_user_id", table_name="fiscal_feedback")
    op.drop_index("ix_fiscal_feedback_decisao", table_name="fiscal_feedback")
    op.drop_index("ix_fiscal_feedback_origem_sugestao", table_name="fiscal_feedback")
    op.drop_table("fiscal_feedback")
    # Remove os tipos Enum criados (necessário para PostgreSQL; SQLite ignora)
    sa.Enum(name="origem_sugestao_enum").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="decisao_feedback_enum").drop(op.get_bind(), checkfirst=True)
