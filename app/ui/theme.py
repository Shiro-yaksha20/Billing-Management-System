"""Application theme and stylesheet."""

from __future__ import annotations

COLORS = {
    "bg_primary": "#1a1a2e",
    "bg_secondary": "#16213e",
    "bg_card": "#0f3460",
    "accent": "#e94560",
    "text": "#eaeaea",
    "text_muted": "#a0a0b0",
    "success": "#4CAF50",
    "warning": "#FF9800",
    "error": "#f44336",
    "border": "#2a2a4a",
}

STYLESHEET = """
QMainWindow {
    background-color: %(bg_primary)s;
}

QWidget#dashboard_page, QStackedWidget#content_stack {
    background-color: %(bg_primary)s;
}

QListWidget#nav_sidebar {
    background-color: %(bg_secondary)s;
    color: %(text)s;
    border: none;
    font-size: 14px;
    padding: 8px;
}

QListWidget#nav_sidebar::item {
    padding: 12px 16px;
    border-radius: 8px;
    margin: 2px 4px;
}

QListWidget#nav_sidebar::item:selected {
    background-color: %(accent)s;
    color: white;
}

QListWidget#nav_sidebar::item:hover:!selected {
    background-color: %(bg_card)s;
}

QGroupBox {
    background-color: %(bg_secondary)s;
    border: 1px solid %(border)s;
    border-radius: 8px;
    margin-top: 12px;
    padding: 16px;
    color: %(text)s;
    font-weight: bold;
}

QGroupBox::title {
    subcontrol-origin: margin;
    padding: 4px 12px;
}

QPushButton {
    background-color: %(accent)s;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 20px;
    font-size: 13px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #ff6b81;
}

QPushButton:pressed {
    background-color: #c0392b;
}

QLineEdit, QTextEdit, QComboBox, QDateEdit, QSpinBox {
    background-color: %(bg_card)s;
    color: %(text)s;
    border: 1px solid %(border)s;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 13px;
}

QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
    border: 1px solid %(accent)s;
}

QTableWidget {
    background-color: %(bg_secondary)s;
    color: %(text)s;
    border: 1px solid %(border)s;
    border-radius: 6px;
    gridline-color: %(border)s;
    selection-background-color: %(accent)s;
}

QTableWidget::item {
    padding: 6px;
}

QHeaderView::section {
    background-color: %(bg_card)s;
    color: %(text)s;
    border: 1px solid %(border)s;
    padding: 6px;
    font-weight: bold;
}

QLabel#page_title {
    font-size: 24px;
    font-weight: bold;
    color: %(text)s;
    padding: 8px 0;
}

QLabel {
    color: %(text)s;
}

QTabWidget::pane {
    border: 1px solid %(border)s;
    border-radius: 8px;
    background-color: %(bg_secondary)s;
}

QTabBar::tab {
    background-color: %(bg_card)s;
    color: %(text_muted)s;
    border: 1px solid %(border)s;
    padding: 8px 20px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}

QTabBar::tab:selected {
    background-color: %(accent)s;
    color: white;
}

QScrollArea {
    border: none;
}

QMessageBox {
    background-color: %(bg_primary)s;
}
""" % COLORS


def apply_theme(app) -> None:
    """Apply the application theme."""
    app.setStyleSheet(STYLESHEET)
