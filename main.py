import sys
from PyQt5.QtWidgets import QApplication

from pages.main_page import BillTracker

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BillTracker()
    window.show()
    sys.exit(app.exec_())