# Application Improvements Plan
**Date**: 2025-12-07  
**Status**: PLANNING PHASE - No Implementation Yet

---

## Issues Identified

### Issue 1: Receipt PDF Formatting for Print
**Problem**: Current receipt has formatting issues visible in screenshot:
- Currency symbol showing as black squares (?250 instead of ?250)
- Layout not optimized for thermal/standard printer paper
- No proper margins or page sizing for print

### Issue 2: New Customer Section - No Scroll
**Problem**: Cannot scroll in New Customer dialog when content overflows.

### Issue 3: Last Visit Date Not Being Saved
**Problem**: Customer's `last_visit_at` field not updating when bill is created.

### Issue 4: Receipt History Linked to Customer
**Problem**: Want to see all receipts/bills associated with a customer in their data view.

### Issue 5: Data Export for Tax/Audit
**Problem**: Need ability to export all transaction data to Excel for:
- Tax reporting
- Audit purposes
- Business analysis
- What customer did what on what date (full receipt data)

---

## Proposed Solutions

### Solution 1: Fix Receipt PDF for Printing

#### File: `app/pdf_generator.py`

**Changes Required:**

1. **Fix Currency Symbol Encoding**
```python
# Current issue: ? symbol not rendering
# Solution: Use proper Unicode or substitute with "Rs." for compatibility

# Option A: Register Unicode font
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
pdfmetrics.registerFont(TTFont('DejaVu', 'DejaVuSans.ttf'))

# Option B: Use "Rs." as fallback
currency = "Rs."  # or "INR "
```

2. **Optimize for Print**
```python
# Use smaller page size for thermal printers (80mm width)
from reportlab.lib.pagesizes import A4
# Or custom size: (80*mm, 297*mm) for thermal

# Add proper margins
doc = SimpleDocTemplate(
    temp_path, 
    pagesize=letter,
    leftMargin=0.5*inch,
    rightMargin=0.5*inch,
    topMargin=0.5*inch,
    bottomMargin=0.5*inch
)
```

3. **Table Alignment Fix**
```python
# Ensure currency aligns properly in table
# Right-align price columns
```

---

### Solution 2: Add Scroll to New Customer Dialog

#### File: `app/gui_customers.py`

**Changes Required:**

1. **Wrap CustomerDialog Content in ScrollArea**
```python
from PyQt6.QtWidgets import QScrollArea

class CustomerDialog(QDialog):
    def __init__(self, parent=None, customer_id=None):
        super().__init__(parent)
        
        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        # Create content widget
        content = QWidget()
        form_layout = QFormLayout(content)
        
        # Add all form fields to form_layout
        # ...
        
        scroll.setWidget(content)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll)
        
        # Buttons outside scroll
        button_layout = QHBoxLayout()
        # ...
        main_layout.addLayout(button_layout)
```

2. **Set Minimum/Maximum Dialog Size**
```python
self.setMinimumSize(400, 300)
self.setMaximumSize(600, 800)
```

---

### Solution 3: Fix Last Visit Date Saving

#### File: `app/gui_billing.py`

**Current Code (in save_bill):**
```python
customer = db.query(Customer).filter(Customer.id == self.selected_customer['id']).first()
customer.last_visit_at = new_bill.bill_datetime
```

**Problem**: May not be committing or `bill_datetime` might be None at that point.

**Changes Required:**

1. **Ensure datetime is set before assignment**
```python
from datetime import datetime

# In save_bill(), before db.flush():
if not new_bill.bill_datetime:
    new_bill.bill_datetime = datetime.utcnow()

customer = db.query(Customer).filter(Customer.id == self.selected_customer['id']).first()
if customer:
    customer.last_visit_at = new_bill.bill_datetime
```

2. **Verify in Customer Model**
```python
# Ensure last_visit_at column exists and is DateTime type
last_visit_at = Column(DateTime)  # Already exists, verify it works
```

---

### Solution 4: Link Receipts to Customer View

#### File: `app/gui_customers.py`

**Changes Required:**

1. **Add Bills History Section to CustomerWindow**
```python
# In CustomerWindow, add a table showing customer's bills

# After customer_table and notes_area:
bills_group = QGroupBox("Bill History")
bills_layout = QVBoxLayout()

self.bills_table = QTableWidget()
self.bills_table.setColumnCount(5)
self.bills_table.setHorizontalHeaderLabels([
    "Bill #", "Date", "Total", "Payment", "Status"
])
bills_layout.addWidget(self.bills_table)

# Add view receipt button
view_receipt_btn = QPushButton("View Receipt PDF")
view_receipt_btn.clicked.connect(self.view_selected_receipt)
bills_layout.addWidget(view_receipt_btn)

bills_group.setLayout(bills_layout)
self.layout.addWidget(bills_group)
```

