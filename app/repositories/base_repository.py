"""Base repository for common CRUD operations."""

from __future__ import annotations

from contextlib import AbstractContextManager
from typing import Callable, Generic, Iterable, Optional, TypeVar

from sqlalchemy.orm import Session

ModelType = TypeVar("ModelType")
SessionFactory = Callable[[], AbstractContextManager[Session]]


class BaseRepository(Generic[ModelType]):
    """Base repository providing common CRUD helpers."""

    def __init__(self, session_factory: SessionFactory, model_type: type[ModelType]) -> None:
        self._session_factory = session_factory
        self._model_type = model_type

    def get_by_id(self, entity_id: int) -> Optional[ModelType]:
        with self._session_factory() as db:
            return db.get(self._model_type, entity_id)

    def list_all(self) -> Iterable[ModelType]:
        with self._session_factory() as db:
            return db.query(self._model_type).all()

    def add(self, entity: ModelType) -> ModelType:
        with self._session_factory() as db:
            db.add(entity)
            db.flush()
            db.refresh(entity)
            db.expunge(entity)
            return entity

    def delete(self, entity_id: int) -> bool:
        with self._session_factory() as db:
            entity = db.get(self._model_type, entity_id)
            if not entity:
                return False
            db.delete(entity)
            return True
