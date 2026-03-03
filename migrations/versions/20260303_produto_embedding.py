"""Adiciona coluna embedding na tabela produto para detecção de duplicatas.

Revision ID: 20260303_produto_embedding
Revises: 20260303_desconto_auditoria
Create Date: 2026-03-03
"""

from alembic import op
import sqlalchemy as sa

revision = "20260303_produto_embedding"
down_revision = "20260303_desconto_auditoria"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("produto", sa.Column("embedding", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("produto", "embedding")
