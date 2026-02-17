# ?? File Structure & Purpose Map
**Salon Billing System - Complete File Reference**

---

## ??? Directory Tree

```
?? Salon Billing System/
?
??? ?? main.py                          # Application entry point - wires dependencies
?
??? ?? app/                             # Main application package
?   ?
?   ??? ?? ui/                          # UI LAYER - PyQt6 widgets
?   ?   ??? ?? __init__.py              # Exports all UI components
?   ?   ??? ?? main_window.py           # Main window with navigation buttons
?   ?   ??? ?? billing_view.py          # Bill creation dialog with services table
?   ?   ??? ?? customer_view.py         # Customer list and management window
?   ?   ??? ?? settings_view.py         # Settings configuration tabs
?   ?   ??? ?? export_view.py           # Export dialog for Excel reports
?   ?   ?
?   ?   ??? ?? dialogs/                 # Reusable form dialogs
?   ?       ??? ?? __init__.py          # Exports dialog classes
?   ?       ??? ?? customer_dialog.py   # Add/edit customer form
?   ?       ??? ?? staff_dialog.py      # Add/edit staff form
?   ?       ??? ?? service_dialog.py    # Add/edit service form
?   ?
?   ??? ?? services/                    # SERVICE LAYER - Business logic
?   ?   ??? ?? __init__.py              # Exports all services
?   ?   ??? ?? billing_service.py       # Bill calculations, creation, PDF gen
?   ?   ??? ?? customer_service.py      # Customer CRUD + summary stats
?   ?   ??? ?? staff_service.py         # Staff management operations
?   ?   ??? ?? service_catalog.py       # Service/category management
?   ?   ??? ?? settings_service.py      # App settings read/write
?   ?   ??? ?? notification_service.py  # WhatsApp message sending
?   ?   ??? ?? backup_service.py        # Database backup creation
?   ?   ??? ?? restore_service.py       # Database restore operations
?   ?   ??? ?? report_service.py        # Excel/PDF report generation
?   ?
?   ??? ?? repositories/                # REPOSITORY LAYER - Data access
?   ?   ??? ?? __init__.py              # Exports all repositories
?   ?   ??? ?? base_repository.py       # Abstract base with common CRUD
?   ?   ??? ?? bill_repository.py       # Bill queries and persistence
?   ?   ??? ?? customer_repository.py   # Customer queries and persistence
?   ?   ??? ?? staff_repository.py      # Staff queries and persistence
?   ?   ??? ?? service_repository.py    # Service queries and persistence
?   ?   ??? ?? settings_repository.py   # Settings key-value storage
?   ?
?   ??? ?? dto/                         # DATA TRANSFER OBJECTS
?   ?   ??? ?? __init__.py              # Exports all DTOs
?   ?   ??? ?? bill_dto.py              # BillData, BillItemInput, BillOptions
?   ?   ??? ?? customer_dto.py          # CustomerData, CustomerSummary
?   ?   ??? ?? backup_dto.py            # BackupInfo, RestoreResult
?   ?
?   ??? ?? exceptions/                  # CUSTOM EXCEPTIONS
?   ?   ??? ?? __init__.py              # Exports all exceptions
?   ?   ??? ?? business_errors.py       # Domain rule violations
?   ?   ??? ?? validation_errors.py     # Input validation failures
?   ?
?   ??? ?? infrastructure/              # INFRASTRUCTURE LAYER - External I/O
?   ?   ??? ?? __init__.py              # Exports db_session, init_db, logger
?   ?   ??? ?? database.py              # SQLAlchemy engine and session factory
?   ?   ??? ?? logging.py               # Logger setup with file handler
?   ?   ??? ?? pdf_generator.py         # ReportLab PDF receipt generation
?   ?   ??? ?? whatsapp_client.py       # Meta WhatsApp Cloud API client
?   ?   ??? ?? cloud_drive.py           # Google Drive adapter (stub)
?   ?   ??? ?? crypto.py                # AES encryption adapter (stub)
?   ?
?   ??? ?? __init__.py                  # Package version (__version__)
?   ??? ?? models.py                    # SQLAlchemy ORM models
?   ??? ?? constants.py                 # App-wide constants and paths
?   ??? ?? csv_service_importer.py      # CSV import/export for services
?   ??? ?? migrate_service_schema.py    # DB migration for service fields
?   ??? ?? migrate_bill_receipt_fields.py # DB migration for bill fields
?
??? ?? tests/                           # TEST SUITE
?   ??? ?? unit/                        # Unit tests (isolated)
?   ?   ??? ?? __init__.py
?   ?   ??? ?? test_billing_service.py  # Tests for billing calculations
?   ?   ??? ?? test_customer_service.py # Tests for customer operations
?   ?
?   ??? ?? integration/                 # Integration tests
?   ?   ??? ?? __init__.py
?   ?   ??? ?? test_backup_restore.py   # Backup/restore flow (stub)
?   ?   ??? ?? test_pdf_generation.py   # PDF generation (stub)
?   ?
?   ??? ?? e2e/                         # End-to-end tests
?   ?   ??? ?? __init__.py
?   ?   ??? ?? test_billing_flow.py     # Full billing workflow (stub)
?   ?
?   ??? ?? test_csv_import.py           # CSV import functionality test
?
??? ?? scripts/                         # Build/utility scripts
?   ??? ?? build_exe.bat                # PyInstaller build script
?
??? ?? .github/workflows/               # CI/CD
?   ??? ?? release.yml                  # GitHub Actions release workflow
?
??? ?? logs/                            # Runtime logs (generated)
?   ??? ?? app.log                      # Application log file
?
??? ?? backups/                         # Database backups (generated)
??? ?? receipts/                        # PDF receipts (generated)
??? ?? releases/                        # Distribution packages
?
??? ?? requirements.txt                 # Production dependencies
??? ?? requirements-dev.txt             # Development dependencies
??? ?? pyproject.toml                   # Project config + tool settings
??? ?? pytest.ini                       # Pytest configuration
??? ?? mypy.ini                         # Type checking config
??? ?? .flake8                          # Linting config
??? ?? .pylintrc                        # Pylint config
??? ?? .pre-commit-config.yaml          # Pre-commit hooks
??? ?? SalonBillingSystem.spec          # PyInstaller build spec
??? ?? setup.py                         # Package setup (for pip install)
??? ?? .env.example                     # Environment variable template
??? ?? .gitignore                       # Git ignore patterns
??? ?? .gitattributes                   # Git attributes
??? ?? .dockerignore                    # Docker ignore patterns
?
??? ?? README.md                        # Project overview and setup guide
??? ?? PLAN.md                          # Clean architecture refactor plan
??? ?? CHANGELOG.md                     # Version history
??? ?? WORKSPACE_AUDIT.md               # Architecture analysis (this session)
??? ?? UNREQUIRED_FILES.md              # Files to clean up (this session)
??? ?? FILE_STRUCTURE_MAP.md            # This file
```

