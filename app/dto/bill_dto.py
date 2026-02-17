"""Billing DTOs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import List, Optional


@dataclass(frozen=True)
class BillItemInput:
    """Input data for a bill item."""

    service_id: int
    quantity: int
    unit_price: Decimal


@dataclass(frozen=True)
class BillOptions:
    """Options that affect bill calculation and persistence."""

    discount_type: str
    discount_value: Decimal
    tax_percent: Decimal
    payment_method: str
    transaction_id: Optional[str]
    payment_status: str


@dataclass(frozen=True)
class BillItemData:
    """Persisted bill item data."""

    id: int
    service_id: int
    quantity: int
    unit_price: Decimal
    line_total: Decimal


@dataclass(frozen=True)
class BillData:
    """Persisted bill data."""

    id: int
    bill_number: Optional[str]
    customer_id: int
    staff_id: int
    bill_datetime: datetime
    subtotal: Decimal
    discount_amount: Decimal
    discount_type: str
    tax_amount: Decimal
    tax_percent: Decimal
    total: Decimal
    payment_method: str
    status: str
    pdf_path: Optional[str]
    whatsapp_status: str
    whatsapp_last_error: Optional[str]
    transaction_id: Optional[str]
    payment_status: str
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None


@dataclass(frozen=True)
class DashboardStats:
    """Statistics for dashboard display."""

    today_sales: Decimal
    today_bills_count: int
    pending_amount: Decimal
    pending_count: int
    today_customers: int
    recent_bills: List[BillData]
