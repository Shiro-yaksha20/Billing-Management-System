# Salon Billing System — What To Do Next

> A prioritised, step-by-step action plan for completing the remaining work.  
> Each task includes what to change, where to change it, and the rules to follow.

---

## Current State (as of report)

| Phase | Completion | Status |
|-------|------------|--------|
| Phase 1 — Repositories | 100% | ? Done |
| Phase 2 — Services | 90% | ?? Two violations remain |
| Phase 3 — UI Refactoring | 100% | ? Done |
| Phase 4 — Backup Infrastructure | 70% | ?? Crypto done, cloud stub |
| Phase 5 — Testing | 40% | ?? 28 tests passing, need more |
| Legacy Cleanup | 100% | ? Done |

**Tests**: 28/28 passing | **Architecture violations**: 4 remaining

---

## Priority 1 — Fix Architecture Violations

These violations break the architecture rules defined in `.github/copilot-instructions.md`. Fix them before adding any new features.

---

### Task 1.1: Create `StaffData` DTO and fix `StaffService`

**Problem**: `StaffService` returns raw ORM `Staff` objects to the UI layer. This violates Rule R2 (UI never receives ORM models) and Rule R11 (services convert ORM ? DTO before returning).

**Files to change**:

| File | Action |
|------|--------|
| `app/dto/staff_dto.py` | **Create** — new DTO file |
| `app/dto/__init__.py` | **Modify** — add exports |
| `app/services/staff_service.py` | **Modify** — return `StaffData` instead of `Staff` |
| `app/ui/settings_view.py` | **Modify** — update to use `StaffData` fields |
| `app/ui/billing_view.py` | **Modify** — update staff combo population |
| `app/ui/dialogs/staff_dialog.py` | **Modify** — update to use `StaffData` |
| `tests/unit/test_staff_service.py` | **Modify** — assert on DTOs |

**Step-by-step**:

1. Create `app/dto/staff_dto.py`:
   ```python
   @dataclass(frozen=True)
   class StaffData:
       id: int
       name: str
       phone: Optional[str]
       role: Optional[str]
       active: bool
   ```
   - Must use `@dataclass(frozen=True)` — Rule R7.
   - Must have `from __future__ import annotations` — Style Rule.
   - No methods, no imports from other layers — Rule R9.

2. Export from `app/dto/__init__.py` — add `StaffData` to `__all__`.

3. In `app/services/staff_service.py`:
   - Add `from ..dto.staff_dto import StaffData`.
   - Add a private `_to_staff_data(staff: Staff) -> StaffData` method.
   - Change every method that currently returns `Staff` to return `StaffData`.
   - Change `list_active_staff()` and `list_all()` to return `List[StaffData]`.

4. Update all UI files that consume staff data to use `StaffData` attributes.

5. Update `test_staff_service.py` to assert on `StaffData` objects.

6. Run `python -m pytest -v` — all 28+ tests must pass.

**Rules to follow**: R2, R7, R11, naming convention (`*Data` for DTOs).

---

### Task 1.2: Fix `ReportService` to use `BillRepository`

**Problem**: `ReportService.export_bills()` imports `db_session` directly and queries `Bill` models. Services must never access `db_session` — they must go through repositories (Rule R5, `.github/copilot-instructions.md` §1.3).

**Files to change**:

| File | Action |
|------|--------|
| `app/services/report_service.py` | **Modify** — inject `BillRepository`, remove `db_session` |
| `app/repositories/bill_repository.py` | **Modify** — add export query method if needed |
| `main.py` | **Modify** — pass `bill_repo` to `ReportService` |
| `tests/unit/test_report_service.py` | **Modify** — use stub repo |

**Step-by-step**:

1. Add a method to `BillRepository` that returns bills with items, customer, staff, and service eagerly loaded. The current `search()` method may work, but it does not load `items`, `staff`, or `service` relationships needed by the export. Add a dedicated method:
   ```python
   def find_for_export(self, start_date=None, end_date=None, customer_id=None) -> Iterable[Bill]:
   ```
   Use `selectinload(Bill.items)`, `selectinload(Bill.customer)`, `selectinload(Bill.staff)`, and within items `selectinload(BillItem.service)`.