---

## ?? Quick Reference Table

### Core Application Files

| File | Layer | Purpose |
|------|-------|---------|
| `main.py` | Entry | Bootstrap app, wire dependencies, launch GUI |
| `app/models.py` | Data | SQLAlchemy ORM: Bill, BillItem, Customer, Staff, Service, Setting |
| `app/constants.py` | Config | DATABASE_URL, RECEIPTS_DIR, BACKUP_DIR, business rules |

### UI Layer (Presentation)

| File | Purpose |
|------|---------|
| `main_window.py` | Main app window with New Bill, Customers, Settings buttons |
| `billing_view.py` | Dialog for creating bills - customer, services, totals |
| `customer_view.py` | Window listing customers with search and edit |
| `settings_view.py` | Tabbed settings: General, Staff, Services, Integrations |
| `export_view.py` | Dialog for exporting bills to Excel |
| `customer_dialog.py` | Form for add/edit customer |
| `staff_dialog.py` | Form for add/edit staff member |
| `service_dialog.py` | Form for add/edit service |

### Service Layer (Business Logic)

| File | Purpose |
|------|---------|
| `billing_service.py` | Calculate subtotal/discount/tax/total, create bill, generate PDF |
| `customer_service.py` | Get customer, search, get summary with stats |
| `staff_service.py` | List active staff, get by ID |
| `service_catalog.py` | List services by category, search |
| `settings_service.py` | Get/set settings, manage secrets via keyring |
| `notification_service.py` | Send WhatsApp message with PDF attachment |
| `backup_service.py` | Create timestamped backup, cleanup old backups |
| `restore_service.py` | Restore database from backup file |
| `report_service.py` | Generate Excel exports, bill summaries |

### Repository Layer (Data Access)

| File | Purpose |
|------|---------|
| `base_repository.py` | Generic CRUD: get_by_id, get_all, create, update, delete |
| `bill_repository.py` | Bill-specific queries: by customer, by date range |
| `customer_repository.py` | Customer queries: search by name/phone |
| `staff_repository.py` | Staff queries: active only |
| `service_repository.py` | Service queries: by category, active only |
| `settings_repository.py` | Key-value settings storage |

