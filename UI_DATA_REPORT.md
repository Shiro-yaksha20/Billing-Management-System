# Salon Billing System - Complete UI Data Report

## Executive Summary
This comprehensive report documents all user interfaces, data inputs, datasets, and data flows in the Salon Billing System application. The system is built using PyQt6 and SQLAlchemy with a SQLite database backend.

---

## Table of Contents
1. [Database Schema & Data Models](#database-schema--data-models)
2. [Main Window](#main-window)
3. [Billing Window](#billing-window)
4. [Customer Management](#customer-management)
5. [Settings Window](#settings-window)
6. [Bill History Window](#bill-history-window)
7. [Data Validation Rules](#data-validation-rules)
8. [Data Flow Summary](#data-flow-summary)

---

## 1. Database Schema & Data Models

### 1.1 Customer Table
**Purpose**: Stores customer information for billing and contact purposes

| Field Name | Data Type | Required | Description |
|------------|-----------|----------|-------------|
| `id` | Integer | Yes | Primary key, auto-increment |
| `name` | String | Yes | Customer's full name |
| `phone` | String | Yes | Customer's phone number (used for WhatsApp) |
| `notes` | Text | No | Additional notes about the customer |
| `last_visit_at` | DateTime | No | Automatically updated with last bill date |
| `created_at` | DateTime | Yes | Auto-generated timestamp |
| `updated_at` | DateTime | Yes | Auto-updated timestamp |

**Relationships**: 
- One-to-Many with Bills (customer can have multiple bills)

---

### 1.2 Staff Table
**Purpose**: Manages salon staff members who perform services

| Field Name | Data Type | Required | Description |
|------------|-----------|----------|-------------|
| `id` | Integer | Yes | Primary key, auto-increment |
| `name` | String | Yes | Staff member's name |
| `phone` | String | No | Staff member's phone number |
| `role` | String | No | Job title/role (e.g., "Stylist", "Manager") |
| `active` | Boolean | Yes | Whether staff is currently active (default: True) |
| `created_at` | DateTime | Yes | Auto-generated timestamp |
| `updated_at` | DateTime | Yes | Auto-updated timestamp |

**Relationships**: 
- One-to-Many with Bills (staff member can handle multiple bills)

---

### 1.3 Service Table
**Purpose**: Catalog of services offered by the salon

| Field Name | Data Type | Required | Description |
|------------|-----------|----------|-------------|
| `id` | Integer | Yes | Primary key, auto-increment |
| `name` | String | Yes | Service name (e.g., "Haircut", "Coloring") |
| `description` | String | No | Detailed service description |
| `price` | Decimal(10,2) | No | Default price for the service |
| `duration_minutes` | Integer | No | Expected duration in minutes |
| `active` | Boolean | Yes | Whether service is currently offered (default: True) |
| `created_at` | DateTime | Yes | Auto-generated timestamp |
| `updated_at` | DateTime | Yes | Auto-updated timestamp |

**Relationships**: 
- One-to-Many with BillItems (service can appear in multiple bills)

---

### 1.4 Bill Table
**Purpose**: Main billing/invoice records

| Field Name | Data Type | Required | Description |
|------------|-----------|----------|-------------|
| `id` | Integer | Yes | Primary key, auto-increment |
| `bill_number` | String | Yes | Unique bill identifier |
| `customer_id` | Integer | Yes | Foreign key to Customer |
| `staff_id` | Integer | Yes | Foreign key to Staff |
| `bill_datetime` | DateTime | Yes | Bill creation date/time (default: current UTC) |
| `subtotal` | Decimal(10,2) | No | Sum of all line items |
| `discount_amount` | Decimal(10,2) | No | Calculated discount (default: 0) |
| `discount_type` | Enum | Yes | "flat", "percent", or "none" (default: "none") |
| `tax_amount` | Decimal(10,2) | No | Calculated tax amount (default: 0) |
| `tax_percent` | Decimal(5,2) | No | Tax percentage applied |
| `total` | Decimal(10,2) | Yes | Final bill total (subtotal - discount + tax) |
| `payment_method` | Enum | Yes | "Cash", "UPI", "Card", "Other" (default: "Cash") |
| `status` | Enum | Yes | "Paid", "Pending", "Cancelled" (default: "Paid") |
| `pdf_path` | String | No | File path to generated PDF receipt |
| `whatsapp_status` | Enum | Yes | "Not Sent", "Sent", "Failed" (default: "Not Sent") |
| `whatsapp_last_error` | Text | No | Error message from failed WhatsApp send |
| `created_at` | DateTime | Yes | Auto-generated timestamp |
| `updated_at` | DateTime | Yes | Auto-updated timestamp |

**Relationships**: 
- Many-to-One with Customer
- Many-to-One with Staff
- One-to-Many with BillItems (cascade delete)

---

### 1.5 BillItem Table
**Purpose**: Line items for each bill (services purchased)

| Field Name | Data Type | Required | Description |
|------------|-----------|----------|-------------|
| `id` | Integer | Yes | Primary key, auto-increment |
| `bill_id` | Integer | Yes | Foreign key to Bill |
| `service_id` | Integer | Yes | Foreign key to Service |
| `quantity` | Integer | Yes | Number of times service was performed (default: 1) |
| `unit_price` | Decimal(10,2) | No | Price at time of sale (can differ from current service price) |
| `line_total` | Decimal(10,2) | No | Quantity × Unit Price |

**Relationships**: 
- Many-to-One with Bill
- Many-to-One with Service

---

### 1.6 Setting Table
**Purpose**: Application-wide configuration settings

| Field Name | Data Type | Required | Description |
|------------|-----------|----------|-------------|
| `id` | Integer | Yes | Primary key, auto-increment |
| `key` | String | Yes | Unique setting name |
| `value` | Text | No | Setting value (stored as string) |

**Common Settings Keys**:
- `salon_name`: Business name
- `salon_address`: Physical address
- `salon_phone`: Contact number
- `salon_gstin`: GST identification number
- `default_tax_percent`: Default tax percentage
- `thank_you_message`: Receipt footer message
- `whatsapp_phone_id`: WhatsApp Business API phone ID
- `whatsapp_account_id`: WhatsApp Business account ID
- `whatsapp_api_version`: API version (e.g., "v15.0")
- `whatsapp_country_code`: Default country code (e.g., "91")
- `whatsapp_message_template`: Message template with placeholders

**Sensitive Settings** (stored in system keyring):
- `whatsapp_api_token`: WhatsApp Business API access token

---

## 2. Main Window

### 2.1 Window Properties
- **Window Title**: "Salon Billing System"
- **Default Size**: 800×600 pixels
- **Purpose**: Main navigation hub

### 2.2 UI Components

| Component | Type | Label/Text | Action |
|-----------|------|------------|--------|
| Settings Button | QPushButton | "Settings" | Opens Settings dialog (modal) |
| Customers Button | QPushButton | "Manage Customers" | Opens Customer Management dialog (modal) |
| New Bill Button | QPushButton | "New Bill" | Opens Billing dialog (modal) |
| Placeholder Area | QPushButton (disabled) | "Main Billing Area (Placeholder)" | Visual placeholder for future dashboard |

### 2.3 Data Flow
- No direct data input
- Acts as navigation gateway to other modules

---

## 3. Billing Window

### 3.1 Window Properties
- **Window Title**: "New Bill"
- **Minimum Width**: 900 pixels
- **Layout**: Two-panel (Left: Bill Details, Right: Totals & Notes)
- **Purpose**: Create new customer bills

### 3.2 Customer Section (GroupBox: "Customer")

#### Input Fields

| Field Name | Widget Type | Placeholder/Label | Data Type | Required | Notes |
|------------|-------------|-------------------|-----------|----------|-------|
| Customer Search | QLineEdit | "Search phone or name..." | String | No | Searches by phone (exact) or name (partial match) |
| New Customer Button | QPushButton | "New Customer" | Action | - | Opens CustomerDialog |
| Customer Name Display | QLabel | "Name: " | String | Display Only | Shows selected customer name |
| Customer Phone Display | QLabel | "Phone: " | String | Display Only | Shows selected customer phone |

#### Search Behavior
- **Enter Key**: Triggers customer search
- **Search Logic**: 
  - Exact match on phone number OR
  - Case-insensitive partial match on name
- **Not Found**: Shows information dialog "No customer found with that name or phone number"

---

### 3.3 Staff Section (GroupBox: "Staff")

| Field Name | Widget Type | Label | Data Source | Required | Notes |
|------------|-------------|-------|-------------|----------|-------|
| Staff Selection | QComboBox | "Select Staff:" | Active staff from database | Yes | Only shows staff where `active=True` |

**ComboBox Data Structure**:
- Display Text: Staff name
- User Data: Staff ID

---

### 3.4 Services Section (GroupBox: "Services")

#### Services Table

| Column Name | Editable | Data Type | Description |
|-------------|----------|-----------|-------------|
| Service | No | String | Service name from catalog |
| Qty | Yes | Integer | Quantity/count (editable in table) |
| Price | Yes | Decimal | Unit price (editable in table) |
| Total | Auto-calculated | Decimal | Qty × Price (read-only, auto-updates) |
| ID | Hidden | Integer | Service ID (hidden column) |

#### Service Controls

| Field Name | Widget Type | Label | Data Source | Action |
|------------|-------------|-------|-------------|--------|
| Service Selector | QComboBox | - | Active services from database | Only shows services where `active=True` |
| Add Service Button | QPushButton | "Add Service" | - | Adds selected service to table with qty=1 |
| Remove Service Button | QPushButton | "Remove Service" | - | Removes currently selected row from table |

**ComboBox Display Format**: `{service.name} - ?{service.price}`

#### Table Behavior
- **Cell Changed Event**: 
  - When Qty or Price column edited ? recalculates line Total
  - Auto-updates bill totals section
- **Validation**: Handles ValueError/TypeError for partial inputs

---

### 3.5 Customer Notes Section (GroupBox: "Customer Notes")

| Field Name | Widget Type | Data Type | Required | Notes |
|------------|-------------|-----------|----------|-------|
| Customer Notes | QTextEdit | Text | No | Auto-populated when customer selected; saved to customer record |

---

### 3.6 Totals Section (GroupBox: "Totals")

| Field Name | Widget Type | Label | Data Type | Default | Editable | Notes |
|------------|-------------|-------|-----------|---------|----------|-------|
| Subtotal Display | QLabel | "Subtotal:" | Decimal | ? 0.00 | No | Sum of all service line totals |
| Discount Type | QComboBox | "Discount:" | Enum | "Flat (?)" | Yes | Options: "Flat (?)", "Percent (%)" |
| Discount Value | QLineEdit | - | Decimal | 0 | Yes | Numeric input for discount amount/percentage |
| Tax Percentage | QLineEdit | "Tax (%):" | Decimal | 0 | Yes | Tax percentage (e.g., 18 for 18% GST) |
| Total Display | QLabel | "Total:" | Decimal | ? 0.00 | No | Subtotal - Discount + Tax |

#### Calculation Logic
```
Subtotal = Sum of all line_total values

IF discount_type == "Flat (?)":
    discount_amount = discount_value
ELSE IF discount_type == "Percent (%)":
    discount_amount = subtotal × (discount_value / 100)

total_before_tax = subtotal - discount_amount
tax_amount = total_before_tax × (tax_percent / 100)
total = total_before_tax + tax_amount
```

#### Live Updates
- Automatically recalculates on:
  - Service table changes (add/remove/edit)
  - Discount value change
  - Tax percentage change
  - Discount type change

---

### 3.7 Payment Section (GroupBox: "Payment")

| Field Name | Widget Type | Label | Options | Default | Required |
|------------|-------------|-------|---------|---------|----------|
| Payment Method | QComboBox | "Payment Method:" | Cash, UPI, Card, Other | Cash | Yes |

---

### 3.8 Action Buttons

| Button Name | Label | Action | Validations |
|-------------|-------|--------|-------------|
| Save Bill | "Save Bill" | Saves bill to database | Customer must be selected |
| Save & Send | "Save, PDF & Send" | Saves bill + generates PDF + sends WhatsApp | Customer must be selected |

#### Save Bill Process
1. Validates customer is selected
2. Creates Bill record with:
   - `customer_id` from selected customer
   - `staff_id` from staff combo
   - `payment_method` from payment combo
3. Creates BillItem records for each service in table
4. Calculates and stores:
   - `subtotal`
   - `discount_type` ("flat" or "percent")
   - `discount_amount`
   - `tax_percent`
   - `tax_amount`
   - `total`
5. Updates customer's `last_visit_at`
6. Generates `bill_number` (uses bill ID)
7. Shows confirmation message
8. If "Save & Send": calls `generate_and_send()`

#### Generate and Send Process
1. **PDF Generation**:
   - Calls `generate_receipt_pdf(bill_id)`
   - Saves PDF path to bill record
   - Shows success message with path
2. **WhatsApp Sending**:
   - Retrieves customer phone
   - Formats message using template:
     - `{customer_name}` ? Customer's name
     - `{salon_name}` ? From settings
     - `{total}` ? Bill total with 2 decimal places
   - Prepends country code to phone
   - Sends message with PDF attachment
   - Updates `whatsapp_status` ("Sent" or "Failed")
   - Stores error in `whatsapp_last_error` if failed
   - Shows success/failure dialog

---

## 4. Customer Management

### 4.1 Customer Window (Main)

#### Window Properties
- **Window Title**: "Manage Customers"
- **Minimum Width**: 800 pixels
- **Purpose**: View and manage customer database

#### Search Section

| Field Name | Widget Type | Placeholder | Search Logic |
|------------|-------------|-------------|--------------|
| Search Input | QLineEdit | "Search by name or phone..." | Case-insensitive partial match on name OR phone |
| Search Button | QPushButton | "Search" | Triggers filtered customer list |

#### Customer Table

| Column Name | Data Type | Source Field | Notes |
|-------------|-----------|--------------|-------|
| Name | String | `customer.name` | Display only |
| Phone | String | `customer.phone` | Display only |
| Last Visit | Date | `customer.last_visit_at` | Format: "YYYY-MM-DD" or "N/A" |
| ID | Integer | `customer.id` | Hidden column |

**Table Properties**:
- Selection Mode: Select entire rows
- Edit Triggers: None (read-only)
- Selection Changed ? Displays customer notes below table

#### Customer Notes Display

| Field Name | Widget Type | Data Type | Editable |
|------------|-------------|-----------|----------|
| Notes Area | QTextEdit | Text | No (read-only) |

**Behavior**: Auto-populates when row selected in table

#### Action Buttons

| Button | Label | Action |
|--------|-------|--------|
| Add Customer | "Add Customer" | Opens CustomerDialog in Add mode |
| Edit Customer | "Edit Customer" | Opens CustomerDialog in Edit mode for selected customer |

---

### 4.2 Customer Dialog (Add/Edit)

#### Window Properties
- **Window Title**: "Add Customer" or "Edit Customer"
- **Mode**: Modal dialog
- **Purpose**: Create new or edit existing customer

#### Input Fields

| Field Name | Widget Type | Label | Data Type | Required | Max Length | Validation |
|------------|-------------|-------|-----------|----------|------------|------------|
| Name | QLineEdit | "Name:" | String | Yes | - | Must not be empty |
| Phone | QLineEdit | "Phone:" | String | Yes | - | Must not be empty |
| Notes | QTextEdit | "Notes:" | Text | No | - | None |

#### Action Buttons

| Button | Label | Action | Validation |
|--------|-------|--------|------------|
| Save | "Save" | Saves customer record | Name and Phone must not be empty |
| Cancel | "Cancel" | Closes dialog without saving | None |

#### Save Logic
- **Add Mode**: Creates new Customer record
- **Edit Mode**: Updates existing Customer record by ID
- **Result**: Returns to Customer Window with refreshed list

---

## 5. Settings Window

### 5.1 Window Properties
- **Window Title**: "Settings"
- **Minimum Width**: 600 pixels
- **Layout**: Tabbed interface (5 tabs)
- **Purpose**: Configure application settings

---

### 5.2 General Tab

#### Input Fields

| Field Name | Widget Type | Label | Data Type | Setting Key | Default Value |
|------------|-------------|-------|-----------|-------------|---------------|
| Salon Name | QLineEdit | "Salon Name:" | String | `salon_name` | "" |
| Salon Address | QTextEdit | "Address:" | Text | `salon_address` | "" |
| Salon Phone | QLineEdit | "Phone:" | String | `salon_phone` | "" |
| GSTIN | QLineEdit | "GSTIN:" | String | `salon_gstin` | "" |
| Default Tax % | QLineEdit | "Default Tax %:" | Decimal | `default_tax_percent` | "0" |
| Thank You Message | QLineEdit | "Thank You Message:" | String | `thank_you_message` | "Thank you for your visit!" |

**Purpose**: Business information used in PDF receipts and WhatsApp messages

---

### 5.3 Staff Tab

#### Staff Table

| Column Name | Data Type | Editable | Source Field |
|-------------|-----------|----------|--------------|
| Name | String | No | `staff.name` |
| Role | String | No | `staff.role` |
| Phone | String | No | `staff.phone` |
| Active | String | No | "Yes" or "No" based on `staff.active` |

**Hidden Data**: Staff ID stored in UserRole of first column

#### Action Buttons

| Button | Label | Action |
|--------|-------|--------|
| Add Staff | "Add Staff" | Opens StaffDialog in Add mode |
| Edit Staff | "Edit Staff" | Opens StaffDialog in Edit mode for selected staff |
| Toggle Active | "Toggle Active" | Flips `active` status of selected staff |

#### StaffDialog Fields

| Field Name | Widget Type | Label | Data Type | Required |
|------------|-------------|-------|-----------|----------|
| Name | QLineEdit | "Name:" | String | Yes (implicit) |
| Role | QLineEdit | "Role:" | String | No |
| Phone | QLineEdit | "Phone:" | String | No |

---

### 5.4 Services Tab

#### Services Table

| Column Name | Data Type | Editable | Source Field |
|-------------|-----------|----------|--------------|
| Name | String | No | `service.name` |
| Description | String | No | `service.description` |
| Price | Decimal | No | `service.price` |
| Duration (min) | Integer | No | `service.duration_minutes` |
| Active | String | No | "Yes" or "No" based on `service.active` |

**Hidden Data**: Service ID stored in UserRole of first column

#### Action Buttons

| Button | Label | Action |
|--------|-------|--------|
| Add Service | "Add Service" | Opens ServiceDialog in Add mode |
| Edit Service | "Edit Service" | Opens ServiceDialog in Edit mode for selected service |
| Toggle Active | "Toggle Active" | Flips `active` status of selected service |

#### ServiceDialog Fields

| Field Name | Widget Type | Label | Data Type | Required | Validation |
|------------|-------------|-------|-----------|----------|------------|
| Name | QLineEdit | "Name:" | String | Yes | Must not be empty |
| Description | QLineEdit | "Description:" | String | No | - |
| Price | QLineEdit | "Price:" | Decimal(10,2) | Yes | Must be valid decimal number |
| Duration (minutes) | QLineEdit | "Duration (minutes):" | Integer | No | Must be valid integer or empty |

**Save Validation**: Shows error dialog if price or duration are invalid numbers

---

### 5.5 Integrations Tab

#### WhatsApp Configuration Fields

| Field Name | Widget Type | Label | Data Type | Setting Key | Default | Validation |
|------------|-------------|-------|-----------|-------------|---------|------------|
| Phone Number ID | QLineEdit | "WhatsApp Phone Number ID:" | String | `whatsapp_phone_id` | "" | - |
| Business Account ID | QLineEdit | "WhatsApp Business Account ID:" | String | `whatsapp_account_id` | "" | - |
| API Version | QLineEdit | "API Version (e.g., v15.0):" | String | `whatsapp_api_version` | "v15.0" | - |
| Country Code | QLineEdit | "Default Country Code (e.g., 91):" | String | `whatsapp_country_code` | "91" | - |
| Message Template | QTextEdit | "Message Template:" | Text | `whatsapp_message_template` | "Hi {customer_name}, thank you for visiting {salon_name}. Your bill total is ?{total}. Your receipt is attached." | Supports placeholders |
| API Token | QLineEdit | "WhatsApp API Token:" | String (Password) | `whatsapp_api_token` (keyring) | "" | Stored securely in system keyring |

**Message Template Placeholders**:
- `{customer_name}` ? Customer's name
- `{salon_name}` ? Salon name from General settings
- `{total}` ? Bill total amount

**Security Note**: API Token uses password echo mode and is stored in system keyring, not database

#### Test Button

| Button | Label | Action | Logic |
|--------|-------|--------|-------|
| Test Connection | "Test Connection" | Validates WhatsApp configuration | Checks if `whatsapp_api_token` and `whatsapp_phone_id` are set |

---

### 5.6 Advanced Tab

**Current Status**: Placeholder buttons (all disabled)

| Button | Label | Status | Future Purpose |
|--------|-------|--------|----------------|
| Database Location | "Change Database Location" | Disabled | Allow custom database path |
| View Logs | "View Logs" | Disabled | Display application logs |
| Export Backup | "Export Backup" | Disabled | Create database backup |

---

### 5.7 Settings Save/Cancel

| Button | Label | Action |
|--------|-------|--------|
| Save | "Save" | Saves all settings from all tabs, shows success message, closes dialog |
| Cancel | "Cancel" | Closes dialog without saving |

**Save Process**:
1. Saves General tab settings to database
2. Saves Integrations tab settings to database/keyring
3. Shows success message: "Your settings have been saved successfully."
4. Closes dialog

---

## 6. Bill History Window

### 6.1 Window Properties
- **Window Title**: "Bill History"
- **Minimum Width**: 800 pixels
- **Purpose**: View and manage past bills

### 6.2 Filter Section

| Field Name | Widget Type | Placeholder | Search Logic |
|------------|-------------|-------------|--------------|
| Search Input | QLineEdit | "Search customer name or bill number..." | Exact match on bill_number OR partial match on customer name |
| Search Button | QPushButton | "Search" | Triggers filtered bill list |

### 6.3 Bill History Table

| Column Name | Data Type | Source Field | Display Format |
|-------------|-----------|--------------|----------------|
| Bill # | String | `bill.bill_number` or `bill.id` | As-is |
| Date | DateTime | `bill.bill_datetime` | "YYYY-MM-DD HH:MM" |
| Customer | String | `bill.customer.name` | As-is |
| Total | Decimal | `bill.total` | "?{total:.2f}" |
| Status | Enum | `bill.status` | "Paid", "Pending", or "Cancelled" |
| WhatsApp | Enum | `bill.whatsapp_status` | "Not Sent", "Sent", or "Failed" |
| ID | Integer | `bill.id` | Hidden column |

**Query Details**:
- Joins: Bill ? Customer
- Order: `bill_datetime` descending (newest first)
- Limit: 500 records

### 6.4 Action Buttons

| Button | Label | Action | Validation |
|--------|-------|--------|------------|
| View PDF | "View PDF" | Displays PDF file path (generates if missing) | Bill must be selected |
| Resend WhatsApp | "Resend WhatsApp" | Re-sends WhatsApp message with PDF | Bill must be selected, valid phone required |

#### View PDF Logic
1. Gets selected bill ID
2. Retrieves bill from database
3. If `pdf_path` exists, uses it; otherwise generates new PDF
4. Shows information dialog with PDF path

#### Resend WhatsApp Logic
1. Gets selected bill ID
2. Validates bill and customer exist
3. Validates phone number (must be digits)
4. Formats message using template with placeholders
5. Prepends country code to phone
6. Generates PDF if missing
7. Calls WhatsApp API
8. Updates `whatsapp_status` and `whatsapp_last_error`
9. Shows success/failure dialog

---

## 7. Data Validation Rules

### 7.1 Customer Validation

| Field | Rule | Error Message |
|-------|------|---------------|
| Name | Must not be empty | "Name and phone number are required." |
| Phone | Must not be empty | "Name and phone number are required." |
| Phone (WhatsApp) | Must contain only digits | "Cannot send WhatsApp; invalid phone." |

### 7.2 Staff Validation

| Field | Rule | Error Message |
|-------|------|---------------|
| Name | Must not be empty | (Implicit - database constraint) |

### 7.3 Service Validation

| Field | Rule | Error Message |
|-------|------|---------------|
| Name | Must not be empty | (Implicit - database constraint) |
| Price | Must be valid decimal | "Please enter a valid number for price and duration." |
| Duration | Must be valid integer or empty | "Please enter a valid number for price and duration." |

### 7.4 Bill Validation

| Field | Rule | Error Message |
|-------|------|---------------|
| Customer | Must be selected | "Please select a customer for the bill." |
| Staff | Must be selected | (Implicit - always has selection) |
| Services | At least one service recommended | (No validation currently) |
| Total | Must not be negative | (Implicit - calculations prevent this) |

### 7.5 Settings Validation

| Field | Rule | Error Message |
|-------|------|---------------|
| WhatsApp Token | Must be set for WhatsApp features | "WhatsApp token or Phone ID is missing." |
| WhatsApp Phone ID | Must be set for WhatsApp features | "WhatsApp token or Phone ID is missing." |

---

## 8. Data Flow Summary

### 8.1 Complete Billing Flow

```
1. USER: Opens "New Bill" window
   ?
2. UI: Loads active staff into combo box
   ?
3. UI: Loads active services into combo box
   ?
4. USER: Searches for customer by phone/name
   ?
5. SYSTEM: Queries Customer table
   ?
6. UI: Displays customer info and notes
   ?
7. USER: Selects staff from dropdown
   ?
8. USER: Adds services to bill (multiple)
   ?
9. UI: Auto-calculates line totals (Qty × Price)
   ?
10. USER: Edits quantity/price in table
    ?
11. UI: Recalculates line totals and subtotal
    ?
12. USER: Enters discount (flat or percent)
    ?
13. USER: Enters tax percentage
    ?
14. UI: Calculates final total:
    - Subtotal = Sum of line totals
    - Discount amount = Based on type
    - Tax amount = (Subtotal - Discount) × Tax%
    - Total = Subtotal - Discount + Tax
    ?
15. USER: Selects payment method
    ?
16. USER: Clicks "Save, PDF & Send"
    ?
17. SYSTEM: Creates Bill record in database
    ?
18. SYSTEM: Creates BillItem records for each service
    ?
19. SYSTEM: Updates customer.last_visit_at
    ?
20. SYSTEM: Generates bill_number (from bill.id)
    ?
21. SYSTEM: Calls PDF generator
    ?
22. PDF GENERATOR: Retrieves bill + items + customer + staff + settings
    ?
23. PDF GENERATOR: Creates PDF file with:
    - Salon header info
    - Bill number and date
    - Customer details
    - Staff member
    - Line items table
    - Subtotal/discount/tax/total
    - Payment method
    - Thank you message
    ?
24. SYSTEM: Updates bill.pdf_path
    ?
25. SYSTEM: Retrieves WhatsApp settings
    ?
26. SYSTEM: Formats message template with customer/salon/total
    ?
27. SYSTEM: Calls WhatsApp Business API
    ?
28. WHATSAPP API: Sends message with PDF attachment
    ?
29. SYSTEM: Updates bill.whatsapp_status
    ?
30. UI: Shows success/failure message
    ?
31. UI: Closes billing window
```

### 8.2 Customer Management Flow

```
1. USER: Opens "Manage Customers"
   ?
2. SYSTEM: Queries all customers, displays in table
   ?
3. USER: Searches by name/phone
   ?
4. SYSTEM: Filters customer list
   ?
5. USER: Selects customer row
   ?
6. UI: Displays customer notes
   ?
7. USER: Clicks "Edit Customer"
   ?
8. UI: Opens CustomerDialog with existing data
   ?
9. USER: Modifies name/phone/notes
   ?
10. USER: Clicks "Save"
    ?
11. SYSTEM: Updates Customer record
    ?
12. UI: Refreshes customer list
```

### 8.3 Settings Configuration Flow

```
1. USER: Opens "Settings"
   ?
2. SYSTEM: Loads all settings from database/keyring
   ?
3. UI: Populates all tab fields
   ?
4. USER: Modifies settings across tabs
   ?
5. USER: Clicks "Save"
   ?
6. SYSTEM: Writes all settings to database
   ?
7. SYSTEM: Writes API token to system keyring
   ?
8. UI: Shows success message
   ?
9. UI: Closes settings dialog
```

### 8.4 Bill History & Resend Flow

```
1. USER: Opens "Bill History"
   ?
2. SYSTEM: Queries last 500 bills (ordered by date desc)
   ?
3. UI: Displays bills in table
   ?
4. USER: Searches by bill number or customer name
   ?
5. SYSTEM: Filters bill list
   ?
6. USER: Selects bill row
   ?
7. USER: Clicks "Resend WhatsApp"
   ?
8. SYSTEM: Retrieves bill + customer + settings
   ?
9. SYSTEM: Validates phone number
   ?
10. SYSTEM: Generates/retrieves PDF
    ?
11. SYSTEM: Formats message template
    ?
12. SYSTEM: Sends WhatsApp message
    ?
13. SYSTEM: Updates whatsapp_status
    ?
14. UI: Shows success/failure message
```

---

## 9. External Integrations

### 9.1 WhatsApp Business API

**Purpose**: Send bill receipts via WhatsApp

**Configuration Required**:
- Phone Number ID
- Business Account ID
- API Version
- API Access Token (secure)
- Country Code

**API Endpoint**: `https://graph.facebook.com/{api_version}/{phone_id}/messages`

**Request Headers**:
- `Authorization: Bearer {token}`
- `Content-Type: application/json`

**Request Body**:
```json
{
  "messaging_product": "whatsapp",
  "to": "{country_code}{phone}",
  "type": "document",
  "document": {
    "link": "{pdf_url}",
    "caption": "{formatted_message}"
  }
}
```

**Response Handling**:
- Success ? Update `whatsapp_status` to "Sent"
- Failure ? Update `whatsapp_status` to "Failed", store error in `whatsapp_last_error`

### 9.2 PDF Generation (ReportLab)

**Purpose**: Generate printable receipt PDFs

**Libraries Used**:
- `reportlab.pdfgen.canvas`
- `reportlab.lib.pagesizes`
- `reportlab.lib.units`
- `reportlab.platypus`
- `reportlab.lib.styles`

**PDF Contains**:
- Business header (name, address, phone, GSTIN)
- Bill metadata (number, date/time)
- Customer information (name, phone)
- Staff member name
- Service line items table
- Financial summary (subtotal, discount, tax, total)
- Payment method
- Footer (thank you message)

**File Naming**: Typically `bill_{bill_number}.pdf` or similar

### 9.3 Secure Storage (Keyring)

**Purpose**: Securely store API tokens outside database

**Backend**: `keyring.backends.Windows` (on Windows)

**Stored Keys**:
- `whatsapp_api_token`

**Access Methods**:
- `settings_service.get_secret(key)` ? Retrieve token
- `settings_service.set_secret(key, value)` ? Store token

---

## 10. Data Security & Privacy

### 10.1 Sensitive Data

| Data Type | Storage Location | Security Measure |
|-----------|------------------|------------------|
| Customer Phone Numbers | SQLite Database | Stored in plain text (required for WhatsApp) |
| WhatsApp API Token | Windows Credential Manager | Encrypted by OS keyring |
| Bill PDFs | Local File System | File system permissions |
| Database File | Local File System | SQLite file permissions |

### 10.2 Data Retention

| Data Type | Retention Policy | Deletion Method |
|-----------|------------------|-----------------|
| Bills | Indefinite | Manual deletion not implemented |
| Customers | Indefinite | Manual deletion not implemented |
| Staff | Soft delete (active=False) | Toggle in UI |
| Services | Soft delete (active=False) | Toggle in UI |
| Settings | Indefinite | Overwrite only |

### 10.3 Backup & Recovery

**Current Status**: No automated backup

**Planned Features** (Advanced tab placeholders):
- Manual database export
- Custom database location
- Application logs viewing

---

## 11. UI/UX Patterns

### 11.1 Dialog Patterns

| Dialog Type | Modality | Close Behavior | Data Persistence |
|-------------|----------|----------------|------------------|
| Settings | Modal | Cancel discards, Save commits | On Save button click |
| Customer Management | Modal | Cancel discards, Save commits | On Save button click |
| Billing | Modal | Close after save | Immediate on save |
| Bill History | Modal | Close button | Read-only (except resend) |

### 11.2 Search Patterns

| Search Type | Match Type | Case Sensitive | Trigger |
|-------------|-----------|----------------|---------|
| Customer (Billing) | Exact phone OR Partial name | No (name) / Yes (phone) | Enter key or Search button |
| Customer (Management) | Partial name OR Partial phone | No | Search button |
| Bill History | Exact bill# OR Partial name | No (name) | Search button |

### 11.3 Validation Patterns

| Pattern | Location | Timing | Error Display |
|---------|----------|--------|---------------|
| Required Field | Customer Dialog, Service Dialog | On Save | QMessageBox Warning |
| Numeric Input | Service Dialog, Billing Window | On Save/Edit | QMessageBox Warning or silent ignore |
| Selection Required | Billing Window | On Save | QMessageBox Warning |

### 11.4 Auto-Calculation Patterns

| Calculation | Trigger Events | Update Frequency |
|-------------|----------------|------------------|
| Line Total | Qty or Price change in table | Immediate (on cell change) |
| Subtotal | Service add/remove/edit | Immediate |
| Discount Amount | Discount value or type change | Immediate |
| Tax Amount | Tax % or subtotal change | Immediate |
| Grand Total | Any financial field change | Immediate |

---

## 12. Data Display Formats

### 12.1 Currency

**Format**: `? {amount:.2f}`
- Symbol: ? (Indian Rupee)
- Decimal Places: 2
- Examples: ? 500.00, ? 1,234.56

### 12.2 Date/Time

**Date Format**: `YYYY-MM-DD`
- Example: 2024-03-15

**DateTime Format**: `YYYY-MM-DD HH:MM`
- Example: 2024-03-15 14:30

### 12.3 Phone Numbers

**Storage Format**: Digits only (no formatting)
- Example: 9876543210

**Display Format**: As stored (no formatting applied)

**WhatsApp Format**: `{country_code}{phone}`
- Example: 919876543210

### 12.4 Boolean Values

**Database**: True/False
**Display**: "Yes"/"No" or checkbox states

---

## 13. Error Handling

### 13.1 Database Errors

| Error Type | Handling | User Feedback |
|------------|----------|---------------|
| Connection Failed | Log error, graceful exit | Critical error dialog |
| Constraint Violation | Rollback transaction | Warning dialog with details |
| Query Error | Log and ignore (for non-critical) | None or warning dialog |

### 13.2 API Errors

| Error Type | Handling | User Feedback |
|------------|----------|---------------|
| WhatsApp Send Failed | Log error, update bill status | Critical dialog with error message |
| Missing Configuration | Skip API call | Warning dialog |
| Network Error | Log and fail gracefully | Error dialog with retry suggestion |

### 13.3 Input Validation Errors

| Error Type | Handling | User Feedback |
|------------|----------|---------------|
| Empty Required Field | Prevent save | Warning dialog |
| Invalid Number Format | Prevent save or ignore | Warning dialog or silent |
| Missing Selection | Prevent action | Warning dialog |

---

## 14. System Requirements (Implied from Code)

### 14.1 Required Python Packages

- PyQt6 (GUI framework)
- SQLAlchemy (ORM)
- ReportLab (PDF generation)
- Requests (HTTP/WhatsApp API)
- Keyring (Secure token storage)
- urllib3, certifi, charset_normalizer, idna (HTTP dependencies)

### 14.2 Database

- SQLite (embedded database)
- Default location: Application directory

### 14.3 Operating System

- Windows (based on keyring backend)
- Likely supports other OS with different keyring backends

---

## 15. Feature Matrix

| Feature | Status | UI Location | Data Source |
|---------|--------|-------------|-------------|
| Create Bill | ? Implemented | Billing Window | Customer, Staff, Service tables |
| Manage Customers | ? Implemented | Customer Window | Customer table |
| Manage Staff | ? Implemented | Settings ? Staff tab | Staff table |
| Manage Services | ? Implemented | Settings ? Services tab | Service table |
| WhatsApp Integration | ? Implemented | Billing, History windows | WhatsApp API |
| PDF Generation | ? Implemented | Billing, History windows | ReportLab |
| Bill History | ? Implemented | Bill History Window | Bill table |
| Search Bills | ? Implemented | Bill History Window | Bill, Customer tables |
| Resend WhatsApp | ? Implemented | Bill History Window | WhatsApp API |
| General Settings | ? Implemented | Settings ? General tab | Setting table |
| WhatsApp Settings | ? Implemented | Settings ? Integrations tab | Setting table + Keyring |
| Database Backup | ? Planned | Settings ? Advanced tab | Not implemented |
| Custom DB Location | ? Planned | Settings ? Advanced tab | Not implemented |
| View Logs | ? Planned | Settings ? Advanced tab | Not implemented |
| Dashboard Analytics | ? Future | Main Window | Not implemented |

---

## 16. Complete Dataset Summary

### 16.1 All User Input Fields (Alphabetical)

| Field Name | Data Type | UI Location | Required | Validation |
|------------|-----------|-------------|----------|------------|
| Country Code | String | Settings ? Integrations | No | None |
| Customer Name | String | Customer Dialog, Billing Window | Yes | Not empty |
| Customer Notes | Text | Customer Dialog, Billing Window | No | None |
| Customer Phone | String | Customer Dialog, Billing Window | Yes | Not empty, digits for WhatsApp |
| Customer Search | String | Customer Window, Billing Window | No | None |
| Default Tax % | Decimal | Settings ? General | No | Numeric |
| Discount Type | Enum | Billing Window | No | "Flat" or "Percent" |
| Discount Value | Decimal | Billing Window | No | Numeric |
| GSTIN | String | Settings ? General | No | None |
| Message Template | Text | Settings ? Integrations | No | Supports placeholders |
| Payment Method | Enum | Billing Window | Yes | Dropdown selection |
| Salon Address | Text | Settings ? General | No | None |
| Salon Name | String | Settings ? General | No | None |
| Salon Phone | String | Settings ? General | No | None |
| Service Description | String | Service Dialog | No | None |
| Service Duration | Integer | Service Dialog | No | Numeric or empty |
| Service Name | String | Service Dialog | Yes | Not empty |
| Service Price | Decimal | Service Dialog | Yes | Valid decimal |
| Service Quantity | Integer | Billing Window (table) | Yes | Positive integer |
| Service Unit Price | Decimal | Billing Window (table) | Yes | Valid decimal |
| Staff Name | String | Staff Dialog | Yes | Not empty |
| Staff Phone | String | Staff Dialog | No | None |
| Staff Role | String | Staff Dialog | No | None |
| Staff Selection | Integer ID | Billing Window | Yes | Dropdown selection |
| Tax Percentage | Decimal | Billing Window | No | Numeric |
| Thank You Message | String | Settings ? General | No | None |
| WhatsApp Account ID | String | Settings ? Integrations | No | None |
| WhatsApp API Token | String (Password) | Settings ? Integrations | No | Stored in keyring |
| WhatsApp API Version | String | Settings ? Integrations | No | None |
| WhatsApp Phone ID | String | Settings ? Integrations | No | None |

### 16.2 All Database Tables

1. **Customer** - Customer contact information
2. **Staff** - Salon staff members
3. **Service** - Service catalog
4. **Bill** - Invoice records
5. **BillItem** - Line items for invoices
6. **Setting** - Application configuration

### 16.3 All Relationships

- Customer ? Bill (One-to-Many)
- Staff ? Bill (One-to-Many)
- Bill ? BillItem (One-to-Many, cascade delete)
- Service ? BillItem (One-to-Many)

---

## 17. Conclusion

This Salon Billing System is a comprehensive desktop application with:

- **6 Database Tables** storing all business data
- **5 Main UI Windows** for different workflows
- **45+ Input Fields** across all dialogs
- **2 External Integrations** (WhatsApp, PDF generation)
- **Real-time Calculations** for billing accuracy
- **Secure Configuration** using system keyring

The application follows a **modal dialog pattern** for data entry, uses **SQLAlchemy ORM** for database operations, and provides **immediate feedback** through auto-calculations and validation messages.

**Primary User Workflows**:
1. Configure settings (one-time)
2. Add customers (as needed)
3. Create bills (daily operation)
4. View/resend bills (as needed)
5. Manage staff/services (periodic updates)

This report serves as a complete reference for understanding the data structures, UI components, and workflows in the Salon Billing System.

---

**Document Version**: 1.0  
**Last Updated**: 2024  
**Application**: Salon Billing System  
**Technology Stack**: Python, PyQt6, SQLAlchemy, SQLite, ReportLab, WhatsApp Business API