2. In `ReportService.__init__`, accept `bill_repo: BillRepository` as a parameter.

3. Replace the `with db_session() as db: ...` block in `export_bills()` with a call to `self._bill_repo.find_for_export(...)`.

4. Remove the imports of `db_session` and `Bill` from `report_service.py`.

5. In `main.py`, change `report_service = ReportService()` to `report_service = ReportService(bill_repo)`.

6. Update `test_report_service.py` to inject a stub or the real repo via the `temp_db` fixture.

7. Run tests.

**Rules to follow**: R1 (no `db_session` in services), R4 (repo has no business logic), R10 (repo returns ORM models to service).

---

### Task 1.3: Add `DashboardStats` to DTO exports

**Problem**: `DashboardStats` is defined in `app/dto/bill_dto.py` but not exported from `app/dto/__init__.py`.

**File**: `app/dto/__init__.py`

**Change**: Add `DashboardStats` to both the import line and `__all__`.

---

### Task 1.4: Complete `app/ui/__init__.py` exports

**Problem**: Only `BillHistoryView` is exported. All public views should be listed.

**File**: `app/ui/__init__.py`

**Change**: Add imports and `__all__` entries for `BillingView`, `CustomerView`, `ExportView`, `SettingsView`, `MainWindow`.

---

## Priority 2 — Increase Test Coverage

The project has a configured coverage threshold of 80% but only ~40% actual coverage. The service layer target is 90%.

---

### Task 2.1: Add `BillingService` edge-case tests

**File**: `tests/unit/test_billing_service.py`

**Tests to add**:
- `test_calculate_discount_flat_valid_returns_amount` — happy path
- `test_calculate_discount_percent_valid_returns_amount` — happy path
- `test_calculate_discount_none_returns_zero`
- `test_calculate_discount_negative_value_raises`
- `test_calculate_discount_invalid_type_raises`
- `test_calculate_tax_valid_returns_amount`
- `test_calculate_tax_negative_percent_raises`
- `test_create_bill_negative_total_raises`

**Rules**: Test naming `test_<method>_<scenario>_<expected>`, AAA pattern, use stubs.

---

### Task 2.2: Add `CustomerService` tests

**File**: `tests/unit/test_customer_service.py`

**Tests to add**:
- `test_create_customer_success_returns_data`
- `test_search_customers_returns_list`
- `test_get_customer_bills_returns_list`
- `test_delete_customer_success`

---

### Task 2.3: Add `StaffService` tests

**File**: `tests/unit/test_staff_service.py`

**Tests to add** (after Task 1.1 — these should assert on `StaffData`):
- `test_get_staff_existing_returns_data`
- `test_list_active_staff_returns_list`
- `test_list_all_returns_list`
- `test_update_staff_success_returns_data`
- `test_toggle_active_success`

---

### Task 2.4: Add `ServiceCatalog` tests

**File**: `tests/unit/test_service_catalog.py`

**Tests to add**:
- `test_list_all_returns_data`
- `test_list_active_returns_data`
- `test_toggle_active_success`
- `test_toggle_active_missing_returns_false`

---

### Task 2.5: Add `BackupService` and `RestoreService` tests

**File**: `tests/integration/test_backup_restore.py`

**Tests to add**:
- `test_create_backup_encrypted_round_trip` — encrypt ? decrypt ? verify bytes match
- `test_create_backup_missing_db_raises`
- `test_list_backups_returns_sorted`
- `test_cleanup_old_backups_keeps_only_n`
- `test_restore_missing_file_returns_failure`
- `test_restore_decrypt_wrong_password_returns_failure`

**Rules**: Use `backup_paths` fixture from `conftest.py`. Use real temp files.

---

### Task 2.6: Run coverage report

After adding tests, run:
```bash
python -m pytest --cov=app --cov-report=term-missing --cov-report=html
```

Verify:
- Overall coverage ? 80%.
- `app/services/` coverage ? 90%.
- Open `htmlcov/index.html` to inspect uncovered lines.

---

## Priority 3 — Minor Improvements

These are lower-priority but keep the codebase clean.

---

