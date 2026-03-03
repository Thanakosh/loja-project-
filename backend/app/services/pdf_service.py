"""Serviço de geração de PDF para orçamentos usando reportlab."""

import io
from datetime import date
from pathlib import Path
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# ---------------------------------------------------------------------------
# Paleta de cores
# ---------------------------------------------------------------------------
AZUL_PRIMARIO = colors.HexColor("#1E40AF")
AZUL_CLARO = colors.HexColor("#DBEAFE")
CINZA_TEXTO = colors.HexColor("#374151")
CINZA_SUAVE = colors.HexColor("#F3F4F6")
CINZA_BORDA = colors.HexColor("#D1D5DB")
VERDE_TOTAL = colors.HexColor("#065F46")
VERDE_BG = colors.HexColor("#ECFDF5")
BRANCO = colors.white

PAGE_W, PAGE_H = A4
MARGIN = 18 * mm
PROJECT_ROOT = Path(__file__).resolve().parents[3]
LOGIN_LOGO_PATH = PROJECT_ROOT / "frontend" / "src" / "assets" / "logo.png"


def _money(value: float) -> str:
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _fmt_date(d) -> str:
    if d is None:
        return "—"
    if isinstance(d, (date,)):
        return d.strftime("%d/%m/%Y")
    try:
        from datetime import datetime
        if isinstance(d, datetime):
            return d.strftime("%d/%m/%Y")
        return str(d)
    except Exception:
        return str(d)


def _header_block(titulo: str, numero: str, styles):
    """Cria bloco de cabeçalho com logo e número do documento."""
    usable_width = PAGE_W - 2 * MARGIN
    header_data = [
        [
            _build_header_logo(styles),
            Paragraph(
                f"<font color='#1E40AF'><b>{titulo}</b></font><br/>"
                f"<font size='11' color='#6B7280'>#{numero}</font>",
                ParagraphStyle(
                    "DocNumStyle",
                    parent=styles["Normal"],
                    fontSize=9,
                    alignment=TA_RIGHT,
                    fontName="Helvetica",
                ),
            ),
        ]
    ]
    header_table = Table(header_data, colWidths=[usable_width * 0.6, usable_width * 0.4])
    header_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return header_table


def _build_header_logo(styles):
    """Retorna flowable da logo do login para o cabeçalho do PDF."""
    if LOGIN_LOGO_PATH.exists():
        logo = Image(str(LOGIN_LOGO_PATH))
        logo.drawHeight = 16 * mm
        logo.drawWidth = 48 * mm
        logo.hAlign = "LEFT"
        return logo

    return Paragraph(
        "<b>Minha Loja</b>",
        ParagraphStyle(
            "LogoFallbackStyle",
            parent=styles["Normal"],
            fontSize=18,
            textColor=AZUL_PRIMARIO,
            fontName="Helvetica-Bold",
        ),
    )


