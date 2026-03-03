from decimal import Decimal
from pathlib import Path

from app.core.nfe_parser import parse_nfe_xml
from app.fiscal.normalizer import VERSAO_PAYLOAD_FISCAL, normalizar_nota_fiscal


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _load_fixture_bytes(filename: str) -> bytes:
    return (FIXTURES_DIR / filename).read_bytes()


def test_normalizar_nota_fiscal_gera_payload_canonico_versionado():
    nota = parse_nfe_xml(_load_fixture_bytes("nfe_minima.xml"))

    payload = normalizar_nota_fiscal(nota)

    assert payload.versao_payload == VERSAO_PAYLOAD_FISCAL
    assert payload.fornecedor_nome == "Fornecedor Exemplo LTDA"
    assert payload.fornecedor_cnpj == "12.345.678/0001-23"
    assert payload.numero_nota == "123"
    assert str(payload.data_emissao) == "2024-06-01"
    assert payload.valor_total_nota == Decimal("21.0")

    item = payload.itens[0]
    assert item.sequencia == 1
    assert item.descricao == "Produto de Teste"
    assert item.quantidade == Decimal("2")
    assert item.unidade_comercial == "UN"
    assert item.valor_unitario == Decimal("10.5")
    assert item.valor_total_item == Decimal("21.0")


def test_normalizar_nota_fiscal_preserva_campos_fiscais_por_item():
    nota = parse_nfe_xml(_load_fixture_bytes("nfe_completa_impostos.xml"))

    payload = normalizar_nota_fiscal(nota)

    primeiro = payload.itens[0]
    assert primeiro.cfop == "5102"
    assert primeiro.cst == "00"
    assert primeiro.csosn is None
    assert primeiro.icms_base_calculo == Decimal("20.0")
    assert primeiro.icms_aliquota == Decimal("18.0")
    assert primeiro.icms_valor == Decimal("3.6")
    assert primeiro.frete_rateado == Decimal("4.0")

    segundo = payload.itens[1]
    assert segundo.cfop == "5102"
    assert segundo.cst is None
    assert segundo.csosn == "102"
