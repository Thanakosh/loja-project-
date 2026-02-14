"""Refatoração do sistema de estoque com transações

Revision ID: refactor_estoque_v2
Revises: 5065442b792a
Create Date: 2026-02-14

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'refactor_estoque_v2'
down_revision = '5065442b792a'
branch_labels = None
depends_on = None


def upgrade():
    # Criar tabela de transações de estoque
    op.create_table(
        'transacao_estoque',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('produto_id', sa.Integer(), nullable=False),
        sa.Column('tipo', sa.Enum('ENTRADA', 'SAIDA', 'AJUSTE', 'DEVOLUCAO', name='tipotransacao'), nullable=False),
        sa.Column('quantidade', sa.Integer(), nullable=False),
        sa.Column('motivo', sa.String(), nullable=True),
        sa.Column('usuario_id', sa.Integer(), nullable=True),
        sa.Column('data_transacao', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['produto_id'], ['produto.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['usuario_id'], ['user.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_transacao_estoque_id', 'transacao_estoque', ['id'])
    op.create_index('ix_transacao_estoque_produto_id', 'transacao_estoque', ['produto_id'])
    op.create_index('ix_transacao_estoque_data', 'transacao_estoque', ['data_transacao'])
    
    # Adicionar novos campos ao produto
    op.add_column('produto', sa.Column('ativo', sa.Boolean(), nullable=False, server_default='1'))
    op.add_column('produto', sa.Column('estoque_minimo', sa.Integer(), nullable=False, server_default='0'))
    op.create_index('ix_produto_nome', 'produto', ['nome'])
    op.create_index('ix_produto_codigo_ncm', 'produto', ['codigo_ncm'])


def downgrade():
    op.drop_index('ix_produto_codigo_ncm', 'produto')
    op.drop_index('ix_produto_nome', 'produto')
    op.drop_column('produto', 'estoque_minimo')
    op.drop_column('produto', 'ativo')
    
    op.drop_index('ix_transacao_estoque_data', 'transacao_estoque')
    op.drop_index('ix_transacao_estoque_produto_id', 'transacao_estoque')
    op.drop_index('ix_transacao_estoque_id', 'transacao_estoque')
    op.drop_table('transacao_estoque')
    
    op.execute("DROP TYPE IF EXISTS tipotransacao")
