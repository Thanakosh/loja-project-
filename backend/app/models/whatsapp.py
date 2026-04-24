from enum import Enum

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from ..core.database import Base


class WhatsAppAccountStatus(str, Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


class WhatsAppMessageStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


class WhatsAppAccount(Base):
    __tablename__ = "whatsapp_account"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_key = Column(String(40), nullable=False, unique=True, index=True)
    provider = Column(String(40), nullable=False, default="baileys_gateway")
    display_name = Column(String(120))
    linked_phone = Column(String(32))
    status = Column(String(20), nullable=False, default=WhatsAppAccountStatus.DISCONNECTED.value)
    self_chat_mode = Column(Boolean, nullable=False, default=False)
    qr_code_data_url = Column(Text)
    qr_expires_at = Column(DateTime)
    last_connected_at = Column(DateTime)
    last_sync_at = Column(DateTime)
    last_error = Column(Text)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    messages = relationship("WhatsAppMessage", back_populates="account", cascade="all, delete-orphan")


class WhatsAppMessage(Base):
    __tablename__ = "whatsapp_message"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey("whatsapp_account.id"), nullable=False, index=True)
    cliente_id = Column(Integer, ForeignKey("cliente.id"), nullable=True, index=True)
    created_by = Column(Integer, ForeignKey("user.id"), nullable=True)
    entity_type = Column(String(40), nullable=False, index=True)
    entity_id = Column(Integer, nullable=False, index=True)
    message_type = Column(String(20), nullable=False, default="document")
    destino = Column(String(32), nullable=False)
    caption = Column(Text)
    media_filename = Column(String(255))
    gateway_message_id = Column(String(120), index=True)
    status = Column(String(20), nullable=False, default=WhatsAppMessageStatus.PENDING.value)
    error_message = Column(Text)
    sent_at = Column(DateTime)
    delivered_at = Column(DateTime)
    read_at = Column(DateTime)
    failed_at = Column(DateTime)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    account = relationship("WhatsAppAccount", back_populates="messages")
    cliente = relationship("Cliente")
