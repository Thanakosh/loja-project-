from __future__ import annotations

import base64
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import httpx
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..models.cliente import Cliente
from ..models.orcamento import Orcamento
from ..models.whatsapp import (
    WhatsAppAccount,
    WhatsAppAccountStatus,
    WhatsAppMessage,
    WhatsAppMessageStatus,
)
from ..schemas.whatsapp import WhatsAppGatewayMessageEvent, WhatsAppGatewaySessionEvent
from .pdf_service import gerar_pdf_orcamento

logger = logging.getLogger(__name__)

_GATEWAY_TOKEN_HEADER = "X-Internal-Token"


class WhatsAppGatewayUnavailableError(RuntimeError):
    pass


def _coerce_datetime(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value
        return value.astimezone(timezone.utc).replace(tzinfo=None)
    if isinstance(value, str) and value.strip():
        normalized = value.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError:
            return None
        return _coerce_datetime(parsed)
    return None


def _has_active_whatsapp_opt_out(cliente: Optional[Cliente]) -> bool:
    if not cliente:
        return False

    opt_out_at = _coerce_datetime(cliente.whatsapp_opt_out_at)
    if not opt_out_at:
        return False

    opt_in_at = _coerce_datetime(cliente.whatsapp_opt_in_at)
    return opt_in_at is None or opt_out_at >= opt_in_at


def normalize_whatsapp_phone(phone: Optional[str], default_country: str) -> Optional[str]:
    if not phone:
        return None

    digits = "".join(char for char in phone if char.isdigit())
    if not digits:
        return None

    if digits.startswith("00"):
        digits = digits[2:]

    if digits.startswith(default_country):
        return f"+{digits}"

    if len(digits) in {10, 11}:
        return f"+{default_country}{digits}"

    if phone.strip().startswith("+"):
        return f"+{digits}"

    if len(digits) >= 12:
        return f"+{digits}"

    return None


def build_orcamento_whatsapp_caption(orcamento: Orcamento) -> str:
    validade = ""
    if orcamento.data_validade:
        validade = f"\nValidade: {orcamento.data_validade.strftime('%d/%m/%Y')}"

    total = sum(item.preco_total for item in orcamento.itens) - (orcamento.desconto_geral or 0.0)
    total_texto = f"{total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    cliente = orcamento.cliente_nome or "cliente"
    return (
        f"Ola, {cliente}.\n"
        f"Segue o orcamento #{orcamento.id:05d} em PDF.{validade}\n"
        f"Valor total: R$ {total_texto}"
    )


async def get_or_create_whatsapp_account(db: AsyncSession, account_key: Optional[str] = None) -> WhatsAppAccount:
    resolved_key = account_key or settings.WHATSAPP_ACCOUNT_KEY
    account = (
        await db.execute(select(WhatsAppAccount).where(WhatsAppAccount.account_key == resolved_key))
    ).scalars().first()

    if account:
        return account

    account = WhatsAppAccount(
        account_key=resolved_key,
        provider="baileys_gateway",
        status=WhatsAppAccountStatus.DISCONNECTED.value,
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return account


def _gateway_headers() -> dict[str, str]:
    if not settings.WHATSAPP_GATEWAY_INTERNAL_TOKEN:
        raise WhatsAppGatewayUnavailableError("WHATSAPP_GATEWAY_INTERNAL_TOKEN nao configurado.")
    return {_GATEWAY_TOKEN_HEADER: settings.WHATSAPP_GATEWAY_INTERNAL_TOKEN}


async def _gateway_request(method: str, path: str, payload: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    if not settings.WHATSAPP_GATEWAY_URL:
        raise WhatsAppGatewayUnavailableError("WHATSAPP_GATEWAY_URL nao configurado.")

    try:
        async with httpx.AsyncClient(base_url=settings.WHATSAPP_GATEWAY_URL, timeout=20.0) as client:
            response = await client.request(method, path, json=payload, headers=_gateway_headers())
            response.raise_for_status()
            return response.json() if response.content else {}
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text or str(exc)
        raise WhatsAppGatewayUnavailableError(f"Gateway WhatsApp respondeu com erro: {detail}") from exc
    except httpx.HTTPError as exc:
        raise WhatsAppGatewayUnavailableError(f"Gateway WhatsApp indisponivel: {exc}") from exc


def _apply_account_snapshot(account: WhatsAppAccount, snapshot: dict[str, Any]) -> None:
    account.status = snapshot.get("status", account.status)
    account.display_name = snapshot.get("display_name", account.display_name)
    account.linked_phone = snapshot.get("linked_phone", account.linked_phone)
    account.self_chat_mode = snapshot.get("self_chat_mode", account.self_chat_mode)
    account.qr_code_data_url = snapshot.get("qr_code_data_url")
    account.qr_expires_at = _coerce_datetime(snapshot.get("qr_expires_at"))
    account.last_connected_at = _coerce_datetime(snapshot.get("last_connected_at")) or account.last_connected_at
    account.last_error = snapshot.get("last_error")
    account.last_sync_at = datetime.utcnow()


async def sync_whatsapp_account_status(db: AsyncSession) -> WhatsAppAccount:
    account = await get_or_create_whatsapp_account(db)
    snapshot = await _gateway_request("GET", "/session/status")
    _apply_account_snapshot(account, snapshot)
    await db.commit()
    await db.refresh(account)
    return account


async def start_whatsapp_pairing(db: AsyncSession, force_refresh: bool = False) -> WhatsAppAccount:
    account = await get_or_create_whatsapp_account(db)
    snapshot = await _gateway_request("POST", "/session/connect", {"force_refresh": force_refresh})
    _apply_account_snapshot(account, snapshot)
    if not account.qr_expires_at and account.status == WhatsAppAccountStatus.CONNECTING.value:
        account.qr_expires_at = datetime.utcnow() + timedelta(minutes=1)
    await db.commit()
    await db.refresh(account)
    return account


async def disconnect_whatsapp_account(db: AsyncSession) -> WhatsAppAccount:
    account = await get_or_create_whatsapp_account(db)
    snapshot = await _gateway_request("POST", "/session/disconnect")
    _apply_account_snapshot(account, snapshot)
    await db.commit()
    await db.refresh(account)
    return account


async def _resolve_cliente_whatsapp_phone(db: AsyncSession, orcamento: Orcamento) -> tuple[Optional[Cliente], Optional[str]]:
    if not orcamento.cliente_id:
        return None, None

    cliente = await db.get(Cliente, orcamento.cliente_id)
    if not cliente:
        return None, None

    return cliente, cliente.telefone_whatsapp or cliente.telefone


async def share_orcamento_via_whatsapp(
    db: AsyncSession,
    *,
    orcamento: Orcamento,
    current_user_id: int,
    telefone_override: Optional[str] = None,
    mensagem_override: Optional[str] = None,
) -> WhatsAppMessage:
    account = await get_or_create_whatsapp_account(db)
    cliente, phone_from_cliente = await _resolve_cliente_whatsapp_phone(db, orcamento)
    if _has_active_whatsapp_opt_out(cliente):
        raise HTTPException(status_code=422, detail="Cliente optou por nao receber mensagens via WhatsApp.")

    destino = normalize_whatsapp_phone(
        telefone_override or phone_from_cliente,
        default_country=settings.WHATSAPP_DEFAULT_COUNTRY,
    )
    if not destino:
        raise HTTPException(status_code=422, detail="Telefone WhatsApp nao informado ou invalido.")

    caption = (mensagem_override or "").strip() or build_orcamento_whatsapp_caption(orcamento)
    filename = f"orcamento-{orcamento.id:05d}.pdf"
    pdf_bytes = gerar_pdf_orcamento(orcamento)

    message = WhatsAppMessage(
        account_id=account.id,
        cliente_id=cliente.id if cliente else None,
        created_by=current_user_id,
        entity_type="orcamento",
        entity_id=orcamento.id,
        message_type="document",
        destino=destino,
        caption=caption,
        media_filename=filename,
        status=WhatsAppMessageStatus.PENDING.value,
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)

    try:
        payload = {
            "to": destino,
            "caption": caption,
            "filename": filename,
            "content_base64": base64.b64encode(pdf_bytes).decode("ascii"),
            "message_db_id": message.id,
        }
        gateway_response = await _gateway_request("POST", "/messages/document", payload)
        message.status = gateway_response.get("status", WhatsAppMessageStatus.SENT.value)
        message.gateway_message_id = gateway_response.get("gateway_message_id")
        if message.status in {
            WhatsAppMessageStatus.SENT.value,
            WhatsAppMessageStatus.DELIVERED.value,
            WhatsAppMessageStatus.READ.value,
        }:
            message.sent_at = datetime.utcnow()
        message.error_message = gateway_response.get("error_message")
    except WhatsAppGatewayUnavailableError as exc:
        logger.warning("Falha ao enviar orcamento via WhatsApp: %s", exc)
        message.status = WhatsAppMessageStatus.FAILED.value
        message.error_message = str(exc)
        message.failed_at = datetime.utcnow()
        await db.commit()
        await db.refresh(message)
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    await db.commit()
    await db.refresh(message)
    return message


async def register_whatsapp_session_event(
    db: AsyncSession, payload: WhatsAppGatewaySessionEvent
) -> WhatsAppAccount:
    account = await get_or_create_whatsapp_account(db, account_key=payload.account_key)
    _apply_account_snapshot(account, payload.model_dump())
    await db.commit()
    await db.refresh(account)
    return account


async def register_whatsapp_message_event(
    db: AsyncSession, payload: WhatsAppGatewayMessageEvent
) -> WhatsAppMessage:
    message = await db.get(WhatsAppMessage, payload.message_db_id)
    if not message:
        raise HTTPException(status_code=404, detail="Mensagem WhatsApp nao encontrada.")

    message.status = payload.status
    if payload.gateway_message_id:
        message.gateway_message_id = payload.gateway_message_id
    if payload.error_message:
        message.error_message = payload.error_message
    sent_at = _coerce_datetime(payload.sent_at)
    delivered_at = _coerce_datetime(payload.delivered_at)
    read_at = _coerce_datetime(payload.read_at)
    failed_at = _coerce_datetime(payload.failed_at)

    if sent_at:
        message.sent_at = sent_at
    elif payload.status == WhatsAppMessageStatus.SENT.value and not message.sent_at:
        message.sent_at = datetime.utcnow()
    if delivered_at:
        message.delivered_at = delivered_at
    elif payload.status == WhatsAppMessageStatus.DELIVERED.value and not message.delivered_at:
        message.delivered_at = datetime.utcnow()
    if read_at:
        message.read_at = read_at
    elif payload.status == WhatsAppMessageStatus.READ.value and not message.read_at:
        message.read_at = datetime.utcnow()
    if failed_at:
        message.failed_at = failed_at
    elif payload.status == WhatsAppMessageStatus.FAILED.value and not message.failed_at:
        message.failed_at = datetime.utcnow()

    await db.commit()
    await db.refresh(message)
    return message
