"""Application theme and stylesheet."""

from __future__ import annotations

COLORS = {
    "bg_primary": "#0f0f1a",
    "bg_secondary": "#1a1a2e",
    "bg_card": "#1e2847",
    "bg_card_hover": "#263356",
    "accent": "#6c5ce7",
    "accent_hover": "#7c6ef7",
    "secondary_accent": "#00cec9",
    "success": "#00b894",
    "warning": "#fdcb6e",
    "danger": "#e17055",
    "text": "#f0f0f5",
    "text_secondary": "#8a8aa0",
    "text_muted": "#5a5a70",
    "border": "#2d2d4a",
    "alt_row": "#1a1a35",
}

STYLESHEET = """
QMainWindow {
    background-color: %(bg_primary)s;
}

QWidget#dashboard_page, QStackedWidget#content_stack {
    background-color: %(bg_primary)s;
}

QListWidget#nav_sidebar {
    background-color: %(bg_primary)s;
    color: %(text)s;
    border-right: 1px solid %(border)s;
    font-size: 14px;
    font-weight: 500;
}

QListWidget#nav_sidebar::item {
    padding: 14px 20px;
    border-radius: 0;
    border-left: 3px solid transparent;
    margin: 0;
}

QListWidget#nav_sidebar::item:selected {
    background-color: %(bg_card)s;
    border-left: 3px solid %(accent)s;
    color: %(accent)s;
    font-weight: 600;
}

QListWidget#nav_sidebar::item:hover:!selected {
    background-color: %(bg_secondary)s;
    border-left: 3px solid %(border)s;
}

QGroupBox {
    background-color: %(bg_card)s;
    border: 1px solid %(border)s;
    border-radius: 12px;
    margin-top: 16px;
    padding: 20px;
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
    border-radius: 8px;
    padding: 10px 24px;
    font-size: 13px;
    font-weight: 600;
}

QPushButton#btn_primary {
    background-color: %(accent)s;
    color: white;
}

QPushButton#btn_success {
    background-color: %(success)s;
    color: white;
}

QPushButton#btn_secondary {
    background-color: %(bg_secondary)s;
    color: %(text)s;
    border: 1px solid %(border)s;
}

QPushButton#btn_danger {
    background-color: %(danger)s;
    color: white;
}

QPushButton:hover {
    background-color: %(accent_hover)s;
}

QPushButton#btn_success:hover {
    background-color: #00c9a2;
}

QPushButton#btn_secondary:hover {
    background-color: %(bg_card_hover)s;
}

QPushButton#btn_danger:hover {
    background-color: #f18469;
}

QPushButton:pressed {
    background-color: %(accent)s;
}

QPushButton#quick_new_bill {
    background-color: %(accent)s;
}

QPushButton#quick_customers {
    background-color: %(success)s;
}

QPushButton#quick_export {
    background-color: %(secondary_accent)s;
    color: %(bg_primary)s;
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
    alternate-background-color: %(alt_row)s;
    color: %(text)s;
    border: 1px solid %(border)s;
    border-radius: 8px;
    gridline-color: %(border)s;
    selection-background-color: %(accent)s;
}

QTableWidget::item {
    padding: 6px;
}

QHeaderView::section {
    background-color: %(bg_card)s;
    color: %(text)s;
    border: none;
    border-bottom: 2px solid %(accent)s;
    padding: 6px;
    font-weight: 600;
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
