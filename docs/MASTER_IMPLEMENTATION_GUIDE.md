# ?? Master Implementation Guide

## Salon Billing System - Complete Development Reference

**Version**: 1.0  
**Branch**: v3  
**Repository**: https://github.com/Shiro-yaksha20/Billing-Management-System

---

## Table of Contents

1. [Project Status Overview](#1-project-status-overview)
2. [Architecture Rules](#2-architecture-rules)
3. [Coding Standards](#3-coding-standards)
4. [Phase Completion Status](#4-phase-completion-status)
5. [Pending Implementation Tasks](#5-pending-implementation-tasks)
6. [UI Implementation Guide](#6-ui-implementation-guide)
7. [Service Layer Implementation](#7-service-layer-implementation)
8. [Infrastructure Implementation](#8-infrastructure-implementation)
9. [Testing Implementation](#9-testing-implementation)
10. [Cleanup Tasks](#10-cleanup-tasks)
11. [File Templates](#11-file-templates)
12. [Quick Reference](#12-quick-reference)

---

## 1. Project Status Overview

### 1.1 Architecture Layers

```
???????????????????????????????????????????????????????????????????
?                         UI LAYER                                ?
?   PyQt6 Widgets – Rendering & User Input ONLY                   ?
?   Location: app/ui/                                             ?
???????????????????????????????????????????????????????????????????
                              ?
                    calls (DTOs only)
                              ?
???????????????????????????????????????????????????????????????????
?                    APPLICATION SERVICES                          ?
?   Business Logic – Orchestration – Validation                    ?
?   Location: app/services/                                        ?
???????????????????????????????????????????????????????????????????
                              ?
                    uses (ORM objects)
                              ?
???????????????????????????????????????????????????????????????????
?                       REPOSITORIES                               ?
?   Data Access – CRUD Operations – Queries                        ?
?   Location: app/repositories/                                    ?
???????????????????????????????????????????????????????????????????
                              ?
???????????????????????????????????????????????????????????????????
?                      INFRASTRUCTURE                              ?
?   External Systems – PDF, Cloud, Crypto, WhatsApp                ?
?   Location: app/infrastructure/                                  ?
???????????????????????????????????????????????????????????????????
```

### 1.2 Current Phase Status

| Phase | Description | Status |
|-------|-------------|--------|
| Phase 1 | Repository Layer | ? COMPLETE |
| Phase 2 | Service Layer | ?? 85% Complete |
| Phase 3 | UI Refactoring | ? COMPLETE |
| Phase 4 | Backup Infrastructure | ? 30% Complete |
| Phase 5 | Testing & Validation | ? 20% Complete |

---

## 2. Architecture Rules

### 2.1 ?? Absolute Rules (NEVER VIOLATE)

| ID | Rule | Consequence |
|----|------|-------------|
| **R1** | UI NEVER imports `db_session` | Breaks testability |
| **R2** | UI NEVER imports ORM models for queries | Tight coupling |
| **R3** | Services NEVER import PyQt6 | Can't unit test |
| **R4** | Repositories contain NO business logic | Wrong responsibility |
| **R5** | All business rules live in Services | Duplicated logic |
| **R6** | Infrastructure modules are stateless | Hard to test |
| **R7** | DTOs are immutable data containers | Thread safety |

### 2.2 Import Rules by Layer

#### UI Layer (`app/ui/`)

```python
# ? ALLOWED
from app.services.billing_service import BillingService
from app.services.customer_service import CustomerService
from app.dto.bill_dto import BillData, BillItemInput
from app.dto.customer_dto import CustomerData
from app.exceptions.business_errors import CustomerNotFoundError
from app.exceptions.validation_errors import ValidationError
from PyQt6.QtWidgets import QDialog, QMessageBox

# ? FORBIDDEN
from app.infrastructure.database import db_session      # NEVER
from app.models import Bill, Customer                   # NEVER for queries
from sqlalchemy.orm import Session                      # NEVER
```

#### Service Layer (`app/services/`)

```python
# ? ALLOWED
from app.repositories.bill_repository import BillRepository
from app.repositories.customer_repository import CustomerRepository
from app.dto.bill_dto import BillData
from app.infrastructure.pdf_generator import PDFGenerator
from app.models import Bill                              # Type hints only

# ? FORBIDDEN
from PyQt6.QtWidgets import QMessageBox                 # NEVER
from app.infrastructure.database import db_session      # Use repository
```

#### Repository Layer (`app/repositories/`)

```python
# ? ALLOWED
from app.models import Bill, Customer, Staff
from app.infrastructure.database import db_session
from sqlalchemy.orm import Session

# ? FORBIDDEN
from app.services.billing_service import BillingService # NEVER
from PyQt6.QtWidgets import QWidget                      # NEVER
```

#### Infrastructure Layer (`app/infrastructure/`)

```python
# ? ALLOWED
from reportlab.lib.pagesizes import letter
from cryptography.fernet import Fernet
import requests

# ? FORBIDDEN
from app.services.billing_service import BillingService # NEVER
from app.repositories.bill_repository import BillRepository # NEVER
from PyQt6.QtWidgets import QWidget                      # NEVER
```

### 2.3 Layer Dependency Matrix

```
???????????????????????????????????????????????????????????????????
? FROM ? TO        ? UI ? Services ? Repos ? Infra ? Models ? DTO ?
???????????????????????????????????????????????????????????????????
? UI               ? -  ?    ?    ?  ?   ?  ?   ?   ?   ? ?  ?
? Services         ? ? ?    -     ?  ?   ?  ?   ?   ?*  ? ?  ?
? Repositories     ? ? ?    ?    ?  -    ?  ?   ?   ?   ? ?  ?
? Infrastructure   ? ? ?    ?    ?  ?   ?  -    ?   ?   ? ?  ?
???????????????????????????????????????????????????????????????????
* Services can import Models for type hints only, not for direct queries
```

---

## 3. Coding Standards

### 3.1 Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| UI View class | `*View` | `BillingView`, `CustomerView` |
| UI Window class | `*Window` | `MainWindow` |
| UI Dialog class | `*Dialog` | `CustomerDialog`, `StaffDialog` |
| Service class | `*Service` | `BillingService`, `CustomerService` |
| Repository class | `*Repository` | `BillRepository` |
| DTO class | `*Data`, `*Info`, `*Result` | `BillData`, `BackupInfo` |
| Exception class | `*Error` | `ValidationError` |
| Private method | `_method_name` | `_calculate_tax` |
| Private attribute | `_attribute` | `_billing_service` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_DISCOUNT_PERCENT` |
| Variables | `snake_case` | `customer_name` |
| Functions | `snake_case` | `calculate_total` |

### 3.2 File Size Limits

| File Type | Max Lines | Max Methods | Max Dependencies |
|-----------|-----------|-------------|------------------|
| UI View | 400 | 15 | 5 services |
| UI Dialog | 200 | 10 | 2 services |
| Service | 300 | 15 | 3 repositories |
| Repository | 200 | 10 | 1 model |
| DTO | 100 | 0 (data only) | None |

### 3.3 Method Design Limits

| Metric | Ideal | Maximum | Fix if Exceeded |
|--------|-------|---------|-----------------|
| Lines per method | 15 | 40 | Extract helper methods |
| Parameters | 3-4 | 5 | Use dataclass/DTO |
| Cyclomatic complexity | ?5 | 10 | Refactor logic |
| Nesting depth | ?2 | 3 | Use early returns |

### 3.4 Type Hints (Mandatory)

```python
# ? CORRECT - All public methods must have type hints
from typing import List, Optional
from decimal import Decimal

def search_customers(self, term: str) -> List[CustomerData]:
    """Search customers by name or phone."""
    ...

def get_customer(self, customer_id: int) -> Optional[CustomerData]:
    """Get customer by ID, returns None if not found."""
    ...

# ? Instance variables should be typed
class BillingView(QDialog):
    def __init__(self, billing_service: BillingService) -> None:
        self._billing_service: BillingService = billing_service
        self._selected_customer: Optional[CustomerData] = None
```

### 3.5 Documentation Standards

#### Class Docstring (Required)

```python
class BillHistoryView(QDialog):
    """
    View for displaying and managing bill history.
    
    Provides functionality to:
    - Search bills by number, customer, or date
    - Filter by payment status and method
    - View/print receipts
    - Resend WhatsApp notifications
    
    Attributes:
        _billing_service: Service for bill operations.
        _notification_service: Service for WhatsApp sending.
    """
```

#### Method Docstring (Required for public methods)

```python
def load_bills(self, filters: Optional[BillFilters] = None) -> None:
    """
    Load bills into the table with optional filters.
    
    Args:
        filters: Optional filter criteria (date range, status, etc.)
        
    Returns:
        None
        
    Raises:
        DatabaseError: If query fails.
        
    Note:
        Clears existing table data before loading.
    """
```

### 3.6 Error Handling Pattern

```python
# ? CORRECT Pattern
def save_bill(self) -> None:
    try:
        bill = self._billing_service.create_bill(
            customer_id=self._selected_customer.id,
            staff_id=self._staff_combo.currentData(),
            items=self._collect_items(),
            options=self._build_options(),
        )
        QMessageBox.information(self, "Success", f"Bill #{bill.bill_number} saved")
        self.accept()
    except ValidationError as exc:
        QMessageBox.warning(self, "Validation Error", str(exc))
    except CustomerNotFoundError:
        QMessageBox.warning(self, "Error", "Customer not found")
    except Exception as exc:
        logger.error(f"Unexpected error: {exc}")
        QMessageBox.critical(self, "Error", "An unexpected error occurred")

# ? WRONG Pattern
try:
    bill = self._billing_service.create_bill(...)
except:                    # ? NEVER use bare except
    pass                   # ? NEVER silently ignore
```

### 3.7 Logging Standards

```python
# ? CORRECT - Use logger, never print
import logging
logger = logging.getLogger(__name__)

logger.debug("Processing bill items: %s", items)
logger.info("Bill created: %s", bill.id)
logger.warning("Customer search returned no results for: %s", search_term)
logger.error("Failed to generate PDF: %s", exc)
logger.critical("Database connection failed")

# ? WRONG - Never use print in production
print("Bill created")  # ? NEVER
```

#### Log Level Guide

| Level | When to Use |
|-------|-------------|
| `DEBUG` | Development info, variable values |
| `INFO` | Normal operations, milestones |
| `WARNING` | Unexpected but recoverable |
| `ERROR` | Operation failed |
| `CRITICAL` | System-level failure |

### 3.8 Code Organization Within Files

```python
"""Module docstring - brief description."""

from __future__ import annotations

# Standard library imports
import logging
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

# Third-party imports
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QVBoxLayout

# Local imports - DTOs
from app.dto.bill_dto import BillData

# Local imports - Exceptions
from app.exceptions.business_errors import CustomerNotFoundError

# Local imports - Services
from app.services.billing_service import BillingService

logger = logging.getLogger(__name__)


class MyView(QDialog):
    """Class docstring."""

    # ?????????????????????????????????????????????????????????????????
    # INITIALIZATION
    # ?????????????????????????????????????????????????????????????????

    def __init__(self, service: BillingService, parent=None) -> None:
        """Initialize the view."""
        super().__init__(parent)
        self._service = service
        self._setup_ui()
        self._connect_signals()
        self._load_initial_data()

    # ?????????????????????????????????????????????????????????????????
    # PUBLIC METHODS
    # ?????????????????????????????????????????????????????????????????

    def refresh(self) -> None:
        """Refresh the view data."""
        ...

    # ?????????????????????????????????????????????????????????????????
    # PRIVATE METHODS - UI Setup
    # ?????????????????????????????????????????????????????????????????

    def _setup_ui(self) -> None:
        """Setup the user interface."""
        ...

    def _connect_signals(self) -> None:
        """Connect UI signals to slots."""
        ...

    # ?????????????????????????????????????????????????????????????????
    # PRIVATE METHODS - Data Loading
    # ?????????????????????????????????????????????????????????????????

    def _load_initial_data(self) -> None:
        """Load initial data into the view."""
        ...

    # ?????????????????????????????????????????????????????????????????
    # PRIVATE METHODS - Event Handlers
    # ?????????????????????????????????????????????????????????????????

    def _on_button_clicked(self) -> None:
        """Handle button click event."""
        ...
```

---

## 4. Phase Completion Status

### 4.1 Phase 1: Repository Layer ? COMPLETE

| File | Status | Tests |
|------|--------|-------|
| `app/repositories/__init__.py` | ? | - |
| `app/repositories/base_repository.py` | ? | ? |
| `app/repositories/bill_repository.py` | ? | ? |
| `app/repositories/customer_repository.py` | ? | ? |
| `app/repositories/staff_repository.py` | ? | ? |
| `app/repositories/service_repository.py` | ? | ? |
| `app/repositories/settings_repository.py` | ? | ? |

### 4.2 Phase 2: Service Layer ?? IN PROGRESS

| File | Status | Tests |
|------|--------|-------|
| `app/services/__init__.py` | ? | - |
| `app/services/billing_service.py` | ? | ? |
| `app/services/customer_service.py` | ? | ? |
| `app/services/staff_service.py` | ? | ? |
| `app/services/service_catalog.py` | ? | ? |
| `app/services/settings_service.py` | ? | ? |
| `app/services/notification_service.py` | ? | ? |
| `app/services/backup_service.py` | ?? | ? |
| `app/services/restore_service.py` | ?? | ? |
| `app/services/report_service.py` | ? | ? |

### 4.3 Phase 3: UI Refactoring ? COMPLETE

| File | Status |
|------|--------|
| `app/ui/__init__.py` | ? |
| `app/ui/main_window.py` | ? |
| `app/ui/billing_view.py` | ? |
| `app/ui/customer_view.py` | ? |
| `app/ui/settings_view.py` | ? |
| `app/ui/export_view.py` | ? |
| `app/ui/dialogs/__init__.py` | ? |
| `app/ui/dialogs/customer_dialog.py` | ? |
| `app/ui/dialogs/staff_dialog.py` | ? |
| `app/ui/dialogs/service_dialog.py` | ? |

### 4.4 Phase 4: Backup Infrastructure ? PENDING

| File | Status |
|------|--------|
| `app/infrastructure/crypto.py` | ?? Stub only |
| `app/infrastructure/cloud_drive.py` | ?? Stub only |
| `app/services/backup_service.py` | ?? Partial |
| `app/services/restore_service.py` | ?? Partial |

### 4.5 Phase 5: Testing ? PENDING

| File | Status |
|------|--------|
| `tests/unit/test_billing_service.py` | ? 6 tests |
| `tests/unit/test_customer_service.py` | ? 4 tests |
| `tests/unit/test_repositories.py` | ? |
| `tests/integration/test_backup_restore.py` | ?? Stub |
| `tests/integration/test_pdf_generation.py` | ?? Stub |
| `tests/e2e/test_billing_flow.py` | ?? Stub |

---

## 5. Pending Implementation Tasks

### 5.1 Critical Priority (Must Do)

#### Task 5.1.1: Bill History View

**File**: `app/ui/bill_history_view.py` (NEW)

**Purpose**: Display and manage past bills

**Features Required**:
- Search by bill number, customer name, date range
- Table: Bill #, Date, Customer, Total, Payment, Status, WhatsApp
- Filter by: Date range, Payment status, Payment method
- Actions: View PDF, Resend WhatsApp, Print

**Implementation Steps**:
1. Create `app/ui/bill_history_view.py`
2. Add `BillHistoryView` class extending `QDialog`
3. Inject `BillingService` and `NotificationService`
4. Implement search filters UI
5. Implement bills table with data loading
6. Implement action buttons
7. Add to `app/ui/__init__.py` exports
8. Wire up in `main_window.py`

---

#### Task 5.1.2: Dashboard on Main Window

**File**: `app/ui/main_window.py` (MODIFY)

**Purpose**: Replace empty placeholder with useful dashboard

**Features Required**:
- Today's sales total
- Bills count today
- Pending payments count/amount
- Recent bills list (last 5)
- Quick action buttons

**Implementation Steps**:
1. Add `DashboardStats` dataclass to `app/dto/bill_dto.py`
2. Add `get_dashboard_stats()` method to `BillingService`
3. Add `BillRepository.find_recent()` method
4. Modify `MainWindow._setup_ui()` to create dashboard widgets
5. Add `_create_stat_card()` helper method
6. Add `_refresh_dashboard()` method
7. Call refresh on `showEvent()`

---

#### Task 5.1.3: Customer Selection Dialog

**File**: `app/ui/dialogs/customer_selection_dialog.py` (NEW)

**Purpose**: Select customer when search returns multiple results

**Features Required**:
- List of matching customers
- Double-click or Select button to choose
- Cancel to abort

**Implementation Steps**:
1. Create `app/ui/dialogs/customer_selection_dialog.py`
2. Add `CustomerSelectionDialog` class
3. Accept `List[CustomerData]` in constructor
4. Implement list widget with customer display
5. Add select/cancel buttons
6. Expose `selected_customer` property
7. Update `billing_view.py` to use dialog when multiple results

---

#### Task 5.1.4: Enable Backup/Restore UI

**File**: `app/ui/settings_view.py` (MODIFY)

**Purpose**: Connect disabled Advanced tab buttons

**Implementation Steps**:
1. Implement `_on_backup_clicked()` handler
2. Implement `_on_restore_clicked()` handler
3. Add file dialogs for backup location
4. Call `BackupService.create_backup()`
5. Call `RestoreService.restore_from_file()`
6. Show progress/status messages
7. Enable the disabled buttons

---

#### Task 5.1.5: Delete Customer Functionality

**File**: `app/ui/customer_view.py` (MODIFY)

**Purpose**: Allow deleting customers

**Implementation Steps**:
1. Add "Delete Customer" button to UI
2. Implement `_on_delete_customer()` handler
3. Add confirmation dialog
4. Check for existing bills (soft delete or prevent)
5. Add `CustomerService.delete_customer()` method
6. Add `CustomerRepository.delete()` method
7. Refresh customer list after delete

---

### 5.2 Important Priority (Should Do)

#### Task 5.2.1: Quick Stats Widget

**File**: `app/ui/main_window.py` (MODIFY)

**Purpose**: Display today's metrics on dashboard

**Implementation Steps**:
1. Create stat card widgets (Sales, Bills, Pending, Customers)
2. Style with large font for values
3. Add icons/emojis for visual clarity
4. Auto-refresh on window show

---

#### Task 5.2.2: View Logs Functionality

**File**: `app/ui/settings_view.py` (MODIFY)

**Purpose**: View application logs from UI

**Implementation Steps**:
1. Implement `_on_view_logs_clicked()` handler
2. Create `LogViewerDialog` class
3. Read `logs/app.log` file
4. Display in scrollable text area
5. Add refresh and clear buttons

---

#### Task 5.2.3: Auto-fill Default Tax

**File**: `app/ui/billing_view.py` (MODIFY)

**Purpose**: Pre-populate tax from settings

**Implementation Steps**:
1. Inject `SettingsService` into `BillingView`
2. In `__init__`, get `default_tax_percent` setting
3. Set `_tax_input.setText()` with default value
4. Allow user to override

---

#### Task 5.2.4: Resend WhatsApp from Customer View

**File**: `app/ui/customer_view.py` (MODIFY)

**Purpose**: Retry failed WhatsApp sends

**Implementation Steps**:
1. Add "Resend WhatsApp" button
2. Implement `_on_resend_whatsapp()` handler
3. Get selected bill from history table
4. Call `NotificationService.send_whatsapp_receipt()`
5. Update bill's whatsapp_status
6. Show success/failure message

---

#### Task 5.2.5: Table Sorting

**Files**: All view files with tables

**Purpose**: Allow sorting by clicking column headers

**Implementation Steps**:
1. Enable sorting on `QTableWidget`
2. Call `setSortingEnabled(True)`
3. Optionally set default sort column
4. Test with different data types (date, number, string)

---

#### Task 5.2.6: Bill Preview

**File**: `app/ui/billing_view.py` (MODIFY)

**Purpose**: Preview bill before saving

**Implementation Steps**:
1. Add "Preview" button next to Save
2. Create `BillPreviewDialog` class
3. Generate preview PDF to temp file
4. Display in dialog (or open with system viewer)
5. Confirm or cancel from preview

---

#### Task 5.2.7: Service Categories UI

**File**: `app/ui/settings_view.py` (MODIFY)

**Purpose**: Manage categories in Settings

**Implementation Steps**:
1. Add "Categories" sub-tab or section in Services tab
2. Display list of existing categories
3. Add/Edit/Delete category buttons
4. Sync with services when category deleted

---

### 5.3 UX Flow Improvements (from uiplan.md)

#### Task 5.3.1: Sticky Totals Panel

**File**: `app/ui/billing_view.py` (MODIFY)

**Purpose**: Keep totals visible while scrolling services

**Implementation Steps**:
1. Restructure layout with splitter or fixed panel
2. Move totals section to right side
3. Make totals panel fixed (non-scrolling)
4. Increase font size for total amount
5. Update totals in real-time as services change

---

#### Task 5.3.2: Visual Progress Feedback

**File**: `app/ui/billing_view.py` (MODIFY)

**Purpose**: Show completion status for billing steps

**Implementation Steps**:
1. Add status labels: ? Customer, ? Services, ? Payment
2. Update status when each section is complete
3. Style completed steps with green checkmark
4. Show "Ready to Save" when all complete

---

#### Task 5.3.3: Hide Transaction ID Unless Needed

**File**: `app/ui/billing_view.py` (MODIFY)

**Purpose**: Reduce cognitive load

**Implementation Steps**:
1. Hide transaction ID field by default
2. Show only when payment method is UPI/Card
3. Connect to payment method combo change signal
4. `_tx_id_input.setVisible(method != "Cash")`

---

#### Task 5.3.4: Sidebar Navigation (Major Change)

**File**: `app/ui/main_window.py` (MODIFY)

**Purpose**: Replace button row with sidebar

**Implementation Steps**:
1. Create sidebar `QListWidget` with navigation items
2. Create stacked widget for content pages
3. Connect sidebar selection to page switching
4. Add Dashboard, New Bill, Customers, Export, Settings pages
5. Style sidebar with icons
6. Preserve dialog-based flow for complex forms

---

#### Task 5.3.5: Step-based Billing Layout

**File**: `app/ui/billing_view.py` (MODIFY)

**Purpose**: Guide user through billing steps

**Implementation Steps**:
1. Restructure into numbered sections
2. Add `QGroupBox("1?? Customer")`, `QGroupBox("2?? Services")`, etc.
3. Visual flow from top to bottom
4. Consider wizard-style with Next/Back buttons

---

### 5.4 Infrastructure Tasks

#### Task 5.4.1: Implement Encryption (crypto.py)

**File**: `app/infrastructure/crypto.py` (MODIFY)

**Purpose**: AES encryption for backups

**Implementation Steps**:
1. Add `cryptography` to requirements.txt
2. Implement `encrypt_file(source, dest, password)` function
3. Implement `decrypt_file(source, dest, password)` function
4. Use Fernet (AES-128-CBC) or AES-256-GCM
5. Handle password derivation with PBKDF2
6. Add unit tests

---

#### Task 5.4.2: Implement Cloud Drive (cloud_drive.py)

**File**: `app/infrastructure/cloud_drive.py` (MODIFY)

**Purpose**: Google Drive backup storage

**Implementation Steps**:
1. Add `google-api-python-client` to requirements.txt
2. Add `google-auth-oauthlib` to requirements.txt
3. Implement OAuth2 authentication flow
4. Implement `upload_file(local_path, remote_name)` function
5. Implement `download_file(remote_name, local_path)` function
6. Implement `list_backups()` function
7. Store credentials securely
8. Add integration tests

---

#### Task 5.4.3: Complete Backup Service

**File**: `app/services/backup_service.py` (MODIFY)

**Purpose**: Full backup with encryption and cloud

**Implementation Steps**:
1. Add encryption option to `create_backup()`
2. Add cloud upload option
3. Create backup manifest with metadata
4. Implement `list_backups()` method
5. Implement `delete_old_backups()` method
6. Add progress callback support

---

#### Task 5.4.4: Complete Restore Service

**File**: `app/services/restore_service.py` (MODIFY)

**Purpose**: Restore from encrypted/cloud backups

**Implementation Steps**:
1. Add decryption support
2. Add cloud download support
3. Validate backup integrity before restore
4. Create restore point before overwriting
5. Implement rollback on failure
6. Add progress callback support

---

### 5.5 Testing Tasks

#### Task 5.5.1: Complete Unit Tests

**Files**: `tests/unit/`

**Target**: 90% coverage for services

**Implementation Steps**:
1. Add tests for `staff_service.py`
2. Add tests for `service_catalog.py`
3. Add tests for `settings_service.py`
4. Add tests for `notification_service.py`
5. Add tests for `report_service.py`
6. Run coverage report: `pytest --cov=app/services`

---

#### Task 5.5.2: Integration Tests - Backup/Restore

**File**: `tests/integration/test_backup_restore.py` (MODIFY)

**Implementation Steps**:
1. Test `create_backup()` creates valid archive
2. Test backup contains database and receipts
3. Test `restore_from_file()` restores data
4. Test encrypted backup/restore cycle
5. Test cloud upload/download (mock API)

---

#### Task 5.5.3: Integration Tests - PDF Generation

**File**: `tests/integration/test_pdf_generation.py` (MODIFY)

**Implementation Steps**:
1. Test PDF generation with all fields
2. Test PDF contains correct totals
3. Test PDF with/without logo
4. Test PDF with different payment methods
5. Verify PDF file is valid

---

#### Task 5.5.4: E2E Tests - Billing Flow

**File**: `tests/e2e/test_billing_flow.py` (MODIFY)

**Implementation Steps**:
1. Test complete billing workflow
2. Create customer ? Add services ? Save bill
3. Verify bill in database
4. Verify PDF generated
5. Verify customer last_visit_at updated

---

## 6. UI Implementation Guide

### 6.1 UI View Template

Use this template for all new UI views:

```python
"""<Description> view for <purpose>."""

from __future__ import annotations

import logging
from typing import Optional, List

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from app.dto.<module>_dto import <DataClass>
from app.exceptions.business_errors import <SpecificError>
from app.services.<module>_service import <ServiceClass>

logger = logging.getLogger(__name__)


class <Name>View(QDialog):
    """
    View for <description>.
    
    Provides functionality to:
    - <Feature 1>
    - <Feature 2>
    - <Feature 3>
    
    Attributes:
        _<service>: Service for <purpose>.
    """

    # ?????????????????????????????????????????????????????????????????
    # INITIALIZATION
    # ?????????????????????????????????????????????????????????????????

    def __init__(
        self,
        <service>: <ServiceClass>,
        parent=None,
    ) -> None:
        """
        Initialize the <name> view.
        
        Args:
            <service>: Service for <purpose>.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._<service> = <service>
        self._selected_item: Optional[<DataClass>] = None
        
        self._setup_ui()
        self._connect_signals()
        self._load_initial_data()

    # ?????????????????????????????????????????????????????????????????
    # PRIVATE METHODS - UI Setup
    # ?????????????????????????????????????????????????????????????????

    def _setup_ui(self) -> None:
        """Setup the user interface components."""
        self.setWindowTitle("<Window Title>")
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        
        layout = QVBoxLayout(self)
        
        # TODO: Add UI components
        
    def _connect_signals(self) -> None:
        """Connect UI signals to slots."""
        # TODO: Connect signals
        pass

    def _load_initial_data(self) -> None:
        """Load initial data into the view."""
        self._load_data()

    # ?????????????????????????????????????????????????????????????????
    # PUBLIC METHODS
    # ?????????????????????????????????????????????????????????????????

    def refresh(self) -> None:
        """Refresh the view data."""
        self._load_data()

    # ?????????????????????????????????????????????????????????????????
    # PRIVATE METHODS - Data Loading
    # ?????????????????????????????????????????????????????????????????

    def _load_data(self) -> None:
        """Load data from service."""
        try:
            data = self._<service>.get_all()
            self._populate_table(data)
        except Exception as exc:
            logger.error(f"Failed to load data: {exc}")
            QMessageBox.critical(self, "Error", "Failed to load data")

    def _populate_table(self, items: List[<DataClass>]) -> None:
        """Populate table with data."""
        # TODO: Implement table population
        pass

    # ?????????????????????????????????????????????????????????????????
    # PRIVATE METHODS - Event Handlers
    # ?????????????????????????????????????????????????????????????????

    def _on_selection_changed(self) -> None:
        """Handle selection change."""
        # TODO: Implement selection handling
        pass

    def _on_action_clicked(self) -> None:
        """Handle action button click."""
        if not self._selected_item:
            QMessageBox.warning(self, "No Selection", "Please select an item")
            return
        
        try:
            # TODO: Implement action
            pass
        except Exception as exc:
            logger.error(f"Action failed: {exc}")
            QMessageBox.critical(self, "Error", "Action failed")
```

### 6.2 Dialog Template

Use this template for modal dialogs:

```python
"""<Description> dialog for <purpose>."""

from __future__ import annotations

from typing import List, Optional

from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from app.dto.<module>_dto import <DataClass>


class <Name>Dialog(QDialog):
    """
    Dialog for <description>.
    
    Used when <use case>.
    Returns the selected/created <DataClass> or None if cancelled.
    """

    def __init__(
        self,
        data: Optional[<DataClass>] = None,
        parent=None,
    ) -> None:
        """
        Initialize the dialog.
        
        Args:
            data: Optional existing data for editing.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._data = data
        self._result: Optional[<DataClass>] = None
        
        self._setup_ui()
        self._populate_fields()

    @property
    def result(self) -> Optional[<DataClass>]:
        """Get the dialog result."""
        return self._result

    def _setup_ui(self) -> None:
        """Setup the user interface."""
        self.setWindowTitle("<Dialog Title>")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        # Form fields
        # TODO: Add form fields
        
        # Buttons
        button_layout = QHBoxLayout()
        self._save_btn = QPushButton("Save")
        self._cancel_btn = QPushButton("Cancel")
        self._save_btn.clicked.connect(self._on_save)
        self._cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self._save_btn)
        button_layout.addWidget(self._cancel_btn)
        layout.addLayout(button_layout)

    def _populate_fields(self) -> None:
        """Populate fields with existing data."""
        if self._data:
            # TODO: Populate fields
            pass

    def _on_save(self) -> None:
        """Handle save button click."""
        # TODO: Validate and create result
        self._result = None  # Create from form fields
        self.accept()
```

---

## 7. Service Layer Implementation

### 7.1 Service Template

```python
"""<Description> service for <purpose>."""

from __future__ import annotations

import logging
from typing import List, Optional
from decimal import Decimal

from app.dto.<module>_dto import <DataClass>
from app.exceptions.business_errors import <SpecificError>
from app.repositories.<module>_repository import <Repository>

logger = logging.getLogger(__name__)


class <Name>Service:
    """
    Service for <description>.
    
    Handles all <domain> business logic including:
    - <Operation 1>
    - <Operation 2>
    - <Operation 3>
    
    Attributes:
        _<repo>: Repository for <purpose>.
    """

    def __init__(self, <repo>: <Repository>) -> None:
        """
        Initialize the service.
        
        Args:
            <repo>: Repository for data access.
        """
        self._<repo> = <repo>

    # ?????????????????????????????????????????????????????????????????
    # PUBLIC METHODS - Queries
    # ?????????????????????????????????????????????????????????????????

    def get_by_id(self, id: int) -> Optional[<DataClass>]:
        """
        Get item by ID.
        
        Args:
            id: Item identifier.
            
        Returns:
            Item data or None if not found.
        """
        entity = self._<repo>.get_by_id(id)
        if not entity:
            return None
        return self._to_dto(entity)

    def get_all(self) -> List[<DataClass>]:
        """
        Get all items.
        
        Returns:
            List of all items.
        """
        entities = self._<repo>.get_all()
        return [self._to_dto(e) for e in entities]

    # ?????????????????????????????????????????????????????????????????
    # PUBLIC METHODS - Commands
    # ?????????????????????????????????????????????????????????????????

    def create(self, data: <DataClass>) -> <DataClass>:
        """
        Create new item.
        
        Args:
            data: Item data.
            
        Returns:
            Created item with ID.
            
        Raises:
            ValidationError: If data is invalid.
        """
        self._validate(data)
        entity = self._to_entity(data)
        created = self._<repo>.create(entity)
        logger.info("Created <item>: %s", created.id)
        return self._to_dto(created)

    # ?????????????????????????????????????????????????????????????????
    # PRIVATE METHODS - Validation
    # ?????????????????????????????????????????????????????????????????

    def _validate(self, data: <DataClass>) -> None:
        """Validate item data."""
        # TODO: Add validation rules
        pass

    # ?????????????????????????????????????????????????????????????????
    # PRIVATE METHODS - Mapping
    # ?????????????????????????????????????????????????????????????????

    def _to_dto(self, entity) -> <DataClass>:
        """Convert entity to DTO."""
        return <DataClass>(
            id=entity.id,
            # TODO: Map fields
        )

    def _to_entity(self, data: <DataClass>):
        """Convert DTO to entity."""
        from app.models import <Model>
        return <Model>(
            # TODO: Map fields
        )
```

### 7.2 Dashboard Stats Implementation

Add to `app/dto/bill_dto.py`:

```python
@dataclass
class DashboardStats:
    """Statistics for dashboard display."""
    
    today_sales: Decimal
    today_bills_count: int
    pending_amount: Decimal
    pending_count: int
    today_customers: int
    recent_bills: List[BillData]
```

Add to `app/services/billing_service.py`:

```python
def get_dashboard_stats(self) -> DashboardStats:
    """
    Get statistics for the dashboard.
    
    Returns:
        DashboardStats with today's metrics and recent bills.
    """
    from datetime import date, datetime
    
    today = date.today()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    
    # Get today's bills
    today_bills = self._bill_repo.find_by_date_range(today_start, today_end)
    
    # Calculate stats
    paid_bills = [b for b in today_bills if b.payment_status == "Paid"]
    pending_bills = [b for b in today_bills if b.payment_status == "Pending"]
    
    today_sales = sum((b.total or Decimal("0")) for b in paid_bills)
    pending_amount = sum((b.total or Decimal("0")) for b in pending_bills)
    
    # Get recent bills (last 5)
    recent_bills = self._bill_repo.find_recent(limit=5)
    
    # Unique customers today
    customer_ids = {b.customer_id for b in today_bills if b.customer_id}
    
    return DashboardStats(
        today_sales=today_sales,
        today_bills_count=len(today_bills),
        pending_amount=pending_amount,
        pending_count=len(pending_bills),
        today_customers=len(customer_ids),
        recent_bills=[self._to_dto(b) for b in recent_bills],
    )
```

---

## 8. Infrastructure Implementation

### 8.1 Crypto Implementation

```python
"""Encryption utilities for secure backup storage."""

from __future__ import annotations

import os
import base64
import logging
from pathlib import Path

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


def derive_key(password: str, salt: bytes) -> bytes:
    """
    Derive encryption key from password.
    
    Args:
        password: User password.
        salt: Random salt bytes.
        
    Returns:
        Derived key bytes.
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key


def encrypt_file(source_path: str, dest_path: str, password: str) -> bool:
    """
    Encrypt a file with password.
    
    Args:
        source_path: Path to source file.
        dest_path: Path to encrypted output.
        password: Encryption password.
        
    Returns:
        True if successful.
    """
    try:
        salt = os.urandom(16)
        key = derive_key(password, salt)
        fernet = Fernet(key)
        
        with open(source_path, "rb") as f:
            data = f.read()
        
        encrypted = fernet.encrypt(data)
        
        with open(dest_path, "wb") as f:
            f.write(salt)
            f.write(encrypted)
        
        logger.info("File encrypted: %s", dest_path)
        return True
        
    except Exception as exc:
        logger.error("Encryption failed: %s", exc)
        return False


def decrypt_file(source_path: str, dest_path: str, password: str) -> bool:
    """
    Decrypt a file with password.
    
    Args:
        source_path: Path to encrypted file.
        dest_path: Path to decrypted output.
        password: Decryption password.
        
    Returns:
        True if successful.
    """
    try:
        with open(source_path, "rb") as f:
            salt = f.read(16)
            encrypted = f.read()
        
        key = derive_key(password, salt)
        fernet = Fernet(key)
        
        decrypted = fernet.decrypt(encrypted)
        
        with open(dest_path, "wb") as f:
            f.write(decrypted)
        
        logger.info("File decrypted: %s", dest_path)
        return True
        
    except Exception as exc:
        logger.error("Decryption failed: %s", exc)
        return False
```

### 8.2 Cloud Drive Implementation

```python
"""Google Drive adapter for cloud backup storage."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

# Placeholder - requires google-api-python-client
SCOPES = ["https://www.googleapis.com/auth/drive.file"]


class CloudDriveAdapter:
    """
    Adapter for Google Drive operations.
    
    Handles backup upload/download to Google Drive.
    """

    def __init__(self, credentials_path: Optional[str] = None) -> None:
        """
        Initialize the adapter.
        
        Args:
            credentials_path: Path to OAuth credentials file.
        """
        self._credentials_path = credentials_path
        self._service = None

    def authenticate(self) -> bool:
        """
        Authenticate with Google Drive.
        
        Returns:
            True if authentication successful.
        """
        # TODO: Implement OAuth2 flow
        logger.warning("Cloud Drive authentication not implemented")
        return False

    def upload_file(self, local_path: str, remote_name: str) -> Optional[str]:
        """
        Upload file to Google Drive.
        
        Args:
            local_path: Path to local file.
            remote_name: Name for remote file.
            
        Returns:
            File ID if successful, None otherwise.
        """
        # TODO: Implement upload
        logger.warning("Cloud Drive upload not implemented")
        return None

    def download_file(self, file_id: str, local_path: str) -> bool:
        """
        Download file from Google Drive.
        
        Args:
            file_id: Google Drive file ID.
            local_path: Path to save file.
            
        Returns:
            True if successful.
        """
        # TODO: Implement download
        logger.warning("Cloud Drive download not implemented")
        return False

    def list_backups(self) -> List[dict]:
        """
        List backup files in Google Drive.
        
        Returns:
            List of backup file metadata.
        """
        # TODO: Implement listing
        logger.warning("Cloud Drive listing not implemented")
        return []
```

---

## 9. Testing Implementation

### 9.1 Test Template

```python
"""Tests for <module> service."""

import pytest
from decimal import Decimal
from unittest.mock import Mock, MagicMock

from app.services.<module>_service import <Service>
from app.dto.<module>_dto import <DataClass>
from app.exceptions.business_errors import <SpecificError>


class Test<Service>:
    """Test cases for <Service>."""

    @pytest.fixture
    def mock_repo(self):
        """Create mock repository."""
        return Mock()

    @pytest.fixture
    def service(self, mock_repo):
        """Create service with mocked dependencies."""
        return <Service>(mock_repo)

    # ?????????????????????????????????????????????????????????????????
    # Query Tests
    # ?????????????????????????????????????????????????????????????????

    def test_get_by_id_existing_returns_data(self, service, mock_repo):
        """Test get_by_id with existing item returns data."""
        # Arrange
        mock_entity = Mock(id=1, name="Test")
        mock_repo.get_by_id.return_value = mock_entity
        
        # Act
        result = service.get_by_id(1)
        
        # Assert
        assert result is not None
        assert result.id == 1
        mock_repo.get_by_id.assert_called_once_with(1)

    def test_get_by_id_missing_returns_none(self, service, mock_repo):
        """Test get_by_id with missing item returns None."""
        # Arrange
        mock_repo.get_by_id.return_value = None
        
        # Act
        result = service.get_by_id(999)
        
        # Assert
        assert result is None

    # ?????????????????????????????????????????????????????????????????
    # Command Tests
    # ?????????????????????????????????????????????????????????????????

    def test_create_valid_data_succeeds(self, service, mock_repo):
        """Test create with valid data succeeds."""
        # Arrange
        data = <DataClass>(name="Test")
        mock_repo.create.return_value = Mock(id=1, name="Test")
        
        # Act
        result = service.create(data)
        
        # Assert
        assert result.id == 1
        mock_repo.create.assert_called_once()

    def test_create_invalid_data_raises_error(self, service):
        """Test create with invalid data raises ValidationError."""
        # Arrange
        data = <DataClass>(name="")  # Invalid
        
        # Act & Assert
        with pytest.raises(ValidationError):
            service.create(data)

    # ?????????????????????????????????????????????????????????????????
    # Business Rule Tests
    # ?????????????????????????????????????????????????????????????????

    def test_<business_rule>_<scenario>_<expected>(self, service):
        """Test <business rule> with <scenario> <expected behavior>."""
        # Arrange
        # TODO: Setup
        
        # Act
        # TODO: Execute
        
        # Assert
        # TODO: Verify
        pass
```

### 9.2 Test Naming Convention

```
test_<method>_<scenario>_<expected>

Examples:
- test_calculate_discount_percent_over_100_raises_error
- test_create_bill_with_valid_data_returns_bill
- test_get_customer_missing_returns_none
- test_restore_from_corrupted_backup_fails_gracefully
```

---

## 10. Cleanup Tasks

### 10.1 Files to Remove

| File | Reason | Replacement |
|------|--------|-------------|
| `app/backup_service.py` | Duplicate | `app/services/backup_service.py` |
| `app/settings_service.py` | Duplicate | `app/services/settings_service.py` |
| `app/export_service.py` | Duplicate | `app/services/report_service.py` |
| `app/database.py` | Duplicate | `app/infrastructure/database.py` |
| `app/utils.py` | Duplicate | `app/infrastructure/logging.py` |
| `app/pdf_generator.py` | Duplicate | `app/infrastructure/pdf_generator.py` |
| `app/whatsapp_client.py` | Duplicate | `app/infrastructure/whatsapp_client.py` |
| `app/gui_*.py` | Legacy | `app/ui/*.py` |
| `ConsoleApp1/` | Unrelated | Remove entirely |

### 10.2 Cleanup Steps

1. **Verify No Imports**
   ```bash
   grep -r "from app.backup_service" .
   grep -r "from app.settings_service" .
   grep -r "from app.database import" .
   ```

2. **Run Tests Before Removal**
   ```bash
   python -m pytest -v
   ```

3. **Create Backup Commit**
   ```bash
   git add .
   git commit -m "chore: backup before cleanup"
   ```

4. **Remove Files**
   ```bash
   rm app/backup_service.py
   rm app/settings_service.py
   rm app/export_service.py
   rm app/database.py
   rm app/utils.py
   rm app/pdf_generator.py
   rm app/whatsapp_client.py
   rm app/gui_main.py
   rm app/gui_billing.py
   rm app/gui_customers.py
   rm app/gui_settings.py
   rm app/gui_export.py
   rm -rf ConsoleApp1/
   rm ConsoleApp1.sln
   ```

5. **Run Tests After Removal**
   ```bash
   python -m pytest -v
   python main.py  # Verify app runs
   ```

6. **Archive Old Documentation**
   ```bash
   mkdir -p docs/archive
   mv APP_IMPROVEMENTS_PLAN.md docs/archive/
   mv RECEIPT_IMPLEMENTATION_PLAN.md docs/archive/
   mv RECEIPT_FEATURES_COMPLETION_REPORT.md docs/archive/
   mv TESTING_STRATEGY_PLAN.md docs/archive/
   mv ARCHITECTURE_PLAN.md docs/archive/
   ```

---

## 11. File Templates

### 11.1 DTO Template

```python
"""Data transfer objects for <domain>."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import List, Optional


@dataclass
class <Name>Data:
    """
    Data transfer object for <entity>.
    
    Attributes:
        id: Unique identifier.
        <field>: <Description>.
    """
    
    id: Optional[int] = None
    <field>: <type> = None
    created_at: Optional[datetime] = None
```

### 11.2 Repository Template

```python
"""Repository for <entity> data access."""

from __future__ import annotations

from typing import List, Optional

from app.models import <Model>
from app.repositories.base_repository import BaseRepository


class <Name>Repository(BaseRepository[<Model>]):
    """
    Repository for <entity> operations.
    
    Provides data access methods for <entity>.
    """

    def __init__(self, session_factory) -> None:
        """Initialize repository with session factory."""
        super().__init__(<Model>, session_factory)

    def find_by_<field>(self, value: <type>) -> List[<Model>]:
        """
        Find entities by <field>.
        
        Args:
            value: <Field> value to search.
            
        Returns:
            List of matching entities.
        """
        with self._session_factory() as session:
            return session.query(self._model).filter(
                self._model.<field> == value
            ).all()
```

### 11.3 Exception Template

```python
"""Business errors for <domain>."""

from __future__ import annotations


class <Domain>Error(Exception):
    """Base exception for <domain> errors."""
    pass


class <Specific>Error(<Domain>Error):
    """
    Raised when <condition>.
    
    Example:
        >>> raise <Specific>Error("message")
    """
    pass
```

---

## 12. Quick Reference

### 12.1 Common Commands

```bash
# Run application
python main.py

# Run tests
python -m pytest -v

# Run tests with coverage
python -m pytest --cov=app --cov-report=html

# Type checking
python -m mypy app/

# Linting
python -m flake8 app/

# Format code
python -m black app/
python -m isort app/

# Build executable
pyinstaller SalonBillingSystem.spec
```

### 12.2 Key File Locations

| Purpose | Location |
|---------|----------|
| Entry point | `main.py` |
| UI Views | `app/ui/` |
| Services | `app/services/` |
| Repositories | `app/repositories/` |
| DTOs | `app/dto/` |
| Exceptions | `app/exceptions/` |
| Infrastructure | `app/infrastructure/` |
| Models | `app/models.py` |
| Constants | `app/constants.py` |
| Tests | `tests/` |

### 12.3 Layer Import Cheat Sheet

```
UI imports:
  ? app.services.*
  ? app.dto.*
  ? app.exceptions.*
  ? app.infrastructure.database
  ? app.models (for queries)
  ? app.repositories.*

Services imports:
  ? app.repositories.*
  ? app.dto.*
  ? app.infrastructure.*
  ? app.models (type hints)
  ? PyQt6.*
  ? app.ui.*

Repositories imports:
  ? app.models
  ? app.infrastructure.database
  ? app.services.*
  ? app.ui.*
```

### 12.4 Git Workflow

```bash
# Feature branch
git checkout -b feature/<name>

# Commit format
git commit -m "<type>(<scope>): <description>"

# Types: feat, fix, refactor, test, docs, chore

# Examples
git commit -m "feat(ui): add bill history view"
git commit -m "fix(billing): correct tax calculation"
git commit -m "refactor(services): extract validation logic"
git commit -m "test(billing): add discount calculation tests"
git commit -m "docs: update implementation guide"
git commit -m "chore: remove legacy files"
```

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | February 2026 | Initial comprehensive guide |

---

*This document consolidates all planning documents into a single implementation reference.*  
*Follow the coding standards and architecture rules strictly for clean, maintainable code.*
