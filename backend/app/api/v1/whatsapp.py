from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.config import settings
from ...core.database import get_async_db
from ...core.limiter import limiter
from ...core.security import get_current_active_user_async
from ...models.user import User
from ...schemas.whatsapp import (
    WhatsAppAccountRead,
    WhatsAppConnectRequest,
    WhatsAppGatewayMessageEvent,
    WhatsAppGatewaySessionEvent,
    WhatsAppMessageRead,
)
from ...services.whatsapp_service import (
    WhatsAppGatewayUnavailableError,
    disconnect_whatsapp_account,
    register_whatsapp_message_event,
    register_whatsapp_session_event,
    start_whatsapp_pairing,
    sync_whatsapp_account_status,
)

router = APIRouter(tags=["WhatsApp"])


def _assert_internal_gateway_token(internal_token: str | None) -> None:
    configured = settings.WHATSAPP_GATEWAY_INTERNAL_TOKEN
    if not configured or internal_token != configured:
        raise HTTPException(status_code=401, detail="Token interno do gateway invalido.")


@router.get("/status", response_model=WhatsAppAccountRead)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def get_whatsapp_status(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user_async),
):
    _ = current_user
    try:
        return await sync_whatsapp_account_status(db)
    except WhatsAppGatewayUnavailableError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/connect", response_model=WhatsAppAccountRead)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def connect_whatsapp(
    payload: WhatsAppConnectRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user_async),
):
    _ = current_user
    try:
        return await start_whatsapp_pairing(db, force_refresh=payload.force_refresh)
    except WhatsAppGatewayUnavailableError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/disconnect", response_model=WhatsAppAccountRead)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def disconnect_whatsapp(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user_async),
):
    _ = current_user
    try:
        return await disconnect_whatsapp_account(db)
    except WhatsAppGatewayUnavailableError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/webhook/session", response_model=WhatsAppAccountRead)
async def register_session_webhook(
    payload: WhatsAppGatewaySessionEvent,
    db: AsyncSession = Depends(get_async_db),
    internal_token: str | None = Header(default=None, alias="X-Internal-Token"),
):
    _assert_internal_gateway_token(internal_token)
    return await register_whatsapp_session_event(db, payload)


@router.post("/webhook/message", response_model=WhatsAppMessageRead)
async def register_message_webhook(
    payload: WhatsAppGatewayMessageEvent,
    db: AsyncSession = Depends(get_async_db),
    internal_token: str | None = Header(default=None, alias="X-Internal-Token"),
):
    _assert_internal_gateway_token(internal_token)
    return await register_whatsapp_message_event(db, payload)
