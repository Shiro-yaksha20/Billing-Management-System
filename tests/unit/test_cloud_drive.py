"""Unit tests for Google Drive adapter."""

from __future__ import annotations

import json
import builtins
from pathlib import Path
from types import ModuleType
import sys

import pytest

from app.infrastructure.cloud_drive import CloudDriveAdapter


def _install_google_stubs(monkeypatch, tmp_path):
    discovery = ModuleType("googleapiclient.discovery")
    http = ModuleType("googleapiclient.http")
    auth_requests = ModuleType("google.auth.transport.requests")
    oauth_credentials = ModuleType("google.oauth2.credentials")
    oauth_flow = ModuleType("google_auth_oauthlib.flow")

    class _Creds:
        def __init__(self, valid=True, expired=False, refresh_token=False):
            self.valid = valid
            self.expired = expired
            self.refresh_token = refresh_token
            self.refreshed = False

        def refresh(self, request):
            self.refreshed = True
            self.valid = True
            self.expired = False

        def to_json(self):
            return json.dumps({"token": "x"})

        @classmethod
        def from_authorized_user_file(cls, filename, scopes):
            return cls(valid=False, expired=True, refresh_token=True)

    class _Flow:
        def run_local_server(self, port=0):
            return _Creds()

    def _from_client_secrets_file(path, scopes):
        return _Flow()

    oauth_credentials.Credentials = _Creds
    oauth_flow.InstalledAppFlow = ModuleType("InstalledAppFlow")
    oauth_flow.InstalledAppFlow.from_client_secrets_file = _from_client_secrets_file
    auth_requests.Request = object

    class _Files:
        def create(self, body=None, media_body=None, fields=None):
            return self

        def execute(self):
            return {"id": "file-id"}

        def list(self, q=None, fields=None, orderBy=None):
            return self

        def get_media(self, fileId=None):
            return object()

    class _Service:
        def files(self):
            return _Files()

    def _build(service_name, version, credentials=None):
        return _Service()

    class _MediaFileUpload:
        def __init__(self, path, resumable=True):
            self.path = path

    class _MediaIoBaseDownload:
        def __init__(self, fh, request):
            self._done = False

        def next_chunk(self):
            if self._done:
                return None, True
            self._done = True
            return None, True

    discovery.build = _build
    http.MediaFileUpload = _MediaFileUpload
    http.MediaIoBaseDownload = _MediaIoBaseDownload

    monkeypatch.setitem(sys.modules, "googleapiclient.discovery", discovery)
    monkeypatch.setitem(sys.modules, "googleapiclient.http", http)
    monkeypatch.setitem(sys.modules, "google.auth.transport.requests", auth_requests)
    monkeypatch.setitem(sys.modules, "google.oauth2.credentials", oauth_credentials)
    monkeypatch.setitem(sys.modules, "google_auth_oauthlib.flow", oauth_flow)

    credentials_path = tmp_path / "credentials.json"
    credentials_path.write_text("{}", encoding="utf-8")
    token_path = tmp_path / "token.json"
    token_path.write_text("{}", encoding="utf-8")
    return credentials_path, token_path


def test_cloud_drive_authenticate_success(monkeypatch, tmp_path):
    credentials_path, token_path = _install_google_stubs(monkeypatch, tmp_path)
    adapter = CloudDriveAdapter(
        credentials_path=str(credentials_path),
        token_path=str(token_path),
    )

    assert adapter.authenticate() is True


def test_cloud_drive_upload_download_list(monkeypatch, tmp_path):
    credentials_path, token_path = _install_google_stubs(monkeypatch, tmp_path)
    adapter = CloudDriveAdapter(
        credentials_path=str(credentials_path),
        token_path=str(token_path),
    )
    adapter.authenticate()

    local_file = tmp_path / "backup.db"
    local_file.write_text("data", encoding="utf-8")
    assert adapter.upload_file(str(local_file), "backup.db") == "file-id"
    assert adapter.download_file("file-id", str(tmp_path / "download.db")) is True
    assert adapter.list_backups() == []


