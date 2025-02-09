from PyQt5.QtWidgets import (
    QVBoxLayout, QGridLayout, QWidget, QPushButton, QTableWidget, 
    QCalendarWidget, QLineEdit, QLabel, QListWidget
)

class bill_page:
    def init_bill_page(self):
        self.bill_page = QWidget()
        self.bill_layout = QVBoxLayout()
        self.bill_page.setLayout(self.bill_layout)

        # Calendar
        self.calendar = QCalendarWidget()
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader) # removes #s on the side
        self.bill_layout.addWidget(self.calendar)

        # Manaul date input
        self.date_input = QLineEdit()
        self.date_input.setPlaceholderText("Enter date (MM/dd/yyyy)")
        self.bill_layout.addWidget(self.date_input)

        # Name input
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter bill name")
        self.name_input.textChanged.connect(self.show_autocomplete_suggestions)
        self.bill_layout.addWidget(self.name_input)

        # Autocomplete suggestions list
        self.suggestions_list = QListWidget()
        self.suggestions_list.setFixedHeight(200)
        self.suggestions_list.itemClicked.connect(self.select_suggestion)
        self.bill_layout.addWidget(self.suggestions_list)

        # Amount input
        self.price_input = QLineEdit()
        self.price_input.setPlaceholderText("Enter price")
        self.bill_layout.addWidget(self.price_input)

        # Category buttons
        self.category_buttons = {}
        self.categories = self.predefined_order  # Changed from category_order
        self.category_layout = QGridLayout()
        for i, category in enumerate(self.categories):
            button = QPushButton(category)
            button.clicked.connect(partial(self.add_category, category))
            button.setFixedHeight(50)  # Set the height of the button
            self.category_layout.addWidget(button, i // 5, i % 5)
            self.category_buttons[category] = button
        self.bill_layout.addLayout(self.category_layout)

        # Image selection button
        self.image_button = QPushButton("Add Photo")
        self.image_button.clicked.connect(self.select_photo)
        self.bill_layout.addWidget(self.image_button)

        # Image preview
        self.image_preview = QLabel()
        self.image_preview.setFixedSize(200, 200)  # Set a fixed size for preview
        self.image_preview.setScaledContents(True)
        self.bill_layout.addWidget(self.image_preview)

        # Store selected image path
        self.selected_image_path = None

        # Save button
        self.save_button = QPushButton("Save Bill")
        self.save_button.clicked.connect(self.save_bill)
        self.bill_layout.addWidget(self.save_button)

        # Table to display bills (only present database)
        self.present_bill_table = QTableWidget(0, 3)
        self.present_bill_table.setHorizontalHeaderLabels(["Date", "Name", "Price"])
        self.bill_layout.addWidget(self.present_bill_table)