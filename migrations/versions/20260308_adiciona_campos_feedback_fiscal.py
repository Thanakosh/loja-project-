"""adiciona campos de rastreabilidade no fiscal_feedback

Revision ID: 20260308_adiciona_campos_feedback_fiscal
Revises: 20260303_fiscal_feedback
Create Date: 2026-03-08
"""

from alembic import op
import sqlalchemy as sa


revision = "20260308_adiciona_campos_feedback_fiscal"
down_revision = "20260303_fiscal_feedback"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("fiscal_feedback", sa.Column("valor_original", sa.Numeric(12, 2), nullable=True))
    op.add_column("fiscal_feedback", sa.Column("valor_final", sa.Numeric(12, 2), nullable=True))
    op.add_column("fiscal_feedback", sa.Column("comentario", sa.String(length=500), nullable=True))
    op.add_column("fiscal_feedback", sa.Column("nota_fiscal_id", sa.Integer(), nullable=True))
    op.add_column("fiscal_feedback", sa.Column("produto_id", sa.Integer(), nullable=True))

    op.create_foreign_key(
        "fk_fiscal_feedback_nota_fiscal_id",
        "fiscal_feedback",
        "nota_fiscal",
        ["nota_fiscal_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_fiscal_feedback_produto_id",
        "fiscal_feedback",
        "produto",
        ["produto_id"],
        ["id"],
    )
    op.create_index("ix_fiscal_feedback_nota_fiscal_id", "fiscal_feedback", ["nota_fiscal_id"])
    op.create_index("ix_fiscal_feedback_produto_id", "fiscal_feedback", ["produto_id"])

    op.execute(
        "UPDATE fiscal_feedback "
        "SET origem_sugestao = REPLACE(REPLACE(REPLACE(REPLACE(origem_sugestao, 'validate_note', 'validate-note'), "
        "'suggest_price', 'suggest-price'), 'classify_ncm', 'classify-ncm'), 'supplier_ranking', 'supplier-ranking')"
    )
    op.execute("UPDATE fiscal_feedback SET decisao = 'modificado' WHERE decisao = 'revisado'")

    op.alter_column("fiscal_feedback", "origem_sugestao", type_=sa.String(length=30), existing_nullable=False)
    op.alter_column("fiscal_feedback", "decisao", type_=sa.String(length=20), existing_nullable=False)

    op.drop_column("fiscal_feedback", "referencia_id")
    op.drop_column("fiscal_feedback", "observacao")


def downgrade() -> None:
    op.add_column("fiscal_feedback", sa.Column("observacao", sa.String(length=500), nullable=True))
    op.add_column("fiscal_feedback", sa.Column("referencia_id", sa.String(length=80), nullable=True))

    op.alter_column("fiscal_feedback", "decisao", type_=sa.String(length=255), existing_nullable=False)
    op.alter_column("fiscal_feedback", "origem_sugestao", type_=sa.String(length=255), existing_nullable=False)

    op.execute(
        "UPDATE fiscal_feedback "
        "SET origem_sugestao = REPLACE(REPLACE(REPLACE(REPLACE(origem_sugestao, 'validate-note', 'validate_note'), "
        "'suggest-price', 'suggest_price'), 'classify-ncm', 'classify_ncm'), 'supplier-ranking', 'supplier_ranking')"
    )
    op.execute("UPDATE fiscal_feedback SET decisao = 'revisado' WHERE decisao = 'modificado'")

    op.drop_index("ix_fiscal_feedback_produto_id", table_name="fiscal_feedback")
    op.drop_index("ix_fiscal_feedback_nota_fiscal_id", table_name="fiscal_feedback")
    op.drop_constraint("fk_fiscal_feedback_produto_id", "fiscal_feedback", type_="foreignkey")
    op.drop_constraint("fk_fiscal_feedback_nota_fiscal_id", "fiscal_feedback", type_="foreignkey")

    op.drop_column("fiscal_feedback", "produto_id")
    op.drop_column("fiscal_feedback", "nota_fiscal_id")
    op.drop_column("fiscal_feedback", "comentario")
    op.drop_column("fiscal_feedback", "valor_final")
    op.drop_column("fiscal_feedback", "valor_original")
