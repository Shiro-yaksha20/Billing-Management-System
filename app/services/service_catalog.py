"""Service catalog operations."""

from __future__ import annotations

from decimal import Decimal
from typing import List, Optional

from ..csv_service_importer import export_services_to_csv, import_services_from_csv
from ..dto.service_dto import ServiceData
from ..exceptions.business_errors import InsufficientDataError
from ..models import Service
from ..repositories.service_repository import ServiceRepository


class ServiceCatalog:
    """Service catalog operations for services and CSV import/export."""

    def __init__(self, service_repo: ServiceRepository) -> None:
        self._service_repo = service_repo

    def list_all(self) -> List[ServiceData]:
        return [self._to_service_data(service) for service in self._service_repo.list_all()]

    def list_active(self) -> List[ServiceData]:
        return [self._to_service_data(service) for service in self._service_repo.list_active()]

    def list_categories(self) -> List[str]:
        return self._service_repo.list_categories()

    def rename_category(self, old_name: str, new_name: str) -> int:
        return self._service_repo.rename_category(old_name, new_name)

    def delete_category(self, category: str) -> int:
        return self._service_repo.clear_category(category)

    def create_service(
        self,
        name: str,
        description: Optional[str],
        price: Optional[Decimal],
        duration_minutes: Optional[int],
    ) -> ServiceData:
        if not name.strip():
            raise InsufficientDataError("Service name is required.")
        service = Service(
            name=name.strip(),
            description=description,
            price=price,
            duration_minutes=duration_minutes,
            active=True,
        )
        created = self._service_repo.add(service)
        return self._to_service_data(created)

    def update_service(
        self,
        service_id: int,
        name: str,
        description: Optional[str],
        price: Optional[Decimal],
        duration_minutes: Optional[int],
    ) -> Optional[ServiceData]:
        service = self._service_repo.update_service(
            service_id,
            name.strip(),
            description,
            price,
            duration_minutes,
        )
        if not service:
            return None
        return self._to_service_data(service)

    def toggle_active(self, service_id: int) -> bool:
        return self._service_repo.toggle_active(service_id)

    def import_from_csv(self, path: str, deactivate_existing: bool) -> dict:
        return import_services_from_csv(
            path,
            service_repo=self._service_repo,
            deactivate_existing=deactivate_existing,
        )

    def export_to_csv(self, path: str, active_only: bool) -> bool:
        return export_services_to_csv(path, service_repo=self._service_repo, active_only=active_only)

    @staticmethod
    def _to_service_data(service: Service) -> ServiceData:
        return ServiceData(
            id=service.id,
            name=service.name,
            description=service.description,
            price=service.price,
            duration_minutes=service.duration_minutes,
            active=service.active,
            category=service.category,
            display_name=service.display_name,
            variant=service.variant,
            notes=service.notes,
        )
