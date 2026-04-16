"""Billing service for bill creation and management."""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Iterable, List

from ..dto.bill_dto import BillData, BillItemInput, BillOptions, DashboardStats
from ..dto.converters import bill_to_dto
from ..dto.receipt_dto import ReceiptData, ReceiptItemData
from ..exceptions.business_errors import (
    CustomerNotFoundError,
    DiscountExceedsSubtotalError,
    InsufficientDataError,
    NegativeTotalError,
    StaffNotFoundError,
)
from ..exceptions.validation_errors import ValidationError
from ..models import Bill, BillItem
from ..infrastructure.pdf_generator import generate_receipt_pdf
from ..repositories.bill_repository import BillRepository
from ..repositories.customer_repository import CustomerRepository
from ..repositories.staff_repository import StaffRepository
from .settings_service import SettingsService


class BillingService:
    """Service for bill creation and calculation."""

    def __init__(
        self,
        bill_repo: BillRepository,
        customer_repo: CustomerRepository,
        staff_repo: StaffRepository,
        settings_service: SettingsService,
    ) -> None:
        self._bill_repo = bill_repo
        self._customer_repo = customer_repo
        self._staff_repo = staff_repo
        self._settings_service = settings_service

    def calculate_discount(
        self, subtotal: Decimal, discount_type: str, discount_value: Decimal
    ) -> Decimal:
        """Calculate discount amount based on type and value."""
        if discount_value < 0:
            raise ValidationError("Discount value cannot be negative.")

        if discount_type == "flat":
            if discount_value > subtotal:
                raise DiscountExceedsSubtotalError("Discount cannot exceed subtotal.")
            return discount_value
        if discount_type == "percent":
            if discount_value > Decimal("100"):
                raise ValidationError("Discount percent cannot exceed 100.")
            return subtotal * (discount_value / Decimal("100"))
        if discount_type == "none":
            return Decimal("0")
        raise ValidationError("Invalid discount type.")

    def calculate_tax(self, amount: Decimal, tax_percent: Decimal) -> Decimal:
        """Calculate tax amount for a given taxable amount."""
        if tax_percent < 0 or tax_percent > Decimal("100"):
            raise ValidationError("Tax percent must be between 0 and 100.")
        return amount * (tax_percent / Decimal("100"))

    def create_bill(
        self,
        customer_id: int,
        staff_id: int,
        items: List[BillItemInput],
        options: BillOptions,
    ) -> BillData:
        """Create a bill with validation and persistence."""
        self._validate_bill_inputs(customer_id, staff_id, items)

        subtotal = sum(
            (item.unit_price * Decimal(item.quantity) for item in items), Decimal("0")
        )
        discount_amount = self.calculate_discount(
            subtotal, options.discount_type, options.discount_value
        )
        total_before_tax = subtotal - discount_amount
        if total_before_tax < 0:
            raise NegativeTotalError("Total cannot be negative.")

        tax_amount = self.calculate_tax(total_before_tax, options.tax_percent)
        total = total_before_tax + tax_amount

        bill = Bill(
            customer_id=customer_id,
            staff_id=staff_id,
            bill_datetime=datetime.now(timezone.utc),
            subtotal=subtotal,
            discount_amount=discount_amount,
            discount_type=options.discount_type,
            tax_amount=tax_amount,
            tax_percent=options.tax_percent,
            total=total,
            payment_method=options.payment_method,
            transaction_id=options.transaction_id,
            payment_status=options.payment_status,
        )

        for item in items:
            line_total = item.unit_price * Decimal(item.quantity)
            bill.items.append(
                BillItem(
                    service_id=item.service_id,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    line_total=line_total,
                )
            )

        persisted_bill = self._bill_repo.add(bill)
        if not persisted_bill.bill_number:
            bill_number = self._generate_bill_number(persisted_bill)
            self._bill_repo.update_bill_number(persisted_bill.id, bill_number)
            persisted_bill.bill_number = bill_number

        self._customer_repo.update_last_visit(customer_id, persisted_bill.bill_datetime)

        return self._to_bill_data(persisted_bill)

    def _validate_bill_inputs(
        self, customer_id: int, staff_id: int, items: Iterable[BillItemInput]
    ) -> None:
        if not items:
            raise InsufficientDataError("At least one bill item is required.")
        if not self._customer_repo.get_by_id(customer_id):
            raise CustomerNotFoundError("Customer not found.")
        if not self._staff_repo.get_by_id(staff_id):
            raise StaffNotFoundError("Staff member not found.")

    def get_bills(
        self,
        bill_number: str | None = None,
        customer_name: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        payment_status: str | None = None,
        payment_method: str | None = None,
    ) -> List[BillData]:
        """Return bills matching the provided filters."""
        bills = self._bill_repo.search(
            bill_number=bill_number,
            customer_name=customer_name,
            start_date=start_date,
            end_date=end_date,
            payment_status=payment_status,
            payment_method=payment_method,
        )
        return [self._to_bill_data(bill) for bill in bills]

    def get_dashboard_stats(self) -> DashboardStats:
        """Get statistics for the dashboard."""
        today = date.today()
        stats_data = self._bill_repo.get_daily_stats(today)
        recent_bills = list(self._bill_repo.find_recent(limit=5))

        return DashboardStats(
            today_sales=stats_data["paid_total"],
            today_bills_count=stats_data["total_bills"],
            pending_amount=stats_data["pending_total"],
            pending_count=stats_data["pending_count"],
            today_customers=stats_data["unique_customers"],
            recent_bills=[self._to_bill_data(b) for b in recent_bills],
        )

    @staticmethod
    def _to_bill_data(bill: Bill) -> BillData:
        return bill_to_dto(bill)

    def generate_receipt(self, bill_id: int) -> str:
        """Generate a receipt PDF for the given bill id."""
        bill = self._bill_repo.get_with_details(bill_id)
        if not bill:
            raise ValidationError("Bill not found.")
        receipt_items = [
            ReceiptItemData(
                service_name=item.service.name if item.service else "",
                display_name=item.service.display_name if item.service else None,
                variant=item.service.variant if item.service else None,
                quantity=item.quantity,
                unit_price=Decimal(item.unit_price or 0),
                line_total=Decimal(item.line_total or 0),
            )
            for item in bill.items
        ]
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
            customer_name=bill.customer.name if bill.customer else "",
            customer_phone=bill.customer.phone if bill.customer else "",
            staff_name=bill.staff.name if bill.staff else "",
            items=receipt_items,
        )
        pdf_path = generate_receipt_pdf(receipt, self._settings_service)
        self._bill_repo.update_pdf_path(bill_id, pdf_path)
        return pdf_path

    def update_whatsapp_status(self, bill_id: int, status: str, error: str | None = None) -> None:
        """Update WhatsApp status for a bill."""
        self._bill_repo.update_whatsapp_status(bill_id, status, error)

    def _generate_bill_number(self, bill: Bill) -> str:
        prefix = self._settings_service.get_setting("bill_number_prefix", "INV") or "INV"
        year = bill.bill_datetime.year if bill.bill_datetime else datetime.now().year
        return f"{prefix}-{year}-{bill.id:04d}"
