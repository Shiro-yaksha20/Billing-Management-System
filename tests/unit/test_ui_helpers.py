"""Unit tests for shared UI helper utilities."""

from __future__ import annotations

from decimal import Decimal

from app.ui import helpers


class _StubParent:
    pass


def test_format_money_formats_decimal() -> None:
    result = helpers.format_money(Decimal("1234.5"), "?")

    assert result == "?1,234.50"


def test_confirm_action_yes(monkeypatch) -> None:
    monkeypatch.setattr(
        "PyQt6.QtWidgets.QMessageBox.question",
        lambda *args, **kwargs: helpers.QMessageBox.StandardButton.Yes,
    )

    assert helpers.confirm_action(_StubParent(), "T", "M") is True


def test_confirm_action_no(monkeypatch) -> None:
    monkeypatch.setattr(
        "PyQt6.QtWidgets.QMessageBox.question",
        lambda *args, **kwargs: helpers.QMessageBox.StandardButton.No,
    )

    assert helpers.confirm_action(_StubParent(), "T", "M") is False


def test_open_pdf_missing_path_shows_warning(monkeypatch) -> None:
    calls = {"warned": False}

    def _warn(*args, **kwargs):
        calls["warned"] = True

    monkeypatch.setattr("PyQt6.QtWidgets.QMessageBox.warning", _warn)

    helpers.open_pdf(None, _StubParent())

    assert calls["warned"] is True
