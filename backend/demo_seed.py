"""
Script para criar banco SQLite demo com dados de exemplo.
Uso: python demo_seed.py
Gera: demo.db no diretório atual
"""
import sys
import os
from datetime import date, datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Forçar variáveis de ambiente ANTES de importar qualquer coisa do app
os.environ["DATABASE_URL"] = "sqlite:///demo.db"
os.environ["JWT_SECRET"] = "demo-secret-key-apenas-para-demonstracao-2026"
os.environ["ENVIRONMENT"] = "development"
os.environ["CORS_ORIGINS"] = '["*"]'
os.environ["DEBUG"] = "false"

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.core.security import get_password_hash
from app.models.user import User
from app.models.produto import Produto
from app.models.transacao_estoque import TransacaoEstoque, TipoTransacao
from app.models.cliente import Cliente
from app.models.fornecedor import Fornecedor
from app.models.categoria import Categoria
from app.models.venda import Venda, VendaItem
from app.models.orcamento import Orcamento, OrcamentoItem
from app.models.conta_receber import ContaReceber
from app.models.estoque import Estoque
from app.models.nota_fiscal import NotaFiscal, NotaFiscalItem
from app.models.ncm import NCM
from app.models.movimentacao_estoque import MovimentacaoEstoque
from app.models.refresh_token import RefreshToken

DB_PATH = "demo.db"

