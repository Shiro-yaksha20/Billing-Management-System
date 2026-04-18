"""Customer dialog for creating or editing customers."""

from __future__ import annotations

from PyQt6.QtCore import QRegularExpression
from PyQt6.QtGui import QRegularExpressionValidator
from PyQt6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ...dto.customer_dto import CustomerData
from ...exceptions.business_errors import CustomerNotFoundError, InsufficientDataError
from ...exceptions.validation_errors import ValidationError
from ...services.customer_service import CustomerService


class CustomerDialog(QDialog):
    """Dialog for adding or editing a customer."""

    def __init__(
        self, customer_service: CustomerService, parent: QWidget | None = None, customer_id: int | None = None
    ) -> None:
        super().__init__(parent)
        self._customer_service = customer_service
        self._customer_id = customer_id
        self.setMinimumSize(420, 300)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        form = QFormLayout(content)

        self.name_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.phone_input.setValidator(
            QRegularExpressionValidator(QRegularExpression(r"^\+?[0-9\-\s\(\)]{7,20}$"), self)
        )
        self.notes_input = QTextEdit()

        if self._customer_id:
            self.setWindowTitle("Edit Customer")
            try:
                customer = self._customer_service.get_customer(self._customer_id)
                self.name_input.setText(customer.name)
                self.phone_input.setText(customer.phone)
                self.notes_input.setPlainText(customer.notes or "")
            except CustomerNotFoundError:
                QMessageBox.critical(self, "Error", "Customer not found in database.")
        else:
            self.setWindowTitle("Add Customer")

        form.addRow("Name:", self.name_input)
        form.addRow("Phone:", self.phone_input)
        form.addRow("Notes:", self.notes_input)
        scroll.setWidget(content)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll)

        button_box = QHBoxLayout()
        save_button = QPushButton("Save")
        save_button.setObjectName("btn_primary")
        cancel_button = QPushButton("Cancel")
        cancel_button.setObjectName("btn_secondary")
        button_box.addWidget(save_button)
        button_box.addWidget(cancel_button)
        main_layout.addLayout(button_box)

        save_button.clicked.connect(self.save_customer)
        cancel_button.clicked.connect(self.reject)

    def save_customer(self) -> None:
        name = self.name_input.text().strip()
        phone = self.phone_input.text().strip()
        notes = self.notes_input.toPlainText().strip() or None

        try:
            if self._customer_id:
                updated = CustomerData(
                    id=self._customer_id,
                    name=name,
                    phone=phone,
                    notes=notes,
                    last_visit_at=None,
                )
                self._customer_service.update_customer(self._customer_id, updated)
            else:
                self._customer_service.create_customer(name=name, phone=phone, notes=notes)
        except InsufficientDataError as exc:
            QMessageBox.warning(self, "Input Error", str(exc))
            return
        except ValidationError as exc:
            QMessageBox.warning(self, "Validation Error", str(exc))
            return
        except CustomerNotFoundError:
            QMessageBox.critical(self, "Error", "Customer not found in database.")
            return

        self.accept()
