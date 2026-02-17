"""Bill repository for bill data access."""

from __future__ import annotations

from contextlib import AbstractContextManager
from datetime import datetime
from typing import Callable, Iterable, Optional

from sqlalchemy.orm import Session, selectinload

from .base_repository import BaseRepository
from ..models import Bill, BillItem, Customer

SessionFactory = Callable[[], AbstractContextManager[Session]]


class BillRepository(BaseRepository[Bill]):
    """Repository for bill CRUD and query operations."""

    def __init__(self, session_factory: SessionFactory) -> None:
        super().__init__(session_factory, Bill)

    def get_by_bill_number(self, bill_number: str) -> Optional[Bill]:
        with self._session_factory() as db:
            return db.query(Bill).filter(Bill.bill_number == bill_number).first()

    def list_by_customer(self, customer_id: int) -> Iterable[Bill]:
        with self._session_factory() as db:
            return (
                db.query(Bill)
                .options(selectinload(Bill.customer))
                .filter(Bill.customer_id == customer_id)
                .order_by(Bill.bill_datetime.desc())
                .all()
            )

    def find_recent(self, limit: int = 5) -> Iterable[Bill]:
        with self._session_factory() as db:
            return (
                db.query(Bill)
                .options(selectinload(Bill.customer))
                .order_by(Bill.bill_datetime.desc())
                .limit(limit)
                .all()
            )

    def find_by_date_range(self, start_date: datetime, end_date: datetime) -> Iterable[Bill]:
        with self._session_factory() as db:
            return (
                db.query(Bill)
                .options(selectinload(Bill.customer))
                .filter(Bill.bill_datetime >= start_date, Bill.bill_datetime <= end_date)
                .order_by(Bill.bill_datetime.desc())
                .all()
            )

    def search(
        self,
        bill_number: str | None = None,
        customer_name: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        payment_status: str | None = None,
        payment_method: str | None = None,
    ) -> Iterable[Bill]:
        with self._session_factory() as db:
            query = db.query(Bill).options(selectinload(Bill.customer))
            if bill_number:
                query = query.filter(Bill.bill_number.ilike(f"%{bill_number}%"))
            if customer_name:
                query = query.join(Customer).filter(Customer.name.ilike(f"%{customer_name}%"))
            if start_date:
                query = query.filter(Bill.bill_datetime >= start_date)
            if end_date:
                query = query.filter(Bill.bill_datetime <= end_date)
            if payment_status:
                query = query.filter(Bill.payment_status == payment_status)
            if payment_method:
                query = query.filter(Bill.payment_method == payment_method)

            return query.order_by(Bill.bill_datetime.desc()).all()

    def update_bill_number(self, bill_id: int, bill_number: str) -> bool:
        with self._session_factory() as db:
            bill = db.query(Bill).filter(Bill.id == bill_id).first()
            if not bill:
                return False
            bill.bill_number = bill_number
            return True

    def update_whatsapp_status(
        self,
        bill_id: int,
        status: str,
        error: str | None = None,
    ) -> bool:
        with self._session_factory() as db:
            bill = db.query(Bill).filter(Bill.id == bill_id).first()
            if not bill:
                return False
            bill.whatsapp_status = status
            bill.whatsapp_last_error = error
            return True

    def update_pdf_path(self, bill_id: int, pdf_path: str) -> bool:
        with self._session_factory() as db:
            bill = db.query(Bill).filter(Bill.id == bill_id).first()
            if not bill:
                return False
            bill.pdf_path = pdf_path
            return True

    def get_with_details(self, bill_id: int) -> Bill | None:
        with self._session_factory() as db:
            return (
                db.query(Bill)
                .options(
                    selectinload(Bill.customer),
                    selectinload(Bill.staff),
                    selectinload(Bill.items).selectinload(BillItem.service),
                )
                .filter(Bill.id == bill_id)
                .first()
            )

    def find_for_export(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        customer_id: int | None = None,
    ) -> Iterable[Bill]:
        with self._session_factory() as db:
            query = db.query(Bill).options(
                selectinload(Bill.customer),
                selectinload(Bill.staff),
                selectinload(Bill.items).selectinload(BillItem.service),
            )
            if start_date:
                query = query.filter(Bill.bill_datetime >= start_date)
            if end_date:
                query = query.filter(Bill.bill_datetime <= end_date)
            if customer_id:
                query = query.filter(Bill.customer_id == customer_id)
            return query.order_by(Bill.bill_datetime.desc()).all()
