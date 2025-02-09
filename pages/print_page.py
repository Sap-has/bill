from PyQt5.QtWidgets import (
    QVBoxLayout, QWidget, QPushButton, QTableWidget, QLineEdit, QComboBox, QHBoxLayout
)

class print_page:
    def init_print_page(self):
        self.print_page = QWidget()
        self.print_layout = QVBoxLayout()
        self.print_page.setLayout(self.print_layout)

        # Date Range Inputs
        date_range_layout = QHBoxLayout()

        self.start_date_input = QLineEdit()
        self.start_date_input.setPlaceholderText("Start date (MM/dd/yyyy)")
        date_range_layout.addWidget(self.start_date_input)

        self.end_date_input = QLineEdit()
        self.end_date_input.setPlaceholderText("End date (MM/dd/yyyy)")
        date_range_layout.addWidget(self.end_date_input)

        self.print_layout.addLayout(date_range_layout)

        # Button to filter by date range
        self.filter_button = QPushButton("Filter by Date Range")
        self.filter_button.clicked.connect(self.filter_by_date_range)
        self.print_layout.addWidget(self.filter_button)

        # Sort buttons
        sort_buttons_layout = QHBoxLayout()

        self.sort_asc_button = QPushButton("Sort by Date (Ascending)")
        self.sort_asc_button.clicked.connect(lambda: self.sort_table("asc"))
        sort_buttons_layout.addWidget(self.sort_asc_button)

        self.sort_desc_button = QPushButton("Sort by Date (Descending)")
        self.sort_desc_button.clicked.connect(lambda: self.sort_table("desc"))
        sort_buttons_layout.addWidget(self.sort_desc_button)

        self.print_layout.addLayout(sort_buttons_layout)

        # Print and Show All Bills buttons
        buttons_layout = QHBoxLayout()

        self.print_button = QPushButton("Print Bills")
        self.print_button.clicked.connect(self.print_bills)
        buttons_layout.addWidget(self.print_button)

        self.show_all_button = QPushButton("Show All Bills")
        self.show_all_button.clicked.connect(self.load_bills)
        buttons_layout.addWidget(self.show_all_button)

        self.print_layout.addLayout(buttons_layout)

        # Database selection dropdown
        self.year_selector = QComboBox()
        self.year_selector.addItem("Present Database")
        self.year_selector.currentIndexChanged.connect(self.load_bills)
        self.print_layout.addWidget(self.year_selector)

        # Table to display bills
        self.bill_table = QTableWidget(0, 3)
        self.bill_table.setHorizontalHeaderLabels(["Date", "Name", "Price"])
        self.print_layout.addWidget(self.bill_table)