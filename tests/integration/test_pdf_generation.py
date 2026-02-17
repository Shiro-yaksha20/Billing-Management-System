"""Integration tests for PDF generation."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from app.dto.receipt_dto import ReceiptData, ReceiptItemData
from app.infrastructure import database as infra_db
from app.infrastructure.pdf_generator import generate_receipt_pdf
from app.models import Bill


def test_generate_receipt_pdf(sample_bill, settings_service, receipts_dir):
    """Generate a receipt PDF using seeded data."""
    with infra_db.db_session() as db:
        bill = db.query(Bill).filter(Bill.id == sample_bill).first()
        assert bill is not None
        receipt = ReceiptData(
            bill_id=bill.id,
            bill_number=bill.bill_number,
            bill_datetime=bill.bill_datetime,
            subtotal=Decimal(bill.subtotal or 0),
            discount_amount=Decimal(bill.discount_amount or 0),
            tax_percent=Decimal(bill.tax_percent or 0),
            tax_amount=Decimal(bill.tax_amount or 0),
            total=Decimal(bill.total or 0),
            payment_method=bill.payment_method or "Cash",
            payment_status=bill.payment_status or "Paid",
            transaction_id=bill.transaction_id,
            customer_name=bill.customer.name,
            customer_phone=bill.customer.phone,
            staff_name=bill.staff.name,
            items=[
                ReceiptItemData(
                    service_name=item.service.name,
                    display_name=item.service.display_name,
                    variant=item.service.variant,
                    quantity=item.quantity,
                    unit_price=Decimal(item.unit_price or 0),
                    line_total=Decimal(item.line_total or 0),
                )
                for item in bill.items
            ],
        )

    pdf_path = generate_receipt_pdf(receipt, settings_service)
    assert Path(pdf_path).exists()
