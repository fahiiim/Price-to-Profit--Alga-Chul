"""Render `DocumentData` to an A4 PDF with ReportLab.

Layout, top to bottom: business header and document title, client block,
optional highlight cards, line table, amounts, payment link, notes and terms,
and a footer on every page.
"""

from io import BytesIO
from xml.sax.saxutils import escape, quoteattr

from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import (
    Flowable,
    HRFlowable,
    Image,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.documents.data import DocumentData, LabeledValue, LineTable
from app.documents.theme import (
    BERRY,
    BERRY_TINT,
    BERRY_WASH,
    GOLD_TINT,
    INK,
    INK_LINE,
    INK_MUTED,
    INK_SOFT,
    FontSet,
    load_fonts,
)

PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN_X = 18 * mm
CONTENT_WIDTH = PAGE_WIDTH - 2 * MARGIN_X
LOGO_MAX_WIDTH = 42 * mm
LOGO_MAX_HEIGHT = 18 * mm
AMOUNTS_WIDTH = 82 * mm


class _Styles:
    """Paragraph styles derived from the brand fonts."""

    def __init__(self, fonts: FontSet) -> None:
        self.fonts = fonts
        self.business_name = ParagraphStyle(
            "business_name",
            fontName=fonts.serif,
            fontSize=17,
            leading=21,
            textColor=INK,
        )
        self.contact = ParagraphStyle(
            "contact",
            fontName=fonts.sans,
            fontSize=8,
            leading=11,
            textColor=INK_MUTED,
        )
        self.title = ParagraphStyle(
            "title",
            fontName=fonts.serif,
            fontSize=28,
            leading=32,
            textColor=BERRY,
            alignment=TA_RIGHT,
        )
        self.number = ParagraphStyle(
            "number",
            fontName=fonts.sans_bold,
            fontSize=10,
            leading=13,
            textColor=INK,
            alignment=TA_RIGHT,
        )
        self.label = ParagraphStyle(
            "label",
            fontName=fonts.sans_bold,
            fontSize=7,
            leading=9,
            textColor=INK_SOFT,
        )
        self.label_right = ParagraphStyle(
            "label_right", parent=self.label, alignment=TA_RIGHT
        )
        self.body = ParagraphStyle(
            "body",
            fontName=fonts.sans,
            fontSize=9,
            leading=12.5,
            textColor=INK,
        )
        self.body_right = ParagraphStyle(
            "body_right", parent=self.body, alignment=TA_RIGHT
        )
        self.body_strong = ParagraphStyle(
            "body_strong", parent=self.body, fontName=fonts.sans_bold
        )
        self.muted = ParagraphStyle(
            "muted",
            parent=self.body,
            fontSize=8.5,
            leading=12,
            textColor=INK_MUTED,
        )
        self.badge = ParagraphStyle(
            "badge",
            fontName=fonts.sans_bold,
            fontSize=7.5,
            leading=9,
            textColor=BERRY,
            alignment=TA_RIGHT,
        )
        self.card_value = ParagraphStyle(
            "card_value",
            fontName=fonts.serif,
            fontSize=14,
            leading=17,
            textColor=INK,
        )
        self.card_value_strong = ParagraphStyle(
            "card_value_strong", parent=self.card_value, textColor=BERRY
        )
        self.amount_strong = ParagraphStyle(
            "amount_strong",
            fontName=fonts.serif,
            fontSize=14,
            leading=17,
            textColor=BERRY,
            alignment=TA_RIGHT,
        )
        self.amount_strong_label = ParagraphStyle(
            "amount_strong_label",
            parent=self.amount_strong,
            textColor=INK,
            alignment=TA_LEFT,
        )
        self.section_heading = ParagraphStyle(
            "section_heading",
            fontName=fonts.sans_bold,
            fontSize=8.5,
            leading=11,
            textColor=INK,
            spaceAfter=2,
        )


def render_document(document: DocumentData) -> bytes:
    """Render the document and return the PDF bytes."""
    fonts = load_fonts()
    styles = _Styles(fonts)
    buffer = BytesIO()
    template = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=MARGIN_X,
        rightMargin=MARGIN_X,
        topMargin=16 * mm,
        bottomMargin=20 * mm,
        title=f"{document.title} {document.number}",
        author=document.business.name,
        creator="Price to Profit",
    )

    story: list[Flowable] = [
        _header(document, styles),
        Spacer(1, 5 * mm),
        HRFlowable(width="100%", thickness=1.2, color=BERRY, spaceAfter=6 * mm),
        _client_block(document, styles),
        Spacer(1, 6 * mm),
    ]
    if document.highlights:
        story += [_highlight_cards(document.highlights, styles), Spacer(1, 6 * mm)]
    story += [
        _line_table(document.table, styles),
        Spacer(1, 4 * mm),
        _amounts_table(document.amounts, styles),
    ]
    if document.payment_link:
        story += [Spacer(1, 6 * mm), _payment_block(document, styles)]
    for section in document.sections:
        story += [
            Spacer(1, 6 * mm),
            KeepTogether(
                [
                    Paragraph(_text(section.heading), styles.section_heading),
                    Paragraph(_multiline(section.body), styles.muted),
                ]
            ),
        ]

    def draw_footer(canvas: Canvas, doc: SimpleDocTemplate) -> None:
        _footer(canvas, doc, document, fonts)

    template.build(story, onFirstPage=draw_footer, onLaterPages=draw_footer)
    return buffer.getvalue()


