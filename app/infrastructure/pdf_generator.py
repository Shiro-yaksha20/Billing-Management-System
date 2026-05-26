"""PDF generation utilities for receipt creation."""

from __future__ import annotations

import os
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from ..constants import RECEIPTS_DIR
from ..dto.receipt_dto import ReceiptData
from .logging import logger

if TYPE_CHECKING:
    from ..services.settings_service import SettingsService

try:
    pdfmetrics.registerFont(TTFont("DejaVuSans", "DejaVuSans.ttf"))
    DEFAULT_FONT = "DejaVuSans"
except Exception:
    DEFAULT_FONT = "Helvetica"

# ── Colour palette ──────────────────────────────────────────────────
ACCENT = colors.HexColor("#C8965A")        # warm gold / amber
DARK_BG = colors.HexColor("#2C3E50")       # slate header
DARK_TEXT = colors.HexColor("#2C3E50")
LIGHT_TEXT = colors.HexColor("#7F8C8D")
ROW_ALT = colors.HexColor("#F8F9FA")       # subtle alternate row
WHITE = colors.white
BLACK = colors.black


def _build_styles():
    """Create all paragraph styles used in the receipt."""
    base = dict(fontName=DEFAULT_FONT)
    return {
        "business_name": ParagraphStyle(
            "BusinessName", **base, fontSize=22, leading=26,
            alignment=TA_CENTER, textColor=DARK_TEXT,
            spaceAfter=2,
        ),
        "business_sub": ParagraphStyle(
            "BusinessSub", **base, fontSize=9, leading=12,
            alignment=TA_CENTER, textColor=LIGHT_TEXT,
        ),
        "section_title": ParagraphStyle(
            "SectionTitle", **base, fontSize=10, leading=14,
            textColor=ACCENT, spaceBefore=6, spaceAfter=4,
        ),
        "label": ParagraphStyle(
            "Label", **base, fontSize=8.5, leading=11,
            textColor=LIGHT_TEXT,
        ),
        "value": ParagraphStyle(
            "Value", **base, fontSize=9.5, leading=13,
            textColor=DARK_TEXT,
        ),
        "value_right": ParagraphStyle(
            "ValueRight", **base, fontSize=9.5, leading=13,
            textColor=DARK_TEXT, alignment=TA_RIGHT,
        ),
        "total_label": ParagraphStyle(
            "TotalLabel", **base, fontSize=12, leading=16,
            textColor=DARK_TEXT, alignment=TA_RIGHT,
        ),
        "total_value": ParagraphStyle(
            "TotalValue", **base, fontSize=14, leading=18,
            textColor=ACCENT, alignment=TA_RIGHT,
        ),
        "footer": ParagraphStyle(
            "Footer", **base, fontSize=9, leading=12,
            alignment=TA_CENTER, textColor=LIGHT_TEXT,
            spaceBefore=4,
        ),
        "preview_banner": ParagraphStyle(
            "PreviewBanner", **base, fontSize=12, leading=16,
            alignment=TA_CENTER, textColor=colors.red,
            spaceBefore=4, spaceAfter=4,
        ),
        "table_header": ParagraphStyle(
            "TableHeader", **base, fontSize=8.5, leading=11,
            textColor=WHITE, alignment=TA_LEFT,
        ),
        "table_header_right": ParagraphStyle(
            "TableHeaderRight", **base, fontSize=8.5, leading=11,
            textColor=WHITE, alignment=TA_RIGHT,
        ),
        "table_cell": ParagraphStyle(
            "TableCell", **base, fontSize=9, leading=12,
            textColor=DARK_TEXT,
        ),
        "table_cell_right": ParagraphStyle(
            "TableCellRight", **base, fontSize=9, leading=12,
            textColor=DARK_TEXT, alignment=TA_RIGHT,
        ),
    }


def _divider(color=ACCENT, thickness=0.75):
    """Return a horizontal rule flowable."""
    return HRFlowable(
        width="100%", thickness=thickness,
        color=color, spaceAfter=8, spaceBefore=8,
    )


