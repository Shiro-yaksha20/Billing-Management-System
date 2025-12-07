from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QTabWidget,
    QWidget,
    QFormLayout,
    QLineEdit,
    QTextEdit,
    QPushButton,
    QHBoxLayout,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QGroupBox,
    QFileDialog,
)
from PyQt6.QtCore import Qt
from . import settings_service
from .models import Staff, Service
from .database import db_session
from .csv_service_importer import import_services_from_csv, export_services_to_csv
from .utils import logger


class SettingsWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(600)

        self.layout = QVBoxLayout(self)
        self.tab_widget = QTabWidget()
        self.layout.addWidget(self.tab_widget)

        # Create tabs
        self.general_tab = QWidget()
        self.staff_tab = QWidget()
        self.services_tab = QWidget()
        self.integrations_tab = QWidget()
        self.advanced_tab = QWidget()

        # Add tabs to the tab widget
        self.tab_widget.addTab(self.general_tab, "General")
        self.tab_widget.addTab(self.staff_tab, "Staff")
        self.tab_widget.addTab(self.services_tab, "Services")
        self.tab_widget.addTab(self.integrations_tab, "Integrations")
        self.tab_widget.addTab(self.advanced_tab, "Advanced")

        # Setup UI for each tab
        self.setup_general_tab()
        self.setup_staff_tab()
        self.setup_services_tab()
        self.setup_integrations_tab()
        self.setup_advanced_tab()

        # Save and Cancel buttons
        self.button_box = QHBoxLayout()
        self.save_button = QPushButton("Save")
        self.cancel_button = QPushButton("Cancel")
        self.button_box.addStretch()
        self.button_box.addWidget(self.save_button)
        self.button_box.addWidget(self.cancel_button)
        self.layout.addLayout(self.button_box)

        # Connect signals
        self.save_button.clicked.connect(self.save_settings)
        self.cancel_button.clicked.connect(self.reject)

    def setup_general_tab(self):
        layout = QFormLayout(self.general_tab)

        self.salon_name_input = QLineEdit()
        self.salon_address_input = QTextEdit()
        self.salon_phone_input = QLineEdit()
        self.salon_gstin_input = QLineEdit()
        self.default_tax_percent_input = QLineEdit()
        self.thank_you_message_input = QLineEdit()

        # NEW: Branding and receipt enhancements
        self.salon_instagram_input = QLineEdit()
        self.salon_tagline_input = QLineEdit()
        self.salon_logo_path_input = QLineEdit()
        self.salon_logo_path_input.setReadOnly(True)
        self.browse_logo_button = QPushButton("Browse...")
        logo_row = QHBoxLayout()
        logo_row.addWidget(self.salon_logo_path_input)
        logo_row.addWidget(self.browse_logo_button)

        self.google_review_link_input = QLineEdit()
        self.receipt_footer_message_input = QTextEdit()
        self.receipt_footer_message_input.setMaximumHeight(100)

        layout.addRow("Salon Name:", self.salon_name_input)
        layout.addRow("Address:", self.salon_address_input)
        layout.addRow("Phone:", self.salon_phone_input)
        layout.addRow("GSTIN:", self.salon_gstin_input)
        layout.addRow("Default Tax %:", self.default_tax_percent_input)
        layout.addRow("Thank You Message:", self.thank_you_message_input)
        # NEW rows
        layout.addRow("Instagram Handle:", self.salon_instagram_input)
        layout.addRow("Tagline:", self.salon_tagline_input)
        layout.addRow("Salon Logo:", logo_row)
        layout.addRow("Google Review Link:", self.google_review_link_input)
        layout.addRow("Receipt Footer:", self.receipt_footer_message_input)

        # Wire browse action
        self.browse_logo_button.clicked.connect(self.browse_logo_file)

        self.load_general_settings()

    def browse_logo_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Logo Image",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp);;All Files (*)"
        )
        if file_path:
            self.salon_logo_path_input.setText(file_path)

    def load_general_settings(self):
        """Loads settings for the General tab."""
        self.salon_name_input.setText(settings_service.get_setting("salon_name", ""))
        self.salon_address_input.setPlainText(settings_service.get_setting("salon_address", ""))
        self.salon_phone_input.setText(settings_service.get_setting("salon_phone", ""))
        self.salon_gstin_input.setText(settings_service.get_setting("salon_gstin", ""))
        self.default_tax_percent_input.setText(settings_service.get_setting("default_tax_percent", "0"))
        self.thank_you_message_input.setText(settings_service.get_setting("thank_you_message", "Thank you for your visit!"))
        # NEW loads
        self.salon_instagram_input.setText(settings_service.get_setting("salon_instagram", ""))
        self.salon_tagline_input.setText(settings_service.get_setting("salon_tagline", ""))
        self.salon_logo_path_input.setText(settings_service.get_setting("salon_logo_path", ""))
        self.google_review_link_input.setText(settings_service.get_setting("google_review_link", ""))
        self.receipt_footer_message_input.setPlainText(settings_service.get_setting("receipt_footer_message", "Thank you for visiting!"))

    def save_general_settings(self):
        """Saves settings from the General tab with validation."""
        # Validate tax percent
        try:
            tax = float(self.default_tax_percent_input.text() or "0")
            if not (0 <= tax <= 100):
                raise ValueError("Tax must be between 0 and 100")
        except ValueError as e:
            QMessageBox.warning(self, "Invalid Tax", f"Invalid tax percentage: {e}")
            return
        
        # Validate required fields
        if not self.salon_name_input.text().strip():
            QMessageBox.warning(self, "Missing Name", "Salon name is required")
            return
        
        # Validate phone (basic check: digits, +, -, spaces)
        phone = self.salon_phone_input.text().strip()
        if phone and not phone.replace("+", "").replace("-", "").replace(" ", "").isdigit():
            QMessageBox.warning(self, "Invalid Phone", "Phone number contains invalid characters")
            return
        
        # Basic GSTIN format check (15 chars alphanumeric)
        gstin = self.salon_gstin_input.text().strip()
        if gstin and (len(gstin) != 15 or not gstin.isalnum()):
            QMessageBox.warning(self, "Invalid GSTIN", "GSTIN must be 15 alphanumeric characters")
            return

        # Save after validation
        settings_service.set_setting("salon_name", self.salon_name_input.text())
        settings_service.set_setting("salon_address", self.salon_address_input.toPlainText())
        settings_service.set_setting("salon_phone", phone)
        settings_service.set_setting("salon_gstin", gstin)
        settings_service.set_setting("default_tax_percent", str(tax))
        settings_service.set_setting("thank_you_message", self.thank_you_message_input.text())
        # NEW saves
        settings_service.set_setting("salon_instagram", self.salon_instagram_input.text().strip())
        settings_service.set_setting("salon_tagline", self.salon_tagline_input.text().strip())
        settings_service.set_setting("salon_logo_path", self.salon_logo_path_input.text().strip())
        settings_service.set_setting("google_review_link", self.google_review_link_input.text().strip())
        settings_service.set_setting("receipt_footer_message", self.receipt_footer_message_input.toPlainText().strip())

    def save_settings(self):
        """Saves all settings and closes the dialog."""
        self.save_general_settings()
        self.save_integrations_settings()
        QMessageBox.information(self, "Settings Saved", "Your settings have been saved successfully.")
        self.accept()

    def setup_staff_tab(self):
        layout = QVBoxLayout(self.staff_tab)

        self.staff_table = QTableWidget()
        self.staff_table.setColumnCount(4)
        self.staff_table.setHorizontalHeaderLabels(["Name", "Role", "Phone", "Active"])
        self.staff_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.staff_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.staff_table)

        button_layout = QHBoxLayout()
        add_staff_button = QPushButton("Add Staff")
        edit_staff_button = QPushButton("Edit Staff")
        toggle_active_button = QPushButton("Toggle Active")
        button_layout.addWidget(add_staff_button)
        button_layout.addWidget(edit_staff_button)
        button_layout.addWidget(toggle_active_button)
        layout.addLayout(button_layout)

        add_staff_button.clicked.connect(self.add_staff)
        edit_staff_button.clicked.connect(self.edit_staff)
        toggle_active_button.clicked.connect(self.toggle_staff_active)

        self.load_staff_data()

    def load_staff_data(self):
        # Block signals during table population
        self.staff_table.blockSignals(True)
        try:
            with db_session() as db:
                staff_list = db.query(Staff).all()
                self.staff_table.setRowCount(len(staff_list))
                for i, staff in enumerate(staff_list):
                    self.staff_table.setItem(i, 0, QTableWidgetItem(staff.name or ""))
                    self.staff_table.setItem(i, 1, QTableWidgetItem(staff.role or ""))
                    self.staff_table.setItem(i, 2, QTableWidgetItem(staff.phone or ""))
                    self.staff_table.setItem(i, 3, QTableWidgetItem("Yes" if staff.active else "No"))
                    self.staff_table.item(i, 0).setData(Qt.ItemDataRole.UserRole, staff.id)
        finally:
            self.staff_table.blockSignals(False)

    def add_staff(self):
        dialog = StaffDialog(self)
        if dialog.exec():
            self.load_staff_data()

    def edit_staff(self):
        selected_row = self.staff_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "No Staff Selected", "Please select a staff member to edit.")
            return

        item = self.staff_table.item(selected_row, 0)
        if not item:
            QMessageBox.warning(self, "Invalid Selection", "Could not identify selected staff.")
            return

        staff_id = item.data(Qt.ItemDataRole.UserRole)
        dialog = StaffDialog(self, staff_id=staff_id)
        if dialog.exec():
            self.load_staff_data()

    def toggle_staff_active(self):
        selected_row = self.staff_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "No Staff Selected", "Please select a staff member to toggle their active status.")
            return

        item = self.staff_table.item(selected_row, 0)
        if not item:
            QMessageBox.warning(self, "Invalid Selection", "Could not identify selected staff.")
            return

        staff_id = item.data(Qt.ItemDataRole.UserRole)
        with db_session() as db:
            staff = db.query(Staff).filter(Staff.id == staff_id).first()
            if staff:
                staff.active = not staff.active
            self.load_staff_data()

    def setup_services_tab(self):
        layout = QVBoxLayout(self.services_tab)

        # CSV Import/Export Section
        csv_group = QGroupBox("Bulk Import/Export")
        csv_layout = QHBoxLayout()
        
        import_csv_button = QPushButton("Import Services from CSV")
        export_csv_button = QPushButton("Export Services to CSV")
        
        import_csv_button.clicked.connect(self.import_services_csv)
        export_csv_button.clicked.connect(self.export_services_csv)
        
        csv_layout.addWidget(import_csv_button)
        csv_layout.addWidget(export_csv_button)
        csv_group.setLayout(csv_layout)
        layout.addWidget(csv_group)

        self.services_table = QTableWidget()
        self.services_table.setColumnCount(5)
        self.services_table.setHorizontalHeaderLabels(["Name", "Description", "Price", "Duration (min)", "Active"])
        self.services_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.services_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.services_table)

        button_layout = QHBoxLayout()
        add_service_button = QPushButton("Add Service")
        edit_service_button = QPushButton("Edit Service")
        toggle_active_button = QPushButton("Toggle Active")
        button_layout.addWidget(add_service_button)
        button_layout.addWidget(edit_service_button)
        button_layout.addWidget(toggle_active_button)
        layout.addLayout(button_layout)

        add_service_button.clicked.connect(self.add_service)
        edit_service_button.clicked.connect(self.edit_service)
        toggle_active_button.clicked.connect(self.toggle_service_active)

        self.load_service_data()

    def load_service_data(self):
        # Block signals during table population
        self.services_table.blockSignals(True)
        try:
            with db_session() as db:
                service_list = db.query(Service).all()
                self.services_table.setRowCount(len(service_list))
                for i, service in enumerate(service_list):
                    self.services_table.setItem(i, 0, QTableWidgetItem(service.name or ""))
                    self.services_table.setItem(i, 1, QTableWidgetItem(service.description or ""))
                    self.services_table.setItem(i, 2, QTableWidgetItem(str(service.price) if service.price is not None else ""))
                    self.services_table.setItem(i, 3, QTableWidgetItem(str(service.duration_minutes) if service.duration_minutes is not None else ""))
                    self.services_table.setItem(i, 4, QTableWidgetItem("Yes" if service.active else "No"))
                    self.services_table.item(i, 0).setData(Qt.ItemDataRole.UserRole, service.id)
        finally:
            self.services_table.blockSignals(False)

    def add_service(self):
        dialog = ServiceDialog(self)
        if dialog.exec():
            self.load_service_data()

    def edit_service(self):
        selected_row = self.services_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "No Service Selected", "Please select a service to edit.")
            return

        item = self.services_table.item(selected_row, 0)
        if not item:
            QMessageBox.warning(self, "Invalid Selection", "Could not identify selected service.")
            return

        service_id = item.data(Qt.ItemDataRole.UserRole)
        dialog = ServiceDialog(self, service_id=service_id)
        if dialog.exec():
            self.load_service_data()

    def toggle_service_active(self):
        selected_row = self.services_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "No Service Selected", "Please select a service to toggle its active status.")
            return

        item = self.services_table.item(selected_row, 0)
        if not item:
            QMessageBox.warning(self, "Invalid Selection", "Could not identify selected service.")
            return

        service_id = item.data(Qt.ItemDataRole.UserRole)
        with db_session() as db:
            service = db.query(Service).filter(Service.id == service_id).first()
            if service:
                service.active = not service.active
            self.load_service_data()

    def import_services_csv(self):
        """Import services from CSV file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Services CSV File",
            "",
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if not file_path:
            return
        
        # Ask user about existing services
        reply = QMessageBox.question(
            self,
            "Import Options",
            "How should existing services be handled?\n\n"
            "• Yes: Deactivate existing services (recommended)\n"
            "• No: Keep existing services active\n"
            "• Cancel: Cancel import",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Yes
        )
        
        if reply == QMessageBox.StandardButton.Cancel:
            return
        
        deactivate_existing = (reply == QMessageBox.StandardButton.Yes)
        
        try:
            # Run import
            results = import_services_from_csv(file_path, deactivate_existing=deactivate_existing)
            
            # Show results
            if results['success']:
                message = (
                    f"Import completed successfully!\n\n"
                    f"✓ Imported: {results['imported']} new services\n"
                    f"✓ Updated: {results['updated']} existing services\n"
                )
                if results['deactivated'] > 0:
                    message += f"✓ Deactivated: {results['deactivated']} old services\n"
                if results['skipped'] > 0:
                    message += f"⚠ Skipped: {results['skipped']} rows with errors\n"
                
                QMessageBox.information(self, "Import Successful", message)
            else:
                error_msg = "\n".join(results['errors'][:5])  # Show first 5 errors
                if len(results['errors']) > 5:
                    error_msg += f"\n... and {len(results['errors']) - 5} more errors"
                
                QMessageBox.warning(
                    self,
                    "Import Completed with Errors",
                    f"Imported: {results['imported']}, Errors: {len(results['errors'])}\n\n{error_msg}"
                )
            
            # Reload service table
            self.load_service_data()
        
        except Exception as e:
            QMessageBox.critical(self, "Import Failed", f"An error occurred during import:\n{str(e)}")
            logger.error(f"CSV import error: {e}")

    def export_services_csv(self):
        """Export services to CSV file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Services CSV File",
            "services_export.csv",
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if not file_path:
            return
        
        # Ask about active-only export
        reply = QMessageBox.question(
            self,
            "Export Options",
            "Export only active services?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        
        active_only = (reply == QMessageBox.StandardButton.Yes)
        
        try:
            success = export_services_to_csv(file_path, active_only=active_only)
            
            if success:
                QMessageBox.information(
                    self,
                    "Export Successful",
                    f"Services exported successfully to:\n{file_path}"
                )
            else:
                QMessageBox.warning(self, "Export Failed", "Failed to export services. Check logs for details.")
        
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"An error occurred during export:\n{str(e)}")
            logger.error(f"CSV export error: {e}")

    def setup_integrations_tab(self):
        layout = QFormLayout(self.integrations_tab)

        self.whatsapp_phone_id_input = QLineEdit()
        self.whatsapp_account_id_input = QLineEdit()
        self.whatsapp_api_version_input = QLineEdit()
        self.whatsapp_country_code_input = QLineEdit()
        self.whatsapp_message_template_input = QTextEdit()
        self.whatsapp_api_token_input = QLineEdit()
        self.whatsapp_api_token_input.setEchoMode(QLineEdit.EchoMode.Password)

        layout.addRow("WhatsApp Phone Number ID:", self.whatsapp_phone_id_input)
        layout.addRow("WhatsApp Business Account ID:", self.whatsapp_account_id_input)
        layout.addRow("API Version (e.g., v15.0):", self.whatsapp_api_version_input)
        layout.addRow("Default Country Code (e.g., 91):", self.whatsapp_country_code_input)
        layout.addRow("Message Template:", self.whatsapp_message_template_input)
        layout.addRow("WhatsApp API Token:", self.whatsapp_api_token_input)

        test_button = QPushButton("Test Connection")
        test_button.clicked.connect(self.test_whatsapp_connection)
        layout.addRow(test_button)

        self.load_integrations_settings()

    def load_integrations_settings(self):
        self.whatsapp_phone_id_input.setText(settings_service.get_setting("whatsapp_phone_id", ""))
        self.whatsapp_account_id_input.setText(settings_service.get_setting("whatsapp_account_id", ""))
        self.whatsapp_api_version_input.setText(settings_service.get_setting("whatsapp_api_version", "v15.0"))
        self.whatsapp_country_code_input.setText(settings_service.get_setting("whatsapp_country_code", "91"))
        self.whatsapp_message_template_input.setPlainText(
            settings_service.get_setting(
                "whatsapp_message_template",
                "Hi {customer_name}, thank you for visiting {salon_name}. Your bill total is ₹{total}. Your receipt is attached."
            )
        )
        if settings_service.get_secret("whatsapp_api_token"):
            self.whatsapp_api_token_input.setPlaceholderText("Token is set. Enter a new token to update.")

    def save_integrations_settings(self):
        settings_service.set_setting("whatsapp_phone_id", self.whatsapp_phone_id_input.text())
        settings_service.set_setting("whatsapp_account_id", self.whatsapp_account_id_input.text())
        settings_service.set_setting("whatsapp_api_version", self.whatsapp_api_version_input.text())
        settings_service.set_setting("whatsapp_country_code", self.whatsapp_country_code_input.text())
        settings_service.set_setting("whatsapp_message_template", self.whatsapp_message_template_input.toPlainText())

        if self.whatsapp_api_token_input.text():
            settings_service.set_secret("whatsapp_api_token", self.whatsapp_api_token_input.text())

    def test_whatsapp_connection(self):
        token = settings_service.get_secret("whatsapp_api_token")
        phone_id = self.whatsapp_phone_id_input.text()

        if token and phone_id:
            QMessageBox.information(self, "Connection Test", "WhatsApp token and Phone ID are present.")
        else:
            QMessageBox.warning(self, "Connection Test", "WhatsApp token or Phone ID is missing.")

    def setup_advanced_tab(self):
        layout = QFormLayout(self.advanced_tab)

        db_location_button = QPushButton("Change Database Location")
        db_location_button.setEnabled(False)

        view_logs_button = QPushButton("View Logs")
        view_logs_button.setEnabled(False)

        export_backup_button = QPushButton("Export Backup")
        export_backup_button.setEnabled(False)

        layout.addRow(db_location_button)
        layout.addRow(view_logs_button)
        layout.addRow(export_backup_button)


