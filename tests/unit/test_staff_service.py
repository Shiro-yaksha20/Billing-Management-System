"""Unit tests for StaffService."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

import pytest

from app.dto.staff_dto import StaffData
from app.exceptions.business_errors import InsufficientDataError, StaffNotFoundError
from app.models import Staff
from app.services.staff_service import StaffService


@dataclass
class _StubStaffRepo:
    staff: Optional[Staff] = None
    active_staff: Optional[Iterable[Staff]] = None

    def get_by_id(self, staff_id: int) -> Optional[Staff]:
        if self.staff and self.staff.id == staff_id:
            return self.staff
        return None

    def list_active(self) -> Iterable[Staff]:
        return list(self.active_staff or [])

    def list_all(self) -> Iterable[Staff]:
        return list(self.active_staff or [])

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


def test_create_staff_requires_name() -> None:
    service = StaffService(_StubStaffRepo())
    with pytest.raises(InsufficientDataError):
        service.create_staff("", None, None)


def test_create_staff_whitespace_name_raises() -> None:
    service = StaffService(_StubStaffRepo())
    with pytest.raises(InsufficientDataError):
        service.create_staff("   ", None, None)


def test_update_staff_missing_raises() -> None:
    service = StaffService(_StubStaffRepo())
    with pytest.raises(StaffNotFoundError):
        service.update_staff(1, "Name", None, None)


def test_toggle_active_missing_raises() -> None:
    service = StaffService(_StubStaffRepo())
    with pytest.raises(StaffNotFoundError):
        service.toggle_active(1)


def test_create_staff_sets_active() -> None:
    service = StaffService(_StubStaffRepo())
    staff = service.create_staff("Name", "123", "Role")
    assert isinstance(staff, StaffData)
    assert staff.id == 1
    assert staff.active is True


def test_get_staff_existing_returns_data() -> None:
    staff_entity = Staff(id=2, name="Alex", phone="9", role="Stylist", active=True)
    service = StaffService(_StubStaffRepo(staff=staff_entity))

    staff = service.get_staff(2)

    assert staff.id == 2
    assert staff.name == "Alex"
    assert staff.role == "Stylist"


def test_get_staff_missing_raises() -> None:
    service = StaffService(_StubStaffRepo())
    with pytest.raises(StaffNotFoundError):
        service.get_staff(1)


def test_list_active_staff_returns_list() -> None:
    staff_entity = Staff(id=1, name="Alex", phone="9", role="Stylist", active=True)
    service = StaffService(_StubStaffRepo(active_staff=[staff_entity]))

    staff_list = service.list_active_staff()

    assert len(staff_list) == 1
    assert staff_list[0].id == 1


def test_list_active_staff_empty_returns_empty_list() -> None:
    service = StaffService(_StubStaffRepo(active_staff=[]))

    staff_list = service.list_active_staff()

    assert staff_list == []


def test_list_all_returns_list() -> None:
    staff_entity = Staff(id=1, name="Alex", phone="9", role="Stylist", active=True)
    service = StaffService(_StubStaffRepo(active_staff=[staff_entity]))

    staff_list = service.list_all()

    assert len(staff_list) == 1
    assert staff_list[0].id == 1


def test_list_all_includes_inactive_staff() -> None:
    active_staff = Staff(id=1, name="Alex", phone="9", role="Stylist", active=True)
    inactive_staff = Staff(id=2, name="Lee", phone="8", role="Stylist", active=False)
    service = StaffService(_StubStaffRepo(active_staff=[active_staff, inactive_staff]))

    staff_list = service.list_all()

    assert len(staff_list) == 2
    assert {staff.id for staff in staff_list} == {1, 2}


def test_update_staff_success_returns_data() -> None:
    staff_entity = Staff(id=1, name="Old", phone="1", role="Old", active=True)
    repo = _StubStaffRepo(staff=staff_entity)
    service = StaffService(repo)

    staff = service.update_staff(1, "New", "2", "Role")

    assert staff.name == "New"
    assert staff.phone == "2"
    assert staff.role == "Role"


def test_update_staff_requires_name() -> None:
    staff_entity = Staff(id=1, name="Old", phone="1", role="Old", active=True)
    repo = _StubStaffRepo(staff=staff_entity)
    service = StaffService(repo)

    with pytest.raises(InsufficientDataError):
        service.update_staff(1, "", "1", "Role")


def test_update_staff_whitespace_name_raises() -> None:
    staff_entity = Staff(id=1, name="Old", phone="1", role="Old", active=True)
    repo = _StubStaffRepo(staff=staff_entity)
    service = StaffService(repo)

    with pytest.raises(InsufficientDataError):
        service.update_staff(1, "   ", "1", "Role")


def test_toggle_active_success() -> None:
    staff_entity = Staff(id=1, name="Alex", phone="9", role="Stylist", active=True)
    repo = _StubStaffRepo(staff=staff_entity)
    service = StaffService(repo)

    result = service.toggle_active(1)

    assert result is True
    assert staff_entity.active is False


def test_toggle_active_twice_restores_state() -> None:
    staff_entity = Staff(id=1, name="Alex", phone="9", role="Stylist", active=True)
    repo = _StubStaffRepo(staff=staff_entity)
    service = StaffService(repo)

    service.toggle_active(1)
    service.toggle_active(1)

    assert staff_entity.active is True
