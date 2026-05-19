"""Main application window."""

from __future__ import annotations

from decimal import Decimal

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QGraphicsDropShadowEffect,
    QGridLayout,
    QGroupBox,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QPushButton,
    QScrollArea,
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
from .helpers import format_money


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
        self._currency_symbol = self._settings_service.get_setting(
            "currency_symbol",
            "\u20B9",
        ) or "\u20B9"

        business_name = self._settings_service.get_setting("business_name", "Billing System")
        self.setWindowTitle(f"{business_name} - Billing")
        self.setMinimumSize(800, 600)
        self.resize(1024, 768)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self._main_layout = QHBoxLayout(self.central_widget)

        self._nav_list = QListWidget()
        self._nav_list.setObjectName("nav_sidebar")
        self._nav_list.setMinimumWidth(120)
        self._nav_list.setMaximumWidth(180)
        self._nav_list.addItems(
            ["Dashboard", "New Bill", "Customers", "Bill History", "Export", "Settings"]
        )
        self._nav_list.currentRowChanged.connect(self._on_nav_changed)
        self._main_layout.addWidget(self._nav_list, 1)

        self._stack = QStackedWidget()
        self._stack.setObjectName("content_stack")
        self._main_layout.addWidget(self._stack, 4)

        self._dashboard_page = QWidget()
        self._dashboard_page.setObjectName("dashboard_page")
        dashboard_page_layout = QVBoxLayout(self._dashboard_page)
        dashboard_scroll = QScrollArea()
        dashboard_scroll.setWidgetResizable(True)
        dashboard_content = QWidget()
        dashboard_layout = QVBoxLayout(dashboard_content)
        dashboard_scroll.setWidget(dashboard_content)
        dashboard_page_layout.addWidget(dashboard_scroll)

        dashboard_title = QLabel("Dashboard")
        dashboard_title.setObjectName("page_title")
        dashboard_layout.addWidget(dashboard_title)

        self._dashboard_group = QGroupBox("Dashboard")
        dashboard_group_layout = QVBoxLayout()

        stats_layout = QGridLayout()
        sales_card, self._today_sales_value = self._create_stat_card(
            "Today's Sales",
            format_money(Decimal("0"), self._currency_symbol),
            "#4CAF50",
            "sales_card",
        )
        bills_card, self._today_bills_value = self._create_stat_card(
            "Bills Today",
            "0",
            "#2196F3",
            "bills_card",
        )
        pending_card, self._pending_amount_value = self._create_stat_card(
            "Pending Amount",
            format_money(Decimal("0"), self._currency_symbol),
            "#FF9800",
            "pending_card",
        )
        pending_count_card, self._pending_count_value = self._create_stat_card(
            "Pending Bills",
            "0",
            "#E94560",
            "pending_count_card",
        )
        customers_card, self._today_customers_value = self._create_stat_card(
            "Customers Today",
            "0",
            "#9C27B0",
            "customers_card",
        )

        stats_layout.addWidget(sales_card, 0, 0)
        stats_layout.addWidget(bills_card, 0, 1)
        stats_layout.addWidget(pending_card, 0, 2)
        stats_layout.addWidget(pending_count_card, 1, 0)
        stats_layout.addWidget(customers_card, 1, 1)
        dashboard_group_layout.addLayout(stats_layout)

        recent_group = QGroupBox("Recent Bills")
        recent_layout = QVBoxLayout()
        self._recent_table = QTableWidget()
        self._recent_table.setColumnCount(5)
        self._recent_table.setHorizontalHeaderLabels(["Bill #", "Customer", "Date", "Total", "Status"])
        self._recent_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._recent_table.setSortingEnabled(True)
        self._recent_table.horizontalHeader().setStretchLastSection(True)
        self._recent_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._recent_table.setAlternatingRowColors(True)
        self._recent_table.verticalHeader().setVisible(False)
        recent_layout.addWidget(self._recent_table)
        recent_group.setLayout(recent_layout)
        dashboard_group_layout.addWidget(recent_group)

        quick_actions = QGroupBox("Quick Actions")
        quick_layout = QHBoxLayout()
        new_bill_button = QPushButton("New Bill", clicked=lambda: self._nav_list.setCurrentRow(1))
        new_bill_button.setObjectName("quick_new_bill")
        customers_button = QPushButton("Customers", clicked=lambda: self._nav_list.setCurrentRow(2))
        customers_button.setObjectName("quick_customers")
        export_button = QPushButton("Export", clicked=lambda: self._nav_list.setCurrentRow(4))
        export_button.setObjectName("quick_export")
        quick_layout.addWidget(new_bill_button)
        quick_layout.addWidget(customers_button)
        quick_layout.addWidget(export_button)
        quick_actions.setLayout(quick_layout)
        dashboard_group_layout.addWidget(quick_actions)

        self._dashboard_group.setLayout(dashboard_group_layout)
        dashboard_layout.addWidget(self._dashboard_group)
        dashboard_layout.addStretch(1)

        self._billing_view = BillingView(
            billing_service=self._billing_service,
            customer_service=self._customer_service,
            staff_service=self._staff_service,
            service_catalog=self._service_catalog,
            notification_service=self._notification_service,
            settings_service=self._settings_service,
            parent=self,
        )
        self._customer_view = CustomerView(
            customer_service=self._customer_service,
            billing_service=self._billing_service,
            notification_service=self._notification_service,
            settings_service=self._settings_service,
            parent=self,
        )
        self._bill_history_view = BillHistoryView(
            billing_service=self._billing_service,
            notification_service=self._notification_service,
            settings_service=self._settings_service,
            parent=self,
        )
        self._export_view = ExportView(
            report_service=self._report_service,
            customer_service=self._customer_service,
            parent=self,
        )
        self._settings_view = SettingsView(
            settings_service=self._settings_service,
            staff_service=self._staff_service,
            service_catalog=self._service_catalog,
            backup_service=self._backup_service,
            restore_service=self._restore_service,
            parent=self,
        )

        self._stack.addWidget(self._dashboard_page)
        self._stack.addWidget(self._billing_view)
        self._stack.addWidget(self._customer_view)
        self._stack.addWidget(self._bill_history_view)
        self._stack.addWidget(self._export_view)
        self._stack.addWidget(self._settings_view)

        self._setup_shortcuts()
        self._nav_list.setCurrentRow(0)

    def _on_nav_changed(self, index: int) -> None:
        if index >= 0:
            self._stack.setCurrentIndex(index)
            self._refresh_current_view(index)

    def _refresh_current_view(self, index: int) -> None:
        if index == 0:
            self._refresh_dashboard()
            return

        current = self._stack.currentWidget()
        if hasattr(current, "refresh"):
            current.refresh()

    def _setup_shortcuts(self) -> None:
        self._shortcuts = [
            QShortcut(QKeySequence("Ctrl+N"), self, lambda: self._nav_list.setCurrentRow(1)),
            QShortcut(QKeySequence("Ctrl+F"), self, self._focus_search),
            QShortcut(QKeySequence("F5"), self, self._refresh_active_view),
            QShortcut(QKeySequence("Ctrl+1"), self, lambda: self._nav_list.setCurrentRow(0)),
            QShortcut(QKeySequence("Ctrl+2"), self, lambda: self._nav_list.setCurrentRow(1)),
            QShortcut(QKeySequence("Ctrl+3"), self, lambda: self._nav_list.setCurrentRow(2)),
        ]

    def _focus_search(self) -> None:
        current = self._stack.currentWidget()
        for attr in ("customer_search_input", "search_input", "_customer_input", "_bill_number_input"):
            widget = getattr(current, attr, None)
            if widget is not None:
                widget.setFocus()
                return

    def _refresh_active_view(self) -> None:
        self._refresh_current_view(self._nav_list.currentRow())

    def _create_stat_card(
        self,
        title: str,
        initial_value: str,
        color: str,
        object_name: str,
    ) -> tuple[QGroupBox, QLabel]:
        card = QGroupBox(title)
        card.setObjectName(object_name)
        card.setStyleSheet(
            f"QGroupBox#{object_name} {{ background-color: {color}; color: white; }}"
        )
        layout = QVBoxLayout(card)
        value_label = QLabel(initial_value)
        value_label.setObjectName(f"{object_name}_value")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(value_label)

        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(18)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 110))
        card.setGraphicsEffect(shadow)
        return card, value_label

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._refresh_dashboard()

    def _refresh_dashboard(self) -> None:
        try:
            stats = self._billing_service.get_dashboard_stats()
        except Exception:
            return

        sort_section = self._recent_table.horizontalHeader().sortIndicatorSection()
        sort_order = self._recent_table.horizontalHeader().sortIndicatorOrder()

        self._today_sales_value.setText(format_money(Decimal(stats.today_sales), self._currency_symbol))
        self._today_bills_value.setText(str(stats.today_bills_count))
        self._pending_amount_value.setText(
            format_money(Decimal(stats.pending_amount), self._currency_symbol)
        )
        self._pending_count_value.setText(str(stats.pending_count))
        self._today_customers_value.setText(str(stats.today_customers))

        self._recent_table.setRowCount(len(stats.recent_bills))
        for row, bill in enumerate(stats.recent_bills):
            bill_number = bill.bill_number or str(bill.id)
            customer_name = bill.customer_name or ""
            bill_date = bill.bill_datetime.strftime("%Y-%m-%d") if bill.bill_datetime else ""
            total = format_money(Decimal(bill.total or 0), self._currency_symbol)
            status = bill.payment_status or ""
            self._recent_table.setItem(row, 0, QTableWidgetItem(bill_number))
            self._recent_table.setItem(row, 1, QTableWidgetItem(customer_name))
            self._recent_table.setItem(row, 2, QTableWidgetItem(bill_date))
            self._recent_table.setItem(row, 3, QTableWidgetItem(total))
            self._recent_table.setItem(row, 4, QTableWidgetItem(status))

        self._recent_table.sortItems(sort_section, sort_order)

    def open_settings_window(self) -> None:
        self._nav_list.setCurrentRow(5)

    def open_customers_window(self) -> None:
        self._nav_list.setCurrentRow(2)

    def open_billing_window(self) -> None:
        self._nav_list.setCurrentRow(1)

    def open_export_dialog(self) -> None:
        self._nav_list.setCurrentRow(4)

    def open_bill_history_window(self) -> None:
        self._nav_list.setCurrentRow(3)
