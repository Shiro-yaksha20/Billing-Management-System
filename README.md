# Salon Billing System

A production-ready Windows desktop billing application for salons, built with **Python** and **PyQt6**. Manages customers, services, staff, invoicing, PDF receipts, WhatsApp delivery, encrypted backups, and Excel exports — all from a single interface.

[![Release](https://img.shields.io/github/v/release/Shiro-yaksha20/Billing-Management-System)](https://github.com/Shiro-yaksha20/Billing-Management-System/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)

---

## Features

| Category | Highlights |
|----------|-----------|
| **Billing** | Create itemised bills, apply flat/percent discounts, calculate GST, select payment method |
| **PDF Receipts** | Auto-generated receipts with salon branding, GST number, and Instagram handle |
| **WhatsApp** | Send PDF receipts to customers via the Meta Cloud API |
| **Customers** | Add, edit, search, view visit history and spending summary |
| **Services** | Category-based catalog with variants, CSV bulk import/export |
| **Staff** | Manage stylists, assign to bills |
| **Dashboard** | Today's sales, pending bills, recent transactions at a glance |
| **Reports** | Export bills to Excel with date/customer filters |
| **Backups** | Timestamped local backups, optional AES encryption, Google Drive upload |
| **Settings** | Salon details, staff, services, WhatsApp integration — all in one place |

---

## Architecture

The application follows a **clean layered architecture** with strict dependency rules:

```
UI (PyQt6)  ?  Services  ?  Repositories  ?  Infrastructure
                                            ?  Models
```

| Layer | Location | Responsibility |
|-------|----------|----------------|
| **UI** | `app/ui/` | Rendering, user input, message boxes |
| **Services** | `app/services/` | Business logic, validation, DTO conversion |
| **Repositories** | `app/repositories/` | Database queries via SQLAlchemy ORM |
| **Infrastructure** | `app/infrastructure/` | PDF generation, WhatsApp API, encryption, logging |
| **DTOs** | `app/dto/` | Immutable data transfer objects (`frozen=True` dataclasses) |
| **Models** | `app/models.py` | SQLAlchemy ORM model definitions |

Dependencies flow **downward only** — no layer imports from a layer above it.

---

## Tech Stack

- **Language:** Python 3.10+
- **GUI:** PyQt6
- **Database:** SQLite via SQLAlchemy ORM
- **PDF:** ReportLab
- **Excel:** openpyxl
- **WhatsApp:** Meta Cloud API (via `requests`)
- **Encryption:** `cryptography` (Fernet / PBKDF2)
- **Credentials:** `keyring` (Windows Credential Manager)
- **Build:** PyInstaller

---

## Quick Start

### Prerequisites

- Python 3.10 or later
- Windows 10/11 (for credential storage and PyInstaller builds)

### Installation

```bash
# Clone the repository
git clone https://github.com/Shiro-yaksha20/Billing-Management-System.git
cd Billing-Management-System

# Create a virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

### First-Time Setup

1. Launch the app and navigate to **Settings**.
2. Fill in your salon name, address, phone, and optional GST/Instagram.
3. Add your **staff members** and **services** (or import services from a CSV).
4. Optionally configure **WhatsApp** under the Integrations tab.

---

## Building from Source

```bash
pip install -r requirements.txt
pyinstaller SalonBillingSystem.spec
```

The executable will be in `dist/SalonBillingSystem/`.

Alternatively, use the build script:

```bash
scripts\build_exe.bat
```

---

## Releases

Pre-built Windows executables are available on the [Releases](https://github.com/Shiro-yaksha20/Billing-Management-System/releases) page.

Each release includes:
- **`SalonBillingSystem-vX.Y.Z.zip`** — ready-to-run Windows executable
- **Source code** (zip and tar.gz)

Releases are built automatically by GitHub Actions when a version tag (`vX.Y.Z`) is pushed.

### Creating a New Release

```bash
# 1. Bump version in app/__init__.py
# 2. Commit and push
git add -A
git commit -m "chore: bump version to vX.Y.Z"
git push origin master

# 3. Tag and push the tag
git tag vX.Y.Z
git push origin vX.Y.Z
```

GitHub Actions will build the `.exe`, package it, and publish a GitHub Release.

---

## Project Structure

```
??? app/
?   ??? ui/                  # PyQt6 views and dialogs
?   ??? services/            # Business logic layer
?   ??? repositories/        # Data access layer
?   ??? infrastructure/      # PDF, WhatsApp, encryption, logging
?   ??? dto/                 # Immutable data transfer objects
?   ??? exceptions/          # Custom exception types
?   ??? models.py            # SQLAlchemy ORM models
?   ??? constants.py         # App-wide constants
?   ??? csv_service_importer.py
?   ??? migrate_*.py         # Database migration scripts
??? tests/
?   ??? unit/                # Isolated unit tests
?   ??? integration/         # Database integration tests
?   ??? e2e/                 # End-to-end workflow tests
??? scripts/                 # Build utilities
??? docs/                    # Documentation and plans
??? main.py                  # Application entry point
??? requirements.txt         # Production dependencies
??? requirements-dev.txt     # Development dependencies
??? pyproject.toml           # Tool configuration
??? SalonBillingSystem.spec  # PyInstaller build spec
```

---

## Testing

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=app --cov-report=term-missing
```

**Current status:** 174 tests passing, ~100% coverage on non-UI code.

---

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to get started.

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## Acknowledgements

- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) — GUI framework
- [SQLAlchemy](https://www.sqlalchemy.org/) — ORM
- [ReportLab](https://www.reportlab.com/) — PDF generation
- [Meta WhatsApp Cloud API](https://developers.facebook.com/docs/whatsapp/cloud-api) — Messaging
