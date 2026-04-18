"""Settings service for app configuration and key migration."""

from __future__ import annotations

import keyring
from keyring.errors import KeyringError

from ..repositories.settings_repository import SettingsRepository
from ..infrastructure.logging import logger

KEYRING_SERVICE_NAME = "BillingApp"

KEY_MIGRATION = {
    "salon_name": "business_name",
    "salon_address": "business_address",
    "salon_phone": "business_phone",
    "salon_gstin": "business_gstin",
    "salon_instagram": "business_instagram",
    "salon_tagline": "business_tagline",
    "salon_logo_path": "business_logo_path",
}

LEGACY_KEY_BY_NEW_KEY = {new_key: old_key for old_key, new_key in KEY_MIGRATION.items()}


class SettingsService:
    """Service for non-sensitive settings and secrets."""

    def __init__(self, settings_repo: SettingsRepository) -> None:
        self._settings_repo = settings_repo

    def get_setting(self, key: str, default: str | None = None) -> str | None:
        candidates = [key]

        migrated_key = KEY_MIGRATION.get(key)
        if migrated_key and migrated_key not in candidates:
            candidates.append(migrated_key)

        legacy_key = LEGACY_KEY_BY_NEW_KEY.get(key)
        if legacy_key and legacy_key not in candidates:
            candidates.append(legacy_key)

        for candidate in candidates:
            setting = self._settings_repo.get_by_key(candidate)
            if setting:
                if key in LEGACY_KEY_BY_NEW_KEY and candidate == legacy_key:
                    self._settings_repo.set_value(key, setting.value)
                return setting.value

        return default

    def set_setting(self, key: str, value: str | None) -> None:
        mapped_key = KEY_MIGRATION.get(key, key)
        if key in KEY_MIGRATION and self._settings_repo.get_by_key(mapped_key):
            self._settings_repo.set_value(key, value)
            return
        self._settings_repo.set_value(mapped_key, value)

    def get_secret(self, key: str) -> str | None:
        try:
            return keyring.get_password(KEYRING_SERVICE_NAME, key)
        except (KeyringError, RuntimeError):
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
        except (KeyringError, RuntimeError):
            logger.error("Keyring write failed", exc_info=True)
            return False
