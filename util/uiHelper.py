from util.translationManager import TranslationManager
import json

from PyQt5.QtWidgets import (
    QWidget, QPushButton, QTableWidget, QLineEdit, QLabel
)

DEFAULT_CATEGORIES = ["Mortgage", "Food", "Gas", "Mechanic", "Work Clothes", "Materials", "Miscellaneous", "Doctor", "Equipment & Rent", "Cash"]

class UIHelper:
    """Helper class for creating consistent UI components."""
    
    # Static translator instance
    translator = TranslationManager()
    
    @staticmethod
    def translate(text):
        """Translate text using the current language.
        
        Args:
            text: Text to translate
            
        Returns:
            str: Translated text
        """
        return UIHelper.translator.translate(text)
    
    @staticmethod
    def create_button(text, callback=None, height=40):
        """Create a styled button with optional callback.
        
        Args:
            text: Button text
            callback: Function to call when button is clicked
            height: Button height in pixels
            
        Returns:
            QPushButton: The created button
        """
        button = QPushButton(UIHelper.translate(text))
        button.setFixedHeight(height)
        button.setProperty("original_text", text)  # Store original text for translation updates
        if callback:
            button.clicked.connect(callback)
        return button
    
    @staticmethod
    def create_input_field(placeholder, validator=None):
        """Create a styled input field with optional validator.
        
        Args:
            placeholder: Placeholder text
            validator: Optional QValidator for input validation
            
        Returns:
            QLineEdit: The created input field
        """
        input_field = QLineEdit()
        input_field.setPlaceholderText(UIHelper.translate(placeholder))
        input_field.setProperty("original_placeholder", placeholder)  # Store original text for translation updates
        if validator:
            input_field.setValidator(validator)
        return input_field
    
    @staticmethod
    def create_date_input():
        """Create a date input field with consistent formatting.
        
        Returns:
            QLineEdit: The created date input field
        """
        date_input = QLineEdit()
        date_input.setPlaceholderText(UIHelper.translate("MM/dd/yyyy"))
        date_input.setProperty("original_placeholder", "MM/dd/yyyy")  # Store original text for translation updates
        return date_input
    
    @staticmethod
    def create_section_label(text):
        """Create a section label with consistent styling.
        
        Args:
            text: Label text
            
        Returns:
            QLabel: The created label
        """
        label = QLabel(UIHelper.translate(text))
        label.setStyleSheet("font-weight: bold; font-size: 16px; margin-top: 10px;")
        label.setProperty("original_text", text)  # Store original text for translation updates
        return label
    
    @staticmethod
    def create_table(columns, headers=None):
        """Create a styled table with specified columns.
        
        Args:
            columns: Number of columns
            headers: Optional list of column headers
            
        Returns:
            QTableWidget: The created table
        """
        table = QTableWidget(0, columns)
        if headers:
            translated_headers = [UIHelper.translate(header) for header in headers]
            table.setHorizontalHeaderLabels(translated_headers)
            table.setProperty("original_headers", headers)  # Store original headers for translation updates
        table.horizontalHeader().setStretchLastSection(True)
        table.setAlternatingRowColors(True)
        return table
    
    @staticmethod
    def add_section_spacing(layout):
        """Add consistent spacing between sections.
        
        Args:
            layout: The layout to add spacing to
        """
        spacer = QWidget()
        spacer.setFixedHeight(20)
        layout.addWidget(spacer)

class SettingsManager:
    """Handles settings and categories for the bill tracker application."""
    
    def __init__(self):
        """Initialize the settings manager."""
        pass
    
    @staticmethod
    def load_categories():
        """Load categories from the categories.json file.
        
        Returns:
            list: The list of categories.
        """
        try:
            with open("categories.json", "r") as file:
                return json.load(file)
        except FileNotFoundError:
            return DEFAULT_CATEGORIES.copy()
    
    @staticmethod
    def save_categories(categories):
        """Save categories to the categories.json file.
        
        Args:
            categories: The list of categories to save.
        """
        with open("categories.json", "w") as file:
            json.dump(categories, file)