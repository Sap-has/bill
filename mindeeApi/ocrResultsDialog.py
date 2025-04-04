from PyQt5.QtWidgets import (
    QVBoxLayout, QPushButton, QLineEdit, QLabel, QHBoxLayout, QDialog
)

from util.uiHelper import UIHelper

class OCRResultsDialog(QDialog):
    """Dialog for confirming OCR results."""
    
    def __init__(self, parent=None, ocr_results=None):
        """Initialize the dialog with OCR results.
        
        Args:
            parent: Parent widget
            ocr_results: Dictionary of OCR results (vendor, date, amount)
        """
        super().__init__(parent)
        
        self.result = {
            "accepted": False,
            "vendor": ocr_results.get("vendor", ""),
            "date": ocr_results.get("date", ""),
            "amount": ocr_results.get("amount", "")
        }
        
        self.setWindowTitle(UIHelper.translate("OCR Results"))
        self.setFixedWidth(400)
        
        # Create layout
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Add fields for OCR results
        # Vendor/Name
        vendor_layout = QHBoxLayout()
        vendor_label = QLabel(UIHelper.translate("Vendor/Name:"))
        vendor_label.setMinimumWidth(100)
        vendor_layout.addWidget(vendor_label)
        
        self.vendor_input = QLineEdit()
        self.vendor_input.setText(self.result["vendor"] or "")
        vendor_layout.addWidget(self.vendor_input)
        layout.addLayout(vendor_layout)
        
        # Date
        date_layout = QHBoxLayout()
        date_label = QLabel(UIHelper.translate("Date:"))
        date_label.setMinimumWidth(100)
        date_layout.addWidget(date_label)
        
        self.date_input = QLineEdit()
        self.date_input.setText(self.result["date"] or "")
        date_layout.addWidget(self.date_input)
        layout.addLayout(date_layout)
        
        # Amount
        amount_layout = QHBoxLayout()
        amount_label = QLabel(UIHelper.translate("Amount:"))
        amount_label.setMinimumWidth(100)
        amount_layout.addWidget(amount_label)
        
        self.amount_input = QLineEdit()
        self.amount_input.setText(self.result["amount"] or "")
        amount_layout.addWidget(self.amount_input)
        layout.addLayout(amount_layout)
        
        # Add buttons
        buttons_layout = QHBoxLayout()
        
        self.apply_button = QPushButton(UIHelper.translate("Apply these values"))
        self.apply_button.clicked.connect(self.accept_values)
        buttons_layout.addWidget(self.apply_button)
        
        self.edit_button = QPushButton(UIHelper.translate("Edit before applying"))
        self.edit_button.clicked.connect(self.edit_values)
        buttons_layout.addWidget(self.edit_button)
        
        self.cancel_button = QPushButton(UIHelper.translate("Cancel"))
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)
        
        layout.addLayout(buttons_layout)
    
    def accept_values(self):
        """Accept the OCR values as is."""
        self.result["accepted"] = True
        self.result["vendor"] = self.vendor_input.text()
        self.result["date"] = self.date_input.text()
        self.result["amount"] = self.amount_input.text()
        self.accept()
    
    def edit_values(self):
        """Accept the OCR values but indicate they need editing."""
        self.result["accepted"] = True
        self.result["edit_needed"] = True
        self.result["vendor"] = self.vendor_input.text()
        self.result["date"] = self.date_input.text()
        self.result["amount"] = self.amount_input.text()
        self.accept()
        
    def get_result(self):
        """Get the result data."""
        return {
            "vendor": self.vendor_input.text(),
            "date": self.date_input.text(),
            "amount": self.amount_input.text()
        }