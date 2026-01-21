# Salon Billing System

A Windows-focused desktop billing application for salons built with Python and PyQt6.

TL;DR
- Run locally: python -m venv venv && venv\Scripts\activate && pip install -r requirements.txt && python main.py
- Build Windows exe: call scripts\build_exe.bat (Windows)
- Securely store API tokens using the app's keyring-backed settings service

---

## Table of contents
- Features
- Tech stack
- Quick start
- Product requirements (PRD)
  - Purpose & scope
  - Goals & success criteria
  - User personas
  - Functional requirements
  - Data requirements & model mapping
  - Acceptance criteria
- Sample data & fixtures
  - CSV examples
  - Python seed script
  - Recommended fixtures location
  - Privacy & test-data guidance
- Configuration (settings & secrets)
- Database & migrations
- Common workflows & examples
  - Generate a PDF receipt (programmatically)
  - Send receipt via WhatsApp (programmatically)
  - Import / Export services CSV
- Building & packaging (PyInstaller)
- Tests & CI
- Troubleshooting & tips
- Contributing, versioning & releases

---

## Features
- Create bills, select staff and services, save receipts as PDFs
- PDF receipt generation using ReportLab with optional Unicode font support
- Send receipts via WhatsApp Cloud API (attachment upload + send)
- Customers, staff, services stored in SQLite via SQLAlchemy ORM
- Secure secret storage using the OS credential store via keyring (Windows Credential Manager recommended)
- CSV bulk import/export for services (safe backup and transactional import)
- PyInstaller spec + build script for creating a Windows distributable

---

## Tech stack
- Python 3.11+ (project tests and tooling assume modern Python)
- PyQt6 — GUI
- SQLAlchemy — ORM for SQLite
- ReportLab — PDF generation
- requests — HTTP for WhatsApp API calls
- keyring — secure secrets
- PyInstaller — build distributable
- openpyxl — Excel exports (available via requirements)

---

## Quick start (development)
1. Clone the repo:
   - git clone <repo-url>
   - cd Billing-Management-System

2. Create and activate a virtual environment (Windows example):
   - python -m venv venv
   - venv\Scripts\activate

3. Install dependencies:
   - pip install -r requirements.txt

4. (Optional) Review `.env.example` for non-sensitive config defaults.

5. Run the application:
   - python main.py

The application runs the DB initialization and startup migrations automatically (see app/database.py and gui_main.startup_migrations()).

---

## Product requirements (PRD)

This section provides a concise product-style spec and data guide so contributors can quickly gather or generate the sample data needed for development and testing.

### Purpose & scope
Purpose: Provide a lightweight desktop billing system for salons that allows staff to create bills, generate PDF receipts, and deliver receipts via WhatsApp. The app supports management of customers, staff and services, and CSV import/export for service catalogs.

Scope:
- Core billing flow (select customer, staff, services → calculate totals → persist Bill and BillItems)
- PDF receipt generation and local storage
- Optional WhatsApp delivery (Cloud API)
- CSV import/export for services
- Local SQLite database with simple migrations and backups

### Goals & success criteria
- Contributors can run the app locally with a minimal dataset and reproduce core scenarios.
- Contributors can import/export services via CSV and understand data formats.
- PDF receipts render correctly (currency support) and are saved to RECEIPTS_DIR.
- WhatsApp integration can be tested using a valid token and phone id without exposing secrets.

### User personas
- Salon Owner: wants printable receipts, simple export for accounting.
- Receptionist: creates bills, selects staff/services, prints/sends receipts.
- Developer/Contributor: needs seed data and clear data contracts to develop features and tests.

### Functional requirements (high level)
- Create and persist bills and bill items (including subtotal, discounts, taxes, total).
- Generate PDF receipt with salon and customer details.
- Upload PDF to WhatsApp Cloud API and send as document.
- Import/export services via CSV with defined columns.
- Store non-sensitive settings in SQLite; store API tokens in keyring.

### Data requirements & model mapping
Primary entities and key fields (as defined in app/models.py):

- Service
  - id, category, name, variant, display_name, price, duration_minutes, notes, active
  - CSV import/export headers: category, service_name, variant, display_name, price, notes

- Customer
  - id, name (required), phone (required), notes, last_visit_at

- Staff
  - id, name (required), phone, role, active

