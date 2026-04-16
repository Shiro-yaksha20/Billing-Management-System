"""Google Drive adapter for cloud backup storage."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import List, Optional

import keyring

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/drive.file"]
KEYRING_SERVICE_NAME = "BillingApp"
CLOUD_DRIVE_TOKEN_KEY = "cloud_drive_token"


class CloudDriveAdapter:
    """Adapter for Google Drive operations."""

    def __init__(
        self,
        credentials_path: Optional[str] = None,
        token_path: Optional[str] = None,
    ) -> None:
        self._credentials_path = credentials_path
        self._token_path = token_path
        self._service = None

    def authenticate(self) -> bool:
        """Authenticate with Google Drive."""
        try:
            self._service = self._get_service()
            return self._service is not None
        except Exception as exc:
            logger.error("Cloud Drive authentication failed: %s", exc, exc_info=True)
            return False

    def upload_file(self, local_path: str, remote_name: str) -> Optional[str]:
        """Upload file to Google Drive."""
        try:
            from googleapiclient.http import MediaFileUpload

            service = self._get_service()
            file_metadata = {"name": remote_name}
            media = MediaFileUpload(local_path, resumable=True)
            result = (
                service.files()
                .create(body=file_metadata, media_body=media, fields="id")
                .execute()
            )
            file_id = result.get("id")
            if file_id:
                logger.info("Uploaded backup to Google Drive: %s", file_id)
            return file_id
        except Exception as exc:
            logger.error("Cloud Drive upload failed: %s", exc, exc_info=True)
            return None

    def download_file(self, file_id: str, local_path: str) -> bool:
        """Download file from Google Drive."""
        try:
            from googleapiclient.http import MediaIoBaseDownload

            service = self._get_service()
            request = service.files().get_media(fileId=file_id)
            local_file = Path(local_path)
            local_file.parent.mkdir(parents=True, exist_ok=True)
            with local_file.open("wb") as file_handle:
                downloader = MediaIoBaseDownload(file_handle, request)
                done = False
                while not done:
                    _, done = downloader.next_chunk()
            logger.info("Downloaded backup from Google Drive: %s", file_id)
            return True
        except Exception as exc:
            logger.error("Cloud Drive download failed: %s", exc, exc_info=True)
            return False

    def list_backups(self) -> List[dict]:
        """List backup files in Google Drive."""
        try:
            service = self._get_service()
            response = (
                service.files()
                .list(
                    q="name contains 'backup_' and trashed=false",
                    fields="files(id, name, modifiedTime, size)",
                    orderBy="modifiedTime desc",
                )
                .execute()
            )
            return response.get("files", [])
        except Exception as exc:
            logger.error("Cloud Drive listing failed: %s", exc, exc_info=True)
            return []

    def _get_service(self):
        if self._service:
            return self._service

        try:
            from googleapiclient.discovery import build
        except ModuleNotFoundError as exc:
            raise ModuleNotFoundError(
                "Google Drive dependencies are not installed. Install google-api-python-client and google-auth-oauthlib."
            ) from exc

        creds = self._load_credentials()
        self._service = build("drive", "v3", credentials=creds)
        return self._service

    def _load_credentials(self):
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
        except ModuleNotFoundError as exc:
            raise ModuleNotFoundError(
                "Google Drive dependencies are not installed. Install google-api-python-client and google-auth-oauthlib."
            ) from exc

        token_path = self._resolve_token_path()
        creds = None
        token_payload = self._read_token_payload()
        if token_payload and hasattr(Credentials, "from_authorized_user_info"):
            creds = Credentials.from_authorized_user_info(json.loads(token_payload), SCOPES)
        elif token_path.exists():
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        elif not creds or not creds.valid:
            credentials_path = self._credentials_path
            if not credentials_path or not Path(credentials_path).exists():
                raise FileNotFoundError("Google Drive credentials file not found")
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)

        token_json = creds.to_json()
        token_saved = self._write_token_payload(token_json)

        if self._token_path or not token_saved:
            token_path.parent.mkdir(parents=True, exist_ok=True)
            token_path.write_text(token_json, encoding="utf-8")
            try:
                token_path.chmod(0o600)
            except OSError:
                logger.warning("Could not set strict permissions on token file: %s", token_path)

        return creds

    def _resolve_token_path(self) -> Path:
        if self._token_path:
            return Path(self._token_path)
        if self._credentials_path:
            return Path(self._credentials_path).with_name("token.json")
        return Path.home() / ".billing_app" / "token.json"

    def _token_storage_key(self) -> str:
        if self._credentials_path:
            return f"{CLOUD_DRIVE_TOKEN_KEY}:{Path(self._credentials_path).name}"
        return CLOUD_DRIVE_TOKEN_KEY

    def _read_token_payload(self) -> str | None:
        try:
            return keyring.get_password(KEYRING_SERVICE_NAME, self._token_storage_key())
        except Exception as exc:
            logger.warning("Keyring read for cloud token failed: %s", exc)
            return None

    def _write_token_payload(self, token_payload: str) -> bool:
        try:
            keyring.set_password(
                KEYRING_SERVICE_NAME,
                self._token_storage_key(),
                token_payload,
            )
            return True
        except Exception as exc:
            logger.warning("Keyring write for cloud token failed: %s", exc)
            return False
