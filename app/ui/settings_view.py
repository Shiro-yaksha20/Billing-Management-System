"""Settings UI view."""

from __future__ import annotations

import shutil
from datetime import datetime

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..constants import BACKUP_DIR
from ..exceptions.business_errors import InsufficientDataError, StaffNotFoundError
from ..services.backup_service import BackupService
from ..services.restore_service import RestoreService
from ..services.service_catalog import ServiceCatalog
from ..services.settings_service import SettingsService
from ..services.staff_service import StaffService
from .dialogs.log_viewer_dialog import LogViewerDialog
from .dialogs.service_dialog import ServiceDialog
from .dialogs.staff_dialog import StaffDialog


class SettingsView(QDialog):
    """Settings dialog UI."""

    def __init__(
        self,
        settings_service: SettingsService,
        staff_service: StaffService,
        service_catalog: ServiceCatalog,
        backup_service: BackupService,
        restore_service: RestoreService,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._settings_service = settings_service
        self._staff_service = staff_service
        self._service_catalog = service_catalog
        self._backup_service = backup_service
        self._restore_service = restore_service
        self.setWindowTitle("Settings")
        self.setMinimumWidth(600)

        self.layout = QVBoxLayout(self)
        self.tab_widget = QTabWidget()
        self.layout.addWidget(self.tab_widget)

        self.general_tab = QWidget()
        self.staff_tab = QWidget()
        self.services_tab = QWidget()
        self.integrations_tab = QWidget()
        self.advanced_tab = QWidget()

        self.tab_widget.addTab(self.general_tab, "General")
        self.tab_widget.addTab(self.staff_tab, "Staff")
        self.tab_widget.addTab(self.services_tab, "Services")
        self.tab_widget.addTab(self.integrations_tab, "Integrations")
        self.tab_widget.addTab(self.advanced_tab, "Advanced")

        self.setup_general_tab()
        self.setup_staff_tab()
        self.setup_services_tab()
        self.setup_integrations_tab()
        self.setup_advanced_tab()

        self.button_box = QHBoxLayout()
        self.save_button = QPushButton("Save")
        self.cancel_button = QPushButton("Cancel")
        self.button_box.addStretch()
        self.button_box.addWidget(self.save_button)
        self.button_box.addWidget(self.cancel_button)
        self.layout.addLayout(self.button_box)

        self.save_button.clicked.connect(self.save_settings)
        self.cancel_button.clicked.connect(self.reject)

    def setup_general_tab(self) -> None:
        layout = QFormLayout(self.general_tab)

        self.salon_name_input = QLineEdit()
        self.salon_address_input = QTextEdit()
        self.salon_phone_input = QLineEdit()
        self.salon_gstin_input = QLineEdit()
        self.default_tax_percent_input = QLineEdit()
        self.thank_you_message_input = QLineEdit()

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
        layout.addRow("Instagram Handle:", self.salon_instagram_input)
        layout.addRow("Tagline:", self.salon_tagline_input)
        layout.addRow("Salon Logo:", logo_row)
        layout.addRow("Google Review Link:", self.google_review_link_input)
        layout.addRow("Receipt Footer:", self.receipt_footer_message_input)

        self.browse_logo_button.clicked.connect(self.browse_logo_file)
        self.load_general_settings()

    def browse_logo_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Logo Image",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp);;All Files (*)",
        )
        if file_path:
            self.salon_logo_path_input.setText(file_path)

    def load_general_settings(self) -> None:
        self.salon_name_input.setText(self._settings_service.get_setting("salon_name", ""))
        self.salon_address_input.setPlainText(self._settings_service.get_setting("salon_address", ""))
        self.salon_phone_input.setText(self._settings_service.get_setting("salon_phone", ""))
        self.salon_gstin_input.setText(self._settings_service.get_setting("salon_gstin", ""))
        self.default_tax_percent_input.setText(self._settings_service.get_setting("default_tax_percent", "0"))
        self.thank_you_message_input.setText(
            self._settings_service.get_setting("thank_you_message", "Thank you for your visit!")
        )
        self.salon_instagram_input.setText(self._settings_service.get_setting("salon_instagram", ""))
        self.salon_tagline_input.setText(self._settings_service.get_setting("salon_tagline", ""))
        self.salon_logo_path_input.setText(self._settings_service.get_setting("salon_logo_path", ""))
        self.google_review_link_input.setText(self._settings_service.get_setting("google_review_link", ""))
        self.receipt_footer_message_input.setPlainText(
            self._settings_service.get_setting("receipt_footer_message", "Thank you for visiting!")
        )

    def save_general_settings(self) -> bool:
        try:
            tax = float(self.default_tax_percent_input.text() or "0")
            if not (0 <= tax <= 100):
                raise ValueError("Tax must be between 0 and 100")
        except ValueError as exc:
            QMessageBox.warning(self, "Invalid Tax", f"Invalid tax percentage: {exc}")
            return False

        if not self.salon_name_input.text().strip():
            QMessageBox.warning(self, "Missing Name", "Salon name is required")
            return False

        phone = self.salon_phone_input.text().strip()
        if phone and not phone.replace("+", "").replace("-", "").replace(" ", "").isdigit():
            QMessageBox.warning(self, "Invalid Phone", "Phone number contains invalid characters")
            return False

        gstin = self.salon_gstin_input.text().strip()
        if gstin and (len(gstin) != 15 or not gstin.isalnum()):
            QMessageBox.warning(self, "Invalid GSTIN", "GSTIN must be 15 alphanumeric characters")
            return False

        self._settings_service.set_setting("salon_name", self.salon_name_input.text())
        self._settings_service.set_setting("salon_address", self.salon_address_input.toPlainText())
        self._settings_service.set_setting("salon_phone", phone)
        self._settings_service.set_setting("salon_gstin", gstin)
        self._settings_service.set_setting("default_tax_percent", str(tax))
        self._settings_service.set_setting("thank_you_message", self.thank_you_message_input.text())
        self._settings_service.set_setting("salon_instagram", self.salon_instagram_input.text().strip())
        self._settings_service.set_setting("salon_tagline", self.salon_tagline_input.text().strip())
        self._settings_service.set_setting("salon_logo_path", self.salon_logo_path_input.text().strip())
        self._settings_service.set_setting("google_review_link", self.google_review_link_input.text().strip())
        self._settings_service.set_setting(
            "receipt_footer_message", self.receipt_footer_message_input.toPlainText().strip()
        )
        return True

    def setup_staff_tab(self) -> None:
        layout = QVBoxLayout(self.staff_tab)

        self.staff_table = QTableWidget()
        self.staff_table.setColumnCount(4)
        self.staff_table.setHorizontalHeaderLabels(["Name", "Role", "Phone", "Active"])
        self.staff_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.staff_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.staff_table.setSortingEnabled(True)
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

    def load_staff_data(self) -> None:
        self.staff_table.blockSignals(True)
        try:
            staff_list = self._staff_service.list_all()
            self.staff_table.setRowCount(len(staff_list))
            for i, staff in enumerate(staff_list):
                self.staff_table.setItem(i, 0, QTableWidgetItem(staff.name or ""))
                self.staff_table.setItem(i, 1, QTableWidgetItem(staff.role or ""))
                self.staff_table.setItem(i, 2, QTableWidgetItem(staff.phone or ""))
                self.staff_table.setItem(i, 3, QTableWidgetItem("Yes" if staff.active else "No"))
                self.staff_table.item(i, 0).setData(Qt.ItemDataRole.UserRole, staff.id)
        finally:
            self.staff_table.blockSignals(False)

    def add_staff(self) -> None:
        dialog = StaffDialog(self._staff_service, self)
        if dialog.exec():
            self.load_staff_data()

    def edit_staff(self) -> None:
        selected_row = self.staff_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "No Staff Selected", "Please select a staff member to edit.")
            return

        item = self.staff_table.item(selected_row, 0)
        if not item:
            QMessageBox.warning(self, "Invalid Selection", "Could not identify selected staff.")
            return

        staff_id = item.data(Qt.ItemDataRole.UserRole)
        dialog = StaffDialog(self._staff_service, self, staff_id=staff_id)
        if dialog.exec():
            self.load_staff_data()

    def toggle_staff_active(self) -> None:
        selected_row = self.staff_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "No Staff Selected", "Please select a staff member to toggle their active status.")
            return

        item = self.staff_table.item(selected_row, 0)
        if not item:
            QMessageBox.warning(self, "Invalid Selection", "Could not identify selected staff.")
            return

        staff_id = item.data(Qt.ItemDataRole.UserRole)
        try:
            self._staff_service.toggle_active(staff_id)
            self.load_staff_data()
        except StaffNotFoundError:
            QMessageBox.critical(self, "Error", "Staff member not found in database.")

    def setup_services_tab(self) -> None:
        layout = QVBoxLayout(self.services_tab)

        category_group = QGroupBox("Service Categories")
        category_layout = QVBoxLayout()
        self._category_list = QListWidget()
        category_buttons = QHBoxLayout()
        add_category_button = QPushButton("Add Category")
        rename_category_button = QPushButton("Rename Category")
        delete_category_button = QPushButton("Delete Category")
        category_buttons.addWidget(add_category_button)
        category_buttons.addWidget(rename_category_button)
        category_buttons.addWidget(delete_category_button)
        category_layout.addWidget(self._category_list)
        category_layout.addLayout(category_buttons)
        category_group.setLayout(category_layout)
        layout.addWidget(category_group)

        add_category_button.clicked.connect(self.add_category)
        rename_category_button.clicked.connect(self.rename_category)
        delete_category_button.clicked.connect(self.delete_category)

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
        self.services_table.setHorizontalHeaderLabels(
            ["Name", "Description", "Price", "Duration (min)", "Active"]
        )
        self.services_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.services_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.services_table.setSortingEnabled(True)
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
        self.load_category_data()

    def load_category_data(self) -> None:
        self._category_list.clear()
        categories = self._service_catalog.list_categories()
        for category in categories:
            self._category_list.addItem(category)

    def add_category(self) -> None:
        name, ok = QInputDialog.getText(self, "Add Category", "Category name:")
        if not ok or not name.strip():
            return
        existing = {self._category_list.item(i).text() for i in range(self._category_list.count())}
        if name.strip() in existing:
            QMessageBox.information(self, "Category Exists", "Category already exists.")
            return
        self._category_list.addItem(name.strip())

    def rename_category(self) -> None:
        item = self._category_list.currentItem()
        if not item:
            QMessageBox.warning(self, "No Category Selected", "Please select a category to rename.")
            return
        new_name, ok = QInputDialog.getText(self, "Rename Category", "New name:", text=item.text())
        if not ok or not new_name.strip():
            return
        old_name = item.text()
        if old_name == new_name.strip():
            return
        self._service_catalog.rename_category(old_name, new_name.strip())
        item.setText(new_name.strip())
        self.load_service_data()

    def delete_category(self) -> None:
        item = self._category_list.currentItem()
        if not item:
            QMessageBox.warning(self, "No Category Selected", "Please select a category to delete.")
            return
        category = item.text()
        confirm = QMessageBox.question(
            self,
            "Delete Category",
            f"Remove category '{category}' from all services?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        self._service_catalog.delete_category(category)
        self.load_category_data()
        self.load_service_data()

    def load_service_data(self) -> None:
        self.services_table.blockSignals(True)
        try:
            service_list = self._service_catalog.list_all()
            self.services_table.setRowCount(len(service_list))
            for i, service in enumerate(service_list):
                self.services_table.setItem(i, 0, QTableWidgetItem(service.name or ""))
                self.services_table.setItem(i, 1, QTableWidgetItem(service.description or ""))
                self.services_table.setItem(
                    i,
                    2,
                    QTableWidgetItem(str(service.price) if service.price is not None else ""),
                )
                self.services_table.setItem(
                    i,
                    3,
                    QTableWidgetItem(
                        str(service.duration_minutes) if service.duration_minutes is not None else ""
                    ),
                )
                self.services_table.setItem(i, 4, QTableWidgetItem("Yes" if service.active else "No"))
                self.services_table.item(i, 0).setData(Qt.ItemDataRole.UserRole, service.id)
        finally:
            self.services_table.blockSignals(False)

    def add_service(self) -> None:
        dialog = ServiceDialog(self._service_catalog, self)
        if dialog.exec():
            self.load_service_data()

    def edit_service(self) -> None:
        selected_row = self.services_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "No Service Selected", "Please select a service to edit.")
            return

        item = self.services_table.item(selected_row, 0)
        if not item:
            QMessageBox.warning(self, "Invalid Selection", "Could not identify selected service.")
            return

        service_id = item.data(Qt.ItemDataRole.UserRole)
        dialog = ServiceDialog(self._service_catalog, self, service_id=service_id)
        if dialog.exec():
            self.load_service_data()

    def toggle_service_active(self) -> None:
        selected_row = self.services_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "No Service Selected", "Please select a service to toggle its active status.")
            return

        item = self.services_table.item(selected_row, 0)
        if not item:
            QMessageBox.warning(self, "Invalid Selection", "Could not identify selected service.")
            return

        service_id = item.data(Qt.ItemDataRole.UserRole)
        if not self._service_catalog.toggle_active(service_id):
            QMessageBox.critical(self, "Error", "Service not found in database.")
        self.load_service_data()

    def import_services_csv(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Services CSV File",
            "",
            "CSV Files (*.csv);;All Files (*)",
        )
        if not file_path:
            return

        reply = QMessageBox.question(
            self,
            "Import Options",
            "How should existing services be handled?\n\n"
            "- Yes: Deactivate existing services (recommended)\n"
            "- No: Keep existing services active\n"
            "- Cancel: Cancel import",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Yes,
        )

        if reply == QMessageBox.StandardButton.Cancel:
            return

        deactivate_existing = reply == QMessageBox.StandardButton.Yes
        results = self._service_catalog.import_from_csv(file_path, deactivate_existing=deactivate_existing)

        if results["success"]:
            message = (
                "Import completed successfully!\n\n"
                f"? Imported: {results['imported']} new services\n"
                f"? Updated: {results['updated']} existing services\n"
            )
            if results["deactivated"] > 0:
                message += f"? Deactivated: {results['deactivated']} old services\n"
            if results["skipped"] > 0:
                message += f"? Skipped: {results['skipped']} rows with errors\n"
            QMessageBox.information(self, "Import Successful", message)
        else:
            error_msg = "\n".join(results["errors"][:5])
            if len(results["errors"]) > 5:
                error_msg += f"\n... and {len(results['errors']) - 5} more errors"
            QMessageBox.warning(
                self,
                "Import Completed with Errors",
                f"Imported: {results['imported']}, Errors: {len(results['errors'])}\n\n{error_msg}",
            )
        self.load_service_data()

    def export_services_csv(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Services CSV File",
            "services_export.csv",
            "CSV Files (*.csv);;All Files (*)",
        )
        if not file_path:
            return

        reply = QMessageBox.question(
            self,
            "Export Options",
            "Export only active services?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        active_only = reply == QMessageBox.StandardButton.Yes

        if self._service_catalog.export_to_csv(file_path, active_only=active_only):
            QMessageBox.information(
                self,
                "Export Successful",
                f"Services exported successfully to:\n{file_path}",
            )
        else:
            QMessageBox.warning(self, "Export Failed", "Failed to export services. Check logs for details.")

    def setup_integrations_tab(self) -> None:
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

    def load_integrations_settings(self) -> None:
        self.whatsapp_phone_id_input.setText(self._settings_service.get_setting("whatsapp_phone_id", ""))
        self.whatsapp_account_id_input.setText(
            self._settings_service.get_setting("whatsapp_account_id", "")
        )
        self.whatsapp_api_version_input.setText(
            self._settings_service.get_setting("whatsapp_api_version", "v15.0")
        )
        self.whatsapp_country_code_input.setText(
            self._settings_service.get_setting("whatsapp_country_code", "91")
        )
        self.whatsapp_message_template_input.setPlainText(
            self._settings_service.get_setting(
                "whatsapp_message_template",
                "Hi {customer_name}, thank you for visiting {salon_name}. Your bill total is ?{total}. Your receipt is attached.",
            )
        )
        if self._settings_service.get_secret("whatsapp_api_token"):
            self.whatsapp_api_token_input.setPlaceholderText(
                "Token is set. Enter a new token to update."
            )

    def save_integrations_settings(self) -> None:
        self._settings_service.set_setting("whatsapp_phone_id", self.whatsapp_phone_id_input.text())
        self._settings_service.set_setting(
            "whatsapp_account_id", self.whatsapp_account_id_input.text()
        )
        self._settings_service.set_setting(
            "whatsapp_api_version", self.whatsapp_api_version_input.text()
        )
        self._settings_service.set_setting(
            "whatsapp_country_code", self.whatsapp_country_code_input.text()
        )
        self._settings_service.set_setting(
            "whatsapp_message_template", self.whatsapp_message_template_input.toPlainText()
        )
        if self.whatsapp_api_token_input.text():
            self._settings_service.set_secret("whatsapp_api_token", self.whatsapp_api_token_input.text())

    def test_whatsapp_connection(self) -> None:
        token = self._settings_service.get_secret("whatsapp_api_token")
        phone_id = self.whatsapp_phone_id_input.text()

        if token and phone_id:
            QMessageBox.information(self, "Connection Test", "WhatsApp token and Phone ID are present.")
        else:
            QMessageBox.warning(self, "Connection Test", "WhatsApp token or Phone ID is missing.")

    def setup_advanced_tab(self) -> None:
        layout = QFormLayout(self.advanced_tab)

        db_location_button = QPushButton("Change Database Location")
        db_location_button.setEnabled(False)

        view_logs_button = QPushButton("View Logs")
        view_logs_button.clicked.connect(self._on_view_logs_clicked)

        self._export_backup_button = QPushButton("Export Backup")
        self._restore_backup_button = QPushButton("Import Backup")

        self._export_backup_button.clicked.connect(self._on_backup_clicked)
        self._restore_backup_button.clicked.connect(self._on_restore_clicked)

        layout.addRow(db_location_button)
        layout.addRow(view_logs_button)
        layout.addRow(self._export_backup_button)
        layout.addRow(self._restore_backup_button)

    def _on_view_logs_clicked(self) -> None:
        dialog = LogViewerDialog(self)
        dialog.exec()

    def _on_backup_clicked(self) -> None:
        default_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        default_path = str(BACKUP_DIR / default_name)
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Backup",
            default_path,
            "Database Files (*.db);;All Files (*)",
        )
        if not file_path:
            return

        try:
            backup_info = self._backup_service.create_backup(reason="manual")
            if file_path != backup_info.path:
                shutil.copy2(backup_info.path, file_path)
            QMessageBox.information(self, "Backup Created", f"Backup saved to:\n{file_path}")
        except Exception as exc:
            QMessageBox.critical(self, "Backup Failed", f"Backup failed: {exc}")

    def _on_restore_clicked(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Backup File",
            str(BACKUP_DIR),
            "Database Files (*.db);;All Files (*)",
        )
        if not file_path:
            return

        result = self._restore_service.restore_from_file(file_path)
        if result.success:
            QMessageBox.information(
                self,
                "Restore Completed",
                "Backup restored successfully. Please restart the application.",
            )
        else:
            QMessageBox.warning(self, "Restore Failed", result.message)

    def save_settings(self) -> None:
        if not self.save_general_settings():
            return
        self.save_integrations_settings()
        QMessageBox.information(self, "Settings Saved", "Your settings have been saved successfully.")
        self.accept()