- Bill
  - id, bill_number, customer_id, staff_id, bill_datetime, subtotal, discount_amount, discount_type, tax_amount, tax_percent, total, payment_method, status, pdf_path, whatsapp_status, transaction_id, payment_status
  - Bill has related BillItems (bill.items), and BillItem has service relation (service.display_name, service.name)

- BillItem
  - id, bill_id, service_id, quantity, unit_price, line_total

Where to read/write:
- SQLite DB location configured via `app/constants.py` (DATABASE_URL). Use the file path there to inspect the DB.
- Receipts are written to RECEIPTS_DIR (`app/constants.py`).

### Acceptance criteria (example)
- A developer can seed the database with 5 services, 3 staff members, and 5 customers using provided CSV or Python seed script.
- Creating a bill persists Bill and BillItems; calling generate_receipt_pdf(bill_id) returns a valid file path and writes a PDF.
- send_whatsapp_message(to, msg, attachment_path=pdf) constructs and posts expected payloads (see "APIs & data contracts" below).
- CSV importer accepts required columns, backs up existing services when clear_existing=True, and handles invalid rows gracefully.

---

## Sample data & fixtures

A focused guide for contributors who need to get a working dataset quickly.

Recommended location for fixtures:
- data/fixtures/services.csv
- data/fixtures/customers.csv
- data/fixtures/staff.csv

Create a top-level data directory (tracked by Git) for non-sensitive sample data. Do NOT commit real customer PII.

### CSV examples

Services CSV (header only — required columns in importer):
```csv
category,service_name,variant,display_name,price,notes
Basic,Haircut,Short,Haircut (Short),250,
Basic,Haircut,Medium,Haircut (Medium),300,
Facial,Classic,,Classic Facial,800,
Bridal,Makeup,Full,Bridal Makeup (Full),5000,"Includes trial"
```

Customers CSV (suggested fields — the app does not currently include a bulk importer for customers, but this format is useful for seeding):
```csv
name,phone,notes,last_visit_at
Anita Sharma,919876543210,"Regular customer","2025-01-12T15:30:00"
Rohit Verma,919812345678,,""
```

Staff CSV:
```csv
name,phone,role,active
Sangeeta,919999111222,Stylist,True
Akhil,919888222333,Manager,True
```

### Python seed script (minimal, safe to run in dev)
Place this as data/fixtures/seed.py or run interactively from a dev shell.

```python
# data/fixtures/seed.py
from app.database import db_session
from app.models import Service, Customer, Staff
from decimal import Decimal

services = [
    {"category": "Basic", "name": "Haircut", "variant": "Short", "display_name": "Haircut (Short)", "price": Decimal("250")},
    {"category": "Basic", "name": "Haircut", "variant": "Medium", "display_name": "Haircut (Medium)", "price": Decimal("300")},
    {"category": "Facial", "name": "Classic", "variant": None, "display_name": "Classic Facial", "price": Decimal("800")},
]

customers = [
    {"name": "Test Customer", "phone": "919900000000", "notes": "Seeded customer"},
]

staff = [
    {"name": "Seed Stylist", "phone": "919911122233", "role": "Stylist"},
]

with db_session() as db:
    for s in services:
        svc = Service(
            category=s["category"],
            name=s["name"],
            variant=s["variant"],
            display_name=s["display_name"],
            price=s["price"],
            active=True
        )
        db.add(svc)

    for c in customers:
        cust = Customer(name=c["name"], phone=c["phone"], notes=c.get("notes"))
        db.add(cust)

    for st in staff:
        stf = Staff(name=st["name"], phone=st["phone"], role=st.get("role"), active=True)
        db.add(stf)
```

Run the script after creating and activating your venv:
```bash
python -c "from data.fixtures.seed import *"  # or run the file directly
```

### Recommended minimal dataset for development
- 3–10 services across categories
- 2–3 staff members
- 5–20 customers (use fake/test phone numbers)
- A couple of bills created via the UI or programmatically for testing PDF generation and WhatsApp sending

### Privacy & test-data guidance
- Do not commit real customer data or API tokens.
- Use clearly synthetic phone numbers and names in fixtures (e.g., starting with 919900...).
- Keep sensitive configuration out of fixtures; store secrets with keyring or local environment variables.

---

## Configuration

