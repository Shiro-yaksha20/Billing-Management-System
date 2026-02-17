"""Staff repository for staff data access."""

from __future__ import annotations

from contextlib import AbstractContextManager
from typing import Callable, Iterable

from sqlalchemy.orm import Session

from .base_repository import BaseRepository
from ..models import Staff

SessionFactory = Callable[[], AbstractContextManager[Session]]


class StaffRepository(BaseRepository[Staff]):
    """Repository for staff CRUD and listing operations."""

    def __init__(self, session_factory: SessionFactory) -> None:
        super().__init__(session_factory, Staff)

    def list_active(self) -> Iterable[Staff]:
        with self._session_factory() as db:
            return db.query(Staff).filter(Staff.active == True).order_by(Staff.name).all()

    def update_staff(
        self,
        staff_id: int,
        name: str,
        phone: str | None,
        role: str | None,
    ) -> Staff | None:
        with self._session_factory() as db:
            staff = db.query(Staff).filter(Staff.id == staff_id).first()
            if not staff:
                return None
            staff.name = name
            staff.phone = phone
            staff.role = role
            db.flush()
            return staff

    def toggle_active(self, staff_id: int) -> bool:
        with self._session_factory() as db:
            staff = db.query(Staff).filter(Staff.id == staff_id).first()
            if not staff:
                return False
            staff.active = not staff.active
            return True
