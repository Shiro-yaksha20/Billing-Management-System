"""Settings repository for key/value configuration access."""

from __future__ import annotations

from contextlib import AbstractContextManager
from typing import Callable, Optional

from sqlalchemy.orm import Session

from .base_repository import BaseRepository
from ..models import Setting

SessionFactory = Callable[[], AbstractContextManager[Session]]


class SettingsRepository(BaseRepository[Setting]):
    """Repository for settings get/set operations."""

    def __init__(self, session_factory: SessionFactory) -> None:
        super().__init__(session_factory, Setting)

    def get_by_key(self, key: str) -> Optional[Setting]:
        with self._session_factory() as db:
            return db.query(Setting).filter(Setting.key == key).first()

    def set_value(self, key: str, value: str) -> Setting:
        with self._session_factory() as db:
            setting = db.query(Setting).filter(Setting.key == key).first()
            if not setting:
                setting = Setting(key=key)
                db.add(setting)
            setting.value = value
            db.flush()
            return setting
