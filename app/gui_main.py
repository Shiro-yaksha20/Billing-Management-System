from PyQt6.QtWidgets import QMainWindow, QPushButton, QVBoxLayout, QWidget, QMessageBox, QHBoxLayout
from .gui_settings import SettingsWindow
from .gui_customers import CustomerWindow
from .gui_billing import BillingWindow

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Salon Billing System")
        self.setGeometry(100, 100, 800, 600)  # x, y, width, height

        # Central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Settings button
        # Button layout
        button_layout = QHBoxLayout()
        self.settings_button = QPushButton("Settings")
        self.settings_button.clicked.connect(self.open_settings_window)
        button_layout.addWidget(self.settings_button)

        self.customers_button = QPushButton("Manage Customers")
        self.customers_button.clicked.connect(self.open_customers_window)
        button_layout.addWidget(self.customers_button)

        self.new_bill_button = QPushButton("New Bill")
        self.new_bill_button.clicked.connect(self.open_billing_window)
        button_layout.addWidget(self.new_bill_button)

        self.layout.addLayout(button_layout)

        # Placeholder for the main billing interface
        # In a real application, this would be replaced with the actual billing UI
        placeholder_label = QPushButton("Main Billing Area (Placeholder)")
        placeholder_label.setEnabled(False)
        self.layout.addWidget(placeholder_label)
        self.layout.addStretch(1)


    def open_settings_window(self):
        """
        Opens the settings dialog.
        """
        # The SettingsWindow is created as a dialog here.
        # It's better to make it modal so the user has to close it
        # before interacting with the main window again.
        self.settings_dialog = SettingsWindow(self)
        self.settings_dialog.exec() # Use exec() for a modal dialog

    def open_customers_window(self):
        """
        Opens the customer management dialog.
        """
        self.customers_dialog = CustomerWindow(self)
        self.customers_dialog.exec()

    def open_billing_window(self):
        """
        Opens the new bill dialog.
        """
        self.billing_dialog = BillingWindow(self)
        self.billing_dialog.exec()
