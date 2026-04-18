"""Service repository for service data access."""

from __future__ import annotations

from contextlib import AbstractContextManager, contextmanager
from typing import Callable, Iterable, List, Optional

from sqlalchemy import distinct
from sqlalchemy.orm import Session

from .base_repository import BaseRepository
from ..models import Service

SessionFactory = Callable[[], AbstractContextManager[Session]]


class ServiceRepository(BaseRepository[Service]):
    """Repository for service CRUD and filter operations."""

    def __init__(self, session_factory: SessionFactory) -> None:
        super().__init__(session_factory, Service)

    @contextmanager
    def transaction_scope(self):
        """Provide a shared transaction session for bulk operations."""
        with self._session_factory() as db:
            yield db

    def list_active(self) -> Iterable[Service]:
        with self._session_factory() as db:
            return (
                db.query(Service)
                .filter(Service.active.is_(True))
                .order_by(Service.category, Service.display_name)
                .all()
            )

    def list_by_category(self, category: str) -> Iterable[Service]:
        with self._session_factory() as db:
            return (
                db.query(Service)
                .filter(Service.active.is_(True), Service.category == category)
                .order_by(Service.display_name)
                .all()
            )

    def list_categories(self) -> List[str]:
        with self._session_factory() as db:
            rows = (
                db.query(distinct(Service.category))
                .filter(Service.category.isnot(None))
                .all()
            )
            return sorted({row[0] for row in rows if row[0]})

    def rename_category(self, old_name: str, new_name: str) -> int:
        with self._session_factory() as db:
            count = (
                db.query(Service)
                .filter(Service.category == old_name)
                .update({Service.category: new_name}, synchronize_session=False)
            )
            return count

    def clear_category(self, category: str) -> int:
        with self._session_factory() as db:
            count = (
                db.query(Service)
                .filter(Service.category == category)
                .update({Service.category: None}, synchronize_session=False)
            )
            return count

    def get_by_display_name(self, display_name: str) -> Optional[Service]:
        with self._session_factory() as db:
            return (
                db.query(Service)
                .filter(Service.display_name == display_name)
                .first()
            )

    def list_for_export(self, active_only: bool = False) -> Iterable[Service]:
        with self._session_factory() as db:
            query = db.query(Service)
            if active_only:
                query = query.filter(Service.active.is_(True))
            return query.order_by(Service.category, Service.name, Service.variant).all()

    def deactivate_all(self, db: Session | None = None) -> int:
        if db is not None:
            return db.query(Service).update({Service.active: False}, synchronize_session=False)
        with self._session_factory() as local_db:
            return local_db.query(Service).update({Service.active: False}, synchronize_session=False)

    def delete_all(self, db: Session | None = None) -> int:
        if db is not None:
            return db.query(Service).delete()
        with self._session_factory() as local_db:
            return local_db.query(Service).delete()

    def upsert_from_import(
        self,
        display_name: str,
        name: str,
        category: str | None,
        variant: str | None,
        price,
        notes: str | None,
        active: bool = True,
        db: Session | None = None,
    ) -> bool:
        if db is None:
            with self._session_factory() as local_db:
                return self.upsert_from_import(
                    display_name=display_name,
                    name=name,
                    category=category,
                    variant=variant,
                    price=price,
                    notes=notes,
                    active=active,
                    db=local_db,
                )

        service = db.query(Service).filter(Service.display_name == display_name).first()
        if service:
            service.category = category
            service.name = name
            service.variant = variant
            service.display_name = display_name
            service.price = price
            service.notes = notes
            service.active = active
            return True
        service = Service(
            category=category,
            name=name,
            variant=variant,
            display_name=display_name,
            price=price,
            notes=notes,
            active=active,
        )
        db.add(service)
        return False

    def update_service(
        self,
        service_id: int,
        name: str,
        description: str | None,
        price,
        duration_minutes,
        category: str | None = None,
        variant: str | None = None,
        display_name: str | None = None,
    ) -> Service | None:
        with self._session_factory() as db:
            service = db.query(Service).filter(Service.id == service_id).first()
            if not service:
                return None
            service.name = name
            service.description = description
            service.price = price
            service.duration_minutes = duration_minutes
            service.category = category
            service.variant = variant
            service.display_name = display_name
            db.flush()
            return service

    def toggle_active(self, service_id: int) -> bool:
        with self._session_factory() as db:
            service = db.query(Service).filter(Service.id == service_id).first()
            if not service:
                return False
            service.active = not service.active
            return True
