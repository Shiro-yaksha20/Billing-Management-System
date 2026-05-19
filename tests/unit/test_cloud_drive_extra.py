"""Additional tests for CloudDriveAdapter."""

from __future__ import annotations

import json
from pathlib import Path
from types import ModuleType
import sys

from app.infrastructure.cloud_drive import CloudDriveAdapter


def _install_auth_stubs(monkeypatch, creds_obj):
    auth_requests = ModuleType("google.auth.transport.requests")
    oauth_credentials = ModuleType("google.oauth2.credentials")
    oauth_flow = ModuleType("google_auth_oauthlib.flow")

    auth_requests.Request = object

    class _Flow:
        def run_local_server(self, port=0):
            return creds_obj

    def _from_client_secrets_file(path, scopes):
        return _Flow()

    oauth_flow.InstalledAppFlow = ModuleType("InstalledAppFlow")
    oauth_flow.InstalledAppFlow.from_client_secrets_file = _from_client_secrets_file
    oauth_credentials.Credentials = creds_obj

    monkeypatch.setitem(sys.modules, "google.auth.transport.requests", auth_requests)
    monkeypatch.setitem(sys.modules, "google.oauth2.credentials", oauth_credentials)
    monkeypatch.setitem(sys.modules, "google_auth_oauthlib.flow", oauth_flow)


def test_token_storage_key_uses_credentials_path(tmp_path) -> None:
    adapter = CloudDriveAdapter(credentials_path=str(tmp_path / "creds.json"))

    assert adapter._token_storage_key().endswith("creds.json")


def test_read_token_payload_handles_keyring_error(monkeypatch) -> None:
    adapter = CloudDriveAdapter()

    def _fail(*args, **kwargs):
        raise RuntimeError("fail")

    monkeypatch.setattr("keyring.get_password", _fail)

    assert adapter._read_token_payload() is None


def test_write_token_payload_handles_keyring_error(monkeypatch) -> None:
    adapter = CloudDriveAdapter()

    def _fail(*args, **kwargs):
        raise RuntimeError("fail")

    monkeypatch.setattr("keyring.set_password", _fail)

    assert adapter._write_token_payload("token") is False


def test_load_credentials_from_keyring_payload(monkeypatch, tmp_path):
    adapter = CloudDriveAdapter(credentials_path=str(tmp_path / "creds.json"))

    class _Creds:
        valid = True
        expired = False
        refresh_token = None

        def to_json(self):
            return json.dumps({"token": "x"})

    class _CredsType:
        @staticmethod
        def from_authorized_user_info(payload, scopes):
            return _Creds()

    _install_auth_stubs(monkeypatch, _CredsType)
    monkeypatch.setattr("app.infrastructure.cloud_drive.CloudDriveAdapter._read_token_payload", lambda self: json.dumps({"token": "x"}))
    monkeypatch.setattr("app.infrastructure.cloud_drive.CloudDriveAdapter._write_token_payload", lambda self, payload: True)
    monkeypatch.setattr(Path, "write_text", lambda *args, **kwargs: None)

    creds = adapter._load_credentials()

    assert creds is not None


def test_load_credentials_handles_chmod_failure(monkeypatch, tmp_path):
    token_path = tmp_path / "token.json"
    creds_path = tmp_path / "creds.json"
    creds_path.write_text("{}", encoding="utf-8")
    token_path.write_text("{}", encoding="utf-8")
    adapter = CloudDriveAdapter(credentials_path=str(creds_path))

    class _Creds:
        valid = True
        expired = False
        refresh_token = None

        def to_json(self):
            return json.dumps({"token": "x"})

    class _CredsType:
        @staticmethod
        def from_authorized_user_file(filename, scopes):
            return _Creds()

    _install_auth_stubs(monkeypatch, _CredsType)
    monkeypatch.setattr("app.infrastructure.cloud_drive.CloudDriveAdapter._read_token_payload", lambda self: None)
    monkeypatch.setattr("app.infrastructure.cloud_drive.CloudDriveAdapter._write_token_payload", lambda self, payload: False)
    monkeypatch.setattr(Path, "write_text", lambda *args, **kwargs: None)

    def _chmod_fail(self, mode):
        raise OSError("fail")

    monkeypatch.setattr(Path, "chmod", _chmod_fail)

    creds = adapter._load_credentials()

    assert creds is not None
