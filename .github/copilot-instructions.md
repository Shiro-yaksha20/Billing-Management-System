# Salon Billing System — Coding & Architecture Rules

> **These rules are non-negotiable. Every code change must comply.**

---

## 1. Architecture Rules

### 1.1 Layer Hierarchy (Top ? Bottom, Never Reverse)

```
UI  ?  Services  ?  Repositories  ?  Infrastructure
                                   ?  Models
```

- Dependencies flow **downward only**.
- No layer may import from a layer above it.
- No layer may skip a layer (UI must not call Repositories directly).

### 1.2 Seven Absolute Rules

| ID | Rule | Violation Consequence |
|----|------|-----------------------|
| **R1** | UI (`app/ui/`) NEVER imports `db_session` | Breaks testability |
| **R2** | UI NEVER imports ORM models for queries | Creates tight coupling |
| **R3** | Services (`app/services/`) NEVER import `PyQt6` | Prevents unit testing |
| **R4** | Repositories (`app/repositories/`) contain NO business logic | Wrong responsibility |
| **R5** | All business rules live ONLY in Services | Prevents duplication |
| **R6** | Infrastructure (`app/infrastructure/`) modules are stateless | Hard to test otherwise |
| **R7** | DTOs (`app/dto/`) are immutable (`frozen=True` dataclasses) | Thread safety |

### 1.3 Import Rules by Layer

**UI Layer** (`app/ui/`):
```python
# ALLOWED
from app.services.<name> import <Service>
from app.dto.<name> import <DTO>
from app.exceptions.<name> import <Error>
from PyQt6.QtWidgets import ...

# FORBIDDEN — never do these
from app.infrastructure.database import db_session
from app.models import Bill, Customer  # (for queries)
from app.repositories.<name> import ...
from sqlalchemy.orm import Session
```

**Service Layer** (`app/services/`):
```python
# ALLOWED
from app.repositories.<name> import <Repository>
from app.dto.<name> import <DTO>
from app.infrastructure.<name> import ...
from app.models import Bill  # type hints ONLY, never direct queries
from app.exceptions.<name> import <Error>

# FORBIDDEN
from PyQt6 import ...
from app.ui.<name> import ...
from app.infrastructure.database import db_session  # use repository
```

**Repository Layer** (`app/repositories/`):
```python
# ALLOWED
from app.models import Bill, Customer, Staff, ...
from app.infrastructure.database import db_session
from sqlalchemy.orm import Session

# FORBIDDEN
from app.services.<name> import ...
from app.ui.<name> import ...
from PyQt6 import ...
```

**Infrastructure Layer** (`app/infrastructure/`):
```python
# ALLOWED
import requests
from cryptography.fernet import Fernet
from reportlab.lib.pagesizes import letter

# FORBIDDEN
from app.services.<name> import ...
from app.repositories.<name> import ...
from app.ui.<name> import ...
from PyQt6 import ...
```

---

## 2. Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| UI View class | `*View` | `BillingView`, `CustomerView` |
| UI Window class | `*Window` | `MainWindow` |
| UI Dialog class | `*Dialog` | `CustomerDialog`, `StaffDialog` |
| Service class | `*Service` or `*Catalog` | `BillingService`, `ServiceCatalog` |
| Repository class | `*Repository` | `BillRepository` |
| DTO class | `*Data`, `*Info`, `*Result`, `*Stats` | `BillData`, `BackupInfo`, `RestoreResult` |
| Exception class | `*Error` | `ValidationError`, `CustomerNotFoundError` |
| Private methods | `_method_name` | `_calculate_tax()` |
| Private attributes | `_attribute` | `_billing_service` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_DISCOUNT_PERCENT` |
| Variables & functions | `snake_case` | `customer_name`, `calculate_total()` |
| Classes | `PascalCase` | `BillingService` |

---

## 3. File Size & Complexity Limits

### 3.1 File Limits

| File Type | Max Lines | Max Methods | Max Dependencies |
|-----------|-----------|-------------|------------------|
| UI View | 400 | 15 | 5 services |
| UI Dialog | 200 | 10 | 2 services |
| Service | 300 | 15 | 3 repositories |
| Repository | 200 | 10 | 1 model |
| DTO | 100 | 0 (data only) | None |
| Test file | 500 | — | — |

### 3.2 Method Limits

| Metric | Ideal | Maximum | Fix if Exceeded |
|--------|-------|---------|-----------------|
| Lines per method | 15 | 40 | Extract helper methods |
| Parameters | 3–4 | 5 | Use dataclass or DTO |
| Cyclomatic complexity | ? 5 | 10 | Refactor logic |
| Nesting depth | ? 2 | 3 | Use early returns |

---

## 4. Type Hints

**Mandatory on all public methods.** Strongly encouraged on private methods.

```python
from typing import List, Optional
from decimal import Decimal

def search_customers(self, term: str) -> List[CustomerData]:
    ...

def get_customer(self, customer_id: int) -> Optional[CustomerData]:
    ...
```

Instance variables should be typed in `__init__`:

```python
def __init__(self, billing_service: BillingService) -> None:
    self._billing_service: BillingService = billing_service
    self._selected_customer: Optional[CustomerData] = None
```

---

## 5. Documentation

### 5.1 Module Docstring (Required)

```python
"""Billing service for bill creation and management."""
```

### 5.2 Class Docstring (Required)

```python
class BillingService:
    """
    Service for bill creation and calculation.

    Handles all billing business logic including:
    - Bill creation with items
    - Discount and tax calculations
    - Validation of business rules
    """
