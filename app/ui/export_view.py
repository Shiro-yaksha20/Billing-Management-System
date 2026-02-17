"""Export dialog UI."""

from __future__ import annotations

from datetime import datetime

from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from ..services.customer_service import CustomerService
from ..services.report_service import ReportService


class ExportView(QDialog):
    """Dialog for exporting data."""

    def __init__(
        self,
        report_service: ReportService,
        customer_service: CustomerService,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._report_service = report_service
        self._customer_service = customer_service
        self.setWindowTitle("Export Data")
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)

        date_group = QGroupBox("Date Range")
        date_layout = QFormLayout()
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate().addMonths(-1))
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        date_layout.addRow("From:", self.start_date)
        date_layout.addRow("To:", self.end_date)
        date_group.setLayout(date_layout)
        layout.addWidget(date_group)

        filter_group = QGroupBox("Filters (Optional)")
        filter_layout = QFormLayout()
        self.customer_combo = QComboBox()
        self.customer_combo.addItem("All Customers", None)
        self._load_customers()
        filter_layout.addRow("Customer:", self.customer_combo)
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)

        format_group = QGroupBox("Export Format")
        format_layout = QFormLayout()
        self._format_combo = QComboBox()
        self._format_combo.addItem("Excel (.xlsx)", "xlsx")
        self._format_combo.addItem("CSV (.csv)", "csv")
        self._format_combo.addItem("PDF Summary (.pdf)", "pdf")
        format_layout.addRow("Format:", self._format_combo)
        format_group.setLayout(format_layout)
        layout.addWidget(format_group)

        buttons = QHBoxLayout()
        export_btn = QPushButton("Export")
        export_btn.clicked.connect(self.do_export)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(export_btn)
        buttons.addWidget(cancel_btn)
        layout.addLayout(buttons)

    def _load_customers(self) -> None:
        customers = self._customer_service.search_customers("")
        for customer in customers:
            self.customer_combo.addItem(f"{customer.name} ({customer.phone})", customer.id)

    def do_export(self) -> None:
        export_format = self._format_combo.currentData()
        extension_map = {"xlsx": "Excel Files (*.xlsx)", "csv": "CSV Files (*.csv)", "pdf": "PDF Files (*.pdf)"}
        default_name = f"bills_export_{datetime.now().strftime('%Y%m%d')}.{export_format}"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Export File",
            default_name,
            extension_map.get(export_format, "All Files (*)"),
        )
        if not file_path:
            return
        start = datetime.combine(self.start_date.date().toPyDate(), datetime.min.time())
        end = datetime.combine(self.end_date.date().toPyDate(), datetime.max.time())
        customer_id = self.customer_combo.currentData()

        if export_format == "csv":
            success = self._report_service.export_bills_csv(
                file_path,
                start_date=start,
                end_date=end,
                customer_id=customer_id,
            )
        elif export_format == "pdf":
            success = self._report_service.export_bills_pdf_summary(
                file_path,
                start_date=start,
                end_date=end,
                customer_id=customer_id,
            )
        else:
            success = self._report_service.export_bills(
                file_path,
                start_date=start,
                end_date=end,
                customer_id=customer_id,
            )

        if success:
            QMessageBox.information(self, "Export Complete", f"Data exported successfully to:\n{file_path}")
            self.accept()
        else:
            QMessageBox.critical(self, "Export Failed", "Failed to export data. Check logs for details.")
