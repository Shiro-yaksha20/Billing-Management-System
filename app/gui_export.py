from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QDateEdit, QPushButton, QFileDialog, QMessageBox,
    QGroupBox, QComboBox
)
from PyQt6.QtCore import QDate
from datetime import datetime
from .export_service import export_bills_to_excel
from .models import Customer
from .database import db_session

class ExportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
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
        self.load_customers()
        filter_layout.addRow("Customer:", self.customer_combo)
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)

        buttons = QHBoxLayout()
        export_btn = QPushButton("Export to Excel")
        export_btn.clicked.connect(self.do_export)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(export_btn)
        buttons.addWidget(cancel_btn)
        layout.addLayout(buttons)

    def load_customers(self):
        with db_session() as db:
            customers = db.query(Customer).order_by(Customer.name).all()
            for c in customers:
                self.customer_combo.addItem(f"{c.name} ({c.phone})", c.id)

    def do_export(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Excel File",
            f"bills_export_{datetime.now().strftime('%Y%m%d')}.xlsx",
            "Excel Files (*.xlsx)"
        )
        if not file_path:
            return
        start = datetime.combine(self.start_date.date().toPyDate(), datetime.min.time())
        end = datetime.combine(self.end_date.date().toPyDate(), datetime.max.time())
        customer_id = self.customer_combo.currentData()
        success = export_bills_to_excel(file_path, start_date=start, end_date=end, customer_id=customer_id)
        if success:
            QMessageBox.information(self, "Export Complete", f"Data exported successfully to:\n{file_path}")
            self.accept()
        else:
            QMessageBox.critical(self, "Export Failed", "Failed to export data. Check logs for details.")
