"""Receipt DTOs for PDF generation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import List, Optional


@dataclass(frozen=True)
class ReceiptItemData:
    """Line item data for receipts."""

    service_name: str
    display_name: Optional[str]
    variant: Optional[str]
    quantity: int
    unit_price: Decimal
    line_total: Decimal


@dataclass(frozen=True)
class ReceiptData:
    """Receipt data for PDF generation."""

    bill_id: int
    bill_number: Optional[str]
    bill_datetime: datetime
    subtotal: Decimal
    discount_amount: Decimal
    tax_percent: Decimal
    tax_amount: Decimal
    total: Decimal
    payment_method: str
    payment_status: str
    transaction_id: Optional[str]
    customer_name: str
    customer_phone: str
    staff_name: str
    items: List[ReceiptItemData]
