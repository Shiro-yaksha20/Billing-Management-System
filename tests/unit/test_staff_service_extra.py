"""Additional unit tests for StaffService."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

import pytest

from app.dto.staff_dto import StaffData
from app.exceptions.business_errors import StaffNotFoundError
from app.models import Staff
from app.services.staff_service import StaffService


@dataclass
class _StubStaffRepo:
    staff: Optional[Staff] = None
    staff_list: Optional[Iterable[Staff]] = None

    def get_by_id(self, staff_id: int) -> Optional[Staff]:
        if self.staff and self.staff.id == staff_id:
            return self.staff
        return None

    def list_active(self) -> Iterable[Staff]:
        return list(self.staff_list or [])

    def list_all(self) -> Iterable[Staff]:
        return list(self.staff_list or [])

    def add(self, staff: Staff) -> Staff:
        staff.id = 1
        self.staff = staff
        return staff

    def update_staff(self, staff_id: int, name: str, phone: str | None, role: str | None):
        if not self.staff or self.staff.id != staff_id:
            return None
        self.staff.name = name
        self.staff.phone = phone
        self.staff.role = role
        return self.staff

    def toggle_active(self, staff_id: int) -> bool:
        if not self.staff or self.staff.id != staff_id:
            return False
        self.staff.active = not self.staff.active
        return True


def test_create_staff_trims_name() -> None:
    service = StaffService(_StubStaffRepo())

    staff = service.create_staff(" Alex ", "1", "Role")

    assert isinstance(staff, StaffData)
    assert staff.name == "Alex"


def test_update_staff_trims_name() -> None:
    staff_entity = Staff(id=1, name="Old", phone="1", role="Old", active=True)
    repo = _StubStaffRepo(staff=staff_entity)
    service = StaffService(repo)

    staff = service.update_staff(1, " New ", "2", "Role")

    assert staff.name == "New"


def test_list_all_empty_returns_empty_list() -> None:
    service = StaffService(_StubStaffRepo(staff_list=[]))

    assert service.list_all() == []


def test_get_staff_inactive_returns_data() -> None:
    staff_entity = Staff(id=2, name="Alex", phone="9", role="Stylist", active=False)
    service = StaffService(_StubStaffRepo(staff=staff_entity))

    staff = service.get_staff(2)

    assert staff.active is False


def test_toggle_active_missing_raises_not_found() -> None:
    service = StaffService(_StubStaffRepo())

    with pytest.raises(StaffNotFoundError):
        service.toggle_active(99)
