"""Staff service for staff operations."""

from __future__ import annotations

from typing import List

from ..dto.staff_dto import StaffData
from ..exceptions.business_errors import InsufficientDataError, StaffNotFoundError
from ..models import Staff
from ..repositories.staff_repository import StaffRepository


class StaffService:
    """Service for staff operations."""

    def __init__(self, staff_repo: StaffRepository) -> None:
        self._staff_repo = staff_repo

    def get_staff(self, staff_id: int) -> StaffData:
        staff = self._staff_repo.get_by_id(staff_id)
        if not staff:
            raise StaffNotFoundError("Staff member not found.")
        return self._to_staff_data(staff)

    def list_active_staff(self) -> List[StaffData]:
        return [self._to_staff_data(staff) for staff in self._staff_repo.list_active()]

    def list_all(self) -> List[StaffData]:
        return [self._to_staff_data(staff) for staff in self._staff_repo.list_all()]

    def create_staff(self, name: str, phone: str | None, role: str | None) -> StaffData:
        if not name.strip():
            raise InsufficientDataError("Staff name is required.")
        staff = Staff(name=name.strip(), phone=phone, role=role, active=True)
        return self._to_staff_data(self._staff_repo.add(staff))

    def update_staff(
        self, staff_id: int, name: str, phone: str | None, role: str | None
    ) -> StaffData:
        if not name.strip():
            raise InsufficientDataError("Staff name is required.")
        staff = self._staff_repo.update_staff(staff_id, name.strip(), phone, role)
        if not staff:
            raise StaffNotFoundError("Staff member not found.")
        return self._to_staff_data(staff)

    def toggle_active(self, staff_id: int) -> bool:
        if not self._staff_repo.toggle_active(staff_id):
            raise StaffNotFoundError("Staff member not found.")
        return True

    @staticmethod
    def _to_staff_data(staff: Staff) -> StaffData:
        return StaffData(
            id=staff.id,
            name=staff.name,
            phone=staff.phone,
            role=staff.role,
            active=staff.active,
        )
