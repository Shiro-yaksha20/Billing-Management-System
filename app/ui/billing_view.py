"""Billing view for creating new bills."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDoubleValidator, QIntValidator, QKeySequence, QShortcut, QValidator
from PyQt6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..dto.bill_dto import BillItemInput, BillOptions
from ..dto.customer_dto import CustomerData
from ..dto.receipt_dto import ReceiptData, ReceiptItemData
from ..dto.service_dto import ServiceData
from ..exceptions.validation_errors import ValidationError
from ..infrastructure.pdf_generator import generate_receipt_pdf
from ..services.billing_service import BillingService
from ..services.customer_service import CustomerService
from ..services.notification_service import NotificationService
from ..services.service_catalog import ServiceCatalog
from ..services.settings_service import SettingsService
from ..services.staff_service import StaffService
from .helpers import confirm_action, format_money, open_pdf, send_whatsapp_receipt
from .dialogs.customer_dialog import CustomerDialog
from .dialogs.customer_selection_dialog import CustomerSelectionDialog


class BillingView(QWidget):
    """Page for creating a new bill."""

    def __init__(
        self,
        billing_service: BillingService,
        customer_service: CustomerService,
        staff_service: StaffService,
        service_catalog: ServiceCatalog,
        notification_service: NotificationService,
        settings_service: SettingsService,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._billing_service = billing_service
        self._customer_service = customer_service
        self._staff_service = staff_service
        self._service_catalog = service_catalog
        self._notification_service = notification_service
        self._settings_service = settings_service
        self._currency_symbol = self._settings_service.get_setting("currency_symbol", "₹") or "₹"

        self.setWindowTitle("New Bill")
        self.setMinimumWidth(600)

        self.selected_customer: CustomerData | None = None
        self.all_services: list[ServiceData] = []
        self._last_load_time = datetime.min

        self._main_layout = QVBoxLayout(self)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        left_widget = QWidget()
        right_widget = QWidget()
        left_widget.setMinimumWidth(360)
        right_widget.setMinimumWidth(260)
        left_panel = QVBoxLayout(left_widget)
        right_panel = QVBoxLayout(right_widget)
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.addWidget(splitter)
        scroll.setWidget(scroll_content)
        self._main_layout.addWidget(scroll)

        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout()
        self._customer_status_label = QLabel("Customer: Pending")
        self._services_status_label = QLabel("Services: Pending")
        self._payment_status_label = QLabel("Payment: Pending")
        self._ready_status_label = QLabel("")
        progress_layout.addWidget(self._customer_status_label)
        progress_layout.addWidget(self._services_status_label)
        progress_layout.addWidget(self._payment_status_label)
        progress_layout.addWidget(self._ready_status_label)
        progress_group.setLayout(progress_layout)
        right_panel.addWidget(progress_group)

        customer_group = QGroupBox("1. Customer")
        customer_layout = QFormLayout()
        self.customer_search_input = QLineEdit()
        self.customer_search_input.setPlaceholderText("Search phone or name...")
        self.new_customer_button = QPushButton("New Customer")
        self.customer_search_input.returnPressed.connect(self.search_customer)
        customer_search_layout = QHBoxLayout()
        customer_search_layout.addWidget(self.customer_search_input)
        customer_search_layout.addWidget(self.new_customer_button)
        customer_layout.addRow(customer_search_layout)

        self.customer_name_label = QLabel("Name: ")
        self.customer_phone_label = QLabel("Phone: ")
        customer_layout.addRow(self.customer_name_label)
        customer_layout.addRow(self.customer_phone_label)
        customer_group.setLayout(customer_layout)
        left_panel.addWidget(customer_group)
        self.new_customer_button.clicked.connect(self.create_new_customer)

        staff_group = QGroupBox("2. Staff")
        staff_layout = QFormLayout()
        self.staff_combo = QComboBox()
        staff_layout.addRow("Select Staff:", self.staff_combo)
        staff_group.setLayout(staff_layout)
        left_panel.addWidget(staff_group)

        services_group = QGroupBox("3. Services")
        services_layout = QVBoxLayout()
        self.services_table = QTableWidget()
        self.services_table.setColumnCount(5)
        self.services_table.setHorizontalHeaderLabels(["Service", "Qty", "Price", "Total", "ID"])
        self.services_table.setColumnHidden(4, True)
        self.services_table.setEditTriggers(QTableWidget.EditTrigger.AllEditTriggers)
        self.services_table.setSortingEnabled(True)
        self.services_table.horizontalHeader().setStretchLastSection(True)
        self.services_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.services_table.setAlternatingRowColors(True)
        self.services_table.verticalHeader().setVisible(False)
        services_layout.addWidget(self.services_table)

        service_controls_layout = QHBoxLayout()
        self.category_combo = QComboBox()
        self.category_combo.addItem("All Categories", None)
        self.category_combo.currentIndexChanged.connect(self.filter_services_by_category)

        self.service_search_input = QLineEdit()
        self.service_search_input.setPlaceholderText("Search services...")
        self.service_search_input.textChanged.connect(self.filter_services_by_search)

        self.service_combo = QComboBox()
        self.add_service_button = QPushButton("Add Service")
        self.remove_service_button = QPushButton("Remove Service")

        service_controls_layout.addWidget(QLabel("Category:"))
        service_controls_layout.addWidget(self.category_combo)
        service_controls_layout.addWidget(QLabel("Search:"))
        service_controls_layout.addWidget(self.service_search_input)
        service_controls_layout.addWidget(self.service_combo)
        service_controls_layout.addWidget(self.add_service_button)
        service_controls_layout.addWidget(self.remove_service_button)
        services_layout.addLayout(service_controls_layout)
        services_group.setLayout(services_layout)
        left_panel.addWidget(services_group)

        notes_group = QGroupBox("Customer Notes")
        notes_layout = QVBoxLayout()
        self.customer_notes_area = QTextEdit()
        notes_layout.addWidget(self.customer_notes_area)
        notes_group.setLayout(notes_layout)
        left_panel.addWidget(notes_group)

        totals_group = QGroupBox("4. Totals")
        totals_layout = QFormLayout()
        self.subtotal_label = QLabel(format_money(Decimal("0"), self._currency_symbol))
        self.discount_type_combo = QComboBox()
        self.discount_type_combo.addItems([f"Flat ({self._currency_symbol})", "Percent (%)"])
        self.discount_input = QLineEdit("0")
        self.discount_input.setValidator(QDoubleValidator(0.0, 9999999.99, 2, self))
        self.tax_input = QLineEdit("0")
        self.tax_input.setValidator(QDoubleValidator(0.0, 100.0, 2, self))
        self.total_label = QLabel(format_money(Decimal("0"), self._currency_symbol))
        totals_layout.addRow("Subtotal:", self.subtotal_label)

        discount_layout = QHBoxLayout()
        discount_layout.addWidget(self.discount_type_combo)
        discount_layout.addWidget(self.discount_input)
        totals_layout.addRow("Discount:", discount_layout)

        totals_layout.addRow("Tax (%):", self.tax_input)
        totals_layout.addRow("Total:", self.total_label)
        totals_group.setLayout(totals_layout)
        right_panel.addWidget(totals_group)

        payment_group = QGroupBox("5. Payment")
        payment_layout = QFormLayout()
        self.payment_method_combo = QComboBox()
        self.payment_method_combo.addItems(["Cash", "UPI", "Card", "Other"])
        payment_layout.addRow("Payment Method:", self.payment_method_combo)

        self.transaction_id_input = QLineEdit()
        self.transaction_id_input.setPlaceholderText("Transaction ID (UPI/Card)")
        payment_layout.addRow("Transaction ID:", self.transaction_id_input)

        self.payment_status_combo = QComboBox()
        self.payment_status_combo.addItems(["Paid", "Pending"])
        payment_layout.addRow("Payment Status:", self.payment_status_combo)

        payment_group.setLayout(payment_layout)
        right_panel.addWidget(payment_group)

        action_button_layout = QHBoxLayout()
        self.preview_button = QPushButton("Preview")
        self.preview_button.setObjectName("btn_secondary")
        self.save_bill_button = QPushButton("Save Bill")
        self.save_bill_button.setObjectName("btn_primary")
        self.save_and_send_button = QPushButton("Save, PDF & Send")
        self.save_and_send_button.setObjectName("btn_success")
        action_button_layout.addWidget(self.preview_button)
        action_button_layout.addWidget(self.save_bill_button)
        action_button_layout.addWidget(self.save_and_send_button)
        self._main_layout.addLayout(action_button_layout)

        self.load_staff()
        self.load_services()
        self._load_default_tax()
        self._update_transaction_visibility()
        self._update_progress_status()

        self.add_service_button.clicked.connect(self.add_service_to_bill)
        self.remove_service_button.clicked.connect(self.remove_service_from_bill)
        self.discount_input.textChanged.connect(self.update_totals)
        self.tax_input.textChanged.connect(self.update_totals)
        self.services_table.cellChanged.connect(self.update_totals_from_table)
        self.save_bill_button.clicked.connect(self.save_bill)
        self.save_and_send_button.clicked.connect(self.save_bill_and_send)
        self.preview_button.clicked.connect(self.preview_bill)
        self.payment_method_combo.currentTextChanged.connect(self._update_transaction_visibility)
        self.payment_method_combo.currentTextChanged.connect(self._update_progress_status)
        self.payment_status_combo.currentTextChanged.connect(self._update_progress_status)

        self._shortcuts = [
            QShortcut(QKeySequence("Ctrl+S"), self, self.save_bill),
            QShortcut(QKeySequence("Ctrl+P"), self, self.preview_bill),
        ]

    def refresh(self) -> None:
        self.load_staff()
        self.load_services()
        self._load_default_tax()
        self._update_progress_status()

    def load_staff(self) -> None:
        self.staff_combo.clear()
        staff_list = self._staff_service.list_active_staff()
        for staff in staff_list:
            self.staff_combo.addItem(staff.name, staff.id)

    def load_services(self) -> None:
        self.category_combo.blockSignals(True)
        self.service_combo.blockSignals(True)
        try:
            self.all_services = self._service_catalog.list_active()
            self._last_load_time = datetime.now()
            categories = sorted({s.category for s in self.all_services if s.category})
            self.category_combo.clear()
            self.category_combo.addItem("All Categories", None)
            for category in categories:
                self.category_combo.addItem(category, category)
            self.populate_service_combo(self.all_services)
        finally:
            self.category_combo.blockSignals(False)
            self.service_combo.blockSignals(False)

    def populate_service_combo(self, services: list[ServiceData]) -> None:
        self.service_combo.blockSignals(True)
        try:
            self.service_combo.clear()
            for service in services:
                display_text = service.display_name or service.name or ""
                price = service.price if service.price is not None else Decimal("0")
                self.service_combo.addItem(
                    f"{display_text} - {format_money(price, self._currency_symbol)}",
                    service.id,
                )
        finally:
            self.service_combo.blockSignals(False)

    def filter_services_by_category(self) -> None:
        selected_category = self.category_combo.currentData()
        search_text = (self.service_search_input.text() or "").lower()
        filtered = self.all_services

        if selected_category:
            filtered = [s for s in filtered if s.category == selected_category]
        if search_text:
            filtered = [
                s
                for s in filtered
                if (
                    search_text in (s.display_name or s.name or "").lower()
                    or search_text in (s.name or "").lower()
                    or (s.notes and search_text in s.notes.lower())
                )
            ]
        self.populate_service_combo(filtered)

    def filter_services_by_search(self) -> None:
        self.filter_services_by_category()

    def search_customer(self) -> None:
        search_term = self.customer_search_input.text().strip()
        if not search_term:
            return
        customers = self._customer_service.search_customers(search_term)
        if not customers:
            QMessageBox.information(self, "Customer Not Found", "No customer found with that name or phone number.")
            self.selected_customer = None
            return

        if len(customers) == 1:
            selected = customers[0]
        else:
            dialog = CustomerSelectionDialog(customers, self)
            if not dialog.exec() or not dialog.selected_customer:
                return
            selected = dialog.selected_customer

        self._apply_selected_customer(selected)

    def create_new_customer(self) -> None:
        dialog = CustomerDialog(self._customer_service, self)
        if dialog.exec():
            self.search_customer()

    def _apply_selected_customer(self, customer: CustomerData) -> None:
        self.selected_customer = customer
        self.customer_name_label.setText(f"Name: {customer.name}")
        self.customer_phone_label.setText(f"Phone: {customer.phone}")
        self.customer_notes_area.setPlainText(customer.notes or "")
        self._update_progress_status()

    def _ensure_fresh_services(self) -> None:
        if (datetime.now() - self._last_load_time).total_seconds() > 300:
            self.load_services()

    def add_service_to_bill(self) -> None:
        self._ensure_fresh_services()
        service_id = self.service_combo.currentData()
        service = next((s for s in self.all_services if s.id == service_id), None)
        if not service:
            QMessageBox.warning(self, "Error", "Service not found.")
            return

        was_sorting_enabled = self.services_table.isSortingEnabled()
        self.services_table.setSortingEnabled(False)
        self.services_table.blockSignals(True)
        try:
            row_position = self.services_table.rowCount()
            self.services_table.insertRow(row_position)
            service_item = QTableWidgetItem(service.name or "")
            service_item.setFlags(service_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.services_table.setItem(row_position, 0, service_item)

            qty_item = QTableWidgetItem("1")
            qty_item.setData(Qt.ItemDataRole.UserRole, QIntValidator(1, 999, self))
            self.services_table.setItem(row_position, 1, qty_item)

            price = service.price if service.price is not None else Decimal("0")
            price_item = QTableWidgetItem(str(price))
            total_item = QTableWidgetItem(str(price))
            id_item = QTableWidgetItem(str(service.id))
            price_item.setFlags(price_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            total_item.setFlags(total_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            id_item.setFlags(id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.services_table.setItem(row_position, 2, price_item)
            self.services_table.setItem(row_position, 3, total_item)
            self.services_table.setItem(row_position, 4, id_item)
        finally:
            self.services_table.blockSignals(False)
            self.services_table.setSortingEnabled(was_sorting_enabled)
        self.update_totals()
        self._update_progress_status()

    def remove_service_from_bill(self) -> None:
        selected_row = self.services_table.currentRow()
        if selected_row >= 0:
            self.services_table.removeRow(selected_row)
            self.update_totals()
            self._update_progress_status()

    def update_totals_from_table(self, row: int, column: int) -> None:
        if column in (1, 2):
            try:
                if column == 1:
                    validator = self.services_table.item(row, 1).data(Qt.ItemDataRole.UserRole)
                    if validator:
                        state, _, _ = validator.validate(self.services_table.item(row, 1).text(), 0)
                    else:
                        state = QValidator.State.Acceptable
                    if state != QValidator.State.Acceptable:
                        self.services_table.item(row, 1).setText("1")
                qty = int(self.services_table.item(row, 1).text())
                price = Decimal(self.services_table.item(row, 2).text())
                line_total = qty * price
                self.services_table.item(row, 3).setText(f"{line_total:.2f}")
            except (InvalidOperation, ValueError, TypeError):
                pass
            self.update_totals()
            self._update_progress_status()

    def update_totals(self) -> None:
        subtotal = Decimal("0")
        for row in range(self.services_table.rowCount()):
            try:
                subtotal += Decimal(self.services_table.item(row, 3).text())
            except (InvalidOperation, ValueError, TypeError):
                pass

        self.subtotal_label.setText(format_money(subtotal, self._currency_symbol))

        try:
            discount_value = Decimal(self.discount_input.text())
        except Exception:
            discount_value = Decimal("0")

        discount_amount = Decimal("0")
        if self.discount_type_combo.currentIndex() == 0:
            discount_amount = min(discount_value, subtotal)
            self.discount_input.setStyleSheet("" if discount_value <= subtotal else "background-color: #ffcccc;")
        else:
            capped_percent = min(discount_value, Decimal("100"))
            discount_amount = subtotal * (capped_percent / Decimal("100"))
            self.discount_input.setStyleSheet("" if discount_value <= Decimal("100") else "background-color: #ffcccc;")

        try:
            tax_percent = Decimal(self.tax_input.text())
        except Exception:
            tax_percent = Decimal("0")

        total = subtotal - discount_amount
        tax_amount = total * (tax_percent / Decimal("100"))
        total += tax_amount

        self.total_label.setText(format_money(total, self._currency_symbol))
        self._update_progress_status()

    def _collect_items_from_table(self) -> list[BillItemInput]:
        items = []
        for row in range(self.services_table.rowCount()):
            items.append(
                BillItemInput(
                    service_id=int(self.services_table.item(row, 4).text()),
                    quantity=int(self.services_table.item(row, 1).text()),
                    unit_price=Decimal(self.services_table.item(row, 2).text()),
                )
            )
        return items

    def save_bill(self, and_send: bool = False) -> None:
        if not self.selected_customer:
            QMessageBox.warning(self, "No Customer", "Please select a customer.")
            return
        if self.staff_combo.currentData() is None:
            QMessageBox.warning(self, "No Staff", "Please select a staff member.")
            return
        if self.services_table.rowCount() == 0:
            QMessageBox.warning(self, "No Services", "Please add at least one service.")
            return

        if not confirm_action(
            self,
            "Save Bill",
            f"Create bill for {self.total_label.text()}?",
        ):
            return

        try:
            self._sync_customer_notes()
            items = self._collect_items_from_table()
            options = BillOptions(
                discount_type="flat" if self.discount_type_combo.currentIndex() == 0 else "percent",
                discount_value=Decimal(self.discount_input.text() or "0"),
                tax_percent=Decimal(self.tax_input.text() or "0"),
                payment_method=self.payment_method_combo.currentText(),
                transaction_id=self.transaction_id_input.text().strip() or None,
                payment_status=self.payment_status_combo.currentText(),
            )
            bill = self._billing_service.create_bill(
                customer_id=self.selected_customer.id,
                staff_id=self.staff_combo.currentData(),
                items=items,
                options=options,
            )
        except ValidationError as exc:
            QMessageBox.warning(self, "Validation Error", str(exc))
            return

        QMessageBox.information(self, "Bill Saved", f"Bill #{bill.bill_number} has been saved.")

        if and_send:
            self.generate_and_send(bill)

        self._clear_form()

    def _clear_form(self) -> None:
        self.selected_customer = None
        self.customer_search_input.clear()
        self.customer_name_label.setText("Name: ")
        self.customer_phone_label.setText("Phone: ")
        self.customer_notes_area.clear()
        self.services_table.setRowCount(0)
        self.discount_input.setText("0")
        self.transaction_id_input.clear()
        self.payment_method_combo.setCurrentText("Cash")
        self.payment_status_combo.setCurrentText("Paid")
        self.update_totals()
        self._update_progress_status()

    def _sync_customer_notes(self) -> None:
        if not self.selected_customer:
            return

        updated_notes = self.customer_notes_area.toPlainText().strip() or None
        if updated_notes == self.selected_customer.notes:
            return

        updated_customer = CustomerData(
            id=self.selected_customer.id,
            name=self.selected_customer.name,
            phone=self.selected_customer.phone,
            notes=updated_notes,
            last_visit_at=self.selected_customer.last_visit_at,
        )
        self.selected_customer = self._customer_service.update_customer(
            self.selected_customer.id,
            updated_customer,
        )

    def save_bill_and_send(self) -> None:
        self.save_bill(and_send=True)

    def generate_and_send(self, bill) -> None:
        try:
            pdf_path = self._billing_service.generate_receipt(bill.id)
            QMessageBox.information(self, "PDF Generated", f"Receipt saved to {pdf_path}")
            send_whatsapp_receipt(
                bill=bill,
                billing_service=self._billing_service,
                notification_service=self._notification_service,
                parent=self,
                customer_phone=self.selected_customer.phone if self.selected_customer else None,
                customer_name=self.selected_customer.name if self.selected_customer else None,
            )
        except Exception as exc:
            self._billing_service.update_whatsapp_status(bill.id, "Error", str(exc))
            QMessageBox.critical(self, "Error", f"An error occurred: {exc}")

    def _load_default_tax(self) -> None:
        default_tax = self._settings_service.get_setting("default_tax_percent", "0")
        self.tax_input.setText(default_tax or "0")

    def _update_transaction_visibility(self) -> None:
        method = self.payment_method_combo.currentText()
        self.transaction_id_input.setVisible(method not in {"Cash"})

    def preview_bill(self) -> None:
        if not self.selected_customer:
            QMessageBox.warning(self, "No Customer", "Please select a customer.")
            return
        if self.services_table.rowCount() == 0:
            QMessageBox.warning(self, "No Services", "Please add at least one service.")
            return
        pdf_path = self._generate_preview_pdf()
        if not pdf_path:
            return
        open_pdf(pdf_path, self, title="Preview Generated")

    def _generate_preview_pdf(self) -> str | None:
        try:
            receipt_items: list[ReceiptItemData] = []
            subtotal = Decimal("0")

            for row in range(self.services_table.rowCount()):
                service_name_item = self.services_table.item(row, 0)
                qty_item = self.services_table.item(row, 1)
                unit_price_item = self.services_table.item(row, 2)

                if not service_name_item or not qty_item or not unit_price_item:
                    continue

                quantity = int(qty_item.text())
                unit_price = Decimal(unit_price_item.text())
                line_total = unit_price * Decimal(quantity)
                subtotal += line_total

                receipt_items.append(
                    ReceiptItemData(
                        service_name=service_name_item.text(),
                        display_name=service_name_item.text(),
                        variant=None,
                        quantity=quantity,
                        unit_price=unit_price,
                        line_total=line_total,
                    )
                )

            discount_value = Decimal(self.discount_input.text() or "0")
            if self.discount_type_combo.currentIndex() == 0:
                discount_amount = min(discount_value, subtotal)
            else:
                capped_percent = min(discount_value, Decimal("100"))
                discount_amount = subtotal * (capped_percent / Decimal("100"))

            taxable_total = subtotal - discount_amount
            tax_percent = Decimal(self.tax_input.text() or "0")
            tax_amount = taxable_total * (tax_percent / Decimal("100"))
            total = taxable_total + tax_amount

            receipt = ReceiptData(
                bill_id=0,
                bill_number="PREVIEW",
                bill_datetime=datetime.now(),
                subtotal=subtotal,
                discount_amount=discount_amount,
                tax_percent=tax_percent,
                tax_amount=tax_amount,
                total=total,
                payment_method=self.payment_method_combo.currentText(),
                payment_status=self.payment_status_combo.currentText(),
                transaction_id=self.transaction_id_input.text().strip() or None,
                customer_name=self.selected_customer.name,
                customer_phone=self.selected_customer.phone,
                staff_name=self.staff_combo.currentText() or "",
                items=receipt_items,
            )

            return generate_receipt_pdf(
                receipt=receipt,
                settings_service=self._settings_service,
                is_preview=True,
            )
        except Exception as exc:
            QMessageBox.warning(self, "Preview Failed", f"Failed to generate preview: {exc}")
            return None

    def _update_progress_status(self) -> None:
        customer_done = self.selected_customer is not None
        services_done = self.services_table.rowCount() > 0
        payment_done = bool(self.payment_method_combo.currentText())

        self._customer_status_label.setText(
            f"Customer: {'Done' if customer_done else 'Pending'}"
        )
        self._services_status_label.setText(
            f"Services: {'Done' if services_done else 'Pending'}"
        )
        self._payment_status_label.setText(
            f"Payment: {'Done' if payment_done else 'Pending'}"
        )

        if customer_done and services_done and payment_done:
            self._ready_status_label.setText("Ready to Save")
        else:
            self._ready_status_label.setText("")
