def apply_styles(self):
    self.setStyleSheet("""
        QWidget {
            font-size: 20px;
        }
        QMainWindow {
            background-color: #f0f0f0;
        }
        QTabBar::tab {
            height: 40px;
            width: 150px;
        }
        QLineEdit, QTableWidget, QCalendarWidget, QPushButton {
            color: black;
            padding: 5px;
        }
        QPushButton {
            background-color: #357a38;
            color: white;
            border: none;
            border-radius: 5px;
            min-height: 40px;
        }
        QPushButton:hover {
            background-color: #45a049;
        }
        QTableWidget {
            background-color: white;
            border: 1px solid #ccc;
        }
    """)