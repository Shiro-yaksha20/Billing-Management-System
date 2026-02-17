# CSV Service Import - User Guide

## Overview

The Salon Billing System now supports **bulk service management** via CSV files. You can:
- ? Import 150+ services in seconds
- ? Update prices across all services at once
- ? Filter services by category in billing
- ? Search services by name
- ? Export current services to CSV for backup

---

## Quick Start

### First-Time Setup

1. **Prepare Your CSV File**
   - Use the provided `services_full_seed.csv` template
   - Required columns: `category`, `service_name`, `display_name`, `price`
   - Optional columns: `variant`, `notes`

2. **Import Services**
   - Open the application
   - Go to **Settings ? Services** tab
   - Click **"Import Services from CSV"**
   - Select your CSV file
   - Choose import option:
     - **Yes**: Deactivate old services (recommended for fresh import)
     - **No**: Keep existing services active
   - Wait for success message

3. **Start Billing**
   - Go to **New Bill**
   - Use **Category dropdown** to filter services
   - Use **Search box** to find specific services
   - Add services to bill as normal

---

## CSV File Format

### Required Columns

```csv
category,service_name,variant,display_name,price,notes
```

### Example Rows

```csv
Basic,Eyebrow,,Basic - Eyebrow,50,
Facial,Hydra Facial,,Facial - Hydra Facial,5000,
Hair Treatment,Hair Smoothening,Short,Hair Treatment - Hair Smoothening (Short),2999,
P&M,Nail Art Simple,,P&M - Nail Art Simple,50,from 50; adjust per design
Bridal,Glass Skin Makeup Package,,Bridal - Glass Skin Makeup Package,50000,approx range 50k-60k
```

### Column Descriptions

| Column | Required | Description | Example |
|--------|----------|-------------|---------|
| `category` | ? Yes | Service category for filtering | "Basic", "Facial", "Bridal" |
| `service_name` | ? Yes | Short service name | "Eyebrow", "Hydra Facial" |
| `variant` | ? No | Size/type variation | "Short", "Medium", "Long" |
| `display_name` | ? Yes | Full name shown to users | "Facial - Hydra Facial" |
| `price` | ? Yes | Base price (can be edited during billing) | 50, 2999, 50000 |
| `notes` | ? No | Pricing notes/instructions | "from 50; adjust per design" |

---

## Import Options Explained

### Option 1: Deactivate Existing Services (Recommended)

**Use when**: Replacing entire menu with new pricing

**What happens**:
- All current services marked as `active=False`
- New services imported as `active=True`
- Old services still in database (for historical bills)
- Billing UI only shows new services

**Example**:
```
Before import: 50 active services
After import: 50 inactive + 150 new active = 200 total
Billing shows: Only the 150 new services
```

### Option 2: Keep Existing Services Active

**Use when**: Adding new services without removing old ones

**What happens**:
- Existing services remain `active=True`
- New services added as `active=True`
- Duplicate display names will be **updated** (not duplicated)

**Example**:
```
Before import: 50 active services
After import: 50 old active + 100 new active = 150 total
Billing shows: All 150 services
```

---

## Updating Prices

### Method 1: Re-import CSV with Updated Prices

1. Edit your CSV file with new prices
2. Go to **Settings ? Services ? Import Services from CSV**
3. Select **"No"** to keep existing services active
4. Import will **update** existing services by matching `display_name`

### Method 2: Export ? Edit ? Re-import

1. **Export** current services to CSV
2. Edit prices in Excel/spreadsheet software
3. **Re-import** the modified CSV
4. Services with matching `display_name` will be updated

---

## Category Management

### Available Categories (from your CSV)

1. **Basic** - Threading, waxing basics
2. **Bleach/Detan** - Bleach types, detan, cleanup
3. **Facial** - All facial treatments
4. **Waxing - Honey** - Honey wax services
5. **Waxing - Rica** - Rica wax services
6. **Waxing - Roll-On** - Roll-on wax services
7. **P&M** - Pedicure & Manicure
8. **Hair Spa & Oil** - Hair treatments
9. **Haircut** - All haircut types
10. **Hair Treatment** - Smoothening, straightening, keratin
11. **Hair Styling** - Curls, straightening, braids
12. **Colour** - Single color services
13. **Colour Multi** - Multi-color services by hair length
14. **Bridal** - Bridal packages

### Using Categories in Billing

1. Open **New Bill** window
2. Under **Services** section, find **Category dropdown**
3. Select a category (e.g., "Facial")
4. Service dropdown now shows **only facial services**
5. Add to bill as normal

### Using Search in Billing

1. Open **New Bill** window
2. Type in **Search box**: "hydra"
3. Service dropdown filters to matching services
4. Works with category filter (both can be used together)

**Search matches**:
- Service name
- Display name
- Notes field