class StaffDialog(QDialog):
    def __init__(self, parent=None, staff_id=None):
        super().__init__(parent)
        self.staff_id = staff_id

        self.layout = QFormLayout(self)
        self.name_input = QLineEdit()
        self.role_input = QLineEdit()
        self.phone_input = QLineEdit()

        if self.staff_id:
            self.setWindowTitle("Edit Staff")
            with db_session() as db:
                staff = db.query(Staff).filter(Staff.id == self.staff_id).first()
                if staff:
                    self.name_input.setText(staff.name or "")
                    self.role_input.setText(staff.role or "")
                    self.phone_input.setText(staff.phone or "")
        else:
            self.setWindowTitle("Add Staff")

        self.layout.addRow("Name:", self.name_input)
        self.layout.addRow("Role:", self.role_input)
        self.layout.addRow("Phone:", self.phone_input)

        button_box = QHBoxLayout()
        save_button = QPushButton("Save")
        cancel_button = QPushButton("Cancel")
        button_box.addWidget(save_button)
        button_box.addWidget(cancel_button)
        self.layout.addRow(button_box)

        save_button.clicked.connect(self.save_staff)
        cancel_button.clicked.connect(self.reject)

    def save_staff(self):
        # Validate inputs
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Input Error", "Staff name is required.")
            return

        with db_session() as db:
            if self.staff_id:
                staff = db.query(Staff).filter(Staff.id == self.staff_id).first()
                if not staff:
                    QMessageBox.critical(self, "Error", "Staff member not found in database.")
                    return
            else:
                staff = Staff()
                db.add(staff)

            staff.name = self.name_input.text().strip()
            staff.role = (self.role_input.text().strip() or None)
            staff.phone = (self.phone_input.text().strip() or None)

        self.accept()

