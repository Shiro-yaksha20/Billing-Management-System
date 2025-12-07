# Testing Strategy Plan
**Date**: 2025-12-07  
**Status**: PLANNING PHASE - No Implementation Yet

---

## Objective

Create a comprehensive testing strategy to validate all implemented features:
- Run every function and check for failures
- Verify data integrity across the application
- Document test results

---

## Testing Approaches

### Option 1: Manual Testing Checklist
Run the application and manually test each feature, documenting results.

### Option 2: Automated Unit Tests
Create `pytest` test files to programmatically test each module.

### Option 3: Integration Test Script
Create a single script that exercises all features and logs results.

---

## Recommended Approach: Automated Test Suite

### Files to Create:
1. `tests/test_models.py` - Test database models
2. `tests/test_billing.py` - Test billing logic
3. `tests/test_export.py` - Test Excel export
4. `tests/test_pdf.py` - Test PDF generation
5. `tests/test_settings.py` - Test settings service
6. `tests/run_all_tests.py` - Master test runner

### Dependencies Required:
```
pytest>=7.0.0
pytest-qt>=4.0.0  # For PyQt6 GUI testing
```

---

## Test Plan by Module

### 1. Database Models (`app/models.py`)

| Test Case | Function/Feature | Expected Result |
|-----------|------------------|-----------------|
| T1.1 | Create Customer | Customer saved with id |
| T1.2 | Create Staff | Staff saved with id |
| T1.3 | Create Service | Service saved with id |
| T1.4 | Create Bill with items | Bill and BillItems saved |
| T1.5 | Bill.transaction_id column | Accepts string or None |
| T1.6 | Bill.payment_status column | Defaults to "Paid" |
| T1.7 | Customer.last_visit_at | Accepts DateTime |
| T1.8 | Setting key-value | Saves and retrieves |

### 2. Settings Service (`app/settings_service.py`)

| Test Case | Function/Feature | Expected Result |
|-----------|------------------|-----------------|
| T2.1 | get_setting(existing) | Returns saved value |
| T2.2 | get_setting(missing) | Returns default |
| T2.3 | set_setting(new) | Creates setting |
| T2.4 | set_setting(update) | Updates existing |
| T2.5 | salon_instagram setting | Saves/loads correctly |
| T2.6 | salon_tagline setting | Saves/loads correctly |
| T2.7 | salon_logo_path setting | Saves/loads correctly |
| T2.8 | google_review_link setting | Saves/loads correctly |
| T2.9 | receipt_footer_message setting | Saves/loads correctly |

### 3. Billing Logic (`app/gui_billing.py`)

| Test Case | Function/Feature | Expected Result |
|-----------|------------------|-----------------|
| T3.1 | save_bill() creates Bill | Bill saved to database |
| T3.2 | save_bill() updates last_visit_at | Customer.last_visit_at updated |
| T3.3 | save_bill() saves transaction_id | Bill.transaction_id persisted |
| T3.4 | save_bill() saves payment_status | Bill.payment_status persisted |
| T3.5 | Subtotal calculation | Correct sum of line items |
| T3.6 | Discount flat | Correct deduction |
| T3.7 | Discount percent | Correct percentage |
| T3.8 | Tax calculation | Correct tax amount |
| T3.9 | Total calculation | Subtotal - discount + tax |

### 4. PDF Generator (`app/pdf_generator.py`)

| Test Case | Function/Feature | Expected Result |
|-----------|------------------|-----------------|
| T4.1 | generate_receipt_pdf(valid_id) | Returns file path |
| T4.2 | PDF file exists | File created at returned path |
| T4.3 | PDF contains salon name | Text present in PDF |
| T4.4 | PDF contains Instagram | Instagram handle if set |
| T4.5 | PDF contains GST | GST number if set |
| T4.6 | PDF contains transaction_id | Transaction ID if present |
| T4.7 | PDF contains payment_status | Payment status displayed |
| T4.8 | PDF contains services | All bill items listed |
| T4.9 | PDF contains totals | Subtotal, discount, tax, total |
| T4.10 | PDF contains stylist | Staff name displayed |
| T4.11 | Currency symbol | ? or Rs. displayed correctly |