def test_cloud_drive_authenticate_failure(monkeypatch, tmp_path):
    adapter = CloudDriveAdapter(credentials_path=str(tmp_path / "missing.json"))

    def _get_service():
        raise RuntimeError("fail")

    monkeypatch.setattr(adapter, "_get_service", _get_service)

    assert adapter.authenticate() is False


def test_cloud_drive_upload_failure(monkeypatch, tmp_path):
    adapter = CloudDriveAdapter(credentials_path=str(tmp_path / "missing.json"))

    def _get_service():
        raise RuntimeError("fail")

    monkeypatch.setattr(adapter, "_get_service", _get_service)

    assert adapter.upload_file("local", "remote") is None


def test_cloud_drive_download_failure(monkeypatch, tmp_path):
    adapter = CloudDriveAdapter(credentials_path=str(tmp_path / "missing.json"))

    def _get_service():
        raise RuntimeError("fail")

    monkeypatch.setattr(adapter, "_get_service", _get_service)

    assert adapter.download_file("file", str(tmp_path / "dest")) is False


def test_cloud_drive_list_backups_failure(monkeypatch, tmp_path):
    adapter = CloudDriveAdapter(credentials_path=str(tmp_path / "missing.json"))

    def _get_service():
        raise RuntimeError("fail")

    monkeypatch.setattr(adapter, "_get_service", _get_service)

    assert adapter.list_backups() == []


def test_cloud_drive_get_service_missing_dependency(monkeypatch):
    adapter = CloudDriveAdapter()

    original_import = builtins.__import__

    def _import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "googleapiclient.discovery":
            raise ModuleNotFoundError("missing discovery")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", _import)

    with pytest.raises(ModuleNotFoundError):
        adapter._get_service()


def test_cloud_drive_load_credentials_missing_file(monkeypatch, tmp_path):
    credentials_path, token_path = _install_google_stubs(monkeypatch, tmp_path)
    credentials_path.unlink()
    token_path.unlink()

    adapter = CloudDriveAdapter(credentials_path=str(credentials_path), token_path=str(token_path))

    with pytest.raises(FileNotFoundError):
        adapter._load_credentials()


def test_cloud_drive_load_credentials_missing_module(monkeypatch):
    adapter = CloudDriveAdapter()

    original_import = builtins.__import__

    def _import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "google.auth.transport.requests":
            raise ModuleNotFoundError("missing requests")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", _import)

    with pytest.raises(ModuleNotFoundError):
        adapter._load_credentials()


def test_cloud_drive_resolve_token_path_with_token_path(tmp_path):
    adapter = CloudDriveAdapter(token_path=str(tmp_path / "token.json"))
    assert adapter._resolve_token_path() == tmp_path / "token.json"


def test_cloud_drive_resolve_token_path_with_credentials_path(tmp_path):
    adapter = CloudDriveAdapter(credentials_path=str(tmp_path / "credentials.json"))
    assert adapter._resolve_token_path() == tmp_path / "token.json"


def test_cloud_drive_resolve_token_path_default(monkeypatch, tmp_path):
    adapter = CloudDriveAdapter()

    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    assert adapter._resolve_token_path() == tmp_path / ".billing_app" / "token.json"


def test_cloud_drive_load_credentials_uses_flow(monkeypatch, tmp_path):
    credentials_path, token_path = _install_google_stubs(monkeypatch, tmp_path)
    token_path.unlink()

    adapter = CloudDriveAdapter(credentials_path=str(credentials_path), token_path=str(token_path))
    creds = adapter._load_credentials()

    assert creds is not None


def test_cloud_drive_keyring_token_fallback(monkeypatch, tmp_path):
    credentials_path, token_path = _install_google_stubs(monkeypatch, tmp_path)
    token_path.unlink(missing_ok=True)

    adapter = CloudDriveAdapter(credentials_path=str(credentials_path), token_path=str(token_path))

    monkeypatch.setattr("keyring.get_password", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        "keyring.set_password",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("no backend")),
    )

    creds = adapter._load_credentials()

    assert creds is not None
    assert token_path.exists()
