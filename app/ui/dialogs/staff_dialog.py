"""Staff dialog for creating or editing staff."""

from __future__ import annotations

from PyQt6.QtWidgets import QDialog, QFormLayout, QHBoxLayout, QLineEdit, QMessageBox, QPushButton

from ...exceptions.business_errors import InsufficientDataError, StaffNotFoundError
from ...services.staff_service import StaffService


class StaffDialog(QDialog):
    """Dialog for adding or editing staff."""

    def __init__(self, staff_service: StaffService, parent=None, staff_id: int | None = None) -> None:
        super().__init__(parent)
        self._staff_service = staff_service
        self._staff_id = staff_id

        self.layout = QFormLayout(self)
        self.name_input = QLineEdit()
        self.role_input = QLineEdit()
        self.phone_input = QLineEdit()

        if self._staff_id:
            self.setWindowTitle("Edit Staff")
            try:
                staff = self._staff_service.get_staff(self._staff_id)
                self.name_input.setText(staff.name or "")
                self.role_input.setText(staff.role or "")
                self.phone_input.setText(staff.phone or "")
            except StaffNotFoundError:
                QMessageBox.critical(self, "Error", "Staff member not found in database.")
        else:
            self.setWindowTitle("Add Staff")

        self.layout.addRow("Name:", self.name_input)
        self.layout.addRow("Role:", self.role_input)
        self.layout.addRow("Phone:", self.phone_input)

        button_box = QHBoxLayout()
        save_button = QPushButton("Save")
        cancel_button = QPushButton("Cancel")
        button_box.addWidget(save_button)
        button_box.addWidget(cancel_button)
        self.layout.addRow(button_box)

        save_button.clicked.connect(self.save_staff)
        cancel_button.clicked.connect(self.reject)

    def save_staff(self) -> None:
        try:
            name = self.name_input.text().strip()
            role = self.role_input.text().strip() or None
            phone = self.phone_input.text().strip() or None
            if self._staff_id:
                self._staff_service.update_staff(self._staff_id, name, phone, role)
            else:
                self._staff_service.create_staff(name=name, phone=phone, role=role)
        except InsufficientDataError as exc:
            QMessageBox.warning(self, "Input Error", str(exc))
            return
        except StaffNotFoundError:
            QMessageBox.critical(self, "Error", "Staff member not found in database.")
            return

        self.accept()