---

## Variant Support

### Hair Length Variants

Many services have **Short/Medium/Long** pricing:

```csv
Hair Treatment,Hair Smoothening,Short,Hair Treatment - Hair Smoothening (Short),2999,
Hair Treatment,Hair Smoothening,Medium,Hair Treatment - Hair Smoothening (Medium),4999,
Hair Treatment,Hair Smoothening,Long,Hair Treatment - Hair Smoothening (Long),7999,
```

**Result in UI**:
- 3 separate service entries
- Each with different price
- All in "Hair Treatment" category

### Waxing Type Variants

Waxing has **Honey/Rica/Roll-On** types:

```csv
Waxing - Honey,Full Arm,,Waxing - Honey - Full Arm,350,
Waxing - Rica,Full Arm,,Waxing - Rica - Full Arm,550,
Waxing - Roll-On,Full Arm,,Waxing - Roll-On - Full Arm,750,
```

**Result in UI**:
- 3 categories: "Waxing - Honey", "Waxing - Rica", "Waxing - Roll-On"
- Each with own pricing

---

## Notes Field Usage

### Flexible Pricing Notes

```csv
P&M,Nail Art Simple,,P&M - Nail Art Simple,50,from 50; adjust per design
```

**In billing**:
- Base price shows as ?50
- Staff can edit price in table (e.g., ?80 for complex design)
- Notes remind staff about flexibility

### Package Range Notes

```csv
Bridal,Glass Skin Makeup Package,,Bridal - Glass Skin Makeup Package,50000,approx range 50k-60k
```

**In billing**:
- Shows ?50,000 as starting price
- Notes remind staff package can go up to ?60,000

---

## Troubleshooting

### Import Shows Errors

**Problem**: "Invalid price" errors

**Solution**: Check CSV for:
- Empty price cells (use `0` if free)
- Non-numeric characters (remove ?, commas)
- Correct decimal format (use `.` not `,`)

### Duplicate Services

**Problem**: Same service appears twice

**Solution**: 
- Services with same `display_name` will update, not duplicate
- Check `display_name` column for uniqueness
- Use variant column for sizes: "Service (Short)", "Service (Medium)"

### Category Not Showing

**Problem**: Category doesn't appear in dropdown

**Solution**:
- At least one service must be `active=True` in that category
- Check spelling in `category` column (case-sensitive)
- Re-import CSV to ensure category is set

### Services Not Filtering

**Problem**: Category filter doesn't work

**Solution**:
- Ensure services have `category` field populated
- Restart application to reload services
- Check database with export function

---

## Best Practices

### 1. Backup Before Import

**Always export current services before bulk import**:
1. Go to Settings ? Services
2. Click "Export Services to CSV"
3. Save as `services_backup_YYYY-MM-DD.csv`

### 2. Test with Small CSV First

Before importing 150+ services:
1. Create test CSV with 5-10 services
2. Import and verify
3. Once confident, import full menu

### 3. Use Consistent Naming

**Good**:
```
Facial - Fruit Facial
Facial - Gold Facial
Facial - Hydra Facial
```

**Bad**:
```
Fruit Facial (Facial Category)
Gold-Facial
facial-hydra
```

### 4. Maintain CSV in Excel

- Keep master CSV in Excel/Google Sheets
- Update prices seasonally
- Version control (save with dates)

### 5. Deactivate vs Delete

**Never delete services** if they appear in historical bills:
- Use "Deactivate existing" during import
- Old bills still reference old service prices
- Inactive services hidden from billing UI

---

## Migration from Old System

If you have existing services in the database:

### Option A: Fresh Start (Recommended)

1. Export old services as backup
2. Import new CSV with "Deactivate existing"
3. All new services active, old ones archived

### Option B: Gradual Migration

1. Import new CSV with "Keep existing active"
2. Manually deactivate old services in Settings
3. Remove duplicates over time

---

## API Reference (for Developers)

### Import Function

```python
from app.csv_service_importer import import_services_from_csv

results = import_services_from_csv(
    csv_file_path='path/to/services.csv',
    clear_existing=False,      # DANGEROUS: Deletes all services
    deactivate_existing=True   # Safer: Marks old services inactive
)

# Returns:
{
    'success': True,
    'imported': 120,
    'updated': 30,
    'skipped': 2,
    'errors': [],
    'deactivated': 50
}
```

### Export Function

```python
from app.csv_service_importer import export_services_to_csv

export_services_to_csv(
    csv_file_path='export.csv',
    active_only=True
)
```

---

## Support

If you encounter issues:

1. Check application logs in `app/utils.py`
2. Verify CSV format matches template
3. Test with small CSV subset
4. Export current services to compare format

---

**Last Updated**: 2024  
**Version**: 1.0  
**Feature**: CSV Service Import/Export
