# Changelog

All notable changes to this project will be documented in this file.

## [2.0.0] - 2026-02-17

### Added
- **Clean architecture** — full separation into UI, Service, Repository, Infrastructure, and DTO layers.
- **Repository layer** — `BaseRepository` with generic CRUD; dedicated repositories for Bill, Customer, Staff, Service, and Settings.
- **DTO layer** — immutable frozen dataclasses: `BillData`, `CustomerData`, `StaffData`, `ServiceData`, `ReceiptData`, `BackupInfo`, `RestoreResult`, `DashboardStats`.
- **Custom exceptions** — `ValidationError`, `CustomerNotFoundError`, `StaffNotFoundError`, `DiscountExceedsSubtotalError`, `NegativeTotalError`, `InsufficientDataError`.
- **Dashboard** — today's sales, pending bills, recent transactions, and quick actions.
- **Bill history view** — search and filter past bills by number, customer, date, and payment status.
- **Customer selection dialog** — searchable customer picker for billing.
- **Log viewer dialog** — view application logs from the UI.
- **Encrypted backups** — AES encryption with Fernet and PBKDF2 key derivation (480,000 iterations).
- **Google Drive backup** — upload/download backups via Google Drive API.
- **CSV service import/export** — bulk import services with category, variant, display name, and price; automatic pre-import backups.
- **Database migrations** — safe schema upgrades for service and bill tables.
- **Comprehensive test suite** — 174 unit tests with ~100% coverage on non-UI code.
- `CONTRIBUTING.md` with development guidelines.
- `LICENSE` (MIT).

### Changed
- **PDF generation** refactored to receive `ReceiptData` DTO instead of querying the database directly — infrastructure layer no longer bypasses the repository.
- **All monetary fields** use `Decimal` consistently (fixed `CustomerSummary.total_spent` from `float`).
- **All modules** include `from __future__ import annotations`.
- **All model classes** have docstrings.
- **Migration scripts** catch `OperationalError` instead of bare `except Exception: pass`.
- `SalonBillingSystem.spec` updated with all new modules.
- `.gitignore` expanded to cover `.vs/`, `env/`, `htmlcov/`, `releases/`, and OS artifacts.
- `README.md` fully rewritten with architecture, features, setup, and release instructions.

### Removed
- Legacy monolithic modules: `gui_main.py`, `gui_billing.py`, `gui_customers.py`, `gui_settings.py`, `gui_export.py`, `app/database.py`, `app/pdf_generator.py`, `app/whatsapp_client.py`, `app/utils.py`, `app/backup_service.py`, `app/settings_service.py`, `app/export_service.py`.
- Unrelated .NET project (`ConsoleApp1/`, `ConsoleApp1.sln`).
- Stale planning documents moved to `docs/archive/`.

## [1.1.0] - 2024-11-25

### Added
- Automated Windows EXE builds with GitHub Actions.
- PyInstaller configuration for building a Windows executable.
- A `CHANGELOG.md` file to track changes.
- A single source of truth for the application version in `app/__init__.py`.

### Changed
- Minor code hardening and polishing, including improved error handling around file I/O and HTTP requests.
- Updated `README.md` with sections on releases, versioning, and building from source.