def generate_receipt_pdf(
    receipt: ReceiptData,
    settings_service: SettingsService,
    is_preview: bool = False,
) -> str:
    """Generate a PDF receipt for the given receipt data and return the path."""
    if not os.path.exists(RECEIPTS_DIR):
        os.makedirs(RECEIPTS_DIR)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"receipt_{receipt.bill_id}_{timestamp}.pdf"
    file_path = os.path.join(RECEIPTS_DIR, filename)

    if os.path.exists(file_path):
        logger.warning("PDF already exists: %s, appending counter", file_path)
        counter = 1
        while os.path.exists(file_path):
            filename = f"receipt_{receipt.bill_id}_{timestamp}_{counter}.pdf"
            file_path = os.path.join(RECEIPTS_DIR, filename)
            counter += 1

    temp_path = file_path + ".tmp"
    try:
        doc = SimpleDocTemplate(
            temp_path,
            pagesize=letter,
            leftMargin=0.6 * inch,
            rightMargin=0.6 * inch,
            topMargin=0.5 * inch,
            bottomMargin=0.5 * inch,
        )
    except Exception as exc:
        raise IOError(f"Failed to create PDF document: {exc}")

    s = _build_styles()
    story = []

    currency_symbol = settings_service.get_setting("currency_symbol", "\u20B9") or "\u20B9"

    def _money(value: Decimal | None) -> str:
        amount = value if value is not None else Decimal("0")
        return f"{currency_symbol}{amount:,.2f}"

    # ── Preview banner ──────────────────────────────────────────────
    if is_preview:
        story.append(Paragraph("⚠ PREVIEW — NOT A RECEIPT", s["preview_banner"]))
        story.append(_divider(colors.red, 1))

    # ── Business header ─────────────────────────────────────────────
    business_name = settings_service.get_setting("business_name", "Your Business")
    business_address = settings_service.get_setting("business_address", "123 Business St.")
    business_phone = settings_service.get_setting("business_phone", "555-1234")
    instagram = settings_service.get_setting("business_instagram", "")
    gstin = settings_service.get_setting("business_gstin", "")

    story.append(Paragraph(business_name.upper(), s["business_name"]))
    story.append(Paragraph(business_address, s["business_sub"]))

    contact_parts = [f"Phone: {business_phone}"]
    if instagram:
        contact_parts.append(f"Instagram: {instagram}")
    story.append(Paragraph("  |  ".join(contact_parts), s["business_sub"]))

    if gstin:
        story.append(Paragraph(f"GSTIN: {gstin}", s["business_sub"]))

    story.append(_divider())

    # ── Invoice & customer info (two-column) ────────────────────────
    left_col = []
    left_col.append(Paragraph("INVOICE DETAILS", s["section_title"]))
    left_col.append(Paragraph("Invoice No", s["label"]))
    left_col.append(Paragraph(
        str(receipt.bill_number or receipt.bill_id), s["value"]
    ))
    left_col.append(Paragraph("Date", s["label"]))
    left_col.append(Paragraph(
        receipt.bill_datetime.strftime("%d %b %Y, %I:%M %p"), s["value"]
    ))
    left_col.append(Paragraph("Payment", s["label"]))
    payment_text = receipt.payment_method
    if receipt.payment_status:
        payment_text += f" ({receipt.payment_status})"
    left_col.append(Paragraph(payment_text, s["value"]))
    if receipt.transaction_id:
        left_col.append(Paragraph("Transaction ID", s["label"]))
        left_col.append(Paragraph(receipt.transaction_id, s["value"]))

    right_col = []
    right_col.append(Paragraph("CUSTOMER", s["section_title"]))
    right_col.append(Paragraph("Name", s["label"]))
    right_col.append(Paragraph(receipt.customer_name, s["value"]))
    right_col.append(Paragraph("Phone", s["label"]))
    right_col.append(Paragraph(receipt.customer_phone, s["value"]))
    right_col.append(Paragraph("Served By", s["label"]))
    right_col.append(Paragraph(receipt.staff_name, s["value"]))

    # Wrap each column's items into a single-cell sub-table
    left_table = Table([[item] for item in left_col], colWidths=[3.2 * inch])
    left_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
    ]))
    right_table = Table([[item] for item in right_col], colWidths=[3.2 * inch])
    right_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
    ]))

    info_table = Table(
        [[left_table, right_table]],
        colWidths=[3.5 * inch, 3.5 * inch],
    )
    info_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 10))

    # ── Services table ──────────────────────────────────────────────
    story.append(Paragraph("SERVICES", s["section_title"]))
    story.append(Spacer(1, 4))

    # Header row
    header = [
        Paragraph("Service", s["table_header"]),
        Paragraph("Qty", s["table_header_right"]),
        Paragraph("Price", s["table_header_right"]),
        Paragraph("Total", s["table_header_right"]),
    ]
    data = [header]

    for item in receipt.items:
        svc_name = item.display_name or item.service_name
        if item.variant:
            svc_name = f"{svc_name} ({item.variant})"
        data.append([
            Paragraph(svc_name, s["table_cell"]),
            Paragraph(str(item.quantity), s["table_cell_right"]),
            Paragraph(_money(item.unit_price), s["table_cell_right"]),
            Paragraph(_money(item.line_total), s["table_cell_right"]),
        ])

    col_widths = [3.4 * inch, 0.6 * inch, 1.3 * inch, 1.3 * inch]
    svc_table = Table(data, colWidths=col_widths)

    table_style_cmds = [
        # Header styling
        ("BACKGROUND", (0, 0), (-1, 0), DARK_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, -1), DEFAULT_FONT),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        # Padding
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("TOPPADDING", (0, 1), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        # Alignment
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        # Grid lines – subtle
        ("LINEBELOW", (0, 0), (-1, 0), 1, ACCENT),
        ("LINEBELOW", (0, -1), (-1, -1), 0.5, colors.HexColor("#DEE2E6")),
    ]

    # Alternating row backgrounds
    for i in range(1, len(data)):
        if i % 2 == 0:
            table_style_cmds.append(
                ("BACKGROUND", (0, i), (-1, i), ROW_ALT)
            )
        # Subtle bottom border on each row
        if i < len(data) - 1:
            table_style_cmds.append(
                ("LINEBELOW", (0, i), (-1, i), 0.25, colors.HexColor("#E9ECEF"))
            )

    svc_table.setStyle(TableStyle(table_style_cmds))
    story.append(svc_table)
    story.append(Spacer(1, 14))

    # ── Totals summary (right-aligned) ──────────────────────────────
    totals_data = []

    totals_data.append([
        "", Paragraph("Subtotal", s["label"]),
        Paragraph(_money(receipt.subtotal), s["value_right"]),
    ])

    if (receipt.discount_amount or Decimal("0")) > Decimal("0"):
        totals_data.append([
            "", Paragraph("Discount", s["label"]),
            Paragraph(f"- {_money(receipt.discount_amount)}", s["value_right"]),
        ])

    tax_pct = receipt.tax_percent or Decimal("0")
    totals_data.append([
        "", Paragraph(f"Tax ({tax_pct:.0f}%)", s["label"]),
        Paragraph(_money(receipt.tax_amount), s["value_right"]),
    ])

    # Separator row before total
    totals_data.append(["", "", ""])

    totals_data.append([
        "", Paragraph("TOTAL", s["total_label"]),
        Paragraph(_money(receipt.total), s["total_value"]),
    ])

    totals_table = Table(
        totals_data,
        colWidths=[3.4 * inch, 2.0 * inch, 1.6 * inch],
    )
    totals_style_cmds = [
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("ALIGN", (2, 0), (2, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]
    # The separator row (second to last) gets a top border
    sep_row = len(totals_data) - 2
    totals_style_cmds.append(
        ("LINEBELOW", (1, sep_row), (-1, sep_row), 0.75, ACCENT)
    )
    totals_table.setStyle(TableStyle(totals_style_cmds))
    story.append(totals_table)
    story.append(Spacer(1, 16))

    # ── Footer ──────────────────────────────────────────────────────
    story.append(_divider(colors.HexColor("#DEE2E6"), 0.5))

    footer_msg = settings_service.get_setting(
        "receipt_footer_message",
        settings_service.get_setting("thank_you_message", "Thank you for your visit!"),
    )
    story.append(Paragraph(footer_msg, s["footer"]))
    if instagram:
        story.append(Paragraph(
            f"Follow us on Instagram: {instagram}", s["footer"]
        ))

    story.append(Spacer(1, 6))
    story.append(Paragraph(
        f"Generated on {datetime.now().strftime('%d %b %Y, %I:%M %p')}",
        ParagraphStyle(
            "Timestamp", fontName=DEFAULT_FONT, fontSize=7,
            leading=9, alignment=TA_CENTER,
            textColor=colors.HexColor("#BDC3C7"),
        ),
    ))

    # ── Build PDF ───────────────────────────────────────────────────
    try:
        doc.build(story)
        os.replace(temp_path, file_path)
        logger.info("PDF generated for bill %s at %s", receipt.bill_id, file_path)
        return file_path
    except Exception as exc:
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except Exception:
            pass
        raise IOError(f"Failed to build PDF content: {exc}")
