"""Additional unit tests for ServiceCatalog."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable, Optional

from app.models import Service
from app.services.service_catalog import ServiceCatalog


@dataclass
class _StubServiceRepo:
    service: Optional[Service] = None

    def list_all(self) -> Iterable[Service]:
        return [self.service] if self.service else []

    def list_active(self) -> Iterable[Service]:
        return [self.service] if self.service and self.service.active else []

    def add(self, service: Service) -> Service:
        service.id = 1
        self.service = service
        return service

    def update_service(
        self,
        service_id: int,
        name: str,
        description: Optional[str],
        price: Optional[Decimal],
        duration_minutes: Optional[int],
        category: Optional[str] = None,
        variant: Optional[str] = None,
        display_name: Optional[str] = None,
    ) -> Optional[Service]:
        if not self.service or self.service.id != service_id:
            return None
        self.service.name = name
        self.service.description = description
        self.service.price = price
        self.service.duration_minutes = duration_minutes
        self.service.category = category
        self.service.variant = variant
        self.service.display_name = display_name
        return self.service

    def toggle_active(self, service_id: int) -> bool:
        if not self.service or self.service.id != service_id:
            return False
        self.service.active = not self.service.active
        return True

    def list_categories(self):
        return []

    def rename_category(self, old_name, new_name):
        return 0

    def clear_category(self, category):
        return 0


def test_create_service_derives_display_name_from_variant() -> None:
    catalog = ServiceCatalog(_StubServiceRepo())

    result = catalog.create_service(
        name="Cut",
        description=None,
        price=Decimal("10"),
        duration_minutes=30,
        variant="Short",
        display_name="",
    )

    assert result.display_name == "Cut (Short)"


def test_create_service_uses_name_when_variant_missing() -> None:
    catalog = ServiceCatalog(_StubServiceRepo())

    result = catalog.create_service(
        name="Cut",
        description=None,
        price=Decimal("10"),
        duration_minutes=30,
        variant=None,
        display_name="",
    )

    assert result.display_name == "Cut"


def test_update_service_derives_display_name_when_missing() -> None:
    service = Service(id=1, name="Old", price=Decimal("5"), active=True)
    repo = _StubServiceRepo(service=service)
    catalog = ServiceCatalog(repo)

    result = catalog.update_service(
        1,
        name="Cut",
        description=None,
        price=Decimal("10"),
        duration_minutes=30,
        variant="Long",
        display_name="",
    )

    assert result is not None
    assert result.display_name == "Cut (Long)"


def test_toggle_active_flips_state() -> None:
    service = Service(id=1, name="Cut", price=Decimal("10"), active=True)
    catalog = ServiceCatalog(_StubServiceRepo(service=service))

    assert catalog.toggle_active(1) is True
    assert service.active is False
