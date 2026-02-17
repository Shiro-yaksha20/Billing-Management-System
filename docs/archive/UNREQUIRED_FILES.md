# ??? Unrequired Files in Workspace
**Date**: February 2026  
**Purpose**: Track legacy/duplicate/obsolete files that can be safely removed

---

## ?? Important Note

**DO NOT DELETE** these files without first:
1. Ensuring all imports have been migrated
2. Running `python -m pytest` to verify nothing breaks
3. Creating a backup/commit before removal

---

## ?? Legacy Python Files (Duplicates)

These files are **superseded** by the new clean architecture and should be removed:

| File | Reason | Replacement |
|------|--------|-------------|
| `app/backup_service.py` | Duplicate of service layer | `app/services/backup_service.py` |
| `app/settings_service.py` | Duplicate of service layer | `app/services/settings_service.py` |
| `app/export_service.py` | Duplicate of service layer | `app/services/report_service.py` |

### Migration Status for Legacy Files

```
app/backup_service.py
??? Status: SUPERSEDED
??? Uses: app.infrastructure.logging (correct)
??? Action: Remove after verifying app/services/backup_service.py works
??? Risk: LOW - service layer has equivalent class

app/settings_service.py  
??? Status: SUPERSEDED
??? Uses: app.infrastructure.database (correct)
??? Action: Remove after verifying app/services/settings_service.py works
??? Note: Some files may still import from here (check imports)
??? Risk: MEDIUM - widely used, verify all callers migrated

app/export_service.py
??? Status: SUPERSEDED  
??? Uses: app.infrastructure.database (correct)
??? Action: Remove after verifying app/services/report_service.py works
??? Risk: LOW - UI export_view likely only caller
```

---

## ?? Unrelated Project Files

The `ConsoleApp1/` directory appears to be an unrelated .NET project:

| Path | Description | Action |
|------|-------------|--------|
| `ConsoleApp1/` | .NET 8.0 console app | Can be removed entirely |
| `ConsoleApp1.sln` | Visual Studio solution | Can be removed |
| `ConsoleApp1/Program.cs` | C# entry point | Can be removed |
| `ConsoleApp1/Dockerfile` | Docker config for .NET | Can be removed |
| `ConsoleApp1/ConsoleApp1.csproj` | C# project file | Can be removed |
| `ConsoleApp1/obj/` | Build artifacts | Can be removed |
| `ConsoleApp1/Properties/` | .NET properties | Can be removed |

**Note**: This appears to be a separate project that was accidentally committed to the Python repository.

---

## ?? Obsolete Documentation Files

These planning/tracking documents may be obsolete after refactoring:

| File | Status | Action |
|------|--------|--------|
| `APP_IMPROVEMENTS_PLAN.md` | Partially implemented | Archive or update |
| `RECEIPT_IMPLEMENTATION_PLAN.md` | Implemented | Archive |
| `RECEIPT_FEATURES_COMPLETION_REPORT.md` | Completed | Archive |
| `TESTING_STRATEGY_PLAN.md` | Partially implemented | Update or archive |
| `CODE_FIXES_UPDATES.md` | Reference doc | Keep for history |
| `DETACHED_ORM_SCAN_REPORT.md` | Fixed | Archive |
| `SOFTWARE_DATA_REVIEW.md` | Reference | Keep or archive |
| `UI_DATA_REPORT.md` | Reference | Keep or archive |
| `CSV_IMPORT_GUIDE.md` | User guide | Keep |

### Recommended Action
Create an `docs/archive/` folder and move completed planning documents there.

---

## ?? Generated/Cache Files

These are auto-generated and safe to remove (they'll be recreated):

| Path | Description |
|------|-------------|
| `.pytest_cache/` | Pytest cache |
| `__pycache__/` | Python bytecode |
| `*.pyc` | Compiled Python |
| `logs/app.log` | Log file (grows over time) |
| `salon_billing.db` | Database (don't delete if contains data!) |
| `receipts/` | Generated PDFs |
| `backups/` | Database backups |

---

## ?? Files to Keep

### Core Application
- All files under `app/ui/`
- All files under `app/services/`
- All files under `app/repositories/`
- All files under `app/dto/`
- All files under `app/exceptions/`
- All files under `app/infrastructure/`
- `app/models.py`
- `app/constants.py`
- `app/__init__.py`
- `app/csv_service_importer.py`
- `app/migrate_*.py` (migration scripts)

### Tests
- All files under `tests/`

### Configuration
- `main.py`
- `requirements.txt`
- `requirements-dev.txt`
- `pyproject.toml`
- `pytest.ini`
- `mypy.ini`
- `.flake8`
- `.pylintrc`
- `.pre-commit-config.yaml`
- `SalonBillingSystem.spec`
- `.env.example`
- `.gitignore`
- `.gitattributes`
- `.dockerignore`

### Documentation
- `README.md`
- `PLAN.md`
- `CHANGELOG.md`
- `WORKSPACE_AUDIT.md`
- `UNREQUIRED_FILES.md` (this file)

### Build/Release
- `scripts/build_exe.bat`
- `.github/workflows/release.yml`
- `setup.py`
- `releases/` (distribution packages)

---

## ?? Cleanup Checklist

Before removing any file, complete this checklist:

- [ ] Search for imports: `grep -r "from app.backup_service" .`
- [ ] Search for imports: `grep -r "from app.settings_service" .`
- [ ] Search for imports: `grep -r "from app.export_service" .`
- [ ] Run tests: `python -m pytest -v`
- [ ] Run application: `python main.py`
- [ ] Create Git commit/backup

### Cleanup Commands (after verification)

```bash
# Remove legacy Python files
rm app/backup_service.py
rm app/settings_service.py
rm app/export_service.py

# Remove unrelated .NET project
rm -rf ConsoleApp1/
rm ConsoleApp1.sln

# Archive old planning docs
mkdir -p docs/archive
mv APP_IMPROVEMENTS_PLAN.md docs/archive/
mv RECEIPT_IMPLEMENTATION_PLAN.md docs/archive/
mv RECEIPT_FEATURES_COMPLETION_REPORT.md docs/archive/
mv DETACHED_ORM_SCAN_REPORT.md docs/archive/
```

---

## ?? Import Dependency Check

Files that may still reference legacy modules:

### `app/settings_service.py` (legacy) is imported by:
- `app/infrastructure/pdf_generator.py` ? Uses `.. import settings_service`
- Check: May need to update to use `app.services.settings_service`

### `app/backup_service.py` (legacy) vs `app/services/backup_service.py`:
- `main.py` ? Uses `app.services.BackupService` ?
- No other direct imports found

### `app/export_service.py` (legacy) vs `app/services/report_service.py`:
- `app/ui/export_view.py` ? Verify which is used
- May need migration

---

*Last updated: February 2026*