```

### 5.3 Public Method Docstring (Required)

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

Private methods: docstring optional but encouraged for complex logic.

---

## 6. Error Handling

### 6.1 Required Pattern

```python
# In Services — raise typed exceptions
raise ValidationError("Discount cannot exceed subtotal")
raise CustomerNotFoundError("Customer not found.")

# In UI — catch specific exceptions, show user messages
try:
    bill = self._billing_service.create_bill(...)
    QMessageBox.information(self, "Success", f"Bill #{bill.bill_number} saved")
except ValidationError as exc:
    QMessageBox.warning(self, "Validation Error", str(exc))
except CustomerNotFoundError:
    QMessageBox.warning(self, "Error", "Customer not found")
except Exception as exc:
    logger.error("Unexpected error: %s", exc)
    QMessageBox.critical(self, "Error", "An unexpected error occurred")
```

### 6.2 Forbidden Patterns

```python
# NEVER use bare except
except:
    pass

# NEVER silently swallow exceptions
except Exception:
    pass

# NEVER catch and only log without re-raising or user feedback
except Exception as e:
    logger.error(e)
    # ...and then continue as if nothing happened
```

---

## 7. Logging

### 7.1 Use `logging`, Never `print()`

```python
import logging
logger = logging.getLogger(__name__)

logger.debug("Processing items: %s", items)
logger.info("Bill created: %s", bill.id)
logger.warning("No results for search: %s", term)
logger.error("PDF generation failed: %s", exc)
logger.critical("Database connection failed")
```

### 7.2 Never Log Secrets

Never log passwords, API tokens, or encryption keys.

---

## 8. Code Organisation Within Files

```python
"""Module docstring."""

from __future__ import annotations

# 1. Standard library imports
import logging
from decimal import Decimal
from typing import List, Optional

# 2. Third-party imports
from PyQt6.QtWidgets import QDialog

# 3. Local imports — DTOs, Exceptions, Services
from app.dto.bill_dto import BillData
from app.exceptions.business_errors import CustomerNotFoundError
from app.services.billing_service import BillingService

logger = logging.getLogger(__name__)


class MyView(QDialog):
    """Class docstring."""

    # ?? INITIALIZATION ??????????????????????????????????????
    def __init__(self, ...) -> None: ...

    # ?? PUBLIC METHODS ??????????????????????????????????????
    def refresh(self) -> None: ...

    # ?? PRIVATE METHODS — UI Setup ??????????????????????????
    def _setup_ui(self) -> None: ...
    def _connect_signals(self) -> None: ...

    # ?? PRIVATE METHODS — Data Loading ??????????????????????
    def _load_data(self) -> None: ...

    # ?? PRIVATE METHODS — Event Handlers ????????????????????
    def _on_save_clicked(self) -> None: ...
```

---

## 9. DTO Rules

- All DTOs use `@dataclass(frozen=True)`.
- DTOs contain **no methods** — they are pure data containers.
- DTOs live in `app/dto/`.
- DTOs never import from services, repositories, UI, or infrastructure.

---

## 10. Repository Rules

- Each repository handles **one model** only.
- All repositories extend `BaseRepository`.
- Repositories receive `session_factory` via constructor (dependency injection).
- Repositories **never** contain business logic (no calculations, no validation beyond DB constraints).
- Repositories return ORM model instances to the service layer.

---

## 11. Service Rules

- Services receive repositories (and optionally other services or infrastructure) via constructor.
- Services convert ORM models ? DTOs before returning data to callers.
- Services contain **all** validation and business rules.
- Services raise custom exceptions from `app/exceptions/`.
- Services never access `db_session` directly — they use repositories.

---

## 12. UI Rules

- UI classes receive services via constructor (dependency injection).
- UI handles **only**: rendering, user input, and displaying messages.
- All data crossing the UI boundary must be DTOs or primitive types.
- UI catches service exceptions and displays appropriate `QMessageBox`.
- UI never performs calculations, validation, or data access.

---

## 13. Testing Rules

- Test naming: `test_<method>_<scenario>_<expected>`
- Test structure: Arrange ? Act ? Assert (AAA pattern)
- Unit tests use stubs or mocks, never real databases.
- Integration tests use temporary SQLite databases (`temp_db` fixture).
- Coverage target: 80% overall, 90% for services.
- UI code is excluded from coverage (`app/ui/*` in `pyproject.toml`).

---

## 14. Git Conventions

```
<type>(<scope>): <description>

Types: feat | fix | refactor | test | docs | chore
Scope: billing | customer | staff | services | ui | infra | backup

Examples:
  feat(ui): add bill history view
  fix(billing): correct tax calculation
  refactor(services): extract validation logic
  test(billing): add discount calculation tests
```

---

## 15. Security Rules

- API tokens stored via `keyring` (OS credential manager), never in code or DB.
- Backup encryption uses Fernet (AES) with PBKDF2 key derivation (480,000 iterations).
- Never log sensitive data (passwords, tokens, keys).
- Always validate external inputs before processing.
- SQLAlchemy parameterised queries only (no raw string concatenation).

---

## 16. Python Style

- Formatter: `black` (line length 88)
- Import sorter: `isort` (profile: black)
- Linter: `flake8`
- Type checker: `mypy` (strict mode)
- Target Python version: 3.11+
- Use comprehensions over explicit loops where readable.
- Use `Decimal` for all monetary values, never `float`.
- Use `from __future__ import annotations` in every module.