### DTO Layer (Data Transfer)

| File | Purpose |
|------|---------|
| `bill_dto.py` | BillData, BillItemData, BillItemInput, BillOptions |
| `customer_dto.py` | CustomerData, CustomerSummary (with visit count, total spent) |
| `backup_dto.py` | BackupInfo, RestoreResult |

### Infrastructure Layer (External I/O)

| File | Purpose |
|------|---------|
| `database.py` | SQLAlchemy engine, SessionLocal factory, db_session context manager |
| `logging.py` | Logger setup with file and console handlers |
| `pdf_generator.py` | Generate PDF receipt using ReportLab |
| `whatsapp_client.py` | Send WhatsApp via Meta Cloud API |
| `cloud_drive.py` | Google Drive upload/download (stub - not implemented) |
| `crypto.py` | AES encrypt/decrypt for backups (stub - not implemented) |

### Exceptions

| File | Purpose |
|------|---------|
| `business_errors.py` | CustomerNotFoundError, StaffNotFoundError, DiscountExceedsSubtotalError, etc. |
| `validation_errors.py` | ValidationError for input validation failures |

### Utilities

| File | Purpose |
|------|---------|
| `csv_service_importer.py` | Import/export services from CSV file |
| `migrate_service_schema.py` | Add category, variant, display_name columns to service table |
| `migrate_bill_receipt_fields.py` | Add transaction_id, payment_status to bill table |

### Tests

| File | Purpose |
|------|---------|
| `test_billing_service.py` | 6 tests for discount, tax, total calculations |
| `test_customer_service.py` | 4 tests for customer operations |
| `test_csv_import.py` | 1 test for CSV import |
| `test_backup_restore.py` | Stub - needs implementation |
| `test_pdf_generation.py` | Stub - needs implementation |
| `test_billing_flow.py` | Stub - needs implementation |

### Configuration

| File | Purpose |
|------|---------|
| `requirements.txt` | Runtime: PyQt6, SQLAlchemy, reportlab, requests, keyring, etc. |
| `requirements-dev.txt` | Dev: pytest, black, isort, flake8, mypy, pre-commit |
| `pyproject.toml` | Project metadata, black/isort/mypy/pytest config |
| `pytest.ini` | Test discovery settings |
| `mypy.ini` | Type checking strictness |
| `.flake8` | Line length, ignored rules |
| `.pylintrc` | Pylint configuration |
| `.pre-commit-config.yaml` | Pre-commit hooks: black, isort, flake8, mypy |
| `SalonBillingSystem.spec` | PyInstaller hidden imports, data files |

### CI/CD

| File | Purpose |
|------|---------|
| `release.yml` | GitHub Actions: build exe on tag, create release |
| `build_exe.bat` | Local PyInstaller build script |

---

## ?? Data Flow Diagram

```
???????????????     ???????????????     ???????????????
?   User      ???????   UI View   ???????   Service   ?
?   Action    ?     ?  (PyQt6)    ?     ?   Layer     ?
???????????????     ???????????????     ???????????????
                                               ?
                           ?????????????????????????????????????????
                           ?                   ?                   ?
                    ???????????????     ???????????????     ???????????????
                    ? Repository  ?     ?Infrastructure?    ?    DTO      ?
                    ?   Layer     ?     ?    Layer    ?     ?   Layer     ?
                    ???????????????     ???????????????     ???????????????
                           ?                   ?
                    ???????????????     ???????????????
                    ?   Models    ?     ?  External   ?
                    ? (SQLAlchemy)?     ?  (PDF, WA)  ?
                    ???????????????     ???????????????
                           ?
                    ???????????????
                    ?   SQLite    ?
                    ?  Database   ?
                    ???????????????
```

---

## ?? Layer Dependency Rules

```
? ALLOWED                          ? FORBIDDEN
?????????????????????????????????????????????????????
UI ? Services                       UI ? Repositories
UI ? DTOs                           UI ? Models (for queries)
UI ? Exceptions                     UI ? db_session
                                    
Services ? Repositories             Services ? PyQt6
Services ? Infrastructure           Services ? UI
Services ? DTOs                     
Services ? Models (type hints)      
                                    
Repositories ? Models               Repositories ? Services
Repositories ? Database             Repositories ? UI
                                    
Infrastructure ? External libs      Infrastructure ? Services
Infrastructure ? Constants          Infrastructure ? UI
```

---

*Generated for Salon Billing System v1.1.0*