### 5. Export Service (`app/export_service.py`)

| Test Case | Function/Feature | Expected Result |
|-----------|------------------|-----------------|
| T5.1 | export_bills_to_excel(all) | Excel file created |
| T5.2 | Export with date filter | Only matching bills |
| T5.3 | Export with customer filter | Only customer's bills |
| T5.4 | Excel has correct headers | 19 columns as defined |
| T5.5 | Excel has correct data | All bill items exported |
| T5.6 | Transaction ID column | Contains bill transaction_id |
| T5.7 | Payment status column | Contains bill payment_status |

### 6. Customer Window (`app/gui_customers.py`)

| Test Case | Function/Feature | Expected Result |
|-----------|------------------|-----------------|
| T6.1 | load_customers() | Populates customer table |
| T6.2 | search_customers() | Filters by name/phone |
| T6.3 | display_customer_notes() | Shows notes and bills |
| T6.4 | Bills table populates | Shows customer's bills |
| T6.5 | view_selected_receipt() | Opens PDF if exists |
| T6.6 | CustomerDialog scrollable | Content scrolls |
| T6.7 | save_customer() new | Creates customer |
| T6.8 | save_customer() edit | Updates customer |

### 7. GUI Settings (`app/gui_settings.py`)

| Test Case | Function/Feature | Expected Result |
|-----------|------------------|-----------------|
| T7.1 | load_general_settings() | Populates all fields |
| T7.2 | save_general_settings() | Saves all fields |
| T7.3 | browse_logo_file() | Opens file dialog |
| T7.4 | Instagram field | Saves/loads |
| T7.5 | Tagline field | Saves/loads |
| T7.6 | Logo path field | Saves/loads |
| T7.7 | Review link field | Saves/loads |
| T7.8 | Footer message field | Saves/loads |

---

## Data Integrity Checks

### Database Schema Verification

| Check | Table | Column | Type | Required |
|-------|-------|--------|------|----------|
| D1.1 | bill | transaction_id | String | No |
| D1.2 | bill | payment_status | String | No (default "Paid") |
| D1.3 | customer | last_visit_at | DateTime | No |
| D1.4 | setting | key | String | Yes (unique) |
| D1.5 | setting | value | Text | No |

### Foreign Key Relationships

| Check | From Table | To Table | Relationship |
|-------|------------|----------|--------------|
| D2.1 | bill | customer | bill.customer_id ? customer.id |
| D2.2 | bill | staff | bill.staff_id ? staff.id |
| D2.3 | bill_item | bill | bill_item.bill_id ? bill.id |
| D2.4 | bill_item | service | bill_item.service_id ? service.id |

### Data Consistency Checks

| Check | Validation | Expected |
|-------|------------|----------|
| D3.1 | All bills have customer_id | No NULL |
| D3.2 | All bills have staff_id | No NULL |
| D3.3 | All bill_items have bill_id | No NULL |
| D3.4 | Bill totals match calculations | total = subtotal - discount + tax |
| D3.5 | payment_status valid values | "Paid" or "Pending" |

---

## Test Execution Plan

### Step 1: Setup Test Database
```python
# Create isolated test database
import tempfile
test_db = tempfile.mktemp(suffix='.db')
```

### Step 2: Run Model Tests
```bash
pytest tests/test_models.py -v
```

### Step 3: Run Service Tests
```bash
pytest tests/test_settings.py -v
pytest tests/test_export.py -v
pytest tests/test_pdf.py -v
```

### Step 4: Run GUI Tests (requires display)
```bash
pytest tests/test_billing.py -v
pytest tests/test_customers.py -v
```

