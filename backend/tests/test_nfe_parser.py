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


def test_parse_nfe_xml_extrai_dados_cadastrais_do_fornecedor():
    xml = b"""<?xml version="1.0" encoding="UTF-8"?>
<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00">
  <NFe>
    <infNFe Id="NFe123" versao="4.00">
      <ide>
        <nNF>1</nNF>
        <dhEmi>2026-03-18T12:58:56-03:00</dhEmi>
      </ide>
      <emit>
        <CNPJ>47854913000139</CNPJ>
        <xNome>SOLAR LED MATERIAIS ELETRICOS LTDA</xNome>
        <xFant>SOLAR LED</xFant>
        <email>contato@solarled.com.br</email>
        <enderEmit>
          <xLgr>AVENIDA INDEPENDENCIA</xLgr>
          <nro>6080</nro>
          <xMun>GOIANIA</xMun>
          <UF>GO</UF>
          <CEP>74070010</CEP>
          <fone>6239246034</fone>
        </enderEmit>
      </emit>
      <det nItem="1">
        <prod>
          <cProd>1</cProd>
          <xProd>Produto Teste</xProd>
          <uCom>UN</uCom>
          <qCom>1.00</qCom>
          <vUnCom>10.00</vUnCom>
        </prod>
      </det>
      <total>
        <ICMSTot>
          <vNF>10.00</vNF>
        </ICMSTot>
      </total>
    </infNFe>
  </NFe>
</nfeProc>"""

    nota = parse_nfe_xml(xml)

    assert nota.telefone_fornecedor == "6239246034"
    assert nota.email_fornecedor == "contato@solarled.com.br"
    assert nota.endereco_fornecedor == "AVENIDA INDEPENDENCIA, 6080"
    assert nota.cidade_fornecedor == "GOIANIA"
    assert nota.uf_fornecedor == "GO"
    assert nota.cep_fornecedor == "74070010"
