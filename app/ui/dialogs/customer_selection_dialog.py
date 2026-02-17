"""Customer selection dialog for multiple matches."""

from __future__ import annotations

from typing import List, Optional

from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
)

from PyQt6.QtCore import Qt

from ...dto.customer_dto import CustomerData


class CustomerSelectionDialog(QDialog):
    """Dialog for selecting a customer from multiple matches."""

    def __init__(self, customers: List[CustomerData], parent=None) -> None:
        super().__init__(parent)
        self._customers = customers
        self._selected_customer: Optional[CustomerData] = None
        self._setup_ui()

    @property
    def selected_customer(self) -> Optional[CustomerData]:
        """Return the selected customer, if any."""
        return self._selected_customer

    def _setup_ui(self) -> None:
        self.setWindowTitle("Select Customer")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)

        self._list_widget = QListWidget()
        for customer in self._customers:
            label = f"{customer.name} ({customer.phone})"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, customer)
            self._list_widget.addItem(item)
        self._list_widget.itemDoubleClicked.connect(self._select_current)
        layout.addWidget(self._list_widget)

        button_layout = QHBoxLayout()
        select_button = QPushButton("Select")
        cancel_button = QPushButton("Cancel")
        select_button.clicked.connect(self._select_current)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(select_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

    def _select_current(self) -> None:
        item = self._list_widget.currentItem()
        if not item:
            return
        self._selected_customer = item.data(Qt.ItemDataRole.UserRole)
        self.accept()
