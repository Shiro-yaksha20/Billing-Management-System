import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import inch
from .models import Bill
from .database import db_session
from . import settings_service
from .utils import logger
from .constants import RECEIPTS_DIR

# Try to register a Unicode font to render ₹ correctly
try:
    pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))
    DEFAULT_FONT = 'DejaVuSans'
except Exception:
    DEFAULT_FONT = 'Helvetica'

"""PDF generation utilities for receipt creation."""

def generate_receipt_pdf(bill_id: int) -> str:
    """
    Generates a PDF receipt for the given bill and returns the file path.
    """
    if not os.path.exists(RECEIPTS_DIR):
        os.makedirs(RECEIPTS_DIR)

    with db_session() as db:
        bill = db.query(Bill).filter(Bill.id == bill_id).first()
        if not bill:
            raise ValueError(f"Bill with id {bill_id} not found.")

        # Generate unique filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"receipt_{bill.id}_{timestamp}.pdf"
        file_path = os.path.join(RECEIPTS_DIR, filename)

        # Ensure uniqueness even if file somehow exists
        if os.path.exists(file_path):
            logger.warning(f"PDF already exists: {file_path}, appending counter")
            counter = 1
            while os.path.exists(file_path):
                filename = f"receipt_{bill.id}_{timestamp}_{counter}.pdf"
                file_path = os.path.join(RECEIPTS_DIR, filename)
                counter += 1

        # Generate to temporary file first
        temp_path = file_path + ".tmp"
        try:
            # Set margins for better print layout
            doc = SimpleDocTemplate(
                temp_path,
                pagesize=letter,
                leftMargin=0.5*inch,
                rightMargin=0.5*inch,
                topMargin=0.5*inch,
                bottomMargin=0.5*inch
            )
        except Exception as e:
            raise IOError(f"Failed to create PDF document: {e}")

        styles = getSampleStyleSheet()
        # Ensure styles use chosen font
        for name in styles.byName:
            styles[name].fontName = DEFAULT_FONT
        h1 = ParagraphStyle('H1', parent=styles['Heading1'], fontName=DEFAULT_FONT)
        normal = ParagraphStyle('Normal', parent=styles['Normal'], fontName=DEFAULT_FONT)
        h3 = ParagraphStyle('H3', parent=styles['Heading3'], fontName=DEFAULT_FONT)
        italic = ParagraphStyle('Italic', parent=styles['Italic'], fontName=DEFAULT_FONT)

        story = []

        # Salon Details
        salon_name = settings_service.get_setting("salon_name", "Your Salon")
        salon_address = settings_service.get_setting("salon_address", "123 Salon St.")
        salon_phone = settings_service.get_setting("salon_phone", "555-1234")
        instagram = settings_service.get_setting("salon_instagram", "")
        gstin = settings_service.get_setting("salon_gstin", "")
        story.append(Paragraph(salon_name, h1))
        story.append(Paragraph(salon_address, normal))
        story.append(Paragraph(f"Phone: {salon_phone}", normal))
        if instagram:
            story.append(Paragraph(f"Instagram: {instagram}", normal))
        if gstin:
            story.append(Paragraph(f"GST: {gstin}", normal))
        story.append(Spacer(1, 12))

        # Invoice Details
        story.append(Paragraph(f"Invoice No: {bill.bill_number or bill.id}", normal))
        story.append(Paragraph(f"Date: {bill.bill_datetime.strftime('%Y-%m-%d %H:%M')}", normal))
        story.append(Paragraph(f"Payment Method: {bill.payment_method} ({getattr(bill, 'payment_status', 'Paid')})", normal))
        if getattr(bill, 'transaction_id', None):
            story.append(Paragraph(f"Transaction ID: {bill.transaction_id}", normal))
        story.append(Spacer(1, 12))

        # Customer Details
        story.append(Paragraph(f"Customer: {bill.customer.name}", normal))
        story.append(Paragraph(f"Phone: {bill.customer.phone}", normal))
        story.append(Spacer(1, 12))

        # Bill Items Table
        currency_symbol = "₹" if DEFAULT_FONT == 'DejaVuSans' else "Rs."
        data = [["Service", "Qty", "Price", "Total"]]
        for item in bill.items:
            svc_name = item.service.display_name or item.service.name
            if item.service.variant:
                svc_name = f"{svc_name} ({item.service.variant})"
            data.append([
                svc_name,
                str(item.quantity),
                f"{currency_symbol}{float(item.unit_price):.0f}",
                f"{currency_symbol}{float(item.line_total):.0f}"
            ])

        table = Table(data)
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), DEFAULT_FONT),
            ('FONTNAME', (0, 0), (-1, 0), DEFAULT_FONT),
            ('FONTNAME', (0, 1), (-1, -1), DEFAULT_FONT),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ])
        table.setStyle(style)
        story.append(table)
        story.append(Spacer(1, 12))

        # Totals
        story.append(Paragraph(f"Subtotal: {currency_symbol}{float(bill.subtotal or 0):.0f}", normal))
        if float(bill.discount_amount or 0) > 0:
            story.append(Paragraph(f"Discount: -{currency_symbol}{float(bill.discount_amount):.0f}", normal))
        story.append(Paragraph(f"Tax ({float(bill.tax_percent or 0):.0f}%): {currency_symbol}{float(bill.tax_amount or 0):.0f}", normal))
        story.append(Paragraph(f"TOTAL: {currency_symbol}{float(bill.total or 0):.0f}", h3))
        story.append(Spacer(1, 12))

        # Stylist attribution
        story.append(Paragraph(f"Served By: {bill.staff.name}", normal))
        story.append(Spacer(1, 12))

        # Footer
        footer_msg = settings_service.get_setting("receipt_footer_message", settings_service.get_setting("thank_you_message", "Thanks for your visit!"))
        story.append(Paragraph(footer_msg, italic))
        if instagram:
            story.append(Paragraph(f"Follow us on Instagram {instagram}", normal))

        try:
            doc.build(story)
            # Only rename to final path after successful build
            os.replace(temp_path, file_path)
            bill.pdf_path = file_path
            logger.info(f"PDF generated for bill {bill_id} at {file_path}")
            return file_path
        except Exception as e:
            # Clean up temp file on failure
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception:
                pass
            raise IOError(f"Failed to build PDF content: {e}")