def _header(document: DocumentData, styles: _Styles) -> Table:
    left: list[Flowable] = []
    logo = _logo(document)
    if logo is not None:
        left += [logo, Spacer(1, 3 * mm)]
    left.append(Paragraph(_text(document.business.name), styles.business_name))
    if document.business.contact_lines:
        contact = "<br/>".join(_text(line) for line in document.business.contact_lines)
        left.append(Paragraph(contact, styles.contact))

    right: list[Flowable] = []
    if document.badge:
        right.append(Paragraph(_text(document.badge), styles.badge))
    right += [
        Paragraph(_text(document.title), styles.title),
        Paragraph(_text(document.number), styles.number),
        Spacer(1, 3 * mm),
        _meta_table(document.meta, styles),
    ]

    table = Table(
        [[left, right]], colWidths=[CONTENT_WIDTH * 0.55, CONTENT_WIDTH * 0.45]
    )
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    return table


def _meta_table(meta: tuple[LabeledValue, ...], styles: _Styles) -> Table:
    rows = [
        [
            Paragraph(_text(item.label.upper()), styles.label_right),
            Paragraph(_text(item.value), styles.body_right),
        ]
        for item in meta
    ]
    table = Table(rows, colWidths=[28 * mm, 40 * mm], hAlign="RIGHT")
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (0, -1), 3 * mm),
                ("TOPPADDING", (0, 0), (-1, -1), 1),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
            ]
        )
    )
    return table


def _client_block(document: DocumentData, styles: _Styles) -> Table:
    lines = [Paragraph(_text(document.client_heading.upper()), styles.label)]
    for index, line in enumerate(document.client_lines):
        style = styles.body_strong if index == 0 else styles.body
        lines.append(Paragraph(_text(line), style))

    table = Table([[lines]], colWidths=[CONTENT_WIDTH])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), BERRY_WASH),
                ("LINEBEFORE", (0, 0), (0, -1), 2, BERRY),
                ("LEFTPADDING", (0, 0), (-1, -1), 4 * mm),
                ("TOPPADDING", (0, 0), (-1, -1), 3 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3 * mm),
            ]
        )
    )
    return table


def _highlight_cards(cards: tuple[LabeledValue, ...], styles: _Styles) -> Table:
    cells = [
        [
            Paragraph(_text(card.label.upper()), styles.label),
            Spacer(1, 1.5 * mm),
            Paragraph(
                _text(card.value),
                styles.card_value_strong if card.emphasis else styles.card_value,
            ),
        ]
        for card in cards
    ]
    width = CONTENT_WIDTH / len(cards)
    table = Table([cells], colWidths=[width] * len(cards))
    commands = [
        ("BOX", (0, 0), (-1, -1), 0.6, INK_LINE),
        ("INNERGRID", (0, 0), (-1, -1), 0.6, INK_LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 3 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3 * mm),
    ]
    for index, card in enumerate(cards):
        if card.emphasis:
            commands.append(("BACKGROUND", (index, 0), (index, 0), GOLD_TINT))
    table.setStyle(TableStyle(commands))
    return table


