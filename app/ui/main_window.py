"""Main application window."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .bill_history_view import BillHistoryView
from .billing_view import BillingView
from .customer_view import CustomerView
from .export_view import ExportView
from .settings_view import SettingsView
from ..services.backup_service import BackupService
from ..services.billing_service import BillingService
from ..services.customer_service import CustomerService
from ..services.notification_service import NotificationService
from ..services.report_service import ReportService
from ..services.restore_service import RestoreService
from ..services.service_catalog import ServiceCatalog
from ..services.settings_service import SettingsService
from ..services.staff_service import StaffService


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(
        self,
        billing_service: BillingService,
        customer_service: CustomerService,
        staff_service: StaffService,
        service_catalog: ServiceCatalog,
        report_service: ReportService,
        settings_service: SettingsService,
        notification_service: NotificationService,
        backup_service: BackupService,
        restore_service: RestoreService,
    ) -> None:
        super().__init__()
        self._billing_service = billing_service
        self._customer_service = customer_service
        self._staff_service = staff_service
        self._service_catalog = service_catalog
        self._report_service = report_service
        self._settings_service = settings_service
        self._notification_service = notification_service
        self._backup_service = backup_service
        self._restore_service = restore_service

        self.setWindowTitle("Salon Billing System")
        self.setGeometry(100, 100, 900, 650)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QHBoxLayout(self.central_widget)

        self._nav_list = QListWidget()
        self._nav_list.addItems(
            ["Dashboard", "New Bill", "Customers", "Export", "Settings", "Bill History"]
        )
        self._nav_list.currentRowChanged.connect(self._on_nav_changed)
        self.layout.addWidget(self._nav_list, 1)

        self._stack = QStackedWidget()
        self.layout.addWidget(self._stack, 4)

        dashboard_page = QWidget()
        dashboard_layout = QVBoxLayout(dashboard_page)

        self._dashboard_group = QGroupBox("Dashboard")
        dashboard_group_layout = QVBoxLayout()

        stats_layout = QHBoxLayout()
        sales_card, self._today_sales_value = self._create_stat_card("Today's Sales")
        bills_card, self._today_bills_value = self._create_stat_card("Bills Today")
        pending_card, self._pending_amount_value = self._create_stat_card("Pending Amount")
        pending_count_card, self._pending_count_value = self._create_stat_card("Pending Bills")
        customers_card, self._today_customers_value = self._create_stat_card("Customers Today")

        stats_layout.addWidget(sales_card)
        stats_layout.addWidget(bills_card)
        stats_layout.addWidget(pending_card)
        stats_layout.addWidget(pending_count_card)
        stats_layout.addWidget(customers_card)
        dashboard_group_layout.addLayout(stats_layout)

        recent_group = QGroupBox("Recent Bills")
        recent_layout = QVBoxLayout()
        self._recent_table = QTableWidget()
        self._recent_table.setColumnCount(3)
        self._recent_table.setHorizontalHeaderLabels(["Bill #", "Customer", "Total"])
        self._recent_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._recent_table.setSortingEnabled(True)
        recent_layout.addWidget(self._recent_table)
        recent_group.setLayout(recent_layout)
        dashboard_group_layout.addWidget(recent_group)

        quick_actions = QGroupBox("Quick Actions")
        quick_layout = QHBoxLayout()
        quick_layout.addWidget(QPushButton("New Bill", clicked=self.open_billing_window))
        quick_layout.addWidget(QPushButton("Customers", clicked=self.open_customers_window))
        quick_layout.addWidget(QPushButton("Export", clicked=self.open_export_dialog))
        quick_actions.setLayout(quick_layout)
        dashboard_group_layout.addWidget(quick_actions)

        self._dashboard_group.setLayout(dashboard_group_layout)
        dashboard_layout.addWidget(self._dashboard_group)
        dashboard_layout.addStretch(1)

        self._stack.addWidget(dashboard_page)
        self._stack.addWidget(self._build_action_page("Create a new bill", "Open Billing", self.open_billing_window))
        self._stack.addWidget(
            self._build_action_page("Manage customers", "Open Customers", self.open_customers_window)
        )
        self._stack.addWidget(
            self._build_action_page("Export billing data", "Open Export", self.open_export_dialog)
        )
        self._stack.addWidget(
            self._build_action_page("Configure settings", "Open Settings", self.open_settings_window)
        )
        self._stack.addWidget(
            self._build_action_page("View bill history", "Open History", self.open_bill_history_window)
        )

        self._nav_list.setCurrentRow(0)

    def _build_action_page(self, title: str, button_text: str, action) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        label = QLabel(title)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        button = QPushButton(button_text)
        button.clicked.connect(action)
        layout.addStretch(1)
        layout.addWidget(label)
        layout.addWidget(button, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch(1)
        return page

    def _on_nav_changed(self, index: int) -> None:
        if index >= 0:
            self._stack.setCurrentIndex(index)

    def _create_stat_card(self, title: str) -> tuple[QGroupBox, QLabel]:
        card = QGroupBox(title)
        layout = QVBoxLayout(card)
        value_label = QLabel("0")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(value_label)
        return card, value_label

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._refresh_dashboard()

    def _refresh_dashboard(self) -> None:
        try:
            stats = self._billing_service.get_dashboard_stats()
        except Exception:
            return

        self._today_sales_value.setText(f"?{float(stats.today_sales):.2f}")
        self._today_bills_value.setText(str(stats.today_bills_count))
        self._pending_amount_value.setText(f"?{float(stats.pending_amount):.2f}")
        self._pending_count_value.setText(str(stats.pending_count))
        self._today_customers_value.setText(str(stats.today_customers))

        self._recent_table.setRowCount(len(stats.recent_bills))
        for row, bill in enumerate(stats.recent_bills):
            bill_number = bill.bill_number or str(bill.id)
            customer_name = bill.customer_name or ""
            total = f"?{float(bill.total or 0):.2f}"
            self._recent_table.setItem(row, 0, QTableWidgetItem(bill_number))
            self._recent_table.setItem(row, 1, QTableWidgetItem(customer_name))
            self._recent_table.setItem(row, 2, QTableWidgetItem(total))

    def open_settings_window(self) -> None:
        dialog = SettingsView(
            settings_service=self._settings_service,
            staff_service=self._staff_service,
            service_catalog=self._service_catalog,
            backup_service=self._backup_service,
            restore_service=self._restore_service,
            parent=self,
        )
        dialog.exec()

    def open_customers_window(self) -> None:
        dialog = CustomerView(
            customer_service=self._customer_service,
            billing_service=self._billing_service,
            notification_service=self._notification_service,
            parent=self,
        )
        dialog.exec()

    def open_billing_window(self) -> None:
        dialog = BillingView(
            billing_service=self._billing_service,
            customer_service=self._customer_service,
            staff_service=self._staff_service,
            service_catalog=self._service_catalog,
            notification_service=self._notification_service,
            settings_service=self._settings_service,
            parent=self,
        )
        dialog.exec()
        self._refresh_dashboard()

    def open_export_dialog(self) -> None:
        dialog = ExportView(
            report_service=self._report_service,
            customer_service=self._customer_service,
            parent=self,
        )
        dialog.exec()

    def open_bill_history_window(self) -> None:
        dialog = BillHistoryView(
            billing_service=self._billing_service,
            notification_service=self._notification_service,
            parent=self,
        )
        dialog.exec()
