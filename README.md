# Salon Billing System

A complete, production-ready Windows desktop billing system for a salon, built with Python and PyQt6.

## Features

*   **Billing:** Create bills for customers by selecting staff and services.
*   **PDF Receipts:** Automatically generate and save PDF receipts.
*   **WhatsApp Integration:** Send PDF receipts to customers via WhatsApp.
*   **Customer Management:** Store and manage customer information and notes.
*   **Settings:** A centralized settings page to manage salon details, staff, services, and integrations.
*   **Secure Credential Storage:** Uses the `keyring` library to securely store sensitive data like API tokens in the Windows Credential Manager.

## Tech Stack

*   **Language:** Python 3.11+
*   **GUI Framework:** PyQt6
*   **Database:** SQLite with SQLAlchemy ORM
*   **PDF Generation:** ReportLab
*   **API Calls:** requests
*   **Secure Credential Storage:** keyring

## Project Structure

```
app/
  __init__.py
  models.py          # SQLAlchemy models
  database.py        # Database session and initialization
  gui_main.py        # Main window
  gui_billing.py     # Billing screen
  gui_customers.py   # Customer management
  gui_settings.py    # Settings page
  pdf_generator.py   # PDF receipt generation
  whatsapp_client.py # WhatsApp Cloud API integration
  settings_service.py# Loading/saving settings
  utils.py           # Logging and other utilities
main.py              # Application entry point
requirements.txt
.env.example
README.md
```

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```

2.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure WhatsApp API:**
    *   Open the application and go to `Settings > Integrations`.
    *   Enter your WhatsApp Phone Number ID and API Token.
    *   The API Token is stored securely in the Windows Credential Manager.
    *   For more information on obtaining these credentials, see the [Meta for Developers documentation](https://developers.facebook.com/docs/whatsapp/cloud-api).

5.  **Run the application:**
    ```bash
    python main.py
    ```

## How to Use

*   **Launch the application:** Run `python main.py`.
*   **Configure settings:** Go to the `Settings` menu to set up your salon's details, staff, services, and WhatsApp integration.
*   **Manage customers:** Use the `Manage Customers` button to add, edit, or view customer information and notes.
*   **Create a new bill:** Click the `New Bill` button to open the billing screen. Select a customer, staff member, and add services to the bill.
*   **Save and send:** You can save the bill, or save it and send the PDF receipt to the customer via WhatsApp.