def _line_table(line_table: LineTable, styles: _Styles) -> Table:
    def cell(text: str, column: int, *, header: bool = False) -> Paragraph:
        numeric = column in line_table.numeric_columns
        if header:
            style = styles.label_right if numeric else styles.label
            return Paragraph(_text(text.upper()), style)
        return Paragraph(_text(text), styles.body_right if numeric else styles.body)

    data = [[cell(text, i, header=True) for i, text in enumerate(line_table.headers)]]
    data += [[cell(text, i) for i, text in enumerate(row)] for row in line_table.rows]

    table = Table(
        data,
        colWidths=[CONTENT_WIDTH * fraction for fraction in line_table.column_widths],
        repeatRows=1,
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), BERRY_TINT),
                ("LINEBELOW", (0, 0), (-1, 0), 0.8, BERRY),
                ("LINEBELOW", (0, 1), (-1, -1), 0.4, INK_LINE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 2.5 * mm),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2.5 * mm),
                ("TOPPADDING", (0, 0), (-1, -1), 2.2 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2.2 * mm),
            ]
        )
    )
    return table


def _amounts_table(amounts: tuple[LabeledValue, ...], styles: _Styles) -> KeepTogether:
    rows = []
    commands = [
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2.5 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 1.6 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.6 * mm),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]
    for index, amount in enumerate(amounts):
        if amount.emphasis:
            rows.append(
                [
                    Paragraph(_text(amount.label), styles.amount_strong_label),
                    Paragraph(_text(amount.value), styles.amount_strong),
                ]
            )
            commands.append(("LINEABOVE", (0, index), (-1, index), 0.8, INK))
        else:
            rows.append(
                [
                    Paragraph(_text(amount.label), styles.muted),
                    Paragraph(_text(amount.value), styles.body_right),
                ]
            )
    table = Table(
        rows, colWidths=[AMOUNTS_WIDTH * 0.5, AMOUNTS_WIDTH * 0.5], hAlign="RIGHT"
    )
    table.setStyle(TableStyle(commands))
    return KeepTogether([table])


def _payment_block(document: DocumentData, styles: _Styles) -> Table:
    link = document.payment_link or ""
    content = [
        Paragraph(_text(document.payment_label.upper()), styles.label),
        Paragraph(
            f'<link href={quoteattr(link)} color="#C2185B">{_text(link)}</link>',
            styles.body,
        ),
    ]
    table = Table([[content]], colWidths=[CONTENT_WIDTH])
    table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.8, BERRY),
                ("LEFTPADDING", (0, 0), (-1, -1), 4 * mm),
                ("TOPPADDING", (0, 0), (-1, -1), 3 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3 * mm),
            ]
        )
    )
    return table


def _footer(
    canvas: Canvas,
    doc: SimpleDocTemplate,
    document: DocumentData,
    fonts: FontSet,
) -> None:
    canvas.saveState()
    canvas.setStrokeColor(INK_LINE)
    canvas.setLineWidth(0.5)
    canvas.line(MARGIN_X, 13 * mm, PAGE_WIDTH - MARGIN_X, 13 * mm)
    canvas.setFont(fonts.sans, 7.5)
    canvas.setFillColor(INK_SOFT)
    canvas.drawString(
        MARGIN_X,
        9 * mm,
        f"{document.business.name}  ·  {document.title} {document.number}",
    )
    canvas.drawRightString(PAGE_WIDTH - MARGIN_X, 9 * mm, f"Page {doc.page}")
    canvas.restoreState()


def _logo(document: DocumentData) -> Image | None:
    path = document.business.logo_path
    if path is None:
        return None
    try:
        width, height = ImageReader(str(path)).getSize()
    except (OSError, ValueError):
        return None
    scale = min(LOGO_MAX_WIDTH / width, LOGO_MAX_HEIGHT / height)
    logo = Image(str(path), width=width * scale, height=height * scale)
    logo.hAlign = "LEFT"
    return logo


def _text(value: str) -> str:
    """Escape user text so ReportLab's mini-markup cannot be injected."""
    return escape(value)


def _multiline(value: str) -> str:
    return "<br/>".join(_text(line) for line in value.splitlines())
