from PyQt5.QtWidgets import (
    QVBoxLayout, QWidget, QPushButton, QLineEdit, QTableWidget, QHBoxLayout, QComboBox
)

class delete_page:
    def init_delete_page(self):
        self.delete_page = QWidget()
        self.delete_layout = QVBoxLayout()
        self.delete_page.setLayout(self.delete_layout)

        # Search by date
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter date (MM/dd/yyyy) to search")
        self.delete_layout.addWidget(self.search_input)

        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.search_by_date)
        self.delete_layout.addWidget(self.search_button)

        # Sorting buttons
        sort_buttons_layout = QHBoxLayout()

        self.sort_asc_button = QPushButton("Sort Ascending")
        self.sort_asc_button.clicked.connect(lambda: self.sort_delete_table("asc"))
        sort_buttons_layout.addWidget(self.sort_asc_button)

        self.sort_desc_button = QPushButton("Sort Descending")
        self.sort_desc_button.clicked.connect(lambda: self.sort_delete_table("desc"))
        sort_buttons_layout.addWidget(self.sort_desc_button)

        self.delete_layout.addLayout(sort_buttons_layout)

        # Show All Bills and Delete buttons
        buttons_layout = QHBoxLayout()

        self.show_all_button = QPushButton("Show All Bills")
        self.show_all_button.clicked.connect(self.load_delete_table)
        buttons_layout.addWidget(self.show_all_button)

        self.delete_button = QPushButton("Delete Selected")
        self.delete_button.clicked.connect(self.delete_selected_row)
        buttons_layout.addWidget(self.delete_button)

        self.delete_layout.addLayout(buttons_layout)

        # Database selection dropdown
        self.delete_year_selector = QComboBox()
        for i in range(self.year_selector.count()):
            year = self.year_selector.itemText(i)
            if year != "Present Database":
                self.delete_year_selector.addItem(year)
        self.delete_year_selector.currentIndexChanged.connect(self.load_delete_table)
        self.delete_layout.addWidget(self.delete_year_selector)

        # Table to display bills
        self.delete_table = QTableWidget(0, 3)
        self.delete_table.setHorizontalHeaderLabels(["Date", "Name", "Price"])
        self.delete_layout.addWidget(self.delete_table)