def main():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"  Removido {DB_PATH} anterior")

    engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    print("Criando dados de demonstração...")

    # === USUÁRIO ADMIN ===
    admin = User(
        email="admin@loja.com",
        hashed_password=get_password_hash("admin"),
        full_name="Administrador",
        is_superuser=True,
        is_active=True,
        is_verified=True,
    )
    db.add(admin)
    db.flush()
    print(f"  Usuário: admin@loja.com / admin")

    # === CATEGORIAS ===
    categorias_data = [
        {"nome": "Material Elétrico"},
        {"nome": "Iluminação"},
        {"nome": "Ferramentas"},
        {"nome": "Hidráulica"},
        {"nome": "Tintas e Acabamento"},
    ]
    categorias = []
    for c in categorias_data:
        cat = Categoria(nome=c["nome"], ativo=True)
        db.add(cat)
        categorias.append(cat)
    db.flush()
    print(f"  {len(categorias)} categorias criadas")

    # === FORNECEDORES ===
    fornecedores_data = [
        {"razao_social": "Eletrofios Distribuidora LTDA", "nome_fantasia": "Eletrofios", "cnpj": "12.345.678/0001-90", "telefone": "(11) 3456-7890", "email": "vendas@eletrofios.com.br", "cidade": "São Paulo", "uf": "SP"},
        {"razao_social": "Iluminart Comércio de Lâmpadas ME", "nome_fantasia": "Iluminart", "cnpj": "98.765.432/0001-10", "telefone": "(21) 2345-6789", "email": "contato@iluminart.com.br", "cidade": "Rio de Janeiro", "uf": "RJ"},
        {"razao_social": "Hidrobras Conexões EIRELI", "nome_fantasia": "Hidrobras", "cnpj": "11.222.333/0001-44", "telefone": "(31) 3456-1234", "email": "compras@hidrobras.com.br", "cidade": "Belo Horizonte", "uf": "MG"},
    ]
    fornecedores = []
    for f in fornecedores_data:
        forn = Fornecedor(**f, ativo=True)
        db.add(forn)
        fornecedores.append(forn)
    db.flush()
    print(f"  {len(fornecedores)} fornecedores criados")

    # === PRODUTOS ===
    produtos_data = [
        {"nome": "Cabo Flex 2.5mm Preto (100m)", "descricao": "Cabo flexível 2.5mm² preto rolo 100m", "fornecedor": "Eletrofios", "preco_unitario": 189.90, "preco_liquido": 169.90, "preco_custo": 120.00, "preco_varejo": 189.90, "preco_atacado": 169.90, "qtd_minima_atacado": 5, "unidade_medida": "UN", "estoque_minimo": 10, "fornecedor_id": 1, "categoria_id": 1},
        {"nome": "Cabo Flex 1.5mm Azul (100m)", "descricao": "Cabo flexível 1.5mm² azul rolo 100m", "fornecedor": "Eletrofios", "preco_unitario": 129.90, "preco_liquido": 119.90, "preco_custo": 85.00, "preco_varejo": 129.90, "preco_atacado": 119.90, "qtd_minima_atacado": 5, "unidade_medida": "UN", "estoque_minimo": 10, "fornecedor_id": 1, "categoria_id": 1},
        {"nome": "Disjuntor Monopolar 20A", "descricao": "Disjuntor monopolar curva C 20A DIN", "fornecedor": "Eletrofios", "preco_unitario": 18.50, "preco_liquido": 16.90, "preco_custo": 10.50, "preco_varejo": 18.50, "preco_atacado": 16.90, "qtd_minima_atacado": 10, "unidade_medida": "UN", "estoque_minimo": 20, "fornecedor_id": 1, "categoria_id": 1},
        {"nome": "Lâmpada LED Bulbo 12W", "descricao": "Lâmpada LED bulbo 12W branco frio E27", "fornecedor": "Iluminart", "preco_unitario": 12.90, "preco_liquido": 11.50, "preco_custo": 6.80, "preco_varejo": 12.90, "preco_atacado": 11.50, "qtd_minima_atacado": 20, "unidade_medida": "UN", "estoque_minimo": 50, "fornecedor_id": 2, "categoria_id": 2},
        {"nome": "Luminária Painel LED 24W", "descricao": "Painel LED embutir 24W redondo branco", "fornecedor": "Iluminart", "preco_unitario": 45.90, "preco_liquido": 42.00, "preco_custo": 28.00, "preco_varejo": 45.90, "preco_atacado": 42.00, "qtd_minima_atacado": 10, "unidade_medida": "UN", "estoque_minimo": 15, "fornecedor_id": 2, "categoria_id": 2},
        {"nome": "Refletor LED 50W", "descricao": "Refletor LED 50W bivolt IP65 branco frio", "fornecedor": "Iluminart", "preco_unitario": 79.90, "preco_liquido": 72.00, "preco_custo": 48.00, "preco_varejo": 79.90, "preco_atacado": 72.00, "qtd_minima_atacado": 5, "unidade_medida": "UN", "estoque_minimo": 8, "fornecedor_id": 2, "categoria_id": 2},
        {"nome": "Tubo PVC Soldável 25mm (6m)", "descricao": "Tubo PVC soldável marrom 25mm barra 6m", "fornecedor": "Hidrobras", "preco_unitario": 14.90, "preco_liquido": 13.50, "preco_custo": 8.50, "preco_varejo": 14.90, "preco_atacado": 13.50, "qtd_minima_atacado": 20, "unidade_medida": "UN", "estoque_minimo": 30, "fornecedor_id": 3, "categoria_id": 4},
        {"nome": "Registro de Esfera 3/4", "descricao": "Registro de esfera 3/4\" latão cromado", "fornecedor": "Hidrobras", "preco_unitario": 32.90, "preco_liquido": 29.90, "preco_custo": 19.00, "preco_varejo": 32.90, "preco_atacado": 29.90, "qtd_minima_atacado": 10, "unidade_medida": "UN", "estoque_minimo": 10, "fornecedor_id": 3, "categoria_id": 4},
        {"nome": "Chave de Fenda 1/4x6\"", "descricao": "Chave de fenda ponta chata 1/4x6 polegadas", "fornecedor": "Eletrofios", "preco_unitario": 15.90, "preco_liquido": 14.50, "preco_custo": 8.00, "preco_varejo": 15.90, "preco_atacado": 14.50, "qtd_minima_atacado": 12, "unidade_medida": "UN", "estoque_minimo": 15, "fornecedor_id": 1, "categoria_id": 3},
        {"nome": "Tinta Acrílica Branca 18L", "descricao": "Tinta acrílica fosca branco neve 18 litros", "fornecedor": "Hidrobras", "preco_unitario": 189.90, "preco_liquido": 175.00, "preco_custo": 120.00, "preco_varejo": 189.90, "preco_atacado": 175.00, "qtd_minima_atacado": 3, "unidade_medida": "UN", "estoque_minimo": 5, "fornecedor_id": 3, "categoria_id": 5},
    ]
    produtos = []
    for p in produtos_data:
        prod = Produto(**p, ativo=True)
        db.add(prod)
        produtos.append(prod)
    db.flush()
    print(f"  {len(produtos)} produtos criados")

    # === TRANSAÇÕES DE ESTOQUE (entradas iniciais) ===
    estoques_iniciais = [50, 40, 100, 200, 60, 30, 80, 50, 40, 15]
    for i, prod in enumerate(produtos):
        t = TransacaoEstoque(
            produto_id=prod.id,
            tipo=TipoTransacao.ENTRADA,
            quantidade=estoques_iniciais[i],
            motivo="Estoque inicial - demonstração",
            usuario_id=admin.id,
            data_transacao=datetime(2026, 2, 15, 10, 0, 0, tzinfo=timezone.utc),
        )
        db.add(t)
    db.flush()
    print(f"  Estoque inicial definido para {len(produtos)} produtos")

    # === CLIENTES ===
    clientes_data = [
        {"codigo_legado": 1, "nome": "João da Silva", "cpf_cnpj": "123.456.789-00", "telefone": "(11) 98765-4321", "cidade": "São Paulo", "uf": "SP", "endereco": "Rua das Flores, 123"},
        {"codigo_legado": 2, "nome": "Maria Oliveira", "cpf_cnpj": "987.654.321-00", "telefone": "(21) 91234-5678", "cidade": "Rio de Janeiro", "uf": "RJ", "endereco": "Av. Brasil, 456"},
        {"codigo_legado": 3, "nome": "Construtora Horizonte LTDA", "cpf_cnpj": "45.678.901/0001-23", "telefone": "(31) 3456-7890", "cidade": "Belo Horizonte", "uf": "MG", "endereco": "Rua Industrial, 789"},
        {"codigo_legado": 4, "nome": "Pedro Santos", "cpf_cnpj": "456.789.012-34", "telefone": "(11) 97654-3210", "cidade": "Campinas", "uf": "SP", "endereco": "Rua do Comércio, 321"},
        {"codigo_legado": 5, "nome": "Ana Costa Materiais ME", "cpf_cnpj": "67.890.123/0001-45", "telefone": "(19) 3456-9876", "cidade": "Sorocaba", "uf": "SP", "endereco": "Av. Paulista, 654"},
    ]
    clientes = []
    for c in clientes_data:
        cl = Cliente(**c, ativo=True)
        db.add(cl)
        clientes.append(cl)
    db.flush()
    print(f"  {len(clientes)} clientes criados")

    # === VENDAS ===
    vendas_data = [
        {"numero_legado": 1001, "data": date(2026, 2, 20), "hora": "09:30", "cliente_id": 1, "vendedor": "admin", "total": 417.30, "desconto": 0, "forma_pagamento": 1, "situacao": 1},
        {"numero_legado": 1002, "data": date(2026, 2, 22), "hora": "14:15", "cliente_id": 2, "vendedor": "admin", "total": 159.60, "desconto": 5.0, "forma_pagamento": 2, "situacao": 1},
        {"numero_legado": 1003, "data": date(2026, 2, 25), "hora": "10:45", "cliente_id": 3, "vendedor": "admin", "total": 1279.20, "desconto": 50.0, "forma_pagamento": 1, "situacao": 1},
        {"numero_legado": 1004, "data": date(2026, 3, 1), "hora": "16:00", "cliente_id": 4, "vendedor": "admin", "total": 95.40, "desconto": 0, "forma_pagamento": 3, "situacao": 1},
    ]
    vendas = []
    for v in vendas_data:
        venda = Venda(**v, cancelada=False)
        db.add(venda)
        vendas.append(venda)
    db.flush()

    # Itens das vendas
    itens_vendas = [
        # Venda 1001: 2x Cabo 2.5mm + 1x Disjuntor 20A
        {"venda_id": vendas[0].id, "produto_id": 1, "codigo_legado": 1, "nome_produto": "Cabo Flex 2.5mm Preto", "quantidade": 2, "preco_unitario": 189.90, "preco_total": 379.80},
        {"venda_id": vendas[0].id, "produto_id": 3, "codigo_legado": 3, "nome_produto": "Disjuntor Monopolar 20A", "quantidade": 2, "preco_unitario": 18.50, "preco_total": 37.00},
        # Venda 1002: 10x Lâmpada LED + 1x Painel LED
        {"venda_id": vendas[1].id, "produto_id": 4, "codigo_legado": 4, "nome_produto": "Lâmpada LED Bulbo 12W", "quantidade": 10, "preco_unitario": 12.90, "preco_total": 129.00},
        {"venda_id": vendas[1].id, "produto_id": 5, "codigo_legado": 5, "nome_produto": "Luminária Painel LED 24W", "quantidade": 1, "preco_unitario": 45.90, "preco_total": 45.90},
        # Venda 1003: 5x Cabo 2.5mm + 20x Tubo PVC + 2x Tinta 18L
        {"venda_id": vendas[2].id, "produto_id": 1, "codigo_legado": 1, "nome_produto": "Cabo Flex 2.5mm Preto", "quantidade": 5, "preco_unitario": 189.90, "preco_total": 949.50},
        {"venda_id": vendas[2].id, "produto_id": 7, "codigo_legado": 7, "nome_produto": "Tubo PVC Soldável 25mm", "quantidade": 20, "preco_unitario": 14.90, "preco_total": 298.00},
        # Venda 1004: 6x Lâmpada LED
        {"venda_id": vendas[3].id, "produto_id": 4, "codigo_legado": 4, "nome_produto": "Lâmpada LED Bulbo 12W", "quantidade": 6, "preco_unitario": 12.90, "preco_total": 77.40},
    ]
    for item in itens_vendas:
        db.add(VendaItem(**item))
    db.flush()
    print(f"  {len(vendas)} vendas com {len(itens_vendas)} itens")

    # Saídas de estoque correspondentes às vendas
    saidas = [
        (1, 7), (3, 2),   # Venda 1001
        (4, 10), (5, 1),  # Venda 1002
        (1, 5), (7, 20),  # Venda 1003
        (4, 6),           # Venda 1004
    ]
    for prod_id, qty in saidas:
        db.add(TransacaoEstoque(
            produto_id=prod_id,
            tipo=TipoTransacao.SAIDA,
            quantidade=-qty,
            motivo="Saída por venda",
            usuario_id=admin.id,
            data_transacao=datetime(2026, 2, 28, 12, 0, 0, tzinfo=timezone.utc),
        ))
    db.flush()

    # === ORÇAMENTOS ===
    orc1 = Orcamento(
        cliente_id=3, cliente_nome="Construtora Horizonte LTDA",
        status="aberto", desconto_geral=100.0,
        observacao="Orçamento para reforma de escritório",
        data_validade=date(2026, 3, 15), criado_por=admin.id,
    )
    db.add(orc1)
    db.flush()
    orc_itens = [
        OrcamentoItem(orcamento_id=orc1.id, produto_id=1, descricao="Cabo Flex 2.5mm Preto (100m)", quantidade=10, preco_unitario=169.90, desconto=0, preco_total=1699.00),
        OrcamentoItem(orcamento_id=orc1.id, produto_id=4, descricao="Lâmpada LED Bulbo 12W", quantidade=50, preco_unitario=11.50, desconto=0, preco_total=575.00),
        OrcamentoItem(orcamento_id=orc1.id, produto_id=6, descricao="Refletor LED 50W", quantidade=4, preco_unitario=72.00, desconto=0, preco_total=288.00),
    ]
    for oi in orc_itens:
        db.add(oi)
    db.flush()
    print(f"  1 orçamento com {len(orc_itens)} itens")

    # === CONTAS A RECEBER ===
    contas = [
        ContaReceber(cliente_id=3, documento=1003, parcela=1, vendedor="admin", data_emissao=date(2026, 2, 25), data_vencimento=date(2026, 3, 25), valor=639.60, valor_pago=0, historico="Ref. venda 1003 - parcela 1/2"),
        ContaReceber(cliente_id=3, documento=1003, parcela=2, vendedor="admin", data_emissao=date(2026, 2, 25), data_vencimento=date(2026, 4, 25), valor=639.60, valor_pago=0, historico="Ref. venda 1003 - parcela 2/2"),
    ]
    for cr in contas:
        db.add(cr)
    db.flush()
    print(f"  {len(contas)} contas a receber")

    db.commit()
    db.close()
    engine.dispose()

    size_mb = os.path.getsize(DB_PATH) / (1024 * 1024)
    print(f"\nBanco demo gerado: {DB_PATH} ({size_mb:.2f} MB)")
    print("Login: admin@loja.com / admin")


if __name__ == "__main__":
    main()
