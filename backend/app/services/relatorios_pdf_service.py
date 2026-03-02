"""Serviço de geração de PDF para relatórios."""

import io
from datetime import date, datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import HRFlowable, Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

AZUL_PRIMARIO = colors.HexColor("#1E40AF")
CINZA_TEXTO = colors.HexColor("#374151")
CINZA_SUAVE = colors.HexColor("#F3F4F6")
CINZA_BORDA = colors.HexColor("#D1D5DB")
BRANCO = colors.white

PAGE_W, _ = A4
MARGIN = 18 * mm
PROJECT_ROOT = Path(__file__).resolve().parents[3]
LOGIN_LOGO_PATH = PROJECT_ROOT / "frontend" / "src" / "assets" / "logo.png"


def _money(value: float) -> str:
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _fmt_date(value) -> str:
    if value is None:
        return "-"
    if isinstance(value, (date, datetime)):
        return value.strftime("%d/%m/%Y")
    return str(value)


def _build_logo(styles):
    if LOGIN_LOGO_PATH.exists():
        logo = Image(str(LOGIN_LOGO_PATH))
        logo.drawHeight = 16 * mm
        logo.drawWidth = 48 * mm
        logo.hAlign = "LEFT"
        return logo

    return Paragraph(
        "<b>Minha Loja</b>",
        ParagraphStyle(
            "LogoFallback",
            parent=styles["Normal"],
            fontSize=16,
            textColor=AZUL_PRIMARIO,
            fontName="Helvetica-Bold",
        ),
    )


def _base_doc(title: str, subtitle: str):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN,
        title=title,
    )
    styles = getSampleStyleSheet()
    usable_width = PAGE_W - 2 * MARGIN

    title_style = ParagraphStyle(
        "PdfTitle",
        parent=styles["Normal"],
        fontSize=9,
        alignment=TA_RIGHT,
        textColor=CINZA_TEXTO,
        fontName="Helvetica",
    )
    label_style = ParagraphStyle(
        "Label",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.HexColor("#6B7280"),
        fontName="Helvetica",
    )

    content = []
    header = Table(
        [[
            _build_logo(styles),
            Paragraph(
                f"<font color='#1E40AF'><b>{title}</b></font><br/><font size='10' color='#6B7280'>{subtitle}</font>",
                title_style,
            ),
        ]],
        colWidths=[usable_width * 0.6, usable_width * 0.4],
    )
    header.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    content.append(header)
    content.append(HRFlowable(width="100%", thickness=2, color=AZUL_PRIMARIO, spaceAfter=8))
    content.append(Paragraph(f"Gerado em: {_fmt_date(datetime.now())}", label_style))
    content.append(Spacer(1, 8))

    return buffer, doc, styles, usable_width, content


def gerar_pdf_relatorio_vendas(vendas, start_date: date, end_date: date) -> bytes:
    buffer, doc, styles, usable_width, content = _base_doc(
        "RELATÓRIO DE VENDAS",
        f"Período: {_fmt_date(start_date)} até {_fmt_date(end_date)}",
    )

    normal = ParagraphStyle("NormalCell", parent=styles["Normal"], fontSize=9, textColor=CINZA_TEXTO)
    right = ParagraphStyle("RightCell", parent=normal, alignment=TA_RIGHT)
    bold = ParagraphStyle("BoldCell", parent=normal, fontName="Helvetica-Bold")

    rows = [[
        Paragraph("Data", bold),
        Paragraph("Nº", bold),
        Paragraph("Itens", bold),
        Paragraph("Pagamento", bold),
        Paragraph("Desconto", bold),
        Paragraph("Total", bold),
    ]]

    total = 0.0
    total_desconto = 0.0
    quantidade_vendas = 0
    forma_pagamento = {
        1: "Dinheiro",
        2: "Débito",
        3: "Crédito",
        4: "PIX",
        5: "Boleto",
        6: "A Prazo",
    }

    for venda in vendas:
        itens_qtd = sum((item.quantidade or 0) for item in venda.itens)
        total_desconto += float(venda.desconto or 0)
        if not venda.cancelada:
            total += float(venda.total or 0)
            quantidade_vendas += 1

        rows.append([
            Paragraph(_fmt_date(venda.data), normal),
            Paragraph(str(venda.numero_legado or venda.id), normal),
            Paragraph(f"{itens_qtd:g}", right),
            Paragraph(forma_pagamento.get(venda.forma_pagamento, "Outro"), normal),
            Paragraph(_money(float(venda.desconto or 0)), right),
            Paragraph(_money(float(venda.total or 0)), right),
        ])

    ticket_medio = (total / quantidade_vendas) if quantidade_vendas > 0 else 0.0
    rows.append([
        Paragraph("", normal),
        Paragraph("", normal),
        Paragraph("", normal),
        Paragraph("", normal),
        Paragraph("Resumo", bold),
        Paragraph("", normal),
    ])
    rows.append([
        Paragraph("", normal),
        Paragraph("", normal),
        Paragraph("", normal),
        Paragraph("Vendas válidas", bold),
        Paragraph(str(quantidade_vendas), right),
        Paragraph("", normal),
    ])
    rows.append([
        Paragraph("", normal),
        Paragraph("", normal),
        Paragraph("", normal),
        Paragraph("Total descontos", bold),
        Paragraph(_money(total_desconto), right),
        Paragraph("", normal),
    ])
    rows.append([
        Paragraph("", normal),
        Paragraph("", normal),
        Paragraph("", normal),
        Paragraph("Total líquido", bold),
        Paragraph(_money(total), right),
        Paragraph("", normal),
    ])
    rows.append([
        Paragraph("", normal),
        Paragraph("", normal),
        Paragraph("", normal),
        Paragraph("Ticket médio", bold),
        Paragraph(_money(ticket_medio), right),
        Paragraph("", normal),
    ])

    table = Table(
        rows,
        colWidths=[usable_width * 0.14, usable_width * 0.12, usable_width * 0.10, usable_width * 0.20, usable_width * 0.17, usable_width * 0.27],
        repeatRows=1,
    )
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), AZUL_PRIMARIO),
        ("TEXTCOLOR", (0, 0), (-1, 0), BRANCO),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [BRANCO, CINZA_SUAVE]),
        ("BOX", (0, 0), (-1, -1), 0.5, CINZA_BORDA),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, CINZA_BORDA),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))

    content.append(table)
    doc.build(content)
    return buffer.getvalue()


