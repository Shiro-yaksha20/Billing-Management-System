# Salon Billing System

A complete, production-ready Windows desktop billing system for a salon, built with Python and PyQt6.

## Releases

Official builds for Windows are available under the [Releases](https://github.com/your-username/your-repo/releases) section of this repository. The `.exe` is built automatically by GitHub Actions whenever a new version is tagged.

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

## Building from Source

To build the Windows executable from source, you will need to have PyInstaller installed.

1.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
2.  **Run the build script:**
    ```bash
    ./scripts/build_exe.bat
    ```
    Alternatively, you can run PyInstaller directly:
    ```bash
    pyinstaller SalonBillingSystem.spec
    ```
3.  The resulting executable will be in the `dist/SalonBillingSystem` directory.

## Versioning

This project follows Semantic Versioning (vMAJOR.MINOR.PATCH). The version is defined in `app/__init__.py`.

To make a new release:
1.  Bump the version in `app/__init__.py`.
2.  Commit and push the change.
3.  Create and push a Git tag `vX.Y.Z`.
4.  GitHub Actions will build the Windows `.exe` and create a GitHub Release with the `.exe` attached.

## How to Use

*   **Launch the application:** Run `python main.py` or the executable.
*   **Configure settings:** Go to the `Settings` menu to set up your salon's details, staff, services, and WhatsApp integration.
*   **Manage customers:** Use the `Manage Customers` button to add, edit, or view customer information and notes.
*   **Create a new bill:** Click the `New Bill` button to open the billing screen. Select a customer, staff member, and add services to the bill.
*   **Save and send:** You can save the bill, or save it and send the PDF receipt to the customer via WhatsApp.
