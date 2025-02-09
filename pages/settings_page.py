from PyQt5.QtWidgets import (
    QVBoxLayout, QWidget, QPushButton, QLineEdit, QLabel
)

class settings_page:
    def init_settings_page(self):
        self.settings_page = QWidget()
        self.settings_layout = QVBoxLayout()
        self.settings_page.setLayout(self.settings_layout)

        self.settings_label = QLabel("Edit Categories:")
        self.settings_layout.addWidget(self.settings_label)

        self.new_category_input = QLineEdit()
        self.new_category_input.setPlaceholderText("Enter new category")
        self.settings_layout.addWidget(self.new_category_input)

        self.add_category_button = QPushButton("Add Category")
        self.add_category_button.clicked.connect(self.add_new_category)
        self.settings_layout.addWidget(self.add_category_button)

        self.category_list_layout = QVBoxLayout()
        self.settings_layout.addLayout(self.category_list_layout)