### Step 5: Run All Tests
```bash
pytest tests/ -v --tb=short
```

---

## Test Script Outline

### `tests/run_all_tests.py`

```python
"""
Master test runner that exercises all functions and logs results.
Run with: python -m tests.run_all_tests
"""
import sys
import traceback
from datetime import datetime

results = []

def log_result(test_name, passed, error=None):
    results.append({
        'test': test_name,
        'passed': passed,
        'error': str(error) if error else None,
        'timestamp': datetime.now().isoformat()
    })

def test_database_connection():
    from app.database import db_session
    with db_session() as db:
        # Simple query to verify connection
        db.execute("SELECT 1")
    return True

def test_models():
    from app.models import Customer, Staff, Service, Bill, BillItem, Setting
    # Verify all models can be imported
    return True

def test_settings_service():
    from app import settings_service
    # Test get/set
    settings_service.set_setting("_test_key", "test_value")
    val = settings_service.get_setting("_test_key")
    assert val == "test_value"
    return True

def test_pdf_generation():
    from app.pdf_generator import generate_receipt_pdf
    # Would need a valid bill_id to test fully
    return True

def test_export_service():
    from app.export_service import export_bills_to_excel
    import tempfile
    output = tempfile.mktemp(suffix='.xlsx')
    result = export_bills_to_excel(output)
    return result

def run_all():
    tests = [
        ("Database Connection", test_database_connection),
        ("Models Import", test_models),
        ("Settings Service", test_settings_service),
        ("Export Service", test_export_service),
    ]
    
    for name, func in tests:
        try:
            func()
            log_result(name, True)
        except Exception as e:
            log_result(name, False, e)
            traceback.print_exc()
    
    # Print summary
    passed = sum(1 for r in results if r['passed'])
    failed = len(results) - passed
    print(f"\n{'='*50}")
    print(f"RESULTS: {passed} passed, {failed} failed")
    print(f"{'='*50}")
    
    for r in results:
        status = "? PASS" if r['passed'] else "? FAIL"
        print(f"{status}: {r['test']}")
        if r['error']:
            print(f"   Error: {r['error']}")

if __name__ == "__main__":
    run_all()
```

---

## How to Run Tests

### Manual Testing:
1. Run the application: `python -m app.main`
2. Go through each feature manually
3. Document results in checklist

### Automated Testing:
1. Install pytest: `pip install pytest pytest-qt`
2. Run: `python -m tests.run_all_tests`
3. View results in console

### Continuous Testing:
1. Set up GitHub Actions workflow
2. Run tests on every commit

---

## Output Files

### Test Results File: `TEST_RESULTS.md`
Will contain:
- Test execution timestamp
- Pass/fail status for each test
- Error messages for failures
- Summary statistics

### Data Integrity Report: `DATA_INTEGRITY_REPORT.md`
Will contain:
- Database schema verification
- Foreign key validation
- Data consistency checks
- Any orphaned records
- Any invalid data

---

## Implementation Steps

1. Create `tests/` directory
2. Create `tests/__init__.py`
3. Create `tests/run_all_tests.py`
4. Create `tests/test_models.py`
5. Create `tests/test_settings.py`
6. Create `tests/test_export.py`
7. Create `tests/test_pdf.py`
8. Add pytest to requirements.txt
9. Run tests
10. Generate TEST_RESULTS.md
11. Generate DATA_INTEGRITY_REPORT.md

---

## Estimated Time

| Task | Time |
|------|------|
| Create test directory structure | 15 min |
| Write model tests | 30 min |
| Write service tests | 30 min |
| Write export tests | 20 min |
| Write PDF tests | 20 min |
| Run tests | 10 min |
| Generate reports | 15 min |
| **TOTAL** | **2-3 hours** |

---

**Status**: PLANNING COMPLETE - AWAITING APPROVAL TO IMPLEMENT
