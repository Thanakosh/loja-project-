"""
Testes unitários para as funções de transformação do ETL DBF → SQLite.
Não requer os arquivos .DBF reais.
"""

import os
import sys
from datetime import date
from pathlib import Path

import pytest

# Setup path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Env vars mínimas
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-key-with-minimum-length-ok")

from scripts.etl_dbf import safe_str, safe_float, safe_int, safe_date


# ─────────────────── safe_str ─────────────────────

class TestSafeStr:
    def test_normal(self):
        assert safe_str("  JOAO BATISTA  ") == "JOAO BATISTA"

    def test_none(self):
        assert safe_str(None) is None

    def test_empty(self):
        assert safe_str("") is None
        assert safe_str("   ") is None

    def test_max_len(self):
        assert safe_str("A" * 100, 10) == "A" * 10

    def test_numeric_input(self):
        assert safe_str(12345) == "12345"


# ─────────────────── safe_float ───────────────────

class TestSafeFloat:
    def test_normal(self):
        assert safe_float("102.5") == 102.5

    def test_none(self):
        assert safe_float(None) == 0.0

    def test_int(self):
        assert safe_float(10) == 10.0

    def test_invalid(self):
        assert safe_float("abc") == 0.0

    def test_already_float(self):
        assert safe_float(3.14) == 3.14


# ─────────────────── safe_int ─────────────────────

class TestSafeInt:
    def test_normal(self):
        assert safe_int("42") == 42

    def test_none(self):
        assert safe_int(None) == 0

    def test_float_string(self):
        assert safe_int("3.7") == 3

    def test_invalid(self):
        assert safe_int("xyz") == 0


# ─────────────────── safe_date ────────────────────

class TestSafeDate:
    def test_date_object(self):
        d = date(2024, 1, 15)
        assert safe_date(d) == d

    def test_none(self):
        assert safe_date(None) is None

    def test_string_none(self):
        assert safe_date("None") is None

    def test_empty(self):
        assert safe_date("") is None

    def test_iso_format(self):
        assert safe_date("2024-01-15") == date(2024, 1, 15)

    def test_br_format_dash(self):
        assert safe_date("15-01-2024") == date(2024, 1, 15)

    def test_br_format_slash(self):
        assert safe_date("15/01/2024") == date(2024, 1, 15)

    def test_invalid(self):
        assert safe_date("not-a-date") is None


# ─────────── Testes de integração com modelos ──────────

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models import (
    Cliente, Produto, Venda, VendaItem,
    ContaReceber, MovimentacaoEstoque,
    NotaFiscal, NotaFiscalItem,
)


@pytest.fixture(scope="module")
def test_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def session(test_engine):
    connection = test_engine.connect()
    transaction = connection.begin()
    sess = sessionmaker(bind=connection)()
    yield sess
    sess.close()
    transaction.rollback()
    connection.close()


class TestModelCreation:
    """Verifica que todos os modelos novos são criáveis e persistíveis."""

    def test_create_cliente(self, session: Session):
        c = Cliente(codigo_legado=1, nome="VENDA A VISTA")
        session.add(c)
        session.flush()
        assert c.id is not None
        assert c.codigo_legado == 1

    def test_create_venda_with_items(self, session: Session):
        c = Cliente(codigo_legado=100, nome="TESTE CLIENTE")
        session.add(c)
        session.flush()

        p = Produto(
            nome="DISJUNTOR 20A",
            fornecedor="IMPORTADO_DBF",
            preco_unitario=25.0,
            preco_liquido=15.0,
        )
        session.add(p)
        session.flush()

        v = Venda(
            numero_legado=1,
            data=date(2024, 1, 1),
            cliente_id=c.id,
            total=50.0,
        )
        session.add(v)
        session.flush()

        item = VendaItem(
            venda_id=v.id,
            produto_id=p.id,
            codigo_legado=5806,
            nome_produto="DISJUNTOR 20A",
            quantidade=2.0,
            preco_unitario=25.0,
            preco_total=50.0,
        )
        session.add(item)
        session.flush()

        assert v.id is not None
        assert item.venda_id == v.id

    def test_create_conta_receber(self, session: Session):
        c = Cliente(codigo_legado=200, nome="TESTE CR")
        session.add(c)
        session.flush()

        cr = ContaReceber(
            cliente_id=c.id,
            documento=10,
            parcela=1,
            valor=500.0,
            data_emissao=date(2024, 1, 1),
            data_vencimento=date(2024, 2, 1),
        )
        session.add(cr)
        session.flush()
        assert cr.id is not None
        assert cr.em_aberto is True

    def test_create_movimentacao(self, session: Session):
        p = Produto(
            nome="CABO PP 2x1",
            fornecedor="IMPORTADO_DBF",
            preco_unitario=5.0,
            preco_liquido=3.0,
        )
        session.add(p)
        session.flush()

        m = MovimentacaoEstoque(
            data=date(2024, 1, 1),
            produto_id=p.id,
            codigo_legado=953,
            nome_produto="CABO PP 2x1",
            saldo_anterior=100,
            saida=10,
            saldo_final=90,
        )
        session.add(m)
        session.flush()
        assert m.id is not None

    def test_create_nota_fiscal_with_items(self, session: Session):
        nf = NotaFiscal(
            numero_legado=1,
            chave_acesso="52171208783137000171650010000000011000000120",
            data_emissao=date(2017, 12, 15),
            situacao=0,
            valor_total=14.5,
        )
        session.add(nf)
        session.flush()

        item = NotaFiscalItem(
            nota_fiscal_id=nf.id,
            codigo_legado=11263,
            nome_produto="LAMPADA BULBO LED 9W",
            quantidade=1.0,
            preco_unitario=14.5,
            preco_total=14.5,
            ncm="85395000",
            cfop="5405",
            cst="500",
        )
        session.add(item)
        session.flush()
        assert item.nota_fiscal_id == nf.id


class TestClienteDedup:
    """Testa que codigo_legado é único (constraint)."""

    def test_unique_codigo_legado(self, session: Session):
        c1 = Cliente(codigo_legado=999, nome="CLIENTE A")
        session.add(c1)
        session.flush()

        c2 = Cliente(codigo_legado=999, nome="CLIENTE B")
        session.add(c2)
        with pytest.raises(Exception):  # IntegrityError
            session.flush()