### Non-sensitive settings (stored in SQLite)
The app stores simple settings (salon name, address, phone, receipt footer, WhatsApp API version, whatsapp_phone_id, etc.) in the SQLite `setting` table.

Use the app Settings UI (recommended) or programmatically:

Python example:
```python
from app.settings_service import set_setting, get_setting
set_setting("salon_name", "My Salon")
print(get_setting("salon_name"))
```

### Sensitive settings (secure secrets via keyring)
Secrets (API tokens) are stored via the OS credential store through the `app/settings_service` module. Do NOT store secrets in Git.

Programmatic example to set/delete secrets:
```python
from app.settings_service import set_secret, get_secret

# Save token (writes to system credential store)
set_secret("whatsapp_api_token", "PASTE_YOUR_SECRET_HERE")

# Retrieve it
token = get_secret("whatsapp_api_token")

# Delete it
set_secret("whatsapp_api_token", None)
```

Important notes:
- On Windows the default keyring backend uses Windows Credential Manager.
- If deploying to macOS or Linux adjust keyring backend accordingly.
- Do not commit secrets or the env/ directory into the repository.

---

## APIs & data contracts (quick reference)

WhatsApp (app/whatsapp_client.py):
- Required settings:
  - whatsapp_api_token (secret via keyring)
  - whatsapp_phone_id (stored in settings)
  - whatsapp_api_version (optional, default "v15.0")
- Attachment flow: upload media to /{api_version}/{phone_id}/media → get media id → send document message with document.id
- Text message payload (when no attachment):
  ```json
  {
    "messaging_product": "whatsapp",
    "to": "<to_number>",
    "type": "text",
    "text": {"body": "<message>"}
  }
  ```

PDF generator (app/pdf_generator.py):
- Input: bill_id (int). The function loads Bill and related items, reads salon settings via settings_service, and writes PDF to RECEIPTS_DIR.
- Ensure DejaVuSans.ttf is available if ₹ is required; otherwise the generator falls back to Helvetica and uses "Rs." currency label.

Services CSV (import/export):
- Required columns for import: category, service_name, display_name, price
- Optional: variant, notes
- Import behavior: updates existing Service by display_name or creates new, with safe transactional handling and optional clearing/backups.

Database:
- See app/models.py for field names and relationships.

---

## Database & migrations
- SQLite is used; connection configured in `app/constants.py` (DATABASE_URL).
- Initialization: `init_db()` (app/database.py) creates tables; it is called at startup.
- A minimal migration helper exists (migrate_service_schema) — the main GUI invokes migrations at startup (see app/gui_main.py).
- Backups: the app attempts a startup backup via app/backup_service.py (called in main.py).

If you need to manually inspect the DB:
- Open the sqlite file (path set in app/constants.py) with your preferred SQLite browser.
- Example: sqlite3 path/to/dbfile.db

---

## Common workflows & examples

### Generate a receipt PDF (programmatic)
You can generate a receipt PDF for an existing bill (id = 123) with:
```python
from app.pdf_generator import generate_receipt_pdf
file_path = generate_receipt_pdf(123)
print("Saved receipt to", file_path)
```

Notes:
- PDFs are generated into RECEIPTS_DIR (see app/constants.py).
- The generator attempts to register DejaVuSans.ttf for full Unicode currency symbols (₹); if not available it falls back to Helvetica.

### Send a receipt via WhatsApp
The WhatsApp flow uploads media then sends a document message (app/whatsapp_client.py). Configure:
- Non-sensitive: `whatsapp_phone_id` in settings (set via UI or set_setting)
- Sensitive: `whatsapp_api_token` via keyring (set_secret)

Example:
```python
from app.pdf_generator import generate_receipt_pdf
from app.whatsapp_client import send_whatsapp_message
from app.settings_service import set_secret, set_setting

# Ensure settings
set_setting("whatsapp_phone_id", "<YOUR_PHONE_ID>")
set_secret("whatsapp_api_token", "<YOUR_TOKEN>")

# Generate PDF and send
pdf_path = generate_receipt_pdf(123)
success, resp = send_whatsapp_message("919876543210", "Here is your receipt", attachment_path=pdf_path)
print(success, resp)
```

### Import / Export services via CSV
CSV importer accepts columns:
- category, service_name, variant, display_name, price, notes

