from datetime import date

from sqlalchemy.orm import Session

from app.models.cliente import Cliente
from app.models.movimentacao_estoque import MovimentacaoEstoque
from app.models.venda import Venda, VendaItem


def test_get_clientes(client, db_session: Session, auth_headers):
    c = Cliente(nome="Teste API", cpf_cnpj="12345678900", codigo_legado=9999)
    db_session.add(c)
    db_session.commit()

    response = client.get("/api/v1/clientes/?search=Teste", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["nome"] == "Teste API"

    response = client.get(f"/api/v1/clientes/{c.id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == c.id


def test_get_vendas_paginadas(client, db_session: Session):
    venda = Venda(
        data=date(2023, 1, 1),
        numero_legado=8888,
        total=100.0,
        desconto=10.0,
        cliente_id=None,
    )
    db_session.add(venda)
    db_session.commit()

    item = VendaItem(
        venda_id=venda.id,
        codigo_legado=1,
        quantidade=1,
        preco_unitario=100.0,
        preco_total=100.0,
        nome_produto="Prod Teste",
    )
    db_session.add(item)
    db_session.commit()

    response = client.get("/api/v1/vendas/?start_date=2023-01-01&page=1&page_size=50")
    assert response.status_code == 200

    payload = response.json()
    assert payload["total"] >= 1
    assert payload["page"] == 1
    assert payload["page_size"] == 50
    assert payload["pages"] >= 1

    primeira_venda = payload["items"][0]
    assert primeira_venda["total"] == 100.0
    assert len(primeira_venda["itens"]) >= 1
    assert primeira_venda["itens"][0]["nome_produto"] == "Prod Teste"


def test_get_vendas_resumo(client, db_session: Session):
    venda_ativa = Venda(
        data=date(2023, 1, 2),
        numero_legado=9001,
        total=200.0,
        desconto=20.0,
        cancelada=False,
        cliente_id=None,
    )
    venda_cancelada = Venda(
        data=date(2023, 1, 2),
        numero_legado=9002,
        total=500.0,
        desconto=50.0,
        cancelada=True,
        cliente_id=None,
    )
    db_session.add_all([venda_ativa, venda_cancelada])
    db_session.commit()

    response = client.get("/api/v1/vendas/resumo?start_date=2023-01-01&end_date=2023-01-31")
    assert response.status_code == 200

    payload = response.json()
    assert payload["total_bruto"] == 220.0
    assert payload["total_descontos"] == 20.0
    assert payload["total_liquido"] == 200.0
    assert payload["quantidade_vendas"] == 1
    assert payload["ticket_medio"] == 200.0


def test_get_movimentacao(client, db_session: Session):
    m = MovimentacaoEstoque(
        data=date(2023, 1, 1),
        produto_id=1,
        codigo_legado=10,
        nome_produto="Prod Mov",
        saldo_anterior=0,
        entrada=10,
        saida=0,
        saldo_final=10,
    )
    db_session.add(m)
    db_session.commit()

    response = client.get("/api/v1/movimentacao/produto/1")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["nome_produto"] == "Prod Mov"
