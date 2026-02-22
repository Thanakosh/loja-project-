"""Adiciona tabela ncm para armazenar códigos NCM importados

Revision ID: 20260222_add_ncm_table
Revises: 20260221_refactor_orcamento
Create Date: 2026-02-22

"""

from alembic import op
import sqlalchemy as sa


revision = "20260222_add_ncm_table"
down_revision = "20260221_refactor_orcamento"
branch_labels = None
depends_on = None


def upgrade():
    # Cria tabela NCM apenas se não existir (pode já existir via Base.metadata.create_all)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "ncm" not in inspector.get_table_names():
        op.create_table(
            "ncm",
            sa.Column("codigo", sa.String(length=8), nullable=False),
            sa.Column("descricao", sa.String(), nullable=False),
            sa.PrimaryKeyConstraint("codigo"),
        )
        op.create_index(op.f("ix_ncm_codigo"), "ncm", ["codigo"], unique=False)
    else:
        # Tabela já existe (criada via importar_ncms.py), garante que o índice existe
        existing_indexes = [idx["name"] for idx in inspector.get_indexes("ncm")]
        if "ix_ncm_codigo" not in existing_indexes:
            op.create_index(op.f("ix_ncm_codigo"), "ncm", ["codigo"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_ncm_codigo"), table_name="ncm")
    op.drop_table("ncm")
