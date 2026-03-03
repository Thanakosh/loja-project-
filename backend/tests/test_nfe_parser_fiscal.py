"""
Testes do parser NFe XML — campos fiscais por item (TASK-029).

Cobre:
- XML com tributação completa (CST, ICMS, CFOP, frete rateado)
- XML com Simples Nacional (CSOSN sem base/alíquota/valor ICMS)
- XML mínimo sem blocos fiscais opcionais (fallback seguro)
"""

from pathlib import Path

import pytest

from app.core.nfe_parser import parse_nfe_xml

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _load(filename: str) -> bytes:
    return (FIXTURES_DIR / filename).read_bytes()


# ─── XML mínimo existente: não deve quebrar após adição dos novos campos ───

def test_parse_nfe_minima_sem_campos_fiscais_nao_quebra():
    """XML mínimo sem imposto não deve falhar — fallback seguro."""
    result = parse_nfe_xml(_load("nfe_minima.xml"))
    assert len(result.produtos) >= 1
    produto = result.produtos[0]
    # Campos fiscais devem ser None quando ausentes no XML
    assert produto.cfop is None
    assert produto.cst is None
    assert produto.csosn is None
    assert produto.icms_base_calculo is None
    assert produto.icms_aliquota is None
    assert produto.icms_valor is None
    assert produto.frete_rateado is None


# ─── XML com tributação completa ───

def test_parse_nfe_fiscal_completa_dois_produtos():
    """XML com dois itens deve retornar dois produtos."""
    result = parse_nfe_xml(_load("nfe_fiscal_completa.xml"))
    assert len(result.produtos) == 2


def test_parse_nfe_fiscal_completa_cfop_extraido():
    """CFOP deve ser extraído corretamente para cada produto."""
    result = parse_nfe_xml(_load("nfe_fiscal_completa.xml"))
    assert result.produtos[0].cfop == "1102"
    assert result.produtos[1].cfop == "1403"


def test_parse_nfe_fiscal_completa_cst_icms_regime_normal():
    """CST do ICMS deve ser extraído no produto tributado pelo regime normal."""
    result = parse_nfe_xml(_load("nfe_fiscal_completa.xml"))
    produto = result.produtos[0]
    assert produto.cst == "00"
    assert produto.csosn is None


def test_parse_nfe_fiscal_completa_icms_base_aliquota_valor():
    """Base de cálculo, alíquota e valor de ICMS devem ser extraídos."""
    result = parse_nfe_xml(_load("nfe_fiscal_completa.xml"))
    produto = result.produtos[0]
    assert produto.icms_base_calculo == pytest.approx(500.00)
    assert produto.icms_aliquota == pytest.approx(12.00)
    assert produto.icms_valor == pytest.approx(60.00)


def test_parse_nfe_fiscal_completa_csosn_simples_nacional():
    """CSOSN deve ser extraído para produto Simples Nacional; CST deve ser None."""
    result = parse_nfe_xml(_load("nfe_fiscal_completa.xml"))
    produto = result.produtos[1]
    assert produto.csosn == "102"
    assert produto.cst is None
    assert produto.icms_base_calculo is None
    assert produto.icms_aliquota is None
    assert produto.icms_valor is None


def test_parse_nfe_fiscal_completa_frete_rateado():
    """Frete deve ser rateado proporcionalmente ao vProd de cada item."""
    result = parse_nfe_xml(_load("nfe_fiscal_completa.xml"))
    p0 = result.produtos[0]  # vProd=500.00 de 1500.00 total → 1/3 de 150
    p1 = result.produtos[1]  # vProd=1000.00 de 1500.00 total → 2/3 de 150

    assert p0.frete_rateado == pytest.approx(50.0, rel=1e-3)
    assert p1.frete_rateado == pytest.approx(100.0, rel=1e-3)


def test_parse_nfe_fiscal_completa_campos_basicos_preservados():
    """Campos originais (nome, qty, preço, NCM, EAN) não devem regredir."""
    result = parse_nfe_xml(_load("nfe_fiscal_completa.xml"))
    p0 = result.produtos[0]
    assert p0.nome == "Produto Tributado Normal"
    assert p0.quantidade == 10
    assert p0.preco_unitario == pytest.approx(50.00)
    assert p0.codigo_ncm == "22030000"
    assert p0.codigo_barras == "7891234567890"
    assert p0.unidade == "UN"

    p1 = result.produtos[1]
    assert p1.nome == "Produto Simples Nacional"
    assert p1.quantidade == 5
    assert p1.preco_unitario == pytest.approx(200.00)
    assert p1.codigo_ncm == "84713012"
    assert p1.codigo_barras is None  # cEAN "SEM GTIN" deve ser ignorado
    assert p1.unidade == "CX"


def test_parse_nfe_fiscal_completa_valor_total_preservado():
    """Valor total da nota não deve regredir após adição dos campos fiscais."""
    result = parse_nfe_xml(_load("nfe_fiscal_completa.xml"))
    assert result.valor_total == pytest.approx(1650.00)
