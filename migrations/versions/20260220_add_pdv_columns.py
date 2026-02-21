"""confirma estrutura existente para módulo PDV

Revision ID: 20260220_add_pdv_columns
Revises: 20260220_add_fornecedor_table
Create Date: 2026-02-20

"""

revision = "20260220_add_pdv_columns"
down_revision = "20260220_add_fornecedor_table"
branch_labels = None
depends_on = None


def upgrade():
    # Estrutura necessária ao PDV já existe nas tabelas legadas (venda, venda_item, conta_receber).
    pass


def downgrade():
    # Migração sem alterações estruturais.
    pass