2. **Load Bills When Customer Selected**
```python
def display_customer_notes(self):
    # ... existing code to show notes ...
    
    # Also load customer bills
    self.load_customer_bills(customer_id)

def load_customer_bills(self, customer_id):
    with db_session() as db:
        bills = db.query(Bill).filter(
            Bill.customer_id == customer_id
        ).order_by(Bill.bill_datetime.desc()).all()
        
        self.bills_table.setRowCount(len(bills))
        for i, bill in enumerate(bills):
            self.bills_table.setItem(i, 0, QTableWidgetItem(str(bill.bill_number or bill.id)))
            self.bills_table.setItem(i, 1, QTableWidgetItem(
                bill.bill_datetime.strftime('%Y-%m-%d') if bill.bill_datetime else ''
            ))
            self.bills_table.setItem(i, 2, QTableWidgetItem(f"?{float(bill.total):.0f}"))
            self.bills_table.setItem(i, 3, QTableWidgetItem(bill.payment_method or ''))
            self.bills_table.setItem(i, 4, QTableWidgetItem(bill.payment_status or 'Paid'))
            # Store bill ID and pdf_path for viewing
            self.bills_table.item(i, 0).setData(Qt.ItemDataRole.UserRole, {
                'id': bill.id,
                'pdf_path': bill.pdf_path
            })
```

3. **View Receipt Handler**
```python
def view_selected_receipt(self):
    row = self.bills_table.currentRow()
    if row < 0:
        QMessageBox.warning(self, "No Bill Selected", "Please select a bill to view.")
        return
    
    bill_data = self.bills_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
    pdf_path = bill_data.get('pdf_path')
    
    if pdf_path and os.path.exists(pdf_path):
        # Open PDF with default viewer
        import subprocess
        subprocess.Popen([pdf_path], shell=True)
    else:
        QMessageBox.warning(self, "Receipt Not Found", "PDF receipt file not found.")
```

---

### Solution 5: Excel Export for Tax/Audit

#### File: `app/export_service.py` (NEW FILE)

**Purpose**: Export all transaction data to Excel

**Dependencies Required:**
```
openpyxl>=3.0.0  # or xlsxwriter
pandas>=1.3.0    # optional, makes it easier
```

**Implementation:**

1. **Create Export Service**
```python
# app/export_service.py

import os
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side
from .models import Bill, BillItem, Customer, Staff, Service
from .database import db_session
from .utils import logger

def export_bills_to_excel(
    output_path: str,
    start_date: datetime = None,
    end_date: datetime = None,
    customer_id: int = None
) -> bool:
    """
    Export bills to Excel with full receipt details.
    
    Columns:
    - Bill Number
    - Date
    - Customer Name
    - Customer Phone
    - Staff Name
    - Service Name
    - Variant
    - Quantity
    - Unit Price
    - Line Total
    - Subtotal
    - Discount
    - Tax %
    - Tax Amount
    - Total
    - Payment Method
    - Payment Status
    - Transaction ID
    """
    try:
        wb = Workbook()
        ws = wb.active
        ws.title = "Bills Export"
        
        # Header row
        headers = [
            "Bill #", "Date", "Time", "Customer Name", "Customer Phone",
            "Staff", "Service", "Variant", "Qty", "Unit Price", "Line Total",
            "Subtotal", "Discount", "Tax %", "Tax Amount", "Total",
            "Payment Method", "Payment Status", "Transaction ID"
        ]
        
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='center')
        
        with db_session() as db:
            query = db.query(Bill)
            
            if start_date:
                query = query.filter(Bill.bill_datetime >= start_date)
            if end_date:
                query = query.filter(Bill.bill_datetime <= end_date)
            if customer_id:
                query = query.filter(Bill.customer_id == customer_id)
            
            bills = query.order_by(Bill.bill_datetime.desc()).all()
            
            row = 2
            for bill in bills:
                for item in bill.items:
                    ws.cell(row=row, column=1, value=bill.bill_number or bill.id)
                    ws.cell(row=row, column=2, value=bill.bill_datetime.strftime('%Y-%m-%d') if bill.bill_datetime else '')
                    ws.cell(row=row, column=3, value=bill.bill_datetime.strftime('%H:%M') if bill.bill_datetime else '')
                    ws.cell(row=row, column=4, value=bill.customer.name if bill.customer else '')
                    ws.cell(row=row, column=5, value=bill.customer.phone if bill.customer else '')
                    ws.cell(row=row, column=6, value=bill.staff.name if bill.staff else '')
                    ws.cell(row=row, column=7, value=item.service.name if item.service else '')
                    ws.cell(row=row, column=8, value=item.service.variant if item.service else '')
                    ws.cell(row=row, column=9, value=item.quantity)
                    ws.cell(row=row, column=10, value=float(item.unit_price) if item.unit_price else 0)
                    ws.cell(row=row, column=11, value=float(item.line_total) if item.line_total else 0)
                    ws.cell(row=row, column=12, value=float(bill.subtotal) if bill.subtotal else 0)
                    ws.cell(row=row, column=13, value=float(bill.discount_amount) if bill.discount_amount else 0)
                    ws.cell(row=row, column=14, value=float(bill.tax_percent) if bill.tax_percent else 0)
                    ws.cell(row=row, column=15, value=float(bill.tax_amount) if bill.tax_amount else 0)
                    ws.cell(row=row, column=16, value=float(bill.total) if bill.total else 0)
                    ws.cell(row=row, column=17, value=bill.payment_method or '')
                    ws.cell(row=row, column=18, value=getattr(bill, 'payment_status', 'Paid') or 'Paid')
                    ws.cell(row=row, column=19, value=getattr(bill, 'transaction_id', '') or '')
                    row += 1
        
        wb.save(output_path)
        logger.info(f"Exported {row - 2} rows to {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Excel export failed: {e}")
        return False
```

