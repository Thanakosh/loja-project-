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
    emit = inf_nfe.find("nfe:emit", ns_real) or inf_nfe.find("emit")
    fornecedor = _ft(emit, "nfe:xNome") or _ft(emit, "xNome") or "Não identificado"
    cnpj = _ft(emit, "nfe:CNPJ") or _ft(emit, "CNPJ") or ""

    # Formatar CNPJ
    if cnpj and len(cnpj) == 14:
        cnpj = f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"

    # ─── Identificação da nota ───
    ide = inf_nfe.find("nfe:ide", ns_real) or inf_nfe.find("ide")
    numero_nota = _ft(ide, "nfe:nNF") or _ft(ide, "nNF") or ""
    data_emissao = _ft(ide, "nfe:dhEmi") or _ft(ide, "dhEmi") or ""
    # Extrair apenas a data (YYYY-MM-DD) de datetime
    if data_emissao and "T" in data_emissao:
        data_emissao = data_emissao.split("T")[0]

    # ─── Produtos/Itens ───
    produtos: List[ProdutoExtraido] = []

    # Buscar todos os elementos det (detalhe)
    dets = inf_nfe.findall("nfe:det", ns_real) or inf_nfe.findall("det")
    for det in dets:
        prod = det.find("nfe:prod", ns_real) or det.find("prod")
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

        produtos.append(
            ProdutoExtraido(
                nome=nome,
                quantidade=quantidade,
                preco_unitario=preco_unitario,
                unidade=unidade.upper(),
                codigo_ncm=ncm,
            )
        )

    # ─── Valor total ───
    total_node = inf_nfe.find("nfe:total", ns_real) or inf_nfe.find("total")
    icms_tot = None
    if total_node is not None:
        icms_tot = total_node.find("nfe:ICMSTot", ns_real) or total_node.find("ICMSTot")

    valor_total_str = "0"
    if icms_tot is not None:
        valor_total_str = _ft(icms_tot, "nfe:vNF") or _ft(icms_tot, "vNF") or "0"

    try:
        valor_total = round(float(valor_total_str), 2)
    except (ValueError, TypeError):
        valor_total = sum(p.preco_unitario * p.quantidade for p in produtos)

    return NotaFiscalExtraida(
        fornecedor=fornecedor,
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
            "Instale com: pip install pdfplumber"
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
