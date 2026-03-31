"""adiciona tabela de pagamentos por venda

Revision ID: 20260330_venda_pagamento
Revises: 20260330_movimentacao_caixa
Create Date: 2026-03-30 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260330_venda_pagamento"
down_revision = "20260330_movimentacao_caixa"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "venda_pagamento",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("venda_id", sa.Integer(), nullable=False),
        sa.Column("forma_pagamento", sa.Integer(), nullable=False),
        sa.Column("valor", sa.Float(), nullable=False),
        sa.Column("ordem", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("valor_recebido", sa.Float(), nullable=True),
        sa.Column("troco", sa.Float(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["venda_id"], ["venda.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_venda_pagamento_forma_pagamento", "venda_pagamento", ["forma_pagamento"])
    op.create_index("ix_venda_pagamento_ordem", "venda_pagamento", ["ordem"])
    op.create_index("ix_venda_pagamento_venda_id", "venda_pagamento", ["venda_id"])


def downgrade() -> None:
    op.drop_index("ix_venda_pagamento_venda_id", table_name="venda_pagamento")
    op.drop_index("ix_venda_pagamento_ordem", table_name="venda_pagamento")
    op.drop_index("ix_venda_pagamento_forma_pagamento", table_name="venda_pagamento")
    op.drop_table("venda_pagamento")
