"""Unit tests for crypto utilities."""

from __future__ import annotations

from pathlib import Path

from app.infrastructure.crypto import decrypt_file, derive_key, encrypt_file


def test_derive_key_returns_bytes() -> None:
    key = derive_key("password", b"1234567890abcdef")
    assert isinstance(key, bytes)
    assert len(key) > 0


def test_encrypt_decrypt_round_trip(tmp_path) -> None:
    source = tmp_path / "source.txt"
    encrypted = tmp_path / "encrypted.bin"
    decrypted = tmp_path / "decrypted.txt"
    source.write_text("data", encoding="utf-8")

    assert encrypt_file(str(source), str(encrypted), "secret") is True
    assert decrypt_file(str(encrypted), str(decrypted), "secret") is True
    assert decrypted.read_text(encoding="utf-8") == "data"


def test_decrypt_wrong_password_returns_false(tmp_path) -> None:
    source = tmp_path / "source.txt"
    encrypted = tmp_path / "encrypted.bin"
    decrypted = tmp_path / "decrypted.txt"
    source.write_text("data", encoding="utf-8")

    assert encrypt_file(str(source), str(encrypted), "secret") is True
    assert decrypt_file(str(encrypted), str(decrypted), "wrong") is False


def test_encrypt_missing_file_returns_false(tmp_path) -> None:
    source = tmp_path / "missing.txt"
    encrypted = tmp_path / "encrypted.bin"

    assert encrypt_file(str(source), str(encrypted), "secret") is False
