import sys
from PyQt6.QtWidgets import QApplication
from app.database import init_db
from app.gui_main import MainWindow
from app.utils import logger

def main():
    """Main function to run the application."""
    logger.info("Application starting...")
    try:
        # Initialize the database and create tables
        init_db()

        # Create the Qt application
        app = QApplication(sys.argv)

        # Create and show the main window
        main_window = MainWindow()
        main_window.show()

        # Start the application event loop
        sys.exit(app.exec())
    except Exception as e:
        logger.critical("An uncaught exception occurred", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
