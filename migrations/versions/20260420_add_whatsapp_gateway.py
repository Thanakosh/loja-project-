"""adiciona base de integracao WhatsApp com gateway estilo OpenClaw

Revision ID: 20260420_add_whatsapp_gateway
Revises: 20260330_venda_pagamento
Create Date: 2026-04-20
"""

from alembic import op
import sqlalchemy as sa


revision = "20260420_add_whatsapp_gateway"
down_revision = "20260330_venda_pagamento"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("cliente", sa.Column("telefone_whatsapp", sa.String(length=20), nullable=True))
    op.add_column("cliente", sa.Column("whatsapp_opt_in_at", sa.DateTime(), nullable=True))
    op.add_column("cliente", sa.Column("whatsapp_opt_out_at", sa.DateTime(), nullable=True))

    op.create_table(
        "whatsapp_account",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("account_key", sa.String(length=40), nullable=False),
        sa.Column("provider", sa.String(length=40), nullable=False, server_default="baileys_gateway"),
        sa.Column("display_name", sa.String(length=120), nullable=True),
        sa.Column("linked_phone", sa.String(length=32), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="disconnected"),
        sa.Column("self_chat_mode", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("qr_code_data_url", sa.Text(), nullable=True),
        sa.Column("qr_expires_at", sa.DateTime(), nullable=True),
        sa.Column("last_connected_at", sa.DateTime(), nullable=True),
        sa.Column("last_sync_at", sa.DateTime(), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_whatsapp_account_account_key", "whatsapp_account", ["account_key"], unique=True)

    op.create_table(
        "whatsapp_message",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("account_id", sa.Integer(), sa.ForeignKey("whatsapp_account.id"), nullable=False),
        sa.Column("cliente_id", sa.Integer(), sa.ForeignKey("cliente.id"), nullable=True),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("user.id"), nullable=True),
        sa.Column("entity_type", sa.String(length=40), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=False),
        sa.Column("message_type", sa.String(length=20), nullable=False, server_default="document"),
        sa.Column("destino", sa.String(length=32), nullable=False),
        sa.Column("caption", sa.Text(), nullable=True),
        sa.Column("media_filename", sa.String(length=255), nullable=True),
        sa.Column("gateway_message_id", sa.String(length=120), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.Column("delivered_at", sa.DateTime(), nullable=True),
        sa.Column("read_at", sa.DateTime(), nullable=True),
        sa.Column("failed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_whatsapp_message_account_id", "whatsapp_message", ["account_id"], unique=False)
    op.create_index("ix_whatsapp_message_cliente_id", "whatsapp_message", ["cliente_id"], unique=False)
    op.create_index("ix_whatsapp_message_entity_type", "whatsapp_message", ["entity_type"], unique=False)
    op.create_index("ix_whatsapp_message_entity_id", "whatsapp_message", ["entity_id"], unique=False)
    op.create_index("ix_whatsapp_message_gateway_message_id", "whatsapp_message", ["gateway_message_id"], unique=False)

    op.execute(
        """
        INSERT INTO whatsapp_account (account_key, provider, status, self_chat_mode)
        VALUES ('default', 'baileys_gateway', 'disconnected', false)
        """
    )


def downgrade() -> None:
    op.drop_index("ix_whatsapp_message_gateway_message_id", table_name="whatsapp_message")
    op.drop_index("ix_whatsapp_message_entity_id", table_name="whatsapp_message")
    op.drop_index("ix_whatsapp_message_entity_type", table_name="whatsapp_message")
    op.drop_index("ix_whatsapp_message_cliente_id", table_name="whatsapp_message")
    op.drop_index("ix_whatsapp_message_account_id", table_name="whatsapp_message")
    op.drop_table("whatsapp_message")

    op.drop_index("ix_whatsapp_account_account_key", table_name="whatsapp_account")
    op.drop_table("whatsapp_account")

    op.drop_column("cliente", "whatsapp_opt_out_at")
    op.drop_column("cliente", "whatsapp_opt_in_at")
    op.drop_column("cliente", "telefone_whatsapp")