Programmatic import:
```python
from app.csv_service_importer import import_services_from_csv
result = import_services_from_csv("data/services.csv", clear_existing=False)
print(result)
```

Programmatic export:
```python
from app.csv_service_importer import export_services_to_csv
export_services_to_csv("data/exported_services.csv")
```

Importer safety:
- Optionally creates a CSV backup before clearing existing services
- Uses SQLAlchemy savepoint to limit partial failures
- MAX_IMPORT_ERRORS prevents noisy imports from continuing (configured in constants)

---

## Building & packaging (Windows / PyInstaller)
A PyInstaller spec and a Windows build script are included.

Windows build (recommended flow from a developer machine):
1. Prepare a clean virtualenv (see Quick start).
2. Activate venv and install requirements.
3. From repository root run:
   - scripts\build_exe.bat
   This script will:
   - create/activate venv (if missing)
   - pip install -r requirements.txt
   - call pyinstaller with SalonBillingSystem.spec

Notes & tips:
- The spec includes many hiddenimports — if you add new modules you may need to add them to the `hiddenimports` list.
- PyQt6 on PyInstaller sometimes needs additional data (qml, plugins). The spec already attempts to bundle `app` as data, but confirm runtime assets (fonts, QML plugins) are present.
- If you want a console output while debugging, update `console=True` in the EXE creation in the .spec.
- The builder uses UPX; if UPX causes issues on some DLLs, disable UPX or add exclusions.

---

## Tests & CI
- Tests are located in `tests/` (for example `tests/test_csv_import.py`).
- Run tests:
  - pip install -r requirements.txt
  - pip install pytest
  - pytest -q

- GitHub Actions workflows are configured in `.github/workflows/` for quality, tests and releases.

---

## Troubleshooting & tips
- If the UI shows missing or garbled currency symbols:
  - Ensure DejaVuSans.ttf is available in the working directory or system fonts; the PDF generator tries to register it but falls back.
- Keyring issues:
  - On non-Windows platforms keyring backend may differ. If keyring.get_password fails, check available backends and system credential store.
- Large env/ directory found in repo:
  - Remove committed virtual environments (e.g., env/). Add them to .gitignore to avoid shipping many third-party files.
- PyInstaller GUI freeze or missing Qt plugins:
  - Check that QML and Qt plugins are included. Inspect the `dist/SalonBillingSystem` folder to confirm qml, platforms, and imageformats folders are present.

---

## Contributing
- Fork, create a branch, make small incremental PRs.
- Follow the existing style; tests are present and should pass.
- Update `app/__init__.py` version before a release. `setup.py` reads the version from there.

Release steps (recommended)
1. Bump version in `app/__init__.py` (semantic versioning)
2. Commit & tag: git tag -a vX.Y.Z -m "release X.Y.Z"
3. Push tag & branch
4. CI / GitHub Actions may create artifacts (see repo workflows). Alternatively, run scripts/build_exe.bat locally.

If you'd like, I can:
- Generate a short CHANGELOG template,
- Produce a CONTRIBUTING.md scaffold with PR and code style guidelines,
- Create a minimal .gitignore that excludes virtualenvs and env/ directory.

---

## Files & locations of interest
- Entry point: main.py
- GUI / windows: app/gui_main.py, app/gui_billing.py, app/gui_customers.py, app/gui_settings.py
- Models & DB: app/models.py, app/database.py
- PDF generator: app/pdf_generator.py
- WhatsApp integration: app/whatsapp_client.py
- Settings & secrets: app/settings_service.py
- CSV importer: app/csv_service_importer.py
- Packaging: SalonBillingSystem.spec, scripts/build_exe.bat
- Requirements: requirements.txt

---

## Security & housekeeping
- Never commit API tokens or credentials. Use keyring for secrets.
- Remove the `env/` directory from the repository and add it to `.gitignore`. It currently contains many vendored files and platform-specific binaries.
- Use `.env.example` for non-sensitive default configuration only.

---

## License
- No license file detected in the repository root. Add a LICENSE file if you intend to open-source the project or specify usage terms.

---

If you'd like, I can:
- Generate a short CHANGELOG template,
- Produce a CONTRIBUTING.md scaffold with PR and code style guidelines,
- Create a minimal .gitignore that excludes virtualenvs and env/ directory.