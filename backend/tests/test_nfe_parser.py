from pathlib import Path

from app.core.nfe_parser import parse_nfe_xml


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _load_fixture_bytes(filename: str) -> bytes:
    return (FIXTURES_DIR / filename).read_bytes()


def test_parse_nfe_xml_com_tributacao_completa_por_item():
    nota = parse_nfe_xml(_load_fixture_bytes("nfe_completa_impostos.xml"))

    assert len(nota.produtos) == 2

    primeiro = nota.produtos[0]
    assert primeiro.cfop == "5102"
    assert primeiro.cst == "00"
    assert primeiro.csosn is None
    assert primeiro.icms_base_calculo == 20.0
    assert primeiro.icms_aliquota == 18.0
    assert primeiro.icms_valor == 3.6
    assert primeiro.frete_rateado == 4.0

    segundo = nota.produtos[1]
    assert segundo.cfop == "5102"
    assert segundo.cst is None
    assert segundo.csosn == "102"
    assert segundo.icms_base_calculo is None
    assert segundo.icms_aliquota is None
    assert segundo.icms_valor is None
    assert segundo.frete_rateado == 6.0


def test_parse_nfe_xml_sem_blocos_fiscais_opcionais_retorna_campos_nulos():
    nota = parse_nfe_xml(_load_fixture_bytes("nfe_minima.xml"))

    produto = nota.produtos[0]
    assert produto.cfop is None
    assert produto.cst is None
    assert produto.csosn is None
    assert produto.icms_base_calculo is None
    assert produto.icms_aliquota is None
    assert produto.icms_valor is None
    assert produto.frete_rateado is None


def test_parse_nfe_xml_fallback_seguro_em_numericos_invalidos():
    xml_content = _load_fixture_bytes("nfe_completa_impostos.xml").replace(b"<vFrete>10.00</vFrete>", b"<vFrete>invalido</vFrete>")
    xml_content = xml_content.replace(b"<vBC>20.00</vBC>", b"<vBC>abc</vBC>")

    nota = parse_nfe_xml(xml_content)

    produto = nota.produtos[0]
    assert produto.icms_base_calculo is None
    assert produto.frete_rateado is None
    assert nota.valor_total == 60.0
