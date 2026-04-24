from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class WhatsAppAccountRead(BaseModel):
    id: int
    account_key: str
    provider: str
    display_name: Optional[str] = None
    linked_phone: Optional[str] = None
    status: str
    self_chat_mode: bool
    qr_code_data_url: Optional[str] = None
    qr_expires_at: Optional[datetime] = None
    last_connected_at: Optional[datetime] = None
    last_sync_at: Optional[datetime] = None
    last_error: Optional[str] = None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WhatsAppConnectRequest(BaseModel):
    force_refresh: bool = False


class WhatsAppShareOrcamentoRequest(BaseModel):
    telefone: Optional[str] = Field(default=None, max_length=32)
    mensagem: Optional[str] = Field(default=None, max_length=1200)


class WhatsAppMessageRead(BaseModel):
    id: int
    account_id: int
    cliente_id: Optional[int] = None
    created_by: Optional[int] = None
    entity_type: str
    entity_id: int
    message_type: str
    destino: str
    caption: Optional[str] = None
    media_filename: Optional[str] = None
    gateway_message_id: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WhatsAppGatewaySessionEvent(BaseModel):
    account_key: str = "default"
    status: Literal["disconnected", "connecting", "connected", "error"]
    linked_phone: Optional[str] = None
    display_name: Optional[str] = None
    self_chat_mode: bool = False
    qr_code_data_url: Optional[str] = None
    qr_expires_at: Optional[datetime] = None
    last_connected_at: Optional[datetime] = None
    last_error: Optional[str] = None


class WhatsAppGatewayMessageEvent(BaseModel):
    account_key: str = "default"
    message_db_id: int
    status: Literal["sent", "delivered", "read", "failed"]
    gateway_message_id: Optional[str] = None
    error_message: Optional[str] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
