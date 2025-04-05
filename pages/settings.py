from PyQt5.QtWidgets import (
    QVBoxLayout, QWidget, QMainWindow
)

from util.uiHelper import UIHelper

class settings(QMainWindow):
    def init_settings_page(self):
        """Initialize the Settings tab for managing categories."""
        self.settings_page = QWidget()
        self.settings_layout = QVBoxLayout()
        self.settings_page.setLayout(self.settings_layout)

        # Section: Add Category
        self.settings_layout.addWidget(UIHelper.create_section_label("Add New Category"))

        # New category input
        self.new_category_input = UIHelper.create_input_field("Enter new category")
        self.settings_layout.addWidget(self.new_category_input)

        # Add category button
        self.add_category_button = UIHelper.create_button("Add Category", self.add_new_category)
        self.settings_layout.addWidget(self.add_category_button)
        
        UIHelper.add_section_spacing(self.settings_layout)
        
        # Section: Existing Categories
        self.settings_layout.addWidget(UIHelper.create_section_label("Existing Categories"))

        # Category list layout (populated in update_settings_page)
        self.category_list_layout = QVBoxLayout()
        self.settings_layout.addLayout(self.category_list_layout)
        