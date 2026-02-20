from datetime import date
from sqlalchemy.orm import Session
from app.models.cliente import Cliente
from app.models.venda import Venda, VendaItem
from app.models.movimentacao_estoque import MovimentacaoEstoque

def test_get_clientes(client, db_session: Session, auth_headers):
    # Setup
    c = Cliente(nome="Teste API", cpf_cnpj="12345678900", codigo_legado=9999)
    db_session.add(c)
    db_session.commit()

    # Test List
    response = client.get("/api/v1/clientes/?search=Teste", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["nome"] == "Teste API"

    # Test Get by ID
    response = client.get(f"/api/v1/clientes/{c.id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == c.id

def test_get_vendas(client, db_session: Session):
    # Setup
    v = Venda(
        data=date(2023, 1, 1),
        numero_legado=8888,
        total=100.0,
        cliente_id=None
    )
    db_session.add(v)
    db_session.commit()
    
    item = VendaItem(
        venda_id=v.id,
        codigo_legado=1,
        quantidade=1,
        preco_unitario=100.0,
        preco_total=100.0,
        nome_produto="Prod Teste"
    )
    db_session.add(item)
    db_session.commit()

    # Test List
    response = client.get("/api/v1/vendas/?start_date=2023-01-01")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["total"] == 100.0
    # Verifica eager loading dos itens
    assert len(data[0]["itens"]) >= 1
    assert data[0]["itens"][0]["nome_produto"] == "Prod Teste"

def test_get_movimentacao(client, db_session: Session):
    # Setup
    m = MovimentacaoEstoque(
        data=date(2023, 1, 1),
        produto_id=1,
        codigo_legado=10,
        nome_produto="Prod Mov",
        saldo_anterior=0,
        entrada=10,
        saida=0,
        saldo_final=10
    )
    db_session.add(m)
    db_session.commit()

    # Test List by Produto
    response = client.get("/api/v1/movimentacao/produto/1")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["nome_produto"] == "Prod Mov"
