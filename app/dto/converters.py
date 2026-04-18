"""DTO conversion utilities."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import inspect as sa_inspect

from ..models import Bill
from .bill_dto import BillData


def bill_to_dto(bill: Bill) -> BillData:
    """Convert a Bill ORM model to a BillData DTO."""
    customer = None
    try:
        state = sa_inspect(bill)
        if "customer" not in state.unloaded:
            customer = bill.customer
    except Exception:
        customer = None

    return BillData(
        id=bill.id,
        bill_number=bill.bill_number,
        customer_id=bill.customer_id,
        staff_id=bill.staff_id,
        bill_datetime=bill.bill_datetime,
        subtotal=Decimal(bill.subtotal or 0),
        discount_amount=Decimal(bill.discount_amount or 0),
        discount_type=bill.discount_type or "none",
        tax_amount=Decimal(bill.tax_amount or 0),
        tax_percent=Decimal(bill.tax_percent or 0),
        total=Decimal(bill.total or 0),
        payment_method=bill.payment_method or "Cash",
        status=bill.payment_status or bill.status or "Paid",
        pdf_path=bill.pdf_path,
        whatsapp_status=bill.whatsapp_status or "Not Sent",
        whatsapp_last_error=bill.whatsapp_last_error,
        transaction_id=bill.transaction_id,
        payment_status=bill.payment_status or bill.status or "Paid",
        customer_name=customer.name if customer else None,
        customer_phone=customer.phone if customer else None,
    )