def gerar_pdf_orcamento(orcamento) -> bytes:
    """
    Gera o PDF de um orçamento e retorna os bytes.

    Parâmetros
    ----------
    orcamento : models.orcamento.Orcamento
        Instância ORM com itens já carregados via joinedload.

    Retorna
    -------
    bytes
        Conteúdo binário do PDF gerado.
    """
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN,
        title=f"Orçamento #{orcamento.id}",
    )

    styles = getSampleStyleSheet()

    # ------------------------------------------------------------------
    # Estilos customizados
    # ------------------------------------------------------------------
    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Normal"],
        fontSize=22,
        textColor=AZUL_PRIMARIO,
        fontName="Helvetica-Bold",
        alignment=TA_LEFT,
        spaceAfter=2,
    )
    subtitle_style = ParagraphStyle(
        "SubtitleStyle",
        parent=styles["Normal"],
        fontSize=10,
        textColor=CINZA_TEXTO,
        fontName="Helvetica",
        alignment=TA_LEFT,
    )
    section_header_style = ParagraphStyle(
        "SectionHeader",
        parent=styles["Normal"],
        fontSize=9,
        textColor=BRANCO,
        fontName="Helvetica-Bold",
        alignment=TA_LEFT,
        leftIndent=4,
        spaceAfter=0,
        spaceBefore=0,
    )
    label_style = ParagraphStyle(
        "LabelStyle",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.HexColor("#6B7280"),
        fontName="Helvetica",
    )
    value_style = ParagraphStyle(
        "ValueStyle",
        parent=styles["Normal"],
        fontSize=10,
        textColor=CINZA_TEXTO,
        fontName="Helvetica-Bold",
    )
    obs_style = ParagraphStyle(
        "ObsStyle",
        parent=styles["Normal"],
        fontSize=9,
        textColor=CINZA_TEXTO,
        fontName="Helvetica",
        leading=13,
    )
    footer_style = ParagraphStyle(
        "FooterStyle",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.HexColor("#9CA3AF"),
        fontName="Helvetica",
        alignment=TA_CENTER,
    )

    content = []

    # ------------------------------------------------------------------
    # Cabeçalho: logo (texto) + número do orçamento
    # ------------------------------------------------------------------
    usable_width = PAGE_W - 2 * MARGIN

    header_data = [
        [
            _build_header_logo(styles),
            Paragraph(
                f"<font color='#1E40AF'><b>ORÇAMENTO</b></font><br/>"
                f"<font size='11' color='#6B7280'>#{orcamento.id:05d}</font>",
                ParagraphStyle(
                    "OrcNumStyle", parent=styles["Normal"],
                    fontSize=9, alignment=TA_RIGHT, fontName="Helvetica",
                ),
            ),
        ]
    ]
    header_table = Table(header_data, colWidths=[usable_width * 0.6, usable_width * 0.4])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    content.append(header_table)
    content.append(HRFlowable(width="100%", thickness=2, color=AZUL_PRIMARIO, spaceAfter=8))

    # ------------------------------------------------------------------
    # Informações do orçamento (cliente + datas)
    # ------------------------------------------------------------------
    status_map = {
        "aberto": "Aberto",
        "aprovado": "Aprovado",
        "cancelado": "Cancelado",
        "convertido": "Convertido",
    }
    status_texto = status_map.get(str(orcamento.status), str(orcamento.status))

    info_data = [
        [
            Paragraph("CLIENTE", label_style),
            Paragraph("DATA DE EMISSÃO", label_style),
            Paragraph("VALIDADE", label_style),
            Paragraph("STATUS", label_style),
        ],
        [
            Paragraph(orcamento.cliente_nome or "Não informado", value_style),
            Paragraph(_fmt_date(orcamento.data_criacao), value_style),
            Paragraph(_fmt_date(orcamento.data_validade), value_style),
            Paragraph(status_texto, value_style),
        ],
    ]
    col_w = usable_width / 4
    info_table = Table(info_data, colWidths=[col_w] * 4)
    info_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), CINZA_SUAVE),
        ("BACKGROUND", (0, 1), (-1, 1), BRANCO),
        ("BOX", (0, 0), (-1, -1), 0.5, CINZA_BORDA),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, CINZA_BORDA),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, 0), 5),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 4),
        ("TOPPADDING", (0, 1), (-1, 1), 6),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    content.append(info_table)
    content.append(Spacer(1, 10))

    # ------------------------------------------------------------------
    # Cabeçalho da tabela de itens
    # ------------------------------------------------------------------
    header_row_style = ParagraphStyle(
        "ItemHeader",
        parent=styles["Normal"],
        fontSize=9,
        textColor=BRANCO,
        fontName="Helvetica-Bold",
        alignment=TA_CENTER,
    )

    itens_header = [
        Paragraph("#", header_row_style),
        Paragraph("DESCRIÇÃO", ParagraphStyle("IH2", parent=header_row_style, alignment=TA_LEFT)),
        Paragraph("QTD", header_row_style),
        Paragraph("PREÇO UNIT.", header_row_style),
        Paragraph("DESC.%", header_row_style),
        Paragraph("TOTAL", header_row_style),
    ]

    # Estilos para células de item
    item_center = ParagraphStyle("IC", parent=styles["Normal"], fontSize=9,
                                 textColor=CINZA_TEXTO, fontName="Helvetica", alignment=TA_CENTER)
    item_left = ParagraphStyle("IL", parent=styles["Normal"], fontSize=9,
                               textColor=CINZA_TEXTO, fontName="Helvetica", alignment=TA_LEFT)
    item_right = ParagraphStyle("IR", parent=styles["Normal"], fontSize=9,
                                textColor=CINZA_TEXTO, fontName="Helvetica", alignment=TA_RIGHT)
    item_total = ParagraphStyle("IT", parent=styles["Normal"], fontSize=9,
                                textColor=CINZA_TEXTO, fontName="Helvetica-Bold", alignment=TA_RIGHT)

    col_widths = [
        usable_width * 0.05,   # #
        usable_width * 0.40,   # Descrição
        usable_width * 0.09,   # Qtd
        usable_width * 0.16,   # Preço Unit.
        usable_width * 0.10,   # Desc%
        usable_width * 0.20,   # Total
    ]

    rows = [itens_header]
    for idx, item in enumerate(orcamento.itens, start=1):
        desc_pct = item.desconto or 0.0
        rows.append([
            Paragraph(str(idx), item_center),
            Paragraph(item.descricao or "", item_left),
            Paragraph(f"{item.quantidade:g}", item_center),
            Paragraph(_money(item.preco_unitario), item_right),
            Paragraph(f"{desc_pct:.1f}%", item_center),
            Paragraph(_money(item.preco_total), item_total),
        ])

    # Linha de subtotal (soma dos itens)
    subtotal = sum(i.preco_total for i in orcamento.itens)

    rows.append([
        Paragraph("", item_center),
        Paragraph("", item_center),
        Paragraph("", item_center),
        Paragraph("", item_center),
        Paragraph("Subtotal", ParagraphStyle("ST", parent=item_right, fontName="Helvetica-Bold")),
        Paragraph(_money(subtotal), item_total),
    ])

    desconto_geral = orcamento.desconto_geral or 0.0
    if desconto_geral > 0:
        rows.append([
            Paragraph("", item_center),
            Paragraph("", item_center),
            Paragraph("", item_center),
            Paragraph("", item_center),
            Paragraph("Desconto Geral", ParagraphStyle("DG", parent=item_right, textColor=colors.HexColor("#DC2626"))),
            Paragraph(f"- {_money(desconto_geral)}", ParagraphStyle(
                "DGV", parent=item_total, textColor=colors.HexColor("#DC2626")
            )),
        ])

    # Total final
    total = subtotal - desconto_geral
    rows.append([
        Paragraph("", item_center),
        Paragraph("", item_center),
        Paragraph("", item_center),
        Paragraph("", item_center),
        Paragraph("TOTAL", ParagraphStyle("TL", parent=item_right, fontSize=11,
                                          fontName="Helvetica-Bold", textColor=VERDE_TOTAL)),
        Paragraph(_money(total), ParagraphStyle("TLV", parent=item_total, fontSize=11,
                                                fontName="Helvetica-Bold", textColor=VERDE_TOTAL)),
    ])

    n_itens = len(orcamento.itens)
    n_rows = len(rows)

    item_table = Table(rows, colWidths=col_widths, repeatRows=1)

    # Estilo base
    ts = TableStyle([
        # Cabeçalho
        ("BACKGROUND", (0, 0), (-1, 0), AZUL_PRIMARIO),
        ("TEXTCOLOR", (0, 0), (-1, 0), BRANCO),
        ("TOPPADDING", (0, 0), (-1, 0), 7),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 7),
        # Linhas de item (zebra)
        ("ROWBACKGROUNDS", (0, 1), (-1, n_itens), [BRANCO, CINZA_SUAVE]),
        # Padding geral
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 1), (-1, n_itens), 5),
        ("BOTTOMPADDING", (0, 1), (-1, n_itens), 5),
        # Borda externa
        ("BOX", (0, 0), (-1, n_itens), 0.5, CINZA_BORDA),
        ("INNERGRID", (0, 0), (-1, n_itens), 0.25, CINZA_BORDA),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        # Linhas de rodapé da tabela (sem borda interna)
        ("LINEABOVE", (0, n_itens + 1), (-1, n_itens + 1), 1, CINZA_BORDA),
        ("TOPPADDING", (0, n_itens + 1), (-1, -1), 4),
        ("BOTTOMPADDING", (0, n_itens + 1), (-1, -1), 4),
    ])

    # Linha de total com fundo verde
    ts.add("BACKGROUND", (0, n_rows - 1), (-1, n_rows - 1), VERDE_BG)
    ts.add("LINEABOVE", (0, n_rows - 1), (-1, n_rows - 1), 1.5, VERDE_TOTAL)

    item_table.setStyle(ts)
    content.append(item_table)
    content.append(Spacer(1, 10))

    # ------------------------------------------------------------------
    # Observação
    # ------------------------------------------------------------------
    if orcamento.observacao:
        obs_block_data = [
            [Paragraph("OBSERVAÇÕES", section_header_style)],
            [Paragraph(orcamento.observacao, obs_style)],
        ]
        obs_table = Table(obs_block_data, colWidths=[usable_width])
        obs_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), AZUL_PRIMARIO),
            ("BACKGROUND", (0, 1), (-1, 1), CINZA_SUAVE),
            ("BOX", (0, 0), (-1, -1), 0.5, CINZA_BORDA),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, 0), 5),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 5),
            ("TOPPADDING", (0, 1), (-1, 1), 8),
            ("BOTTOMPADDING", (0, 1), (-1, 1), 8),
        ]))
        content.append(obs_table)
        content.append(Spacer(1, 10))

    # ------------------------------------------------------------------
    # Rodapé
    # ------------------------------------------------------------------
    content.append(HRFlowable(width="100%", thickness=0.5, color=CINZA_BORDA, spaceBefore=4, spaceAfter=6))
    content.append(Paragraph(
        "Este orçamento foi gerado automaticamente pelo sistema. "
        "Para dúvidas, entre em contato com nossa equipe.",
        footer_style,
    ))

    doc.build(content)
    return buffer.getvalue()


