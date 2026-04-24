from datetime import date, datetime, timedelta, timezone

import pytest
from fastapi import HTTPException

from app.models.cliente import Cliente
from app.models.orcamento import Orcamento, OrcamentoItem, StatusOrcamento
from app.models.whatsapp import WhatsAppAccount, WhatsAppAccountStatus, WhatsAppMessage, WhatsAppMessageStatus
from app.schemas.whatsapp import WhatsAppGatewayMessageEvent
from app.services import whatsapp_service


def _criar_cliente(db_session):
    cliente = Cliente(
        codigo_legado=101,
        nome="Cliente WhatsApp",
        telefone="(11) 99888-7766",
        telefone_whatsapp="(11) 99888-7766",
        ativo=True,
    )
    db_session.add(cliente)
    db_session.commit()
    db_session.refresh(cliente)
    return cliente


def _criar_orcamento(db_session, cliente_id):
    orcamento = Orcamento(
        cliente_id=cliente_id,
        cliente_nome="Cliente WhatsApp",
        status=StatusOrcamento.ABERTO.value,
        desconto_geral=0.0,
        data_validade=date(2026, 4, 30),
    )
    orcamento.itens = [
        OrcamentoItem(
            descricao="Produto teste",
            quantidade=2,
            preco_unitario=15.0,
            desconto=0.0,
            preco_total=30.0,
        )
    ]
    db_session.add(orcamento)
    db_session.commit()
    db_session.refresh(orcamento)
    return orcamento


def test_normalize_whatsapp_phone():
    assert whatsapp_service.normalize_whatsapp_phone("(11) 99888-7766", "55") == "+5511998887766"
    assert whatsapp_service.normalize_whatsapp_phone("+55 11 99888-7766", "55") == "+5511998887766"
    assert whatsapp_service.normalize_whatsapp_phone("0011998887766", "55") == "+5511998887766"
    assert whatsapp_service.normalize_whatsapp_phone("abc", "55") is None


def test_coerce_datetime_normaliza_timezone_para_utc_ingenuo():
    coerced = whatsapp_service._coerce_datetime("2026-04-20T12:00:00-03:00")

    assert coerced == datetime(2026, 4, 20, 15, 0, 0)
    assert coerced.tzinfo is None


def test_get_whatsapp_status_returns_account(client, auth_headers, db_session, monkeypatch):
    account = WhatsAppAccount(
        account_key="default",
        provider="baileys_gateway",
        status=WhatsAppAccountStatus.DISCONNECTED.value,
    )
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)

    async def fake_sync(db):
        account.status = WhatsAppAccountStatus.CONNECTING.value
        account.qr_code_data_url = "data:image/png;base64,abc"
        account.linked_phone = None
        return account

    monkeypatch.setattr("app.api.v1.whatsapp.sync_whatsapp_account_status", fake_sync)

    response = client.get("/api/v1/integracoes/whatsapp/status", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "connecting"
    assert body["qr_code_data_url"] == "data:image/png;base64,abc"


def test_compartilhar_orcamento_whatsapp(client, auth_headers, db_session, test_user, monkeypatch):
    cliente = _criar_cliente(db_session)
    orcamento = _criar_orcamento(db_session, cliente.id)

    async def fake_share(db, *, orcamento, current_user_id, telefone_override=None, mensagem_override=None):
        return {
            "id": 1,
            "account_id": 1,
            "cliente_id": cliente.id,
            "created_by": current_user_id,
            "entity_type": "orcamento",
            "entity_id": orcamento.id,
            "message_type": "document",
            "destino": "+5511998887766",
            "caption": mensagem_override or "Teste",
            "media_filename": "orcamento-00001.pdf",
            "gateway_message_id": "wamid.123",
            "status": "sent",
            "error_message": None,
            "sent_at": "2026-04-20T12:00:00",
            "delivered_at": None,
            "read_at": None,
            "failed_at": None,
            "created_at": "2026-04-20T12:00:00",
            "updated_at": "2026-04-20T12:00:00",
        }

    monkeypatch.setattr("app.api.v1.orcamento.share_orcamento_via_whatsapp", fake_share)

    response = client.post(
        f"/api/v1/orcamentos/{orcamento.id}/compartilhar-whatsapp",
        json={"telefone": "(11) 99888-7766", "mensagem": "Segue seu PDF"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["entity_type"] == "orcamento"
    assert body["entity_id"] == orcamento.id
    assert body["status"] == "sent"
    assert body["caption"] == "Segue seu PDF"


@pytest.mark.asyncio
async def test_compartilhar_orcamento_bloqueia_cliente_com_opt_out(async_db, db_session, test_user):
    cliente = _criar_cliente(db_session)
    cliente.whatsapp_opt_out_at = datetime(2026, 4, 20, 12, 0, 0)
    db_session.commit()
    db_session.refresh(cliente)
    orcamento = _criar_orcamento(db_session, cliente.id)

    with pytest.raises(HTTPException) as exc_info:
        await whatsapp_service.share_orcamento_via_whatsapp(
            async_db,
            orcamento=orcamento,
            current_user_id=test_user.id,
        )

    assert exc_info.value.status_code == 422
    assert "nao receber" in exc_info.value.detail


@pytest.mark.asyncio
async def test_webhook_message_normaliza_datetime_com_timezone(async_db, db_session):
    account = WhatsAppAccount(
        account_key="default",
        provider="baileys_gateway",
        status=WhatsAppAccountStatus.CONNECTED.value,
    )
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)

    message = WhatsAppMessage(
        account_id=account.id,
        entity_type="orcamento",
        entity_id=123,
        message_type="document",
        destino="+5511998887766",
        status=WhatsAppMessageStatus.PENDING.value,
    )
    db_session.add(message)
    db_session.commit()
    db_session.refresh(message)

    payload = WhatsAppGatewayMessageEvent(
        message_db_id=message.id,
        status=WhatsAppMessageStatus.SENT.value,
        gateway_message_id="wamid.123",
        sent_at=datetime(2026, 4, 20, 12, 0, 0, tzinfo=timezone(-timedelta(hours=3))),
    )

    updated = await whatsapp_service.register_whatsapp_message_event(async_db, payload)

    assert updated.sent_at == datetime(2026, 4, 20, 15, 0, 0)
    assert updated.sent_at.tzinfo is None
