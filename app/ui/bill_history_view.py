"""Bill history view for past bills."""

from __future__ import annotations

import os
from datetime import datetime
from typing import Optional

from PyQt6.QtCore import QDate, Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from ..dto.bill_dto import BillData
from ..services.billing_service import BillingService
from ..services.notification_service import NotificationService


class BillHistoryView(QDialog):
    """View for displaying and managing bill history."""

    def __init__(
        self,
        billing_service: BillingService,
        notification_service: NotificationService,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._billing_service = billing_service
        self._notification_service = notification_service
        self._selected_bill: Optional[BillData] = None

        self.setWindowTitle("Bill History")
        self.setMinimumWidth(900)
        self.setMinimumHeight(600)

        self._setup_ui()
        self._connect_signals()
        self._load_bills()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        filter_group = QGroupBox("Search & Filters")
        filter_layout = QFormLayout()

        self._bill_number_input = QLineEdit()
        self._customer_input = QLineEdit()

        date_layout = QHBoxLayout()
        self._date_filter_checkbox = QCheckBox("Use date range")
        self._from_date = QDateEdit()
        self._from_date.setCalendarPopup(True)
        self._to_date = QDateEdit()
        self._to_date.setCalendarPopup(True)
        today = QDate.currentDate()
        self._from_date.setDate(today.addDays(-30))
        self._to_date.setDate(today)
        date_layout.addWidget(self._date_filter_checkbox)
        date_layout.addWidget(QLabel("From"))
        date_layout.addWidget(self._from_date)
        date_layout.addWidget(QLabel("To"))
        date_layout.addWidget(self._to_date)

        self._payment_status_combo = QComboBox()
        self._payment_status_combo.addItem("All", None)
        self._payment_status_combo.addItem("Paid", "Paid")
        self._payment_status_combo.addItem("Pending", "Pending")

        self._payment_method_combo = QComboBox()
        self._payment_method_combo.addItem("All", None)
        self._payment_method_combo.addItems(["Cash", "UPI", "Card", "Other"])

        filter_layout.addRow("Bill #:", self._bill_number_input)
        filter_layout.addRow("Customer:", self._customer_input)
        filter_layout.addRow("Date Range:", date_layout)
        filter_layout.addRow("Payment Status:", self._payment_status_combo)
        filter_layout.addRow("Payment Method:", self._payment_method_combo)

        search_button = QPushButton("Search")
        filter_layout.addRow(search_button)
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)

        self._search_button = search_button

        self._bills_table = QTableWidget()
        self._bills_table.setColumnCount(7)
        self._bills_table.setHorizontalHeaderLabels(
            ["Bill #", "Date", "Customer", "Total", "Payment", "Status", "WhatsApp"]
        )
        self._bills_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._bills_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._bills_table.setSortingEnabled(True)
        layout.addWidget(self._bills_table)

        action_layout = QHBoxLayout()
        self._view_pdf_button = QPushButton("View PDF")
        self._resend_button = QPushButton("Resend WhatsApp")
        self._print_button = QPushButton("Print")
        action_layout.addWidget(self._view_pdf_button)
        action_layout.addWidget(self._resend_button)
        action_layout.addWidget(self._print_button)
        layout.addLayout(action_layout)

    def _connect_signals(self) -> None:
        self._search_button.clicked.connect(self._load_bills)
        self._bills_table.itemSelectionChanged.connect(self._on_selection_changed)
        self._view_pdf_button.clicked.connect(self._view_pdf)
        self._resend_button.clicked.connect(self._resend_whatsapp)
        self._print_button.clicked.connect(self._print_pdf)

    def _load_bills(self) -> None:
        bill_number = self._bill_number_input.text().strip() or None
        customer = self._customer_input.text().strip() or None
        start_date = None
        end_date = None
        if self._date_filter_checkbox.isChecked():
            start_date = datetime.combine(self._from_date.date().toPyDate(), datetime.min.time())
            end_date = datetime.combine(self._to_date.date().toPyDate(), datetime.max.time())
        payment_status = self._payment_status_combo.currentData()
        payment_method = self._payment_method_combo.currentText()
        if self._payment_method_combo.currentIndex() == 0:
            payment_method = None

        bills = self._billing_service.get_bills(
            bill_number=bill_number,
            customer_name=customer,
            start_date=start_date,
            end_date=end_date,
            payment_status=payment_status,
            payment_method=payment_method,
        )
        self._populate_table(bills)

    def _populate_table(self, bills: list[BillData]) -> None:
        self._bills_table.setRowCount(len(bills))
        for row, bill in enumerate(bills):
            bill_number = bill.bill_number or str(bill.id)
            bill_date = bill.bill_datetime.strftime("%Y-%m-%d") if bill.bill_datetime else ""
            customer_name = bill.customer_name or f"#{bill.customer_id}"
            total = f"?{float(bill.total or 0):.2f}"
            payment = bill.payment_method or ""
            status = bill.payment_status or bill.status or ""
            whatsapp = bill.whatsapp_status or ""

            self._bills_table.setItem(row, 0, QTableWidgetItem(bill_number))
            self._bills_table.setItem(row, 1, QTableWidgetItem(bill_date))
            self._bills_table.setItem(row, 2, QTableWidgetItem(customer_name))
            self._bills_table.setItem(row, 3, QTableWidgetItem(total))
            self._bills_table.setItem(row, 4, QTableWidgetItem(payment))
            self._bills_table.setItem(row, 5, QTableWidgetItem(status))
            self._bills_table.setItem(row, 6, QTableWidgetItem(whatsapp))
            self._bills_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, bill)

    def _on_selection_changed(self) -> None:
        selected_row = self._bills_table.currentRow()
        if selected_row < 0:
            self._selected_bill = None
            return
        item = self._bills_table.item(selected_row, 0)
        if not item:
            self._selected_bill = None
            return
        self._selected_bill = item.data(Qt.ItemDataRole.UserRole)

    def _view_pdf(self) -> None:
        bill = self._selected_bill
        if not bill:
            QMessageBox.warning(self, "No Bill Selected", "Please select a bill.")
            return
        pdf_path = bill.pdf_path
        if not pdf_path or not os.path.exists(pdf_path):
            pdf_path = self._billing_service.generate_receipt(bill.id)
        if pdf_path and os.path.exists(pdf_path):
            try:
                os.startfile(pdf_path)
            except Exception:
                QMessageBox.information(self, "Receipt", f"Receipt saved at:\n{pdf_path}")
        else:
            QMessageBox.warning(self, "Receipt Not Found", "PDF receipt file not found.")

    def _resend_whatsapp(self) -> None:
        bill = self._selected_bill
        if not bill:
            QMessageBox.warning(self, "No Bill Selected", "Please select a bill.")
            return
        if not bill.customer_phone:
            QMessageBox.warning(self, "Missing Phone", "Customer phone number is missing.")
            return

        pdf_path = bill.pdf_path
        if not pdf_path or not os.path.exists(pdf_path):
            pdf_path = self._billing_service.generate_receipt(bill.id)

        result = self._notification_service.send_whatsapp_receipt(
            phone_number=bill.customer_phone,
            customer_name=bill.customer_name or "Customer",
            total=f"{float(bill.total or 0):.2f}",
            attachment_path=pdf_path,
        )
        if result.success:
            self._billing_service.update_whatsapp_status(bill.id, "Sent")
            QMessageBox.information(self, "WhatsApp Sent", "Receipt sent successfully.")
            self._load_bills()
        else:
            self._billing_service.update_whatsapp_status(bill.id, "Failed", result.error_message)
            QMessageBox.warning(self, "WhatsApp Failed", result.error_message or "Send failed")
            self._load_bills()

    def _print_pdf(self) -> None:
        bill = self._selected_bill
        if not bill:
            QMessageBox.warning(self, "No Bill Selected", "Please select a bill.")
            return

        pdf_path = bill.pdf_path
        if not pdf_path or not os.path.exists(pdf_path):
            pdf_path = self._billing_service.generate_receipt(bill.id)

        if not pdf_path or not os.path.exists(pdf_path):
            QMessageBox.warning(self, "Receipt Not Found", "PDF receipt file not found.")
            return

        try:
            os.startfile(pdf_path, "print")
        except Exception:
            QMessageBox.information(self, "Print Receipt", f"Receipt saved at:\n{pdf_path}")
