"""PDF generation utilities for receipt creation."""

from __future__ import annotations

import os
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

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
            leftMargin=0.5 * inch,
            rightMargin=0.5 * inch,
            topMargin=0.5 * inch,
            bottomMargin=0.5 * inch,
        )
    except Exception as exc:
        raise IOError(f"Failed to create PDF document: {exc}")

    styles = getSampleStyleSheet()
    for name in styles.byName:
        styles[name].fontName = DEFAULT_FONT
    h1 = ParagraphStyle("H1", parent=styles["Heading1"], fontName=DEFAULT_FONT)
    normal = ParagraphStyle("Normal", parent=styles["Normal"], fontName=DEFAULT_FONT)
    h3 = ParagraphStyle("H3", parent=styles["Heading3"], fontName=DEFAULT_FONT)
    italic = ParagraphStyle("Italic", parent=styles["Italic"], fontName=DEFAULT_FONT)

    story = []

    if is_preview:
        story.append(Paragraph("PREVIEW - NOT A RECEIPT", h3))
        story.append(Spacer(1, 8))

    business_name = settings_service.get_setting("business_name", "Your Business")
    business_address = settings_service.get_setting("business_address", "123 Business St.")
    business_phone = settings_service.get_setting("business_phone", "555-1234")
    instagram = settings_service.get_setting("business_instagram", "")
    gstin = settings_service.get_setting("business_gstin", "")
    story.append(Paragraph(business_name, h1))
    story.append(Paragraph(business_address, normal))
    story.append(Paragraph(f"Phone: {business_phone}", normal))
    if instagram:
        story.append(Paragraph(f"Instagram: {instagram}", normal))
    if gstin:
        story.append(Paragraph(f"GST: {gstin}", normal))
    story.append(Spacer(1, 12))

    story.append(Paragraph(f"Invoice No: {receipt.bill_number or receipt.bill_id}", normal))
    story.append(Paragraph(f"Date: {receipt.bill_datetime.strftime('%Y-%m-%d %H:%M')}", normal))
    story.append(
        Paragraph(
            f"Payment Method: {receipt.payment_method} ({receipt.payment_status})",
            normal,
        )
    )
    if receipt.transaction_id:
        story.append(Paragraph(f"Transaction ID: {receipt.transaction_id}", normal))
    story.append(Spacer(1, 12))

    story.append(Paragraph(f"Customer: {receipt.customer_name}", normal))
    story.append(Paragraph(f"Phone: {receipt.customer_phone}", normal))
    story.append(Spacer(1, 12))

    currency_symbol = settings_service.get_setting("currency_symbol", "?") or "?"

    def _money(value: Decimal | None) -> str:
        amount = value if value is not None else Decimal("0")
        return f"{currency_symbol}{amount:,.2f}"

    data = [["Service", "Qty", "Price", "Total"]]
    for item in receipt.items:
        svc_name = item.display_name or item.service_name
        if item.variant:
            svc_name = f"{svc_name} ({item.variant})"
        data.append(
            [
                svc_name,
                str(item.quantity),
                _money(item.unit_price),
                _money(item.line_total),
            ]
        )

    table = Table(data)
    style = TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (0, -1), "LEFT"),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ("FONTNAME", (0, 0), (-1, -1), DEFAULT_FONT),
            ("FONTNAME", (0, 0), (-1, 0), DEFAULT_FONT),
            ("FONTNAME", (0, 1), (-1, -1), DEFAULT_FONT),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
            ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ]
    )
    table.setStyle(style)
    story.append(table)
    story.append(Spacer(1, 12))

    story.append(Paragraph(f"Subtotal: {_money(receipt.subtotal)}", normal))
    if (receipt.discount_amount or Decimal("0")) > Decimal("0"):
        story.append(
            Paragraph(
                f"Discount: -{_money(receipt.discount_amount)}",
                normal,
            )
        )
    story.append(
        Paragraph(
            f"Tax ({(receipt.tax_percent or Decimal('0')):.0f}%): {_money(receipt.tax_amount)}",
            normal,
        )
    )
    story.append(Paragraph(f"TOTAL: {_money(receipt.total)}", h3))
    story.append(Spacer(1, 12))

    story.append(Paragraph(f"Served By: {receipt.staff_name}", normal))
    story.append(Spacer(1, 12))

    footer_msg = settings_service.get_setting(
        "receipt_footer_message",
        settings_service.get_setting("thank_you_message", "Thanks for your visit!"),
    )
    story.append(Paragraph(footer_msg, italic))
    if instagram:
        story.append(Paragraph(f"Follow us on Instagram {instagram}", normal))

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
