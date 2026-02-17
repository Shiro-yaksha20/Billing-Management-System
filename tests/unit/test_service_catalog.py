"""Unit tests for ServiceCatalog."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable, Optional

import pytest

from app.exceptions.business_errors import InsufficientDataError
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
    ) -> Optional[Service]:
        if not self.service or self.service.id != service_id:
            return None
        self.service.name = name
        self.service.description = description
        self.service.price = price
        self.service.duration_minutes = duration_minutes
        return self.service

    def toggle_active(self, service_id: int) -> bool:
        if not self.service or self.service.id != service_id:
            return False
        self.service.active = not self.service.active
        return True


def test_create_service_requires_name() -> None:
    catalog = ServiceCatalog(_StubServiceRepo())
    with pytest.raises(InsufficientDataError):
        catalog.create_service("", None, None, None)


def test_create_service_returns_data() -> None:
    catalog = ServiceCatalog(_StubServiceRepo())
    created = catalog.create_service("Cut", "", Decimal("10"), 30)
    assert created.id == 1
    assert created.active is True


def test_update_service_missing_returns_none() -> None:
    catalog = ServiceCatalog(_StubServiceRepo())
    result = catalog.update_service(1, "Name", None, None, None)
    assert result is None


def test_list_all_returns_data() -> None:
    service = Service(id=1, name="Cut", price=Decimal("10"), active=True)
    catalog = ServiceCatalog(_StubServiceRepo(service=service))

    result = catalog.list_all()

    assert len(result) == 1
    assert result[0].id == 1


def test_list_active_returns_data() -> None:
    service = Service(id=1, name="Cut", price=Decimal("10"), active=True)
    catalog = ServiceCatalog(_StubServiceRepo(service=service))

    result = catalog.list_active()

    assert len(result) == 1
    assert result[0].id == 1


def test_toggle_active_success() -> None:
    service = Service(id=1, name="Cut", price=Decimal("10"), active=True)
    repo = _StubServiceRepo(service=service)
    catalog = ServiceCatalog(repo)

    result = catalog.toggle_active(1)

    assert result is True
    assert service.active is False


def test_toggle_active_missing_returns_false() -> None:
    catalog = ServiceCatalog(_StubServiceRepo())
    result = catalog.toggle_active(1)
    assert result is False


def test_rename_and_delete_category_returns_counts() -> None:
    class _Repo(_StubServiceRepo):
        def rename_category(self, old_name, new_name):
            return 2

        def clear_category(self, category):
            return 3

    catalog = ServiceCatalog(_Repo())

    assert catalog.rename_category("Old", "New") == 2
    assert catalog.delete_category("Old") == 3


def test_import_export_delegates(monkeypatch) -> None:
    class _Repo(_StubServiceRepo):
        pass

    calls = {"import": False, "export": False}

    def _import(path, service_repo, deactivate_existing=False, clear_existing=False):
        calls["import"] = True
        return {"success": True}

    def _export(path, service_repo, active_only=False):
        calls["export"] = True
        return True

    monkeypatch.setattr("app.services.service_catalog.import_services_from_csv", _import)
    monkeypatch.setattr("app.services.service_catalog.export_services_to_csv", _export)

    catalog = ServiceCatalog(_Repo())

    assert catalog.import_from_csv("file.csv", deactivate_existing=False)["success"] is True
    assert catalog.export_to_csv("file.csv", active_only=True) is True
    assert calls["import"] is True
    assert calls["export"] is True


def test_list_categories_returns_data() -> None:
    class _Repo(_StubServiceRepo):
        def list_categories(self):
            return ["Hair"]

    catalog = ServiceCatalog(_Repo())

    assert catalog.list_categories() == ["Hair"]


def test_update_service_returns_data() -> None:
    service = Service(id=1, name="Cut", price=Decimal("10"), active=True)

    class _Repo(_StubServiceRepo):
        def update_service(self, *args, **kwargs):
            return service

    catalog = ServiceCatalog(_Repo())

    result = catalog.update_service(1, "Cut", None, Decimal("10"), 30)

    assert result is not None
    assert result.id == 1
