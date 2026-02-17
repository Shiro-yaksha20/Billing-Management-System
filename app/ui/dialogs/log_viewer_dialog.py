"""Log viewer dialog for application logs."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from ...constants import LOGS_DIR


class LogViewerDialog(QDialog):
    """Dialog for viewing application logs."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Application Logs")
        self.setMinimumWidth(700)
        self.setMinimumHeight(500)

        layout = QVBoxLayout(self)

        self._log_view = QTextEdit()
        self._log_view.setReadOnly(True)
        layout.addWidget(self._log_view)

        button_layout = QHBoxLayout()
        refresh_button = QPushButton("Refresh")
        clear_button = QPushButton("Clear")
        close_button = QPushButton("Close")
        refresh_button.clicked.connect(self._load_logs)
        clear_button.clicked.connect(self._clear_logs)
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(refresh_button)
        button_layout.addWidget(clear_button)
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)

        self._load_logs()

    def _log_path(self) -> Path:
        return Path(LOGS_DIR) / "app.log"

    def _load_logs(self) -> None:
        log_path = self._log_path()
        if not log_path.exists():
            self._log_view.setPlainText("Log file not found.")
            return
        try:
            self._log_view.setPlainText(log_path.read_text(encoding="utf-8"))
        except Exception as exc:
            self._log_view.setPlainText(f"Failed to read log file: {exc}")

    def _clear_logs(self) -> None:
        log_path = self._log_path()
        try:
            log_path.write_text("", encoding="utf-8")
            self._log_view.setPlainText("")
        except Exception as exc:
            QMessageBox.warning(self, "Clear Failed", f"Failed to clear log file: {exc}")
