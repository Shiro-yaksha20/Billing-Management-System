# -*- mode: python ; coding: utf-8 -*-

a = Analysis(['main.py'],
             pathex=[],
             binaries=[],
             datas=[('app', 'app')],
             hiddenimports=[
                 # Keyring backend (Windows)
                 'keyring.backends.Windows',

                 # PyQt6 core and common submodules
                 'PyQt6',
                 'PyQt6.QtWidgets',
                 'PyQt6.QtCore',
                 'PyQt6.QtGui',
                 'PyQt6.QtNetwork',
                 'PyQt6.QtPrintSupport',
                 'PyQt6.QtSvg',
                 'PyQt6.QtSvgWidgets',

                 # SQLAlchemy ORM and related
                 'sqlalchemy',
                 'sqlalchemy.orm',
                 'sqlalchemy.sql',
                 'sqlalchemy.ext.declarative',

                 # ReportLab for PDF generation
                 'reportlab',
                 'reportlab.platypus',
                 'reportlab.pdfgen',
                 'reportlab.pdfgen.canvas',
                 'reportlab.lib',
                 'reportlab.lib.styles',
                 'reportlab.lib.pagesizes',
                 'reportlab.lib.units',

                 # Requests HTTP stack (for WhatsApp client)
                 'requests',
                 'urllib3',
                 'certifi',
                 'charset_normalizer',
                 'idna',

                 # Excel export (openpyxl)
                 'openpyxl',
                 'et_xmlfile',

                 # Application modules
                 'app',
                 'app.constants',
                 'app.models',

                 # Infrastructure layer
                 'app.infrastructure.database',
                 'app.infrastructure.logging',
                 'app.infrastructure.pdf_generator',
                 'app.infrastructure.whatsapp_client',
                 'app.infrastructure.cloud_drive',
                 'app.infrastructure.crypto',

                 # Service layer
                 'app.services.billing_service',
                 'app.services.customer_service',
                 'app.services.staff_service',
                 'app.services.service_catalog',
                 'app.services.settings_service',
                 'app.services.report_service',
                 'app.services.notification_service',
                 'app.services.backup_service',
                 'app.services.restore_service',

                 # Repository layer
                 'app.repositories.bill_repository',
                 'app.repositories.customer_repository',
                 'app.repositories.staff_repository',
                 'app.repositories.service_repository',
                 'app.repositories.settings_repository',

                 # UI layer
                 'app.ui.main_window',
                 'app.ui.billing_view',
                 'app.ui.customer_view',
                 'app.ui.settings_view',
                 'app.ui.export_view',
                 'app.ui.bill_history_view',
                 'app.ui.dialogs.customer_dialog',
                 'app.ui.dialogs.customer_selection_dialog',
                 'app.ui.dialogs.staff_dialog',
                 'app.ui.dialogs.service_dialog',
                 'app.ui.dialogs.log_viewer_dialog',

                 # DTO layer
                 'app.dto.bill_dto',
                 'app.dto.customer_dto',
                 'app.dto.backup_dto',
                 'app.dto.staff_dto',
                 'app.dto.service_dto',
                 'app.dto.receipt_dto',

                 # Exceptions
                 'app.exceptions.business_errors',
                 'app.exceptions.validation_errors',
             ],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=None,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=None)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='SalonBillingSystem',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='SalonBillingSystem')
