"""Unit tests for WhatsApp client."""

from __future__ import annotations

from pathlib import Path

import requests

from app.infrastructure.whatsapp_client import send_whatsapp_message


class _StubSettings:
    def __init__(self, token: str | None, phone_id: str | None) -> None:
        self._token = token
        self._phone_id = phone_id

    def get_secret(self, key: str):
        return self._token

    def get_setting(self, key: str, default: str | None = None):
        if key == "whatsapp_phone_id":
            return self._phone_id
        if key == "whatsapp_api_version":
            return "v15.0"
        return default


def test_send_whatsapp_message_missing_credentials() -> None:
    settings = _StubSettings(None, None)
    success, response = send_whatsapp_message("123", "hi", settings)
    assert success is False
    assert "error" in response


def test_send_whatsapp_message_text_success(monkeypatch) -> None:
    settings = _StubSettings("token", "phone")

    class _Response:
        status_code = 200

        def json(self):
            return {"ok": True}

        text = "ok"

    def _post(url, headers=None, data=None, files=None, timeout=None):
        return _Response()

    monkeypatch.setattr("requests.post", _post)

    success, response = send_whatsapp_message("123", "hi", settings)
    assert success is True
    assert response["ok"] is True


def test_send_whatsapp_message_text_failure(monkeypatch) -> None:
    settings = _StubSettings("token", "phone")

    class _Response:
        status_code = 400

        def json(self):
            return {"error": "fail"}

        text = "fail"

    def _post(url, headers=None, data=None, files=None, timeout=None):
        return _Response()

    monkeypatch.setattr("requests.post", _post)

    success, response = send_whatsapp_message("123", "hi", settings)
    assert success is False
    assert response["error"] == "fail"


def test_send_whatsapp_message_with_attachment_success(tmp_path, monkeypatch) -> None:
    settings = _StubSettings("token", "phone")
    attachment = tmp_path / "receipt.pdf"
    attachment.write_bytes(b"data")

    class _UploadResponse:
        status_code = 200

        def json(self):
            return {"id": "media"}

        text = "ok"

    class _MessageResponse:
        status_code = 200

        def json(self):
            return {"ok": True}

        text = "ok"

    def _post(url, headers=None, data=None, files=None, timeout=None):
        if url.endswith("/media"):
            return _UploadResponse()
        return _MessageResponse()

    monkeypatch.setattr("requests.post", _post)

    success, response = send_whatsapp_message("123", "hi", settings, attachment_path=str(attachment))
    assert success is True
    assert response["ok"] is True


def test_send_whatsapp_message_upload_failure(tmp_path, monkeypatch) -> None:
    settings = _StubSettings("token", "phone")
    attachment = tmp_path / "receipt.pdf"
    attachment.write_bytes(b"data")

    class _UploadResponse:
        status_code = 400

        def json(self):
            return {"error": "upload failed"}

        text = "fail"

    def _post(url, headers=None, data=None, files=None, timeout=None):
        return _UploadResponse()

    monkeypatch.setattr("requests.post", _post)

    success, response = send_whatsapp_message("123", "hi", settings, attachment_path=str(attachment))
    assert success is False
    assert "error" in response


def test_send_whatsapp_message_handles_request_exception(monkeypatch) -> None:
    settings = _StubSettings("token", "phone")

    def _post(*args, **kwargs):
        raise requests.exceptions.RequestException("fail")

    monkeypatch.setattr("requests.post", _post)

    success, response = send_whatsapp_message("123", "hi", settings)
    assert success is False
    assert response["error"] == "HTTP error."


def test_send_whatsapp_message_handles_io_error(monkeypatch) -> None:
    settings = _StubSettings("token", "phone")

    def _open(*args, **kwargs):
        raise IOError("fail")

    monkeypatch.setattr("builtins.open", _open)

    success, response = send_whatsapp_message("123", "hi", settings, attachment_path="file.pdf")
    assert success is False
    assert response["error"] == "IO error."


def test_send_whatsapp_message_missing_media_id(tmp_path, monkeypatch) -> None:
    settings = _StubSettings("token", "phone")
    attachment = tmp_path / "receipt.pdf"
    attachment.write_bytes(b"data")

    class _UploadResponse:
        status_code = 200

        def json(self):
            return {}

        text = "ok"

    def _post(url, headers=None, data=None, files=None, timeout=None):
        return _UploadResponse()

    monkeypatch.setattr("requests.post", _post)

    success, response = send_whatsapp_message("123", "hi", settings, attachment_path=str(attachment))
    assert success is False
    assert response["error"] == "Media ID not found in upload response."


def test_send_whatsapp_message_handles_unexpected_exception(monkeypatch) -> None:
    settings = _StubSettings("token", "phone")

    def _post(*args, **kwargs):
        raise ValueError("boom")

    monkeypatch.setattr("requests.post", _post)

    success, response = send_whatsapp_message("123", "hi", settings)
    assert success is False
    assert response["error"] == "Unexpected error."
