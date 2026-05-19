from __future__ import annotations

import sys

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QApplication
from app.infrastructure.database import init_db, db_session
from app.repositories import (
    BillRepository,
    CustomerRepository,
    ServiceRepository,
    SettingsRepository,
    StaffRepository,
)
from app.services import (
    BackupService,
    BillingService,
    CustomerService,
    NotificationService,
    ReportService,
    ServiceCatalog,
    SettingsService,
    StaffService,
)
from app.services.restore_service import RestoreService
from app.ui.main_window import MainWindow
from app.ui.theme import apply_theme
from app.infrastructure.logging import logger

def main():
    """Main function to run the application."""
    logger.info("Application starting...")
    try:
        backup_service = BackupService()
        try:
            backup_service.create_backup(reason="startup")
        except Exception as be:
            logger.warning(f"Startup backup not created: {be}")

        init_db()
        try:
            from app.migrate_service_schema import migrate_service_table
            from app.migrate_bill_status_sync import migrate as migrate_bill_status_sync

            migrate_service_table()
            migrate_bill_status_sync()
        except Exception as migration_error:
            logger.error(f"Database migration failed: {migration_error}")

        app = QApplication(sys.argv)
        app.setFont(QFont("Segoe UI", 10))
        apply_theme(app)

        session_factory = db_session
        bill_repo = BillRepository(session_factory)
        customer_repo = CustomerRepository(session_factory)
        staff_repo = StaffRepository(session_factory)
        service_repo = ServiceRepository(session_factory)
        settings_repo = SettingsRepository(session_factory)

        settings_service = SettingsService(settings_repo)
        notification_service = NotificationService(settings_service)
        billing_service = BillingService(bill_repo, customer_repo, staff_repo, settings_service)
        customer_service = CustomerService(customer_repo, bill_repo)
        staff_service = StaffService(staff_repo)
        service_catalog = ServiceCatalog(service_repo)
        report_service = ReportService(bill_repo, settings_service)
        restore_service = RestoreService()

        main_window = MainWindow(
            billing_service=billing_service,
            customer_service=customer_service,
            staff_service=staff_service,
            service_catalog=service_catalog,
            report_service=report_service,
            settings_service=settings_service,
            notification_service=notification_service,
            backup_service=backup_service,
            restore_service=restore_service,
        )
        main_window.show()

        sys.exit(app.exec())
    except Exception:
        logger.critical("An uncaught exception occurred", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
