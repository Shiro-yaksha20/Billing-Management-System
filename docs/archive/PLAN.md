# ??? CLEAN ARCHITECTURE IMPLEMENTATION PLAN
## Salon Billing System — Complete Refactoring Guide

**Version**: 3.0  
**Date**: February 2026  
**Status**: IN PROGRESS — PHASE 2  
**Branch**: `v3` (same repository)  
**Repository**: https://github.com/Shiro-yaksha20/Billing-Management-System

---

## ?? TABLE OF CONTENTS

1. [Executive Summary](#1-executive-summary)
2. [Current State Analysis](#2-current-state-analysis)
3. [Target Architecture](#3-target-architecture)
4. [Project Structure](#4-project-structure)
5. [Implementation Phases](#5-implementation-phases)
6. [Detailed Step-by-Step Plan](#6-detailed-step-by-step-plan)
7. [Coding Standards & Rules](#7-coding-standards--rules)
8. [Python Engineering Standards](#8-python-engineering-standards)
9. [File Size & Complexity Limits](#9-file-size--complexity-limits)
10. [Testing Strategy](#10-testing-strategy)
11. [Migration Checklist](#11-migration-checklist)
12. [Risk Mitigation](#12-risk-mitigation)
13. [Tooling & Quality Gates](#13-tooling--quality-gates)

---

## 1. EXECUTIVE SUMMARY

### 1.1 Goal

Transform the current monolithic GUI-centric codebase into a **clean layered architecture** where:

- **UI** is presentation-only (no business logic, no DB access)
- **Services** contain all business logic
- **Repositories** handle all data access
- **Infrastructure** handles external concerns (PDF, cloud, crypto)

### 1.2 Key Outcomes

| Outcome | Benefit |
|---------|---------|
| Testable business logic | Unit tests without PyQt dependencies |
| Maintainable codebase | Clear separation of concerns |
| Cloud backup ready | Isolated infrastructure layer |
| Future SaaS readiness | Clean API boundaries |
| Senior-level code quality | Understandable, modular, replaceable |

### 1.3 Golden Rule

> **UI never touches DB, filesystem, or cloud directly.**

### 1.4 Branch Strategy

- **Branch**: `v3` (create from `master`)
- **Tag**: `v3.0.0` upon completion
- **No new repository** — use existing repo with new branch

---

## 2. CURRENT STATE ANALYSIS

### 2.1 Existing File Structure

```
app/
??? models.py              ? Good (ORM only)
??? database.py            ? Good (session management)
??? constants.py           ? Good (config values)
??? utils.py               ? Good (logging)
??? settings_service.py    ? Good (already a service)
??? backup_service.py      ??  Partial (local only, no encryption)
??? export_service.py      ? Good (already a service)
??? csv_service_importer.py ? Good (utility)
??? pdf_generator.py       ??  Mixed (service + infrastructure)
??? whatsapp_client.py     ? Good (infrastructure adapter)
??? gui_main.py            ??  Mixed (has migrations)
??? gui_billing.py         ? BAD (DB access + business logic)
??? gui_customers.py       ? BAD (DB access in UI)
??? gui_settings.py        ??  Mixed (some DB access)
??? gui_export.py          ? Good (delegates to service)
```

### 2.2 Violations Found

| File | Violation | Line(s) | Severity |
|------|-----------|---------|----------|
| `gui_billing.py` | Direct `db_session()` in UI | 82, 166, 210, 273, 314 | **HIGH** |
| `gui_billing.py` | Business logic (total calc) | 240-280 | **HIGH** |
| `gui_billing.py` | ORM queries in UI | Multiple | **HIGH** |
| `gui_customers.py` | Direct `db_session()` in UI | 47, 66, 92, 125, 146 | **HIGH** |
| `gui_settings.py` | Direct `db_session()` in UI | 163, 209, 241, etc. | **MEDIUM** |
| `pdf_generator.py` | Mixes generation + DB query | 34-100 | **MEDIUM** |

### 2.3 Business Logic in Wrong Places

**Current `gui_billing.py:save_bill()` — 80+ lines of mixed concerns:**

```python
# ? WRONG: Mixed validation, calculation, persistence, notification
def save_bill(self):
    with db_session() as db:
        new_bill = Bill(...)
        for row in range(self.services_table.rowCount()):
            item = BillItem(...)
            new_bill.items.append(item)
        subtotal = sum(...)  # Business logic in UI!
        # ... discount logic ...
        # ... tax logic ...
        # ... total calculation ...
        db.add(new_bill)
        # ... PDF generation ...
        # ... WhatsApp send ...
```

**Target state:**

```python
# ? CORRECT: UI delegates to service
def save_bill(self):
    try:
        items = self._collect_items_from_table()
        options = BillOptions(...)
        bill = self.billing_service.create_bill(
            customer_id=self.selected_customer['id'],
            staff_id=self.staff_combo.currentData(),
            items=items,
            options=options
        )
        QMessageBox.information(self, "Success", f"Bill #{bill.bill_number} saved")
        self.accept()
    except ValidationError as e:
        QMessageBox.warning(self, "Validation Error", str(e))
```

---

## 3. TARGET ARCHITECTURE

### 3.1 Architecture Diagram

```
???????????????????????????????????????????????????????????????
?                        UI LAYER                             ?
?   PyQt6 Widgets — Rendering & User Input ONLY               ?
?   ??????????????? ????????????????? ???????????????????    ?
?   ? MainWindow  ? ? BillingView   ? ? CustomerView    ?    ?
?   ??????????????? ????????????????? ???????????????????    ?
???????????????????????????????????????????????????????????????
           ?                ?                  ?
           ?        calls (DTOs only)          ?
           ?                ?                  ?
???????????????????????????????????????????????????????????????
?                   APPLICATION SERVICES                       ?
?   Business Logic — Orchestration — Validation                ?
?   ????????????????? ??????????????????? ??????????????????? ?
?   ?BillingService ? ?CustomerService  ? ? BackupService   ? ?
?   ?               ? ?                 ? ?                 ? ?
?   ? create_bill() ? ? get_customer()  ? ? create_backup() ? ?
?   ? calculate_*() ? ? get_summary()   ? ? restore()       ? ?
?   ????????????????? ??????????????????? ??????????????????? ?
???????????????????????????????????????????????????????????????
            ?                  ?                   ?
            ?          uses (ORM objects)          ?
            ?                  ?                   ?
???????????????????????????????????????????????????????????????
?                      REPOSITORIES                            ?
?   Data Access — CRUD Operations — Queries                    ?
?   ?????????????????? ???????????????????? ????????????????? ?
?   ? BillRepository ? ?CustomerRepository? ?StaffRepository? ?
?   ?????????????????? ???????????????????? ????????????????? ?
???????????????????????????????????????????????????????????????
             ?                  ?                   ?
             ?           SQLAlchemy ORM             ?
             ?                  ?                   ?
???????????????????????????????????????????????????????????????
?                       ORM MODELS                             ?
?   Bill, BillItem, Customer, Staff, Service, Setting          ?
???????????????????????????????????????????????????????????????
                           ?
                           ?
???????????????????????????????????????????????????????????????
?                    INFRASTRUCTURE                            ?
?   ???????????? ??????????????? ???????????? ??????????????  ?
?   ? SQLite   ? ?PDFGenerator ? ? CloudDrive? ?  Crypto    ?  ?
?   ? Database ? ?             ? ? (GDrive)  ? ? (AES)      ?  ?
?   ???????????? ??????????????? ???????????? ??????????????  ?
???????????????????????????????????????????????????????????????
```

### 3.2 Layer Responsibilities

| Layer | Responsibility | Allowed Dependencies |
|-------|----------------|---------------------|
| **UI** | Render data, capture input, show messages | Services, DTOs, Exceptions |
| **Services** | Business logic, validation, orchestration | Repositories, Infrastructure, DTOs |
| **Repositories** | CRUD operations, queries | Models, Database |
| **Infrastructure** | External systems (PDF, cloud, crypto) | Nothing (adapters) |
| **Models** | Data structure definition | SQLAlchemy only |
| **DTOs** | Data transfer between layers | Nothing (plain data) |

---

## 4. PROJECT STRUCTURE

### 4.1 Target Directory Layout

```
billing_system/
?
??? app/
?   ??? __init__.py
?   ?
?   ??? ui/                              # UI LAYER
?   ?   ??? __init__.py
?   ?   ??? main_window.py               # Main application window
?   ?   ??? billing_view.py              # Bill creation UI
?   ?   ??? customer_view.py             # Customer management UI
?   ?   ??? settings_view.py             # Settings UI
?   ?   ??? export_view.py               # Export dialog UI
?   ?   ??? dialogs/                     # Reusable dialog components
?   ?       ??? __init__.py
?   ?       ??? customer_dialog.py
?   ?       ??? staff_dialog.py
?   ?       ??? service_dialog.py
?   ?
?   ??? services/                        # APPLICATION SERVICES
?   ?   ??? __init__.py
?   ?   ??? billing_service.py           # Bill creation, calculation
?   ?   ??? customer_service.py          # Customer operations
?   ?   ??? staff_service.py             # Staff operations
?   ?   ??? service_catalog.py           # Service/catalog management
?   ?   ??? settings_service.py          # Settings management
?   ?   ??? backup_service.py            # Backup orchestration
?   ?   ??? restore_service.py           # Restore orchestration
?   ?   ??? report_service.py            # Reports & exports
?   ?   ??? notification_service.py      # WhatsApp, email
?   ?
?   ??? repositories/                    # DATA ACCESS LAYER
?   ?   ??? __init__.py
?   ?   ??? base_repository.py           # Base class with common ops
?   ?   ??? bill_repository.py
?   ?   ??? customer_repository.py
?   ?   ??? staff_repository.py
?   ?   ??? service_repository.py
?   ?   ??? settings_repository.py
?   ?
?   ??? models/                          # ORM MODELS
?   ?   ??? __init__.py                  # Re-exports all models
?   ?   ??? entities.py                  # All ORM model classes
?   ?
?   ??? dto/                             # DATA TRANSFER OBJECTS
?   ?   ??? __init__.py
?   ?   ??? bill_dto.py                  # BillData, BillItemData
?   ?   ??? customer_dto.py              # CustomerData, CustomerSummary
?   ?   ??? backup_dto.py                # BackupInfo, RestoreResult
?   ?
?   ??? exceptions/                      # CUSTOM EXCEPTIONS
?   ?   ??? __init__.py
?   ?   ??? validation_errors.py
?   ?   ??? business_errors.py
?   ?   ??? infrastructure_errors.py
?   ?
?   ??? infrastructure/                  # EXTERNAL CONCERNS
?   ?   ??? __init__.py
?   ?   ??? database.py                  # Session management
?   ?   ??? pdf_generator.py             # PDF creation only
?   ?   ??? cloud_drive.py               # Google Drive adapter
?   ?   ??? crypto.py                    # Encryption/decryption
?   ?   ??? whatsapp_client.py           # WhatsApp API adapter
?   ?
?   ??? config/                          # CONFIGURATION
?       ??? __init__.py
?       ??? constants.py                 # App constants
?       ??? settings.json                # User settings (runtime)
?
??? data/                                # LOCAL STORAGE
?   ??? salon_billing.db                 # SQLite database
?   ??? receipts/                        # Generated PDFs
?
??? backups/                             # Local backup storage
?
??? logs/                                # Application logs
?
??? tests/                               # TEST SUITE
?   ??? __init__.py
?   ??? conftest.py                      # Pytest fixtures
?   ??? unit/
?   ?   ??? __init__.py
?   ?   ??? test_billing_service.py
?   ?   ??? test_customer_service.py
?   ?   ??? test_repositories.py
?   ??? integration/
?   ?   ??? __init__.py
?   ?   ??? test_backup_restore.py
?   ?   ??? test_pdf_generation.py
?   ??? e2e/
?       ??? __init__.py
?       ??? test_billing_flow.py
?
??? docs/                                # DOCUMENTATION
?   ??? architecture.md
?   ??? api.md
?   ??? setup.md
?
??? scripts/                             # UTILITY SCRIPTS
?   ??? migrate.py
?   ??? seed_data.py
?
??? main.py                              # Application entry point
??? requirements.txt                     # Dependencies
??? requirements-dev.txt                 # Dev dependencies
??? pyproject.toml                       # Project config
??? .env.example                         # Environment template
??? .gitignore
??? PLAN.md                              # This file
??? README.md
```

### 4.2 File Mapping (Old ? New)

| Current File | Target Location | Action |
|--------------|-----------------|--------|
| `gui_main.py` | `ui/main_window.py` | Refactor |
| `gui_billing.py` | `ui/billing_view.py` + `services/billing_service.py` | **Split** |
| `gui_customers.py` | `ui/customer_view.py` + `services/customer_service.py` | **Split** |
| `gui_settings.py` | `ui/settings_view.py` | Refactor |
| `gui_export.py` | `ui/export_view.py` | Keep (already clean) |
| `models.py` | `models/entities.py` | Move |
| `database.py` | `infrastructure/database.py` | Move |
| `pdf_generator.py` | `infrastructure/pdf_generator.py` | Refactor |
| `backup_service.py` | `services/backup_service.py` | Enhance |
| `export_service.py` | `services/report_service.py` | Rename |
| `settings_service.py` | `services/settings_service.py` | Keep |
| `whatsapp_client.py` | `infrastructure/whatsapp_client.py` | Move |
| `constants.py` | `config/constants.py` | Move |
| `utils.py` | `infrastructure/logging.py` | Move + Rename |

---

## 5. IMPLEMENTATION PHASES

### 5.1 Phase Overview

| Phase | Focus | Duration | Dependencies | Status |
|-------|-------|----------|--------------|--------|
| **Phase 1** | Repository Layer | 2-3 days | None | ? COMPLETE |
| **Phase 2** | Service Layer (Core) | 3-4 days | Phase 1 | ?? IN PROGRESS |
| **Phase 3** | UI Refactoring | 3-4 days | Phase 2 | ? Pending |
| **Phase 4** | Backup Infrastructure | 2-3 days | Phase 3 | ? Pending |
| **Phase 5** | Testing & Validation | 2-3 days | Phase 4 | ? Pending |

**Total Estimated Time: 12-17 days**

### 5.2 Phase 1: Repository Layer (Foundation) ? COMPLETE

**Objective:** Create clean data access with no business logic

**Deliverables:**
```
repositories/
??? __init__.py           ?
??? base_repository.py    ?
??? bill_repository.py    ?
??? customer_repository.py ?
??? staff_repository.py   ?
??? service_repository.py ?
??? settings_repository.py ?
```

**Exit Criteria:**
- ? All repositories implement CRUD operations
- ? No business logic in repositories
- ? Unit tests pass for all repositories
- ? 80%+ code coverage

### 5.3 Phase 2: Service Layer (Business Logic) ?? IN PROGRESS

**Objective:** Extract all business logic from UI

**Deliverables:**
```
services/
??? __init__.py           ?
??? billing_service.py    ?
??? customer_service.py   ?? IN PROGRESS
??? staff_service.py      ?
??? notification_service.py ?
??? ...

dto/
??? __init__.py           ?
??? bill_dto.py           ?
??? customer_dto.py       ?
??? ...

exceptions/
??? __init__.py           ?
??? validation_errors.py  ?
??? business_errors.py    ?
```

**Exit Criteria:**
- All business rules in services
- DTOs used for data transfer
- Custom exceptions for error handling
- Unit tests pass with 90%+ coverage

### 5.4 Phase 3: UI Refactoring

**Objective:** Make UI presentation-only

**Deliverables:**
```
ui/
??? __init__.py
??? main_window.py
??? billing_view.py
??? customer_view.py
??? settings_view.py
??? export_view.py
??? dialogs/
    ??? __init__.py
    ??? customer_dialog.py
    ??? staff_dialog.py
    ??? service_dialog.py
```

**Exit Criteria:**
- Zero `db_session()` calls in UI
- Zero ORM imports for queries in UI
- All UI uses services
- Manual testing passes

### 5.5 Phase 4: Backup Infrastructure

**Objective:** Add encryption and cloud support

**Deliverables:**
```
infrastructure/
??? cloud_drive.py      # Google Drive adapter
??? crypto.py           # AES encryption

services/
??? backup_service.py   # Enhanced
??? restore_service.py  # New
```

**Exit Criteria:**
- Backup creates encrypted archives
- Restore validates and recovers data
- Cloud upload/download works
- Integration tests pass

### 5.6 Phase 5: Testing & Validation

**Objective:** Comprehensive test coverage

**Deliverables:**
```
tests/
??? conftest.py
??? unit/
?   ??? test_billing_service.py
?   ??? test_customer_service.py
?   ??? test_repositories.py
??? integration/
?   ??? test_backup_restore.py
?   ??? test_pdf_generation.py
??? e2e/
    ??? test_billing_flow.py
```

**Exit Criteria:**
- 80%+ overall code coverage
- All critical paths tested
- E2E tests for main workflows
- Performance benchmarks established

---

## 6. DETAILED STEP-BY-STEP PLAN

### 6.1 PHASE 1: Repository Layer ? COMPLETE

All repositories implemented with:
- Base repository pattern
- Session factory injection
- CRUD operations
- Search/filter methods
- No business logic

### 6.2 PHASE 2: Service Layer ?? IN PROGRESS

#### Step 2.1: Create DTOs ? COMPLETE

**File:** `app/dto/bill_dto.py` — Implemented
**File:** `app/dto/customer_dto.py` — Implemented

#### Step 2.2: Create Business Exceptions ? COMPLETE

**File:** `app/exceptions/business_errors.py` — Implemented

#### Step 2.3: Create Billing Service ? COMPLETE

**File:** `app/services/billing_service.py` — Implemented

**Business Rules Encoded:**

| Rule | Location | Validation |
|------|----------|------------|
| Discount ? subtotal | `calculate_discount()` | Raises `DiscountExceedsSubtotalError` |
| Discount % ? 100 | `calculate_discount()` | Raises `ValidationError` |
| Tax % 0-100 | `calculate_tax()` | Raises `ValidationError` |
| Total ? 0 | `create_bill()` | Raises `NegativeTotalError` |
| At least 1 item | `_validate_bill_inputs()` | Raises `InsufficientDataError` |
| Customer exists | `create_bill()` | Raises `CustomerNotFoundError` |
| Staff exists | `create_bill()` | Raises `StaffNotFoundError` |

#### Step 2.4: Create Customer Service ?? IN PROGRESS

**File:** `app/services/customer_service.py`

**Methods:**

| Method | Returns | Purpose |
|--------|---------|---------|
| `get_customer(id)` | `CustomerData` | Fetch single customer |
| `search_customers(term)` | `List[CustomerData]` | Search by name/phone |
| `get_customer_summary(id)` | `CustomerSummary` | Customer with statistics |
| `create_customer(name, phone, notes)` | `CustomerData` | Create new customer |
| `update_customer(id, data)` | `CustomerData` | Update existing customer |
| `get_customer_bills(id)` | `List[BillData]` | Customer's bill history |

#### Step 2.5: Create Notification Service ? PENDING

**File:** `app/services/notification_service.py`

---

## 7. CODING STANDARDS & RULES

### 7.1 Absolute Architecture Rules (NEVER VIOLATE)

| Rule | Description | Consequence |
|------|-------------|-------------|
| **R1** | UI classes NEVER import `db_session` | Breaks testability |
| **R2** | UI classes NEVER import ORM models for queries | Tight coupling |
| **R3** | Services NEVER import PyQt6 | Can't unit test |
| **R4** | Repositories contain NO business logic | Wrong responsibility |
| **R5** | All business rules live in Services | Single source of truth |
| **R6** | Infrastructure modules are stateless adapters | Side-effect free |
| **R7** | DTOs are immutable data containers | Thread safety |

### 7.2 Import Rules

**? ALLOWED in UI:**
```python
from app.services.billing_service import BillingService
from app.dto.bill_dto import BillData
from app.exceptions.business_errors import ValidationError
```

**? FORBIDDEN in UI:**
```python
from app.database import db_session        # NEVER
from app.models import Bill, Customer      # NEVER for queries
from sqlalchemy.orm import Session         # NEVER
```

**? ALLOWED in Services:**
```python
from app.repositories.bill_repository import BillRepository
from app.models import Bill                # For type hints only
from app.infrastructure.pdf_generator import PDFGenerator
```

**? FORBIDDEN in Services:**
```python
from PyQt6.QtWidgets import QMessageBox    # NEVER
from app.database import db_session        # Use repository
```

### 7.3 Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Service class | `*Service` | `BillingService` |
| Repository class | `*Repository` | `BillRepository` |
| DTO class | `*Data`, `*Info`, `*Result` | `BillData`, `BackupInfo` |
| Exception class | `*Error` | `ValidationError` |
| UI class | `*View`, `*Window`, `*Dialog` | `BillingView` |
| Private method | `_method_name` | `_calculate_tax` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_DISCOUNT_PERCENT` |
| Variables/functions | `snake_case` | `calculate_total` |

### 7.4 Error Handling Pattern

```python
# Services raise typed exceptions:
raise ValidationError("Discount cannot exceed subtotal")

# UI catches and displays:
try:
    bill = self.billing_service.create_bill(...)
except ValidationError as e:
    QMessageBox.warning(self, "Validation Error", str(e))
except BillingError as e:
    QMessageBox.critical(self, "Error", str(e))
```

---

## 8. PYTHON ENGINEERING STANDARDS

### 8.1 Core Python Philosophy (PEP 20)

Follow the **Zen of Python** principles:

- **Explicit is better than implicit** — No hidden behavior
- **Simple is better than complex** — Avoid over-engineering
- **Readability counts** — Code is read more than written
- **Errors should never pass silently** — Always handle or propagate
- **There should be one obvious way to do it** — Consistency

### 8.2 Mandatory PEP Standards

| PEP | Description | Enforcement |
|-----|-------------|-------------|
| **PEP 8** | Code formatting and styling | `black`, `flake8` |
| **PEP 20** | Zen of Python philosophy | Code review |
| **PEP 257** | Docstring conventions | `pydocstyle` |
| **PEP 484** | Type hinting standards | `mypy` |
| **PEP 526** | Variable annotations | `mypy` |
| **PEP 544** | Protocol typing | For interfaces |

### 8.3 Naming Convention Standards

| Element | Convention | Example |
|---------|------------|---------|
| Variables | `snake_case`, descriptive | `customer_name`, `total_amount` |
| Functions | `snake_case`, verb-based | `calculate_total()`, `get_customer()` |
| Classes | `PascalCase` | `BillingService`, `CustomerData` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_DISCOUNT_PERCENT` |
| Private | `_single_underscore` | `_validate_input()` |
| Module-private | `__double_underscore` | Rare, avoid |

**? Avoid:**
- Single-letter variables (except `i`, `j` in loops)
- Abbreviations unless universally understood
- Hungarian notation

### 8.4 Function Design Standards

| Metric | Ideal | Maximum | Action if Exceeded |
|--------|-------|---------|-------------------|
| Lines | 5-25 | 40 | Extract helper methods |
| Parameters | 3-4 | 5 | Use dataclass/object |
| Cyclomatic complexity | ?5 | 10 | Refactor logic |
| Nesting depth | ?2 | 3 | Early returns |

### 8.5 Type Hints (Mandatory)

**All public functions must have type hints:**

```python
from typing import List, Optional, Dict, Any
from decimal import Decimal

def create_bill(
    self,
    customer_id: int,
    staff_id: int,
    items: List[BillItemInput],
    options: BillOptions,
) -> BillData:
    ...
```

### 8.6 Documentation Standards

**Module-level docstring (required):**
```python
"""
Billing service for bill creation and management.

This service contains all business logic for billing operations,
including calculations, validation, and persistence orchestration.
"""
```

**Class docstring (required):**
```python
class BillingService:
    """
    Service for bill creation and calculation.
    
    Handles all billing business logic including:
    - Bill creation with items
    - Price calculations (subtotal, discount, tax, total)
    - Validation of business rules
    - Persistence orchestration
    
    Attributes:
        bill_repo: Repository for bill data access.
        customer_repo: Repository for customer data access.
    """
```

**Function docstring (required for public functions):**
```python
def calculate_tax(self, amount: Decimal, tax_percent: Decimal) -> Decimal:
    """
    Calculate tax amount.
    
    Args:
        amount: Taxable amount.
        tax_percent: Tax percentage (0-100).
        
    Returns:
        Calculated tax amount.
        
    Raises:
        ValidationError: If tax_percent is not between 0 and 100.
    """
```

### 8.7 Error Handling Standards

**? DO:**
```python
# Catch specific exceptions
try:
    result = self._billing.create_bill(...)
except ValidationError as e:
    logger.warning(f"Validation failed: {e}")
    raise
except DatabaseError as e:
    logger.error(f"Database error: {e}")
    raise BillingError("Unable to save bill") from e
```

**? DON'T:**
```python
# Never use bare except
try:
    result = self._billing.create_bill(...)
except:  # ? NEVER
    pass  # ? NEVER silently ignore
```

### 8.8 Logging Standards

**? NEVER use `print()` in production:**
```python
# ? WRONG
print("Bill created")

# ? CORRECT
import logging
logger = logging.getLogger(__name__)
logger.info("Bill created: %s", bill.id)
```

**Log levels:**

| Level | When to Use |
|-------|-------------|
| `DEBUG` | Development info, variable values |
| `INFO` | Normal operations, milestones |
| `WARNING` | Unexpected but recoverable |
| `ERROR` | Operation failed |
| `CRITICAL` | System-level failure |

### 8.9 Configuration Management

**? NEVER hardcode:**
```python
# ? WRONG
API_KEY = "sk-12345"
DATABASE_URL = "sqlite:///prod.db"

# ? CORRECT
import os
API_KEY = os.getenv("API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///default.db")
```

### 8.10 Pythonic Code Standards

**? Use comprehensions:**
```python
# ? Good
items = [item.line_total for item in bill.items]
active_staff = {s.id: s.name for s in staff if s.active}
```

**? Use built-in functions:**
```python
total = sum(item.amount for item in items)
has_pending = any(bill.status == "Pending" for bill in bills)
all_paid = all(bill.status == "Paid" for bill in bills)
```

**? Use generators for large datasets:**
```python
def get_all_bills(self):
    for bill in self._query_bills():
        yield self._to_dto(bill)
```

### 8.11 Security Standards

- **Validate all external inputs**
- **Never trust user input**
- **Sanitize database queries** (SQLAlchemy handles this)
- **Use secrets manager for production**
- **Never log sensitive data** (passwords, tokens)

### 8.12 Code Review Standards

Before merging code, verify:

- [ ] Naming is clear and consistent
- [ ] No duplicated logic
- [ ] All tests passing
- [ ] Lint checks passing (`flake8`, `black`)
- [ ] Type checks passing (`mypy`)
- [ ] Documentation updated
- [ ] No hardcoded secrets
- [ ] Error handling is appropriate

### 8.13 Senior Engineering Golden Rules

> **Code should be understandable within 30 seconds**

> **Another developer should modify it safely without explanation**

> **Code should be testable, replaceable, and modular**

---

## 9. FILE SIZE & COMPLEXITY LIMITS

### 9.1 Maximum Lines Per File

| File Type | Max Lines | Rationale |
|-----------|-----------|-----------|
| Service | 300 | Split if exceeds |
| Repository | 200 | Should be simple CRUD |
| UI View | 400 | Complex but acceptable |
| DTO | 100 | Data only |
| Test file | 500 | More verbose is OK |
| Config | 50 | Simple values |

### 9.2 Method Complexity

| Metric | Ideal | Maximum | Action |
|--------|-------|---------|--------|
| Lines per method | 15 | 40 | Extract helpers |
| Parameters | 3 | 5 | Use parameter object |
| Cyclomatic complexity | 5 | 10 | Refactor |
| Nesting depth | 2 | 3 | Early returns |

### 9.3 Class Limits

| Metric | Maximum |
|--------|---------|
| Methods per class | 15 |
| Constructor dependencies | 5 |
| Public methods | 10 |
| Lines of code | 300 |

---

## 10. TESTING STRATEGY

### 10.1 Test Coverage Targets

| Layer | Coverage Target | Focus |
|-------|-----------------|-------|
| Services | **90%** | All business logic |
| Repositories | 80% | CRUD operations |
| Infrastructure | 70% | Integration points |
| UI | 50% | Critical flows only |

### 10.2 Test Types

| Type | Location | Purpose | Framework |
|------|----------|---------|-----------|
| Unit | `tests/unit/` | Isolated logic | `pytest` |
| Integration | `tests/integration/` | Component interaction | `pytest` |
| E2E | `tests/e2e/` | Full user flows | `pytest-qt` |

### 10.3 Test Naming Convention

```python
def test_<method>_<scenario>_<expected>():
    """
    Examples:
    test_calculate_discount_percent_over_100_raises_error
    test_create_bill_with_valid_data_returns_bill
    test_restore_from_corrupted_backup_fails_gracefully
    """
```

### 10.4 Test Structure (AAA Pattern)

```python
def test_calculate_discount_flat_within_subtotal_returns_discount():
    """Flat discount within subtotal should return discount value."""
    # Arrange
    service = BillingService(mock_repos...)
    subtotal = Decimal("100")
    discount_value = Decimal("20")
    
    # Act
    result = service.calculate_discount(subtotal, "flat", discount_value)
    
    # Assert
    assert result == Decimal("20")
```

---

## 11. MIGRATION CHECKLIST

### 11.1 Pre-Migration

- [x] Create full database backup
- [x] Document current functionality
- [x] Set up test environment
- [x] Create feature branch (`v3`)
- [x] Install dev dependencies

### 11.2 Phase 1 Checklist (Repository Layer) ? COMPLETE

- [x] Create `app/repositories/` directory
- [x] Implement `base_repository.py`
- [x] Implement `customer_repository.py`
- [x] Implement `bill_repository.py`
- [x] Implement `staff_repository.py`
- [x] Implement `service_repository.py`
- [x] Implement `settings_repository.py`
- [x] Write repository unit tests
- [x] All tests pass
- [x] Code review completed

### 11.3 Phase 2 Checklist (Service Layer) ?? IN PROGRESS

- [x] Create `app/dto/` directory
- [x] Create `app/exceptions/` directory
- [x] Implement `bill_dto.py`
- [x] Implement `customer_dto.py`
- [x] Implement `business_errors.py`
- [x] Implement `billing_service.py`
- [ ] Implement `customer_service.py`
- [ ] Implement `staff_service.py`
- [ ] Implement `notification_service.py`
- [ ] Write service unit tests
- [ ] All tests pass (90%+ coverage)
- [ ] Code review completed

### 11.4 Phase 3 Checklist (UI Refactoring)

- [ ] Create `app/ui/` directory
- [ ] Migrate `gui_billing.py` ? `ui/billing_view.py`
- [ ] Migrate `gui_customers.py` ? `ui/customer_view.py`
- [ ] Migrate `gui_settings.py` ? `ui/settings_view.py`
- [ ] Create `ui/dialogs/` with components
- [ ] Remove ALL `db_session` from UI
- [ ] Wire dependency injection in `main_window.py`
- [ ] Manual UI testing
- [ ] All tests pass
- [ ] Code review completed

### 11.5 Phase 4 Checklist (Backup Infrastructure)

- [ ] Add `cryptography` to requirements
- [ ] Add `google-api-python-client` to requirements
- [ ] Implement `infrastructure/crypto.py`
- [ ] Implement `infrastructure/cloud_drive.py`
- [ ] Enhance `services/backup_service.py`
- [ ] Implement `services/restore_service.py`
- [ ] Write backup/restore integration tests
- [ ] Manual backup/restore testing
- [ ] All tests pass
- [ ] Code review completed

### 11.6 Phase 5 Checklist (Testing & Validation)

- [ ] Complete unit test suite
- [ ] Complete integration test suite
- [ ] E2E tests for critical flows
- [ ] Performance benchmarks
- [ ] Security review
- [ ] Documentation complete
- [ ] All tests pass
- [ ] 80%+ overall coverage

### 11.7 Post-Migration

- [ ] Remove old `gui_*.py` files
- [ ] Update all imports
- [ ] Update README
- [ ] Update CI/CD pipeline
- [ ] Final integration testing
- [ ] Create release notes
- [ ] Tag release (`v3.0.0`)

---

## 12. RISK MITIGATION

### 12.1 Risk Matrix

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Data loss during migration | Low | **Critical** | Backup before each phase |
| Breaking existing functionality | Medium | High | Incremental changes, feature flags |
| Scope creep | High | Medium | Strict phase boundaries |
| Performance regression | Low | Medium | Benchmark critical paths |
| Incomplete testing | Medium | High | Coverage requirements |
| Team unfamiliarity | Medium | Medium | Documentation, pairing |

### 12.2 Rollback Strategy

Each phase should be independently deployable:

```
Current State (master)
    ? Phase 1 (can rollback to master)
    ? Phase 2 (can rollback to Phase 1)
    ? Phase 3 (can rollback to Phase 2)
    ? Phase 4 (can rollback to Phase 3)
    ? Phase 5 (can rollback to Phase 4)
Final State (v3.0.0 tag)
```

### 12.3 Feature Flags (Optional)

For gradual rollout:

```python
import os

USE_NEW_BILLING_SERVICE = os.getenv("USE_NEW_BILLING", "false") == "true"

if USE_NEW_BILLING_SERVICE:
    bill = billing_service.create_bill(...)
else:
    # Legacy path
    bill = self._legacy_create_bill(...)
```

---

## 13. TOOLING & QUALITY GATES

### 13.1 Required Tools

| Tool | Purpose | Config File |
|------|---------|-------------|
| `black` | Code formatting | `pyproject.toml` |
| `isort` | Import sorting | `pyproject.toml` |
| `flake8` | Linting | `.flake8` |
| `pylint` | Advanced linting | `.pylintrc` |
| `mypy` | Type checking | `mypy.ini` |
| `pytest` | Testing | `pytest.ini` |
| `bandit` | Security checks | `.bandit` |

### 13.2 Pre-commit Hooks

**File:** `.pre-commit-config.yaml`

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
      - id: flake8

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

### 13.3 Development Dependencies

**File:** `requirements-dev.txt`

```
# Testing
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-qt>=4.2.0
pytest-mock>=3.12.0

# Formatting
black>=23.12.0
isort>=5.13.0

# Linting
flake8>=7.0.0
pylint>=3.0.0
pydocstyle>=6.3.0

# Type checking
mypy>=1.8.0
types-requests>=2.31.0

# Security
bandit>=1.7.0

# Pre-commit
pre-commit>=3.6.0
```

### 13.4 pyproject.toml Configuration

```toml
[tool.black]
line-length = 88
target-version = ['py311']
include = '\.pyi?$'

[tool.isort]
profile = "black"
line_length = 88
known_first_party = ["app"]

[tool.mypy]
python_version = "3.11"
strict = true
ignore_missing_imports = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
addopts = "-v --tb=short"

[tool.coverage.run]
source = ["app"]
omit = ["app/ui/*"]

[tool.coverage.report]
fail_under = 80
show_missing = true
```

---

## ?? SUMMARY

### What to Do

1. **Create repositories first** — clean data access foundation ?
2. **Extract business logic to services** — single source of truth ??
3. **Make UI dumb** — presentation only ?
4. **Add encryption** — protect user data ?
5. **Add cloud backup** — disaster recovery ?
6. **Test everything** — maintain quality ?
7. **Follow Python standards** — maintainable code ?

### What NOT to Do

| ? Don't | Why |
|----------|-----|
| Skip repository layer | Creates tight coupling |
| Put validation in UI | Duplicates logic |
| Import PyQt in services | Breaks testability |
| Skip encryption | Security risk |
| Make cloud mandatory | Breaks offline use |
| Big-bang rewrite | High risk |
| Use bare `except:` | Hides errors |
| Use `print()` | Not production-ready |
| Hardcode secrets | Security vulnerability |
| Skip type hints | Reduces maintainability |

### Success Criteria

- [ ] Zero `db_session` calls in UI code
- [ ] All business logic in services with >90% test coverage
- [ ] Backup/restore works with encryption
- [ ] Cloud backup optional but functional
- [ ] All existing features still work
- [ ] Build passes, no regressions
- [ ] Code passes all linters and type checks
- [ ] Documentation is complete and accurate

---

## APPENDIX A: Quick Reference Card

### Layer Import Rules

```
???????????????????????????????????????????????????
? UI Layer                                        ?
? ? Can import: services, dto, exceptions        ?
? ? Cannot import: db_session, models (queries)  ?
???????????????????????????????????????????????????
? Service Layer                                   ?
? ? Can import: repositories, dto, infrastructure?
? ? Cannot import: PyQt6, UI components          ?
???????????????????????????????????????????????????
? Repository Layer                                ?
? ? Can import: models, database                 ?
? ? Cannot import: services, UI, business logic  ?
???????????????????????????????????????????????????
? Infrastructure Layer                            ?
? ? Can import: external libraries only          ?
? ? Cannot import: services, repositories, UI    ?
???????????????????????????????????????????????????
```

### File Size Limits

```
Service:     ?300 lines
Repository:  ?200 lines
UI View:     ?400 lines
DTO:         ?100 lines
Test:        ?500 lines
```

### Method Limits

```
Parameters:  ?5 (use object if more)
Lines:       ?40 (ideal: 15-25)
Nesting:     ?3 levels
Complexity:  ?10 cyclomatic
```

---

## APPENDIX B: Git Workflow

### Branch Strategy

```bash
# Create v3 branch from master
git checkout master
git pull origin master
git checkout -b v3

# Work on phases
git add .
git commit -m "Phase 1: Repository layer complete"
git push origin v3

# When all phases complete
git tag -a v3.0.0 -m "Clean architecture refactor complete"
git push origin v3 --tags
```

### Commit Message Format

```
<type>(<scope>): <description>

Types:
- feat: New feature
- fix: Bug fix
- refactor: Code refactoring
- test: Adding tests
- docs: Documentation
- chore: Maintenance

Examples:
feat(repositories): add base repository pattern
refactor(billing): extract business logic to service
test(billing): add unit tests for discount calculation
```

---

*Document generated for Salon Billing System refactoring project.*  
*Version: 3.0 | Branch: v3 | Last updated: February 2026*
