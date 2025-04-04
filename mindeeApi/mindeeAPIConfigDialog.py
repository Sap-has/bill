from PyQt5.QtWidgets import (
    QVBoxLayout, QPushButton, QLineEdit, QLabel, QHBoxLayout, QDialog, QCheckBox
)

from mindeeApi.mindeeHelper import MindeeHelper
from util.uiHelper import UIHelper
from mindee import Client


class MindeeAPIConfigDialog(QDialog):
    """Dialog for configuring Mindee API key."""
    
    def __init__(self, parent=None):
        """Initialize the dialog for configuring Mindee API key."""
        super().__init__(parent)
        
        self.setWindowTitle(UIHelper.translate("Configure Mindee API"))
        self.setFixedWidth(500)
        
        # Create layout
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Add explanation
        info_label = QLabel(UIHelper.translate(
            "To use the Mindee Receipt OCR API, you need to enter your API key. "
            "You can get an API key by signing up at https://mindee.com."
        ))
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # API key input
        key_layout = QHBoxLayout()
        key_label = QLabel(UIHelper.translate("API Key:"))
        key_layout.addWidget(key_label)
        
        self.key_input = QLineEdit()
        if MindeeHelper.api_key:
            self.key_input.setText(MindeeHelper.api_key)
        self.key_input.setEchoMode(QLineEdit.Password)  # Hide the API key for security
        key_layout.addWidget(self.key_input)
        
        layout.addLayout(key_layout)
        
        # Show/hide API key checkbox
        self.show_key_checkbox = QCheckBox(UIHelper.translate("Show API Key"))
        self.show_key_checkbox.toggled.connect(self.toggle_key_visibility)
        layout.addWidget(self.show_key_checkbox)
        
        # Test button
        self.test_button = QPushButton(UIHelper.translate("Test API Key"))
        self.test_button.clicked.connect(self.test_api_key)
        layout.addWidget(self.test_button)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.status_label)
        
        # Add buttons
        buttons_layout = QHBoxLayout()
        
        self.save_button = QPushButton(UIHelper.translate("Save"))
        self.save_button.clicked.connect(self.save_api_key)
        buttons_layout.addWidget(self.save_button)
        
        self.cancel_button = QPushButton(UIHelper.translate("Cancel"))
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)
        
        layout.addLayout(buttons_layout)
    
    def toggle_key_visibility(self, checked):
        """Toggle the visibility of the API key input."""
        if checked:
            self.key_input.setEchoMode(QLineEdit.Normal)
        else:
            self.key_input.setEchoMode(QLineEdit.Password)
    
    def test_api_key(self):
        """Test if the specified API key works with Mindee."""
        api_key = self.key_input.text()
        
        if not api_key:
            self.status_label.setText(UIHelper.translate("Please enter an API key"))
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            return
        
        # Try to initialize the client with the API key
        try:
            # Set the API key temporarily
            client = Client(api_key=api_key)
            
            # Success
            self.status_label.setText(UIHelper.translate("API Key is valid"))
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            
        except Exception as e:
            # Failure
            self.status_label.setText(UIHelper.translate("API Key validation failed") + f": {str(e)}")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
    
    def save_api_key(self):
        """Save the Mindee API key if valid."""
        api_key = self.key_input.text()
        
        if not api_key:
            self.status_label.setText(UIHelper.translate("Please enter an API key"))
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            return
        
        # Set the API key
        if MindeeHelper.set_api_key(api_key):
            # Save the API key to a file
            try:
                with open('mindee_api_key.txt', 'w') as f:
                    f.write(api_key)
            except Exception as e:
                print(f"Error saving Mindee API key: {e}")
            
            # API key set successfully
            self.accept()
        else:
            self.status_label.setText(UIHelper.translate("Failed to set API key"))
            self.status_label.setStyleSheet("color: red; font-weight: bold;")