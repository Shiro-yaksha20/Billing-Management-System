"""Customer management view."""

from __future__ import annotations

from decimal import Decimal

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QGroupBox,
    QHeaderView,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..dto.customer_dto import CustomerData
from ..exceptions.business_errors import CustomerNotFoundError
from ..exceptions.validation_errors import ValidationError
from ..services.billing_service import BillingService
from ..services.customer_service import CustomerService
from ..services.notification_service import NotificationService
from ..services.settings_service import SettingsService
from .helpers import format_money, open_pdf, send_whatsapp_receipt
from .dialogs.customer_dialog import CustomerDialog


class CustomerView(QWidget):
    """UI for managing customers."""

    def __init__(
        self,
        customer_service: CustomerService,
        billing_service: BillingService,
        notification_service: NotificationService,
        settings_service: SettingsService,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._customer_service = customer_service
        self._billing_service = billing_service
        self._notification_service = notification_service
        self._settings_service = settings_service
        self._currency_symbol = self._settings_service.get_setting("currency_symbol", "?") or "?"
        self.setWindowTitle("Manage Customers")
        self.setMinimumWidth(800)

        self._main_layout = QVBoxLayout(self)

        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by name or phone...")
        self.search_button = QPushButton("Search")
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_button)
        self._main_layout.addLayout(search_layout)

        self.customer_table = QTableWidget()
        self.customer_table.setColumnCount(4)
        self.customer_table.setHorizontalHeaderLabels(["Name", "Phone", "Last Visit", "ID"])
        self.customer_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.customer_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.customer_table.setColumnHidden(3, True)
        self.customer_table.setSortingEnabled(True)
        self.customer_table.horizontalHeader().setStretchLastSection(True)
        self.customer_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.customer_table.setAlternatingRowColors(True)
        self.customer_table.verticalHeader().setVisible(False)
        self._main_layout.addWidget(self.customer_table)

        self.notes_area = QTextEdit()
        self.notes_area.setReadOnly(True)
        self._main_layout.addWidget(self.notes_area)

        bills_group = QGroupBox("Bill History")
        bills_layout = QVBoxLayout()
        self.bills_table = QTableWidget()
        self.bills_table.setColumnCount(5)
        self.bills_table.setHorizontalHeaderLabels(["Bill #", "Date", "Total", "Payment", "Status"])
        self.bills_table.setSortingEnabled(True)
        self.bills_table.horizontalHeader().setStretchLastSection(True)
        self.bills_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.bills_table.setAlternatingRowColors(True)
        self.bills_table.verticalHeader().setVisible(False)
        bills_layout.addWidget(self.bills_table)
        self.view_receipt_btn = QPushButton("View Receipt PDF")
        self.view_receipt_btn.clicked.connect(self.view_selected_receipt)
        self.resend_whatsapp_btn = QPushButton("Resend WhatsApp")
        self.resend_whatsapp_btn.clicked.connect(self.resend_whatsapp)
        bills_layout.addWidget(self.view_receipt_btn)
        bills_layout.addWidget(self.resend_whatsapp_btn)
        bills_group.setLayout(bills_layout)
        self._main_layout.addWidget(bills_group)

        button_layout = QHBoxLayout()
        self.add_button = QPushButton("Add Customer")
        self.edit_button = QPushButton("Edit Customer")
        self.delete_button = QPushButton("Delete Customer")
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
        self._main_layout.addLayout(button_layout)

        self.search_button.clicked.connect(self.search_customers)
        self.search_input.returnPressed.connect(self.search_customers)
        self.customer_table.itemSelectionChanged.connect(self.display_customer_notes)
        self.add_button.clicked.connect(self.add_customer)
        self.edit_button.clicked.connect(self.edit_customer)
        self.delete_button.clicked.connect(self.delete_customer)

        self.load_customers()

    def refresh(self) -> None:
        self.load_customers(self.search_input.text().strip() or None)

    def load_customers(self, search_term: str | None = None) -> None:
        self.customer_table.blockSignals(True)
        try:
            customers = self._customer_service.search_customers(search_term or "")
            self.customer_table.setRowCount(len(customers))
            for i, customer in enumerate(customers):
                self._set_customer_row(i, customer)
        finally:
            self.customer_table.blockSignals(False)

    def _set_customer_row(self, row: int, customer: CustomerData) -> None:
        self.customer_table.setItem(row, 0, QTableWidgetItem(customer.name))
        self.customer_table.setItem(row, 1, QTableWidgetItem(customer.phone))
        last_visit = customer.last_visit_at.strftime("%Y-%m-%d") if customer.last_visit_at else "N/A"
        self.customer_table.setItem(row, 2, QTableWidgetItem(last_visit))
        self.customer_table.setItem(row, 3, QTableWidgetItem(str(customer.id)))

    def search_customers(self) -> None:
        self.load_customers(self.search_input.text())

    def display_customer_notes(self) -> None:
        selected_rows = self.customer_table.selectedItems()
        if not selected_rows:
            self.notes_area.clear()
            self.bills_table.setRowCount(0)
            return

        current_row = self.customer_table.currentRow()
        if current_row < 0:
            self.notes_area.clear()
            self.bills_table.setRowCount(0)
            return

        id_item = self.customer_table.item(current_row, 3)
        if not id_item:
            self.notes_area.clear()
            self.bills_table.setRowCount(0)
            return

        customer_id = int(id_item.text())
        try:
            customer = self._customer_service.get_customer(customer_id)
            self.notes_area.setPlainText(customer.notes or "")
            bills = self._customer_service.get_customer_bills(customer_id)
            self.bills_table.setRowCount(len(bills))
            for i, bill in enumerate(bills):
                self.bills_table.setItem(i, 0, QTableWidgetItem(str(bill.bill_number or bill.id)))
                bill_date = bill.bill_datetime.strftime("%Y-%m-%d") if bill.bill_datetime else ""
                self.bills_table.setItem(i, 1, QTableWidgetItem(bill_date))
                self.bills_table.setItem(
                    i,
                    2,
                    QTableWidgetItem(
                        format_money(Decimal(bill.total or 0), self._currency_symbol)
                    ),
                )
                self.bills_table.setItem(i, 3, QTableWidgetItem(bill.payment_method or ""))
                self.bills_table.setItem(i, 4, QTableWidgetItem(bill.payment_status or "Paid"))
                self.bills_table.item(i, 0).setData(Qt.ItemDataRole.UserRole, bill)
        except CustomerNotFoundError:
            self.notes_area.clear()
            self.bills_table.setRowCount(0)

    def view_selected_receipt(self) -> None:
        row = self.bills_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "No Bill Selected", "Please select a bill to view.")
            return
        bill = self.bills_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if not bill:
            QMessageBox.warning(self, "No Bill Selected", "Please select a bill to view.")
            return
        pdf_path = bill.pdf_path
        if not pdf_path:
            pdf_path = self._billing_service.generate_receipt(bill.id)
        open_pdf(pdf_path, self, title="Open Receipt")

    def resend_whatsapp(self) -> None:
        row = self.bills_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "No Bill Selected", "Please select a bill.")
            return
        bill = self.bills_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if not bill:
            QMessageBox.warning(self, "Missing Data", "Customer data is missing.")
            return
        send_whatsapp_receipt(
            bill=bill,
            billing_service=self._billing_service,
            notification_service=self._notification_service,
            parent=self,
        )

    def add_customer(self) -> None:
        dialog = CustomerDialog(self._customer_service, self)
        if dialog.exec():
            self.load_customers()

    def edit_customer(self) -> None:
        current_row = self.customer_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Customer Selected", "Please select a customer to edit.")
            return

        id_item = self.customer_table.item(current_row, 3)
        if not id_item:
            QMessageBox.warning(self, "Invalid Selection", "Could not identify the selected customer.")
            return

        customer_id = int(id_item.text())
        dialog = CustomerDialog(self._customer_service, self, customer_id=customer_id)
        if dialog.exec():
            self.load_customers()
            self.display_customer_notes()

    def delete_customer(self) -> None:
        current_row = self.customer_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Customer Selected", "Please select a customer to delete.")
            return

        id_item = self.customer_table.item(current_row, 3)
        if not id_item:
            QMessageBox.warning(self, "Invalid Selection", "Could not identify the selected customer.")
            return

        customer_id = int(id_item.text())
        confirm = QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to delete this customer? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        try:
            self._customer_service.delete_customer(customer_id)
            QMessageBox.information(self, "Customer Deleted", "Customer deleted successfully.")
            self.load_customers()
            self.notes_area.clear()
            self.bills_table.setRowCount(0)
        except ValidationError as exc:
            QMessageBox.warning(self, "Delete Failed", str(exc))
        except CustomerNotFoundError:
            QMessageBox.warning(self, "Delete Failed", "Customer not found.")