def gerar_pdf_comprovante_venda(venda) -> bytes:
    """Gera comprovante simples de venda em PDF."""
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN,
        title=f"Comprovante Venda #{venda.numero_legado}",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ComprovanteTitle",
        parent=styles["Normal"],
        fontSize=18,
        textColor=AZUL_PRIMARIO,
        fontName="Helvetica-Bold",
        alignment=TA_LEFT,
    )
    normal_style = ParagraphStyle(
        "ComprovanteNormal",
        parent=styles["Normal"],
        fontSize=9,
        textColor=CINZA_TEXTO,
        fontName="Helvetica",
        alignment=TA_LEFT,
    )
    right_style = ParagraphStyle(
        "ComprovanteRight",
        parent=normal_style,
        alignment=TA_RIGHT,
    )

    content = []
    usable_width = PAGE_W - 2 * MARGIN

    header_data = [
        [
            _build_header_logo(styles),
            Paragraph(
                f"<font color='#1E40AF'><b>COMPROVANTE DE VENDA</b></font><br/>"
                f"<font size='11' color='#6B7280'>#{venda.numero_legado:05d}</font>",
                ParagraphStyle("CompNumStyle", parent=styles["Normal"], fontSize=9, alignment=TA_RIGHT),
            ),
        ]
    ]
    header_table = Table(header_data, colWidths=[usable_width * 0.6, usable_width * 0.4])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    content.append(header_table)
    content.append(HRFlowable(width="100%", thickness=2, color=AZUL_PRIMARIO, spaceAfter=8))

    forma_pagamento_map = {
        1: "Dinheiro",
        2: "Cartão Débito",
        3: "Cartão Crédito",
        4: "PIX",
        5: "Boleto",
        6: "A Prazo",
    }
    forma_pagamento = forma_pagamento_map.get(venda.forma_pagamento, "Não informado")
    info = [
        [Paragraph("Data", normal_style), Paragraph(_fmt_date(venda.data), right_style)],
        [Paragraph("Cliente", normal_style), Paragraph(venda.cliente.nome if venda.cliente else "Consumidor final", right_style)],
        [Paragraph("Pagamento", normal_style), Paragraph(forma_pagamento, right_style)],
    ]
    if venda.autorizacao_terceiro_nome:
        info.append([
            Paragraph("Autorizado para retirada", normal_style),
            Paragraph(venda.autorizacao_terceiro_nome, right_style),
        ])
    info_table = Table(info, colWidths=[usable_width * 0.45, usable_width * 0.55])
    info_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CINZA_SUAVE),
        ("BOX", (0, 0), (-1, -1), 0.5, CINZA_BORDA),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, CINZA_BORDA),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    content.append(info_table)
    content.append(Spacer(1, 10))

    rows = [["#", "Produto", "Qtd", "Unit.", "Desc%", "Total"]]
    for idx, item in enumerate(venda.itens, start=1):
        rows.append([
            str(idx),
            item.nome_produto or "",
            f"{item.quantidade:g}",
            _money(item.preco_unitario),
            f"{(item.desconto or 0.0):.1f}%",
            _money(item.preco_total),
        ])

    subtotal = sum(i.preco_total for i in venda.itens)
    rows.append(["", "", "", "", "Subtotal", _money(subtotal)])
    if (venda.desconto or 0.0) > 0:
        rows.append(["", "", "", "", "Desconto", f"- {_money(venda.desconto)}"])
    rows.append(["", "", "", "", "TOTAL", _money(venda.total)])

    item_table = Table(
        rows,
        colWidths=[usable_width * 0.06, usable_width * 0.42, usable_width * 0.1, usable_width * 0.16, usable_width * 0.1, usable_width * 0.16],
        repeatRows=1,
    )
    item_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), AZUL_PRIMARIO),
        ("TEXTCOLOR", (0, 0), (-1, 0), BRANCO),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [BRANCO, CINZA_SUAVE]),
        ("BOX", (0, 0), (-1, -1), 0.5, CINZA_BORDA),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, CINZA_BORDA),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    content.append(item_table)
    content.append(Spacer(1, 10))

    if venda.observacao or venda.autorizacao_terceiro_observacao:
        texto_obs = venda.observacao or ""
        if venda.autorizacao_terceiro_observacao:
            texto_obs = f"{texto_obs}\nAutorização: {venda.autorizacao_terceiro_observacao}".strip()
        content.append(Paragraph("<b>Observações</b>", normal_style))
        content.append(Paragraph(texto_obs, normal_style))
        content.append(Spacer(1, 8))

    content.append(HRFlowable(width="100%", thickness=0.5, color=CINZA_BORDA, spaceBefore=4, spaceAfter=6))
    content.append(Paragraph("Documento não fiscal de conferência da compra.", ParagraphStyle(
        "ComprovanteFooter",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.HexColor("#9CA3AF"),
        alignment=TA_CENTER,
    )))

    doc.build(content)
    return buffer.getvalue()
