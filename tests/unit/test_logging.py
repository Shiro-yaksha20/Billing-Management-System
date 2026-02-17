"""Unit tests for logging utilities."""

from __future__ import annotations

import app.infrastructure.logging as logging_utils


def test_log_info_calls_logger(monkeypatch) -> None:
    calls = {"count": 0}

    class _StubLogger:
        def info(self, message):
            calls["count"] += 1

    monkeypatch.setattr(logging_utils, "logger", _StubLogger())

    logging_utils.log_info("message")

    assert calls["count"] == 1


def test_log_error_calls_logger(monkeypatch) -> None:
    calls = {"count": 0}

    class _StubLogger:
        def error(self, message):
            calls["count"] += 1

    monkeypatch.setattr(logging_utils, "logger", _StubLogger())

    logging_utils.log_error("message")

    assert calls["count"] == 1


def test_log_info_handles_logger_failure(monkeypatch) -> None:
    class _FailLogger:
        def info(self, message):
            raise RuntimeError("fail")

    monkeypatch.setattr(logging_utils, "logger", _FailLogger())

    logging_utils.log_info("message")


def test_log_error_handles_logger_failure(monkeypatch) -> None:
    class _FailLogger:
        def error(self, message):
            raise RuntimeError("fail")

    monkeypatch.setattr(logging_utils, "logger", _FailLogger())

    logging_utils.log_error("message")


def test_setup_logger_creates_dir(monkeypatch, tmp_path) -> None:
    logs_dir = tmp_path / "logs"

    monkeypatch.setattr(logging_utils, "LOGS_DIR", str(logs_dir))

    logging_utils.setup_logger()

    assert logs_dir.exists()
