from PyQt5.QtWidgets import (
    QVBoxLayout, QWidget, QLabel, QComboBox, QTableWidget
)

class data_page:
    def init_data_page(self):
        self.data_page = QWidget()
        self.data_layout = QVBoxLayout()
        self.data_page.setLayout(self.data_layout)

        self.data_label = QLabel("Monthly Expenditure:")
        self.data_layout.addWidget(self.data_label)

        self.data_year_selector = QComboBox()
        self.data_year_selector.addItem("Present Database")
        self.data_year_selector.currentIndexChanged.connect(self.load_data)
        self.data_layout.addWidget(self.data_year_selector)

        self.data_table = QTableWidget(0, 4)
        self.data_table.setHorizontalHeaderLabels(["Month", "Cash", "Not Cash", "Total"])
        self.data_layout.addWidget(self.data_table)