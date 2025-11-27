import pytest
import os
import sys

# Force offscreen platform before importing PyQt
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt6.QtWidgets import QApplication
from app.gui_main import MainWindow

@pytest.fixture(scope="session")
def qapp():
    if not QApplication.instance():
        app = QApplication(sys.argv)
    else:
        app = QApplication.instance()
    yield app

def test_mainwindow_initialization(qapp, qtbot, mocker):
    # Mock database session to prevent actual DB connection during UI init
    # MainWindow likely loads data in __init__ or showEvent

    # We need to mock db_session context manager in gui_billing and gui_main if used.
    # gui_main.py imports MainWindow from .gui_main ... wait, gui_main IS where MainWindow is.

    # Let's inspect gui_main.py first to see what it does on init.
    pass

    # For now, let's try to just instantiate. If it fails due to DB, we will fix mocks.
    try:
        window = MainWindow()
        qtbot.addWidget(window)
        assert window.windowTitle() == "Salon Billing System"
    except Exception as e:
        pytest.fail(f"MainWindow failed to initialize: {e}")
