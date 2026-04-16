"""Customer repository for customer data access."""

from __future__ import annotations

from contextlib import AbstractContextManager
from typing import Callable, Iterable, Optional

from sqlalchemy.orm import Session

from .base_repository import BaseRepository
from .utils import escape_like
from ..models import Bill, Customer

SessionFactory = Callable[[], AbstractContextManager[Session]]


class CustomerRepository(BaseRepository[Customer]):
    """Repository for customer CRUD and search operations."""

    def __init__(self, session_factory: SessionFactory) -> None:
        super().__init__(session_factory, Customer)

    def search(self, term: str) -> Iterable[Customer]:
        with self._session_factory() as db:
            query = db.query(Customer)
            if term:
                safe_term = escape_like(term)
                query = query.filter(
                    Customer.name.ilike(f"%{safe_term}%", escape="\\")
                    | Customer.phone.ilike(f"%{safe_term}%", escape="\\")
                )
            return query.order_by(Customer.name).all()

    def get_with_bills(self, customer_id: int) -> Optional[Customer]:
        with self._session_factory() as db:
            return db.query(Customer).filter(Customer.id == customer_id).first()

    def get_bills(self, customer_id: int) -> Iterable[Bill]:
        with self._session_factory() as db:
            return (
                db.query(Bill)
                .filter(Bill.customer_id == customer_id)
                .order_by(Bill.bill_datetime.desc())
                .all()
            )

    def update_customer(
        self, customer_id: int, name: str, phone: str, notes: str | None
    ) -> Customer | None:
        with self._session_factory() as db:
            customer = db.query(Customer).filter(Customer.id == customer_id).first()
            if not customer:
                return None
            customer.name = name
            customer.phone = phone
            customer.notes = notes
            db.flush()
            return customer

    def update_last_visit(self, customer_id: int, last_visit_at) -> bool:
        with self._session_factory() as db:
            customer = db.query(Customer).filter(Customer.id == customer_id).first()
            if not customer:
                return False
            customer.last_visit_at = last_visit_at
            return True