### Task 3.1: Refactor `csv_service_importer.py` to use repository

**Problem**: `csv_service_importer.py` imports `db_session` directly. It should go through `ServiceRepository`.

**Approach**:
1. Accept `service_repo: ServiceRepository` as a parameter in `import_services_from_csv()`.
2. Replace raw `db.query(Service)` calls with repository methods.
3. Update `ServiceCatalog.import_from_csv()` to pass the repo.

**Note**: This is a larger refactor. It is acceptable to defer if the CSV importer is considered a utility rather than a service-layer component.

---

### Task 3.2: Reduce `BillingView` and `SettingsView` line count

**Problem**: `BillingView` is 492 lines (limit: 400). `SettingsView` is 579 lines (limit: 400).

**Approach for `BillingView`**:
- Extract the service-selection section into a helper method or a separate `ServiceSelectionWidget`.
- Extract the totals-calculation UI into a `TotalsPanel` widget.

**Approach for `SettingsView`**:
- Each tab's setup method (`setup_general_tab`, `setup_staff_tab`, etc.) could live in its own file under `app/ui/settings/`.
- Or extract each tab into a `QWidget` subclass: `GeneralSettingsTab`, `StaffSettingsTab`, etc.

**Rules**: UI file max 400 lines, max 15 methods.

---

### Task 3.3: Clean `dist/` directory

The `dist/SalonBillingSystem/_internal/app/` directory contains legacy files (`gui_billing.py`, `database.py`, `utils.py`, etc.) from an old build. These are not used at runtime but are confusing.

**Action**: Delete the `dist/` directory or add it to `.gitignore`. It will be regenerated by `pyinstaller SalonBillingSystem.spec`.

---

## Priority 4 — Future Features (Optional)

These are not blockers. Implement only after Priorities 1–3 are done.

| Feature | Where | Effort |
|---------|-------|--------|
| Google Drive cloud backup | `app/infrastructure/cloud_drive.py` | 2–3 days |
| Delete staff / delete service | `StaffService`, `ServiceCatalog`, UI | 0.5 day |
| CSV & PDF summary export | `ReportService` | 1 day |
| Keyboard shortcuts | `MainWindow` | 0.5 day |
| Dark mode / theme | Stylesheet in `MainWindow` | 1 day |
| Menu bar (File / Edit / Help) | `MainWindow` | 0.5 day |
| Status bar | `MainWindow` | 0.5 day |

---

## Execution Order (Recommended)

```
1.1  Create StaffData DTO + fix StaffService     ? do first
1.2  Fix ReportService to use BillRepository      ? do second
1.3  Add DashboardStats to DTO exports            ? quick fix
1.4  Complete UI __init__ exports                  ? quick fix
     ?
     Run tests — confirm 28/28 still pass
     ?
2.1  Add BillingService edge-case tests
2.2  Add CustomerService happy-path tests
2.3  Add StaffService tests (with StaffData)
2.4  Add ServiceCatalog tests
2.5  Add BackupService + RestoreService tests
2.6  Run coverage report — verify ? 80%
     ?
3.1  Refactor csv_service_importer (optional)
3.2  Reduce BillingView / SettingsView line count
3.3  Clean dist/ directory
     ?
4.x  Future features (only after above are done)
```

---

## Rules Checklist (Before Every Commit)

- [ ] No `db_session` imports in `app/services/` or `app/ui/`.
- [ ] No `PyQt6` imports in `app/services/`.
- [ ] No ORM models returned from services to UI — DTOs only.
- [ ] All DTOs use `@dataclass(frozen=True)`.
- [ ] All public methods have type hints and docstrings.
- [ ] No bare `except:` or silent `except Exception: pass`.
- [ ] No `print()` statements — use `logger`.
- [ ] All monetary values use `Decimal`, never `float`.
- [ ] `from __future__ import annotations` in every module.
- [ ] Tests pass: `python -m pytest -v`.
- [ ] New tests follow `test_<method>_<scenario>_<expected>` naming.
- [ ] File size limits respected (Service ? 300, UI View ? 400, DTO ? 100).
- [ ] Commit message format: `<type>(<scope>): <description>`.
