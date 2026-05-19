"""Service dialog for creating or editing services."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from PyQt6.QtWidgets import QDialog, QFormLayout, QHBoxLayout, QLineEdit, QMessageBox, QPushButton

from ...exceptions.business_errors import InsufficientDataError
from ...services.service_catalog import ServiceCatalog


class ServiceDialog(QDialog):
    """Dialog for adding or editing a service."""

    def __init__(self, service_catalog: ServiceCatalog, parent=None, service_id: int | None = None) -> None:
        super().__init__(parent)
        self._service_catalog = service_catalog
        self._service_id = service_id

        self.layout = QFormLayout(self)
        self.name_input = QLineEdit()
        self.category_input = QLineEdit()
        self.variant_input = QLineEdit()
        self.display_name_input = QLineEdit()
        self.description_input = QLineEdit()
        self.price_input = QLineEdit()
        self.duration_input = QLineEdit()

        if self._service_id:
            self.setWindowTitle("Edit Service")
            service = next((s for s in self._service_catalog.list_all() if s.id == self._service_id), None)
            if service:
                self.name_input.setText(service.name or "")
                self.category_input.setText(service.category or "")
                self.variant_input.setText(service.variant or "")
                self.display_name_input.setText(service.display_name or "")
                self.description_input.setText(service.description or "")
                self.price_input.setText(str(service.price) if service.price is not None else "")
                self.duration_input.setText(
                    str(service.duration_minutes) if service.duration_minutes is not None else ""
                )
        else:
            self.setWindowTitle("Add Service")

        self.layout.addRow("Name:", self.name_input)
        self.layout.addRow("Category:", self.category_input)
        self.layout.addRow("Variant:", self.variant_input)
        self.layout.addRow("Display Name:", self.display_name_input)
        self.layout.addRow("Description:", self.description_input)
        self.layout.addRow("Price:", self.price_input)
        self.layout.addRow("Duration (minutes):", self.duration_input)

        button_box = QHBoxLayout()
        save_button = QPushButton("Save")
        save_button.setObjectName("btn_primary")
        cancel_button = QPushButton("Cancel")
        cancel_button.setObjectName("btn_secondary")
        button_box.addWidget(save_button)
        button_box.addWidget(cancel_button)
        self.layout.addRow(button_box)

        save_button.clicked.connect(self.save_service)
        cancel_button.clicked.connect(self.reject)

    def save_service(self) -> None:
        try:
            name = self.name_input.text().strip()
            category = self.category_input.text().strip() or None
            variant = self.variant_input.text().strip() or None
            display_name = self.display_name_input.text().strip() or None
            description = self.description_input.text().strip() or None
            price_text = self.price_input.text().strip()
            price = Decimal(price_text) if price_text else None
            duration_text = self.duration_input.text().strip()
            duration = int(duration_text) if duration_text else None
        except (InvalidOperation, ValueError):
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid number for price and duration.")
            return

        try:
            if self._service_id:
                updated = self._service_catalog.update_service(
                    self._service_id,
                    name=name,
                    category=category,
                    variant=variant,
                    display_name=display_name,
                    description=description,
                    price=price,
                    duration_minutes=duration,
                )
                if not updated:
                    QMessageBox.critical(self, "Error", "Service not found in database.")
                    return
            else:
                self._service_catalog.create_service(
                    name=name,
                    category=category,
                    variant=variant,
                    display_name=display_name,
                    description=description,
                    price=price,
                    duration_minutes=duration,
                )
        except InsufficientDataError as exc:
            QMessageBox.warning(self, "Input Error", str(exc))
            return

        self.accept()
