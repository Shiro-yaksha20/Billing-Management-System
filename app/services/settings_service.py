"""Settings service for app configuration."""

from __future__ import annotations

import keyring

from ..repositories.settings_repository import SettingsRepository
from ..infrastructure.logging import logger

KEYRING_SERVICE_NAME = "SalonBillingApp"


class SettingsService:
    """Service for non-sensitive settings and secrets."""

    def __init__(self, settings_repo: SettingsRepository) -> None:
        self._settings_repo = settings_repo

    def get_setting(self, key: str, default: str | None = None) -> str | None:
        setting = self._settings_repo.get_by_key(key)
        return setting.value if setting else default

    def set_setting(self, key: str, value: str | None) -> None:
        self._settings_repo.set_value(key, value)

    def get_secret(self, key: str) -> str | None:
        try:
            return keyring.get_password(KEYRING_SERVICE_NAME, key)
        except Exception:
            logger.error("Keyring access failed for secret", exc_info=True)
            return None

    def set_secret(self, key: str, value: str | None) -> bool:
        try:
            if value is None:
                keyring.delete_password(KEYRING_SERVICE_NAME, key)
            else:
                keyring.set_password(KEYRING_SERVICE_NAME, key, value)
            logger.info("Secret updated")
            return True
        except Exception:
            logger.error("Keyring write failed", exc_info=True)
            return False