def gerar_pdf_relatorio_estoque_baixo(itens) -> bytes:
    buffer, doc, styles, usable_width, content = _base_doc(
        "RELATÓRIO DE ESTOQUE BAIXO",
        "Produtos com estoque abaixo ou igual ao mínimo",
    )

    normal = ParagraphStyle("NormalEst", parent=styles["Normal"], fontSize=9, textColor=CINZA_TEXTO)
    right = ParagraphStyle("RightEst", parent=normal, alignment=TA_RIGHT)
    bold = ParagraphStyle("BoldEst", parent=normal, fontName="Helvetica-Bold")

    rows = [[
        Paragraph("Produto", bold),
        Paragraph("Estoque Atual", bold),
        Paragraph("Estoque Mínimo", bold),
        Paragraph("Déficit", bold),
        Paragraph("Última Mov.", bold),
    ]]

    for item in itens:
        deficit = max(0, int(item.estoque_minimo or 0) - int(item.quantidade_atual or 0))
        rows.append([
            Paragraph(item.nome_produto, normal),
            Paragraph(str(item.quantidade_atual), right),
            Paragraph(str(item.estoque_minimo), right),
            Paragraph(str(deficit), right),
            Paragraph(_fmt_date(item.ultima_movimentacao), normal),
        ])

    table = Table(
        rows,
        colWidths=[usable_width * 0.42, usable_width * 0.14, usable_width * 0.14, usable_width * 0.12, usable_width * 0.18],
        repeatRows=1,
    )
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), AZUL_PRIMARIO),
        ("TEXTCOLOR", (0, 0), (-1, 0), BRANCO),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [BRANCO, CINZA_SUAVE]),
        ("BOX", (0, 0), (-1, -1), 0.5, CINZA_BORDA),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, CINZA_BORDA),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))

    content.append(table)
    doc.build(content)
    return buffer.getvalue()


def gerar_pdf_relatorio_resumo_mes(resumo, start_date: date, end_date: date) -> bytes:
    buffer, doc, styles, usable_width, content = _base_doc(
        "RELATÓRIO RESUMO DO MÊS",
        f"Período: {_fmt_date(start_date)} até {_fmt_date(end_date)}",
    )

    label = ParagraphStyle("LabelResumo", parent=styles["Normal"], fontSize=10, textColor=CINZA_TEXTO)
    value = ParagraphStyle(
        "ValueResumo",
        parent=styles["Normal"],
        fontSize=12,
        textColor=AZUL_PRIMARIO,
        fontName="Helvetica-Bold",
        alignment=TA_RIGHT,
    )

    rows = [
        [Paragraph("Faturamento Bruto", label), Paragraph(_money(float(resumo.get("total_bruto", 0.0))), value)],
        [Paragraph("Descontos", label), Paragraph(_money(float(resumo.get("total_descontos", 0.0))), value)],
        [Paragraph("Faturamento Líquido", label), Paragraph(_money(float(resumo.get("total_liquido", 0.0))), value)],
        [Paragraph("Quantidade de Vendas", label), Paragraph(str(int(resumo.get("quantidade_vendas", 0))), value)],
        [Paragraph("Ticket Médio", label), Paragraph(_money(float(resumo.get("ticket_medio", 0.0))), value)],
    ]

    table = Table(rows, colWidths=[usable_width * 0.65, usable_width * 0.35])
    table.setStyle(TableStyle([
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [BRANCO, CINZA_SUAVE]),
        ("BOX", (0, 0), (-1, -1), 0.5, CINZA_BORDA),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, CINZA_BORDA),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))

    content.append(table)
    doc.build(content)
    return buffer.getvalue()