2. **Add Export Button to Main Window or Settings**

#### File: `app/gui_main.py`

```python
# Add Export button to main window
self.export_button = QPushButton("Export Data")
self.export_button.clicked.connect(self.export_data_dialog)
button_layout.addWidget(self.export_button)

def export_data_dialog(self):
    from .gui_export import ExportDialog
    dialog = ExportDialog(self)
    dialog.exec()
```

3. **Create Export Dialog**

#### File: `app/gui_export.py` (NEW FILE)

```python
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QDateEdit, QPushButton, QFileDialog, QMessageBox,
    QGroupBox, QCheckBox, QComboBox
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
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        # Date Range
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
        
        # Filter by Customer (optional)
        filter_group = QGroupBox("Filters (Optional)")
        filter_layout = QFormLayout()
        
        self.customer_combo = QComboBox()
        self.customer_combo.addItem("All Customers", None)
        self.load_customers()
        filter_layout.addRow("Customer:", self.customer_combo)
        
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        export_btn = QPushButton("Export to Excel")
        export_btn.clicked.connect(self.do_export)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(export_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
    
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
        
        start = datetime.combine(
            self.start_date.date().toPyDate(),
            datetime.min.time()
        )
        end = datetime.combine(
            self.end_date.date().toPyDate(),
            datetime.max.time()
        )
        customer_id = self.customer_combo.currentData()
        
        success = export_bills_to_excel(
            file_path,
            start_date=start,
            end_date=end,
            customer_id=customer_id
        )
        
        if success:
            QMessageBox.information(
                self,
                "Export Complete",
                f"Data exported successfully to:\n{file_path}"
            )
            self.accept()
        else:
            QMessageBox.critical(
                self,
                "Export Failed",
                "Failed to export data. Check logs for details."
            )
```

---

## Summary of Changes

### Files to Modify:
1. `app/pdf_generator.py` - Fix currency symbol, print optimization
2. `app/gui_customers.py` - Add scroll, add bill history section
3. `app/gui_billing.py` - Fix last_visit_at saving

### Files to Create:
4. `app/export_service.py` - Excel export logic
5. `app/gui_export.py` - Export dialog UI

### Files to Update:
6. `app/gui_main.py` - Add Export Data button

### Dependencies to Add:
```
openpyxl>=3.0.0
```

---

## Implementation Order

### Phase 1: Bug Fixes (Quick Wins)
1. Fix currency symbol in PDF (encoding issue)
2. Fix last_visit_at not saving
3. Add scroll to CustomerDialog

### Phase 2: Customer Bill History
4. Add bills table to CustomerWindow
5. Add view receipt functionality

### Phase 3: Export Feature
6. Create export_service.py
7. Create gui_export.py
8. Add Export button to main window
9. Test export with date filters

### Phase 4: Print Optimization
10. Test PDF on thermal printer
11. Adjust page size if needed
12. Add print-specific styles

---

## Testing Checklist

### PDF Fixes:
- [ ] Currency symbol displays correctly (? or Rs.)
- [ ] Receipt prints without cutoff
- [ ] Table alignment correct on print

### Last Visit Date:
- [ ] Create new bill for customer
- [ ] Verify last_visit_at updates in database
- [ ] Verify displays in customer list

### Customer Bill History:
- [ ] Select customer, bills load in table
- [ ] Click View Receipt opens PDF
- [ ] Handle missing PDF gracefully

### Export:
- [ ] Export all bills works
- [ ] Date range filter works
- [ ] Customer filter works
- [ ] Excel opens correctly in Excel/Sheets
- [ ] All columns have correct data

---

## Estimated Time

| Task | Time |
|------|------|
| Fix currency symbol | 30 min |
| Fix last_visit_at | 15 min |
| Add scroll to dialog | 30 min |
| Customer bill history | 1-2 hours |
| Export service | 1-2 hours |
| Export dialog | 1 hour |
| Testing | 1 hour |
| **TOTAL** | **5-7 hours** |

---

**Status**: PLANNING COMPLETE - AWAITING APPROVAL TO IMPLEMENT
