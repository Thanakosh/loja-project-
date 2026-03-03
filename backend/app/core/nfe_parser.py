"""Parser de Nota Fiscal Eletrônica (NFe) em XML e extração de texto de PDF."""

import importlib.util
import re
from typing import List, Optional
from xml.etree import ElementTree as ET

from ..schemas.ocr import NotaFiscalExtraida, ProdutoExtraido


# ─── Namespace da NFe ───
NFE_NS = {
    "nfe": "http://www.portalfiscal.inf.br/nfe",
}


def _find_text(element: Optional[ET.Element], path: str, ns: dict = NFE_NS) -> Optional[str]:
    """Busca texto em um elemento XML com namespace."""
    if element is None:
        return None
    node = element.find(path, ns)
    return node.text.strip() if node is not None and node.text else None




def _first_not_none(*elements: Optional[ET.Element]) -> Optional[ET.Element]:
    for element in elements:
        if element is not None:
            return element
    return None

def parse_nfe_xml(xml_content: bytes) -> NotaFiscalExtraida:
    """
    Faz o parse de um XML de NFe brasileira e retorna dados estruturados.
    Funciona tanto com o XML completo (nfeProc) quanto com o corpo (NFe).
    """
    root = ET.fromstring(xml_content)

    # Tentar encontrar o nó infNFe (pode estar dentro de nfeProc > NFe ou direto)
    inf_nfe = root.find(".//nfe:infNFe", NFE_NS)
    if inf_nfe is None:
        # Tentar sem namespace (alguns XMLs não usam)
        inf_nfe = root.find(".//infNFe")
    if inf_nfe is None:
        # Fallback: tentar com namespace dinâmico
        for elem in root.iter():
            if elem.tag.endswith("infNFe"):
                inf_nfe = elem
                break

    if inf_nfe is None:
        raise ValueError("XML não contém um nó infNFe válido. Verifique se é um XML de NFe.")

    # ─── Detectar namespace real ───
    tag = inf_nfe.tag
    ns_real = {}
    if "{" in tag:
        ns_uri = tag.split("}")[0] + "}"
        ns_real = {"nfe": ns_uri.strip("{}")}
    else:
        ns_real = {}

    def _ft(element, path):
        """Find text helper com namespace dinâmico."""
        if element is None:
            return None
        # Tentar com namespace
        if ns_real:
            node = element.find(path, ns_real)
            if node is not None and node.text:
                return node.text.strip()
        # Tentar sem namespace
        plain_path = re.sub(r"nfe:", "", path)
        node = element.find(plain_path)
        return node.text.strip() if node is not None and node.text else None

    # ─── Emitente (fornecedor) ───
    emit = _first_not_none(inf_nfe.find("nfe:emit", ns_real), inf_nfe.find("emit"))
    fornecedor = _ft(emit, "nfe:xNome") or _ft(emit, "xNome") or "Não identificado"
    nome_fantasia = _ft(emit, "nfe:xFant") or _ft(emit, "xFant")
    cnpj = _ft(emit, "nfe:CNPJ") or _ft(emit, "CNPJ") or ""

    # Formatar CNPJ
    if cnpj and len(cnpj) == 14:
        cnpj = f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"

    # ─── Identificação da nota ───
    ide = _first_not_none(inf_nfe.find("nfe:ide", ns_real), inf_nfe.find("ide"))
    numero_nota = _ft(ide, "nfe:nNF") or _ft(ide, "nNF") or ""
    data_emissao = _ft(ide, "nfe:dhEmi") or _ft(ide, "dhEmi") or ""
    # Extrair apenas a data (YYYY-MM-DD) de datetime
    if data_emissao and "T" in data_emissao:
        data_emissao = data_emissao.split("T")[0]

    # ─── Frete total da nota (para rateio por item) — lido de ICMSTot/vFrete ───
    frete_total = 0.0
    total_node_tmp = _first_not_none(inf_nfe.find("nfe:total", ns_real), inf_nfe.find("total"))
    if total_node_tmp is not None:
        icms_tot_tmp = _first_not_none(
            total_node_tmp.find("nfe:ICMSTot", ns_real), total_node_tmp.find("ICMSTot")
        )
        if icms_tot_tmp is not None:
            frete_str = _ft(icms_tot_tmp, "nfe:vFrete") or _ft(icms_tot_tmp, "vFrete") or "0"
            try:
                frete_total = float(frete_str)
            except (ValueError, TypeError):
                frete_total = 0.0

    # ─── Produtos/Itens ───
    produtos: List[ProdutoExtraido] = []

    # Buscar todos os elementos det (detalhe)
    dets = inf_nfe.findall("nfe:det", ns_real)
    if not dets:
        dets = inf_nfe.findall("det")

    # Pré-calcular valor total dos produtos para rateio de frete proporcional
    def _safe_float(value: Optional[str], default: float = 0.0) -> float:
        try:
            return float(value) if value else default
        except (ValueError, TypeError):
            return default

    # Primeira passagem: coletar vProd para rateio de frete
    valor_total_produtos = 0.0
    for det in dets:
        prod_tmp = _first_not_none(det.find("nfe:prod", ns_real), det.find("prod"))
        if prod_tmp is not None:
            vp = _ft(prod_tmp, "nfe:vProd") or _ft(prod_tmp, "vProd") or "0"
            valor_total_produtos += _safe_float(vp)

    for det in dets:
        prod = _first_not_none(det.find("nfe:prod", ns_real), det.find("prod"))
        if prod is None:
            continue

        nome = _ft(prod, "nfe:xProd") or _ft(prod, "xProd") or "Produto sem nome"
        unidade = _ft(prod, "nfe:uCom") or _ft(prod, "uCom") or "UN"

        # Quantidade
        qtd_str = _ft(prod, "nfe:qCom") or _ft(prod, "qCom") or "1"
        try:
            quantidade = int(float(qtd_str))
            if quantidade < 1:
                quantidade = 1
        except (ValueError, TypeError):
            quantidade = 1

        # Preço unitário
        preco_str = _ft(prod, "nfe:vUnCom") or _ft(prod, "vUnCom") or "0"
        try:
            preco_unitario = round(float(preco_str), 2)
        except (ValueError, TypeError):
            preco_unitario = 0.0

        # NCM
        ncm = _ft(prod, "nfe:NCM") or _ft(prod, "NCM") or ""

        # Código de barras (EAN/GTIN)
        cean_raw = _ft(prod, "nfe:cEAN") or _ft(prod, "cEAN") or ""
        cean_trib = _ft(prod, "nfe:cEANTrib") or _ft(prod, "cEANTrib") or ""
        # cEAN pode vir como "SEM GTIN" — ignorar nesses casos
        codigo_barras: str | None = None
        if cean_raw and cean_raw.strip().isdigit() and len(cean_raw.strip()) >= 8:
            codigo_barras = cean_raw.strip()
        elif cean_trib and cean_trib.strip().isdigit() and len(cean_trib.strip()) >= 8:
            codigo_barras = cean_trib.strip()

        # ─── CFOP ───
        cfop = _ft(prod, "nfe:CFOP") or _ft(prod, "CFOP") or None

        # ─── Frete rateado por item (proporcional ao vProd) ───
        frete_rateado: Optional[float] = None
        if frete_total > 0.0 and valor_total_produtos > 0.0:
            vprod = _safe_float(_ft(prod, "nfe:vProd") or _ft(prod, "vProd"))
            frete_rateado = round(frete_total * vprod / valor_total_produtos, 4)

        # ─── ICMS por item ───
        cst: Optional[str] = None
        csosn: Optional[str] = None
        icms_base: Optional[float] = None
        icms_aliquota: Optional[float] = None
        icms_valor: Optional[float] = None

        imposto = _first_not_none(det.find("nfe:imposto", ns_real), det.find("imposto"))
        if imposto is not None:
            icms_group = _first_not_none(imposto.find("nfe:ICMS", ns_real), imposto.find("ICMS"))
            if icms_group is not None:
                # Iterar sobre filhos do grupo ICMS (ICMS00, ICMS10, ..., ICMSSN101, etc.)
                children = list(icms_group)
                for icms_node in children:
                    # CST (regime normal) ou CSOSN (Simples Nacional)
                    cst_val = _ft(icms_node, "nfe:CST") or _ft(icms_node, "CST")
                    csosn_val = _ft(icms_node, "nfe:CSOSN") or _ft(icms_node, "CSOSN")
                    if cst_val:
                        cst = cst_val
                    if csosn_val:
                        csosn = csosn_val
                    # Base de cálculo ICMS
                    vbc = _ft(icms_node, "nfe:vBC") or _ft(icms_node, "vBC")
                    if vbc is not None:
                        icms_base = _safe_float(vbc)
                    # Alíquota ICMS
                    picms = _ft(icms_node, "nfe:pICMS") or _ft(icms_node, "pICMS")
                    if picms is not None:
                        icms_aliquota = _safe_float(picms)
                    # Valor ICMS
                    vicms = _ft(icms_node, "nfe:vICMS") or _ft(icms_node, "vICMS")
                    if vicms is not None:
                        icms_valor = _safe_float(vicms)

        produtos.append(
            ProdutoExtraido(
                nome=nome,
                quantidade=quantidade,
                preco_unitario=preco_unitario,
                unidade=unidade.upper(),
                codigo_ncm=ncm,
                codigo_barras=codigo_barras,
                cfop=cfop,
                cst=cst,
                csosn=csosn,
                icms_base=icms_base,
                icms_aliquota=icms_aliquota,
                icms_valor=icms_valor,
                frete_rateado=frete_rateado,
            )
        )

    # ─── Valor total ───
    total_node = _first_not_none(inf_nfe.find("nfe:total", ns_real), inf_nfe.find("total"))
    icms_tot = None
    if total_node is not None:
        icms_tot = _first_not_none(total_node.find("nfe:ICMSTot", ns_real), total_node.find("ICMSTot"))

    valor_total_str = "0"
    if icms_tot is not None:
        valor_total_str = _ft(icms_tot, "nfe:vNF") or _ft(icms_tot, "vNF") or "0"

    try:
        valor_total = round(float(valor_total_str), 2)
    except (ValueError, TypeError):
        valor_total = sum(p.preco_unitario * p.quantidade for p in produtos)

    return NotaFiscalExtraida(
        fornecedor=fornecedor,
        nome_fantasia_fornecedor=nome_fantasia if nome_fantasia else None,
        cnpj_fornecedor=cnpj if cnpj else None,
        numero_nota=numero_nota if numero_nota else None,
        data_emissao=data_emissao if data_emissao else None,
        produtos=produtos,
        valor_total=valor_total,
    )


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extrai texto de um PDF usando pdfplumber.
    Retorna o texto concatenado de todas as páginas.
    """
    if importlib.util.find_spec("pdfplumber") is None:
        raise ImportError(
            "Dependência 'pdfplumber' não instalada. "
            "Instale com: pip install -r requirements-ocr.txt"
        )

    import pdfplumber

    text_parts = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)

            # Também extrair tabelas se houver
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    if row:
                        row_text = " | ".join(cell or "" for cell in row)
                        text_parts.append(row_text)

    return "\n".join(text_parts)
