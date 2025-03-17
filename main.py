import sys
from PyQt5.QtWidgets import QApplication
from src.ui import TirageApp

def main():
    # Create the application instance
    app = QApplication(sys.argv)
    window = TirageApp()
    window.resize(500, 600)
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