class ServiceDialog(QDialog):
    def __init__(self, parent=None, service_id=None):
        super().__init__(parent)
        self.service_id = service_id

        self.layout = QFormLayout(self)
        self.name_input = QLineEdit()
        self.description_input = QLineEdit()
        self.price_input = QLineEdit()
        self.duration_input = QLineEdit()

        if self.service_id:
            self.setWindowTitle("Edit Service")
            with db_session() as db:
                service = db.query(Service).filter(Service.id == self.service_id).first()
                if service:
                    self.name_input.setText(service.name or "")
                    self.description_input.setText(service.description or "")
                    self.price_input.setText(str(service.price) if service.price is not None else "")
                    self.duration_input.setText(str(service.duration_minutes) if service.duration_minutes is not None else "")
        else:
            self.setWindowTitle("Add Service")

        self.layout.addRow("Name:", self.name_input)
        self.layout.addRow("Description:", self.description_input)
        self.layout.addRow("Price:", self.price_input)
        self.layout.addRow("Duration (minutes):", self.duration_input)

        button_box = QHBoxLayout()
        save_button = QPushButton("Save")
        cancel_button = QPushButton("Cancel")
        button_box.addWidget(save_button)
        button_box.addWidget(cancel_button)
        self.layout.addRow(button_box)

        save_button.clicked.connect(self.save_service)
        cancel_button.clicked.connect(self.reject)

    def save_service(self):
        from decimal import Decimal, InvalidOperation
        
        # Validate required fields
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Input Error", "Service name is required.")
            return
        
        try:
            price_text = self.price_input.text().strip()
            price = Decimal(price_text) if price_text else None
            
            duration_text = self.duration_input.text().strip()
            duration = int(duration_text) if duration_text else None
        except (InvalidOperation, ValueError):
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid number for price and duration.")
            return

        with db_session() as db:
            if self.service_id:
                service = db.query(Service).filter(Service.id == self.service_id).first()
                if not service:
                    QMessageBox.critical(self, "Error", "Service not found in database.")
                    return
            else:
                service = Service()
                db.add(service)

            service.name = self.name_input.text().strip()
            service.description = (self.description_input.text().strip() or None)
            service.price = price
            service.duration_minutes = duration

        self.accept()
