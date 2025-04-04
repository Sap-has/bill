from functools import partial
import json
from datetime import datetime
import sys
import os

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QGridLayout, QWidget, QPushButton, QTableWidgetItem, 
    QCalendarWidget, QLineEdit, QLabel, QMessageBox, QComboBox, QHBoxLayout, QTabWidget, QFileDialog,
    QDialog, QProgressBar, QCheckBox, QMenu
)

from PyQt5.QtPrintSupport import QPrinter, QPrintDialog, QPrintPreviewDialog, QPageSetupDialog
from PyQt5.QtGui import QPixmap

from PyQt5.QtCore import Qt, QTimer
import sqlite3

from database.databaseManager import DatabaseManager
from mindeeApi.mindeeAPIConfigDialog import MindeeAPIConfigDialog
from mindeeApi.mindeeHelper import MindeeHelper
from mindeeApi.mindeeWorker import MindeeWorker
from mindeeApi.ocrResultsDialog import OCRResultsDialog
from util.dateHelper import DateHelper
from util.trie import Trie
from util.uiHelper import SettingsManager, UIHelper
from util.style import Style


# Define constants
DATE_FORMAT = "%m/%d/%Y"
DATE_FORMATS = ["%m/%d/%y", "%m/%d/%Y"]

# Main Application Class
class BillTracker(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(UIHelper.translate('Bill Tracker'))
        self.setGeometry(100, 100, 1000, 800)
        
        # Initialize managers
        self.db_manager = DatabaseManager()
        
        # Set up OCR functionality
        self.setup_ocr()
        
        # Create top toolbar for language selection
        self.toolbar = self.addToolBar(UIHelper.translate("Settings"))
        self.init_toolbar()

        # Set up tab widget
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        self.predefined_order = self.load_categories()
        self.selected_categories = []
        self.selected_image_path = None
        
        # Initialize pages
        self.init_dashboard_page()  # New dashboard page
        self.init_bill_page()
        self.init_manage_bills_page()  # Combined print and delete functionality
        self.init_photos_page()  # Initialize photos page
        self.init_data_page()
        self.init_settings_page()

        # Add pages to tab widget with new structure
        self.tab_widget.addTab(self.dashboard_page, UIHelper.translate("Dashboard"))
        self.tab_widget.addTab(self.bill_page, UIHelper.translate("Bill Entry"))
        self.tab_widget.addTab(self.manage_bills_page, UIHelper.translate("Manage Bills"))
        self.tab_widget.addTab(self.photos_page, UIHelper.translate("Photos"))  # Add photos tab
        self.tab_widget.addTab(self.data_page, UIHelper.translate("Reports"))
        self.tab_widget.addTab(self.settings_page, UIHelper.translate("Settings"))
        
        # Load existing databases and bills
        self.load_existing_databases()
        self.load_bills()
        self.load_present_bills()

        # Apply stylesheet
        self.setStyleSheet(Style.get_stylesheet())

        self.update_settings_page()

        # Initialize the trie for name suggestions
        self.trie = Trie()
        self.load_names_into_trie()
        
        # Show notifications area
        self.init_notification_system()
    
    def setup_ocr(self):
        """Set up OCR functionality by loading Mindee API key."""
        # Try to load the API key
        MindeeHelper.load_api_key()
        
        # Make sure usage data is loaded even if API key isn't set
        MindeeHelper.load_usage_data()
    
    def init_toolbar(self):
        """Initialize the toolbar with language options."""
        # Language selector
        language_label = QLabel(UIHelper.translate("Language") + ": ")
        self.toolbar.addWidget(language_label)
        
        self.language_selector = QComboBox()
        self.language_selector.addItem("English")
        self.language_selector.addItem("Español")
        self.language_selector.currentIndexChanged.connect(self.change_language)
        self.toolbar.addWidget(self.language_selector)
    
    def change_language(self, index):
        """Change the application language.
        
        Args:
            index: Index of the selected language in the dropdown
        """
        language_code = "en" if index == 0 else "es"
        UIHelper.translator.set_language(language_code)
        self.update_ui_translations()
    
    def update_ui_translations(self):
        """Update all UI element translations when language changes."""
        # Update window title
        self.setWindowTitle(UIHelper.translate('Bill Tracker'))
        
        # Update tab names
        self.tab_widget.setTabText(0, UIHelper.translate("Dashboard"))
        self.tab_widget.setTabText(1, UIHelper.translate("Bill Entry"))
        self.tab_widget.setTabText(2, UIHelper.translate("Manage Bills"))
        self.tab_widget.setTabText(3, UIHelper.translate("Photos"))
        self.tab_widget.setTabText(4, UIHelper.translate("Reports"))
        self.tab_widget.setTabText(5, UIHelper.translate("Settings"))
        
        # Update all widgets with stored original text
        self.update_widget_translations(self)
        
        # Update OCR button tooltip if OCR is not available
        if hasattr(self, 'scan_button') and not MindeeHelper.is_available():
            self.scan_button.setToolTip(UIHelper.translate(
                "OCR functionality requires Mindee API. Please configure your API key to use receipt scanning."
            ))
        
        # Refresh tables with translated headers
        if hasattr(self, 'bill_table') and hasattr(self.bill_table, 'property') and self.bill_table.property("original_headers"):
            headers = self.bill_table.property("original_headers")
            translated_headers = [UIHelper.translate(header) for header in headers]
            self.bill_table.setHorizontalHeaderLabels(translated_headers)
            
        if hasattr(self, 'present_bill_table') and hasattr(self.present_bill_table, 'property') and self.present_bill_table.property("original_headers"):
            headers = self.present_bill_table.property("original_headers")
            translated_headers = [UIHelper.translate(header) for header in headers]
            self.present_bill_table.setHorizontalHeaderLabels(translated_headers)
            
        if hasattr(self, 'delete_table') and hasattr(self.delete_table, 'property') and self.delete_table.property("original_headers"):
            headers = self.delete_table.property("original_headers")
            translated_headers = [UIHelper.translate(header) for header in headers]
            self.delete_table.setHorizontalHeaderLabels(translated_headers)
            
        if hasattr(self, 'data_table') and hasattr(self.data_table, 'property') and self.data_table.property("original_headers"):
            headers = self.data_table.property("original_headers")
            translated_headers = [UIHelper.translate(header) for header in headers]
            self.data_table.setHorizontalHeaderLabels(translated_headers)
            

    def update_scan_button_state(self):
        """Update the scan button state based on OCR availability."""
        is_ocr_available = MindeeHelper.is_available()
        has_pages_available = MindeeHelper.has_available_pages()
        
        # Button is enabled only if OCR is available AND we have pages left
        self.scan_button.setEnabled(is_ocr_available and has_pages_available)
        
        if not is_ocr_available:
            # OCR libraries installed but API key not set
            self.scan_button.setToolTip(UIHelper.translate(
                "Mindee API key not set. Right-click to configure API key."
            ))
        elif not has_pages_available:
            # No pages left this month
            self.scan_button.setToolTip(UIHelper.translate(
                "You have reached the monthly limit of 250 pages for the Mindee API."
            ))
        else:
            # Show remaining page count
            remaining = MindeeHelper.get_remaining_pages()
            self.scan_button.setToolTip(UIHelper.translate(
                f"Scan a receipt using OCR. {remaining} pages remaining this month."
            ))
    
    def show_scan_context_menu(self, position):
        """Show a context menu for the scan button with OCR configuration options."""
        menu = QMenu(self)
        
        # Add an action to configure API key
        configure_action = menu.addAction(UIHelper.translate("Configure Mindee API Key"))
        configure_action.triggered.connect(lambda: self.scan_receipt())

        
        # Add an action to just scan without OCR processing
        scan_only_action = menu.addAction(UIHelper.translate("Just Scan (No OCR)"))
        scan_only_action.triggered.connect(lambda: self.scan_receipt(ocr_enabled=False))
        
        # Show the menu at the requested position
        menu.exec_(self.scan_button.mapToGlobal(position))
    
    def show_mindee_config_dialog(self):
        """Show the dialog for configuring Mindee API key."""
        dialog = MindeeAPIConfigDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            # Update the scan button state
            self.update_scan_button_state()
    
    def scan_receipt(self, ocr_enabled=True):
        """Scan a receipt using OCR to extract bill information or just save the image.
        
        Args:
            ocr_enabled: If True, use OCR to extract data. If False, just save the image.
        """
        # If OCR is enabled, check if API key is set
        if ocr_enabled and not MindeeHelper.is_available():
            result = QMessageBox.question(
                self, 
                UIHelper.translate("API Key Not Set"), 
                UIHelper.translate("Mindee API key is not set. Would you like to configure it now?"),
                QMessageBox.Yes | QMessageBox.No
            )
                
            if result == QMessageBox.Yes:
                self.show_mindee_config_dialog()
            return
        
        # If OCR is enabled, check if we've reached the monthly limit
        if ocr_enabled and not MindeeHelper.has_available_pages():
            result = QMessageBox.question(
                self,
                UIHelper.translate("API Limit Reached"),
                UIHelper.translate("You have reached the monthly limit of 250 pages for the Mindee API. "
                                  "Would you like to scan the image without OCR processing?"),
                QMessageBox.Yes | QMessageBox.No
            )
            
            if result == QMessageBox.Yes:
                # Continue without OCR
                ocr_enabled = False
            else:
                return
        
        # Select an image first
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Select Receipt Image", 
            "", 
            "Images (*.png *.jpg *.jpeg *.bmp);;All Files (*)", 
            options=options
        )
        
        if not file_path:
            return  # User canceled
        
        # Show image preview
        self.selected_image_path = file_path
        self.image_preview.setPixmap(QPixmap(file_path))
        
        # If OCR is disabled, just save the image and return
        if not ocr_enabled:
            self.show_notification(UIHelper.translate("Image scanned and saved (no OCR processing)."), "info")
            return
        
        # Create and show progress dialog
        progress_dialog = QDialog(self)
        progress_dialog.setWindowTitle(UIHelper.translate("Processing Receipt"))
        progress_dialog.setFixedSize(300, 100)
        
        # Set up dialog layout
        layout = QVBoxLayout()
        progress_dialog.setLayout(layout)
        
        # Add progress bar and label
        progress_label = QLabel(UIHelper.translate("Extracting information from receipt..."))
        layout.addWidget(progress_label)
        
        progress_bar = QProgressBar()
        progress_bar.setRange(0, 100)
        layout.addWidget(progress_bar)
        
        # Create worker thread for OCR processing
        self.ocr_worker = MindeeWorker(file_path)
        self.ocr_worker.progress.connect(progress_bar.setValue)
        self.ocr_worker.finished.connect(lambda results: self.handle_ocr_results(results, progress_dialog))
        
        # Show dialog and start worker
        progress_dialog.show()
        
        try:
            self.ocr_worker.start()
        except Exception as e:
            # Close the progress dialog
            progress_dialog.accept()
            
            error_msg = str(e)
            if "API key is not set" in error_msg:
                # API key not set, prompt user to configure it
                result = QMessageBox.question(
                    self, 
                    UIHelper.translate("API Key Not Set"), 
                    UIHelper.translate("Mindee API key is not set. Would you like to configure it now?"),
                    QMessageBox.Yes | QMessageBox.No
                )
                
                if result == QMessageBox.Yes:
                    self.show_mindee_config_dialog()
            else:
                # Other error
                QMessageBox.critical(
                    self, 
                    UIHelper.translate("OCR Error"), 
                    f"{UIHelper.translate('An error occurred during OCR processing:')} {str(e)}"
                )
    
    def select_photo(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Bill Image", "", "Images (*.png *.jpg *.jpeg *.bmp);;All Files (*)", options=options)
        
        if file_path:
            self.selected_image_path = file_path
            self.image_preview.setPixmap(QPixmap(file_path))  # Show image preview
    
    def handle_ocr_results(self, ocr_results, progress_dialog):
        """Handle the results from the OCR worker."""
        # Close the progress dialog
        progress_dialog.accept()
        
        # Check if there was an error
        if 'error' in ocr_results:
            error_message = ocr_results['error']
            if "API limit" in error_message or "monthly limit" in error_message:
                # API limit reached - inform user but still save the image
                self.show_notification(UIHelper.translate(
                    "Mindee API limit reached. The image was saved but no data was extracted."), 
                    "warning"
                )
            else:
                # Other error
                QMessageBox.warning(
                    self, 
                    UIHelper.translate("OCR Processing Error"), 
                    UIHelper.translate("Failed to extract information from receipt. The image was saved.")
                )
        
        # Show OCR results dialog if we have data to show
        has_data = any(ocr_results.get(key, "") for key in ["vendor", "date", "amount"])
        if has_data:
            dialog = OCRResultsDialog(self, ocr_results)
            if dialog.exec_() == QDialog.Accepted:
                # Apply the OCR results to the form if user accepted them
                results = dialog.get_result()
                self.name_input.setText(results["vendor"])
                self.date_input.setText(results["date"])
                self.price_input.setText(results["amount"])
            
        # Update scan button state (API usage may have changed)
        self.update_scan_button_state()
    
    def show_autocomplete_suggestions(self):
        query = self.name_input.text()
        suggestions = self.trie.get_suggestions(query)
        self.suggestions_list.clear()
        self.suggestions_list.addItems(suggestions)

    def select_suggestion(self, item):
        self.name_input.setText(item.text())
        self.suggestions_list.clear()
    
    def load_present_bills(self):
        self.present_bill_table.setRowCount(0)  # Clear the table
        
        bills = self.db_manager.get_bills()
        
        for bill in bills:
            row_count = self.present_bill_table.rowCount()
            self.present_bill_table.insertRow(row_count)
            self.present_bill_table.setItem(row_count, 0, QTableWidgetItem(bill[0]))
            self.present_bill_table.setItem(row_count, 1, QTableWidgetItem(bill[1]))
            self.present_bill_table.setItem(row_count, 2, QTableWidgetItem(bill[2]))
    
    def filter_photos_by_date(self):
        """Filter photos by date range."""
        start_date, end_date = DateHelper.parse_date_range(
            self.photo_start_date_input.text(),
            self.photo_end_date_input.text()
        )
        
        if not start_date or not end_date:
            # If invalid date range, show all photos
            self.load_all_photos()
            return
            
        self.clear_layout(self.scroll_layout)  # Clear existing images
        
        selected_year = self.photos_year_selector.currentText() if hasattr(self, 'photos_year_selector') else None
        
        # Get filtered bill images
        bill_images = self.db_manager.get_bill_images(selected_year, start_date, end_date)
        
        # Add images to the photos page
        for date, image_filename in bill_images:
            if image_filename:
                image_path = os.path.join("bill_images", image_filename)
                if os.path.exists(image_path):
                    self.add_image_to_photos_page(date, image_path)
    
    def load_existing_databases(self):
        """Load existing year-specific databases into the selectors."""
        years = self.db_manager.get_existing_databases()
        
        # Update all year selectors that exist in the application
        for year in years:
            # Update the Print Page year selector (main bills page)
            if hasattr(self, 'year_selector'):
                if year not in [self.year_selector.itemText(i) for i in range(self.year_selector.count())]:
                    self.year_selector.addItem(year)
            
            # Update the Data Page year selector
            if hasattr(self, 'data_year_selector'):
                if year not in [self.data_year_selector.itemText(i) for i in range(self.data_year_selector.count())]:
                    self.data_year_selector.addItem(year)
            
            # Update the Delete Page year selector
            if hasattr(self, 'delete_year_selector'):
                if year not in [self.delete_year_selector.itemText(i) for i in range(self.delete_year_selector.count())]:
                    self.delete_year_selector.addItem(year)
                    
            # Update the Manage Page year selector
            if hasattr(self, 'manage_year_selector'):
                if year not in [self.manage_year_selector.itemText(i) for i in range(self.manage_year_selector.count())]:
                    self.manage_year_selector.addItem(year)
                    
            # Update the Photos Page year selector
            if hasattr(self, 'photos_year_selector'):
                if year not in [self.photos_year_selector.itemText(i) for i in range(self.photos_year_selector.count())]:
                    self.photos_year_selector.addItem(year)
    
    def load_bills(self):
        """Load bills into the bill table based on the selected year."""
        if not hasattr(self, 'bill_table'):
            return  # Exit early if bill_table doesn't exist yet
            
        self.bill_table.setRowCount(0)  # Clear the table
        
        if not hasattr(self, 'year_selector'):
            return  # Exit early if year_selector doesn't exist yet
            
        selected_year = self.year_selector.currentText()
        
        bills = self.db_manager.get_bills(selected_year)
        
        for bill in bills:
            row_count = self.bill_table.rowCount()
            self.bill_table.insertRow(row_count)
            self.bill_table.setItem(row_count, 0, QTableWidgetItem(bill[0]))
            self.bill_table.setItem(row_count, 1, QTableWidgetItem(bill[1]))
            self.bill_table.setItem(row_count, 2, QTableWidgetItem(bill[2]))
    
    def save_bill(self):
        """Save a bill to the database."""
        # Get date from input or calendar
        date_text = self.date_input.text().strip()
        if not date_text:
            self.show_notification(UIHelper.translate("Please enter a date."), "warning")
            self.date_input.setFocus()
            return
            
        # Validate date format
        date = None
        for date_format in DATE_FORMATS:
            try:
                date = datetime.strptime(date_text, date_format).strftime(DATE_FORMAT)
                break
            except ValueError:
                continue
                
        if not date:
            self.show_notification(
                UIHelper.translate("Invalid date format. Please use MM/dd/yyyy."), 
                "warning"
            )
            self.date_input.setFocus()
            return
        
        # Get and validate name
        name = self.name_input.text().strip()
        if not name:
            self.show_notification(UIHelper.translate("Please enter a bill name."), "warning")
            self.name_input.setFocus()
            return
        
        # Get and validate price
        price_text = self.price_input.text().strip()
        if not price_text:
            self.show_notification(UIHelper.translate("Please enter an amount."), "warning")
            self.price_input.setFocus()
            return
            
        try:
            # Allow both "10.99" and "$10.99" formats
            price_text = price_text.replace('$', '').strip()
            price = float(price_text)
            if price <= 0:
                self.show_notification(UIHelper.translate("Amount must be greater than zero."), "warning")
                self.price_input.setFocus()
                return
        except ValueError:
            self.show_notification(UIHelper.translate("Invalid amount format. Please enter a number."), "warning")
            self.price_input.setFocus()
            return

        # Save the bill using the database manager
        success = self.db_manager.save_bill(date, name, str(price), self.selected_image_path)
        
        if success:
            # Refresh the bill tables
            self.load_bills()
            self.load_present_bills()
            
            # Update dashboard if it's available
            if hasattr(self, 'update_dashboard_stats'):
                self.update_dashboard_stats()
                self.update_recent_bills_table()
            
            # Update year selectors after saving
            self.load_existing_databases()
            
            # Clear selected categories and inputs
            self.selected_categories = []
            for category, button in self.category_buttons.items():
                button.setChecked(False)
                
            # Clear inputs after saving
            self.price_input.clear()
            self.name_input.clear()
            self.date_input.clear()
            
            # Clear selected image
            self.selected_image_path = None
            self.image_preview.clear()
            
            # Show success notification
            self.show_notification(UIHelper.translate("Bill saved successfully!"), "success")
            
        else:
            self.show_notification(
                UIHelper.translate("Failed to save bill. Please try again."), 
                "error"
            )
    
    def create_table_in_db(self, conn):
        query = """
        CREATE TABLE IF NOT EXISTS bills (
            id INTEGER PRIMARY KEY,
            date TEXT,
            name TEXT,
            price TEXT,
            image TEXT -- stores  the image filename
        )
        """
        conn.execute(query)
        conn.commit()
    
    def add_category(self, category):
        if category in self.selected_categories:
            self.selected_categories.remove(category)
        else:
            self.selected_categories.append(category)
        self.update_name_input()

    def update_name_input(self):
        current_text = self.name_input.text().split('(')[0].strip()
        # Sort selected categories based on predefined order
        sorted_categories = sorted(self.selected_categories, key=lambda x: self.predefined_order.index(x))
        categories_text = ' '.join(f'({cat})' for cat in sorted_categories)
        self.name_input.setText(f"{current_text} {categories_text}".strip())
    
    def add_new_category(self):
        new_category = self.new_category_input.text()
        if new_category and new_category not in self.categories:
            self.categories.append(new_category)
            
            # Create a button without translation marking
            button = QPushButton(new_category)
            button.setFixedHeight(40)
            button.clicked.connect(partial(self.add_category, new_category))
            
            # Calculate position based on updated categories list
            row = (len(self.categories) - 1) // 5
            col = (len(self.categories) - 1) % 5
            self.category_layout.addWidget(button, row, col)
            self.category_buttons[new_category] = button
            self.new_category_input.clear()
            self.save_categories()
            self.update_settings_page()  # No longer modifying category_order
    
    def delete_category(self, category):
        if category in self.categories:
            self.categories.remove(category)
            button = self.category_buttons.pop(category)
            self.category_layout.removeWidget(button)
            button.deleteLater()
            self.save_categories()
            self.update_settings_page()  # No longer modifying category_order
    
    def update_settings_page(self):
        """Update the settings page category list."""
        self.clear_layout(self.category_list_layout)

        for category in self.categories:
            category_layout = QHBoxLayout()
            
            # Category name label
            category_label = QLabel(category)
            category_label.setStyleSheet("font-size: 16px;")
            category_layout.addWidget(category_label)
            
            # Delete button
            delete_button = UIHelper.create_button("Delete", partial(self.delete_category, category))
            delete_button.setMaximumWidth(100)
            category_layout.addWidget(delete_button)
            
            self.category_list_layout.addLayout(category_layout)
    
    def clear_layout(self, layout):
        """Recursively clear a layout and its child widgets/layouts."""
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self.clear_layout(item.layout())

    def load_categories(self):
        """Load categories from the settings manager."""
        return SettingsManager.load_categories()
    
    def save_categories(self):
        """Save categories using the settings manager."""
        SettingsManager.save_categories(self.categories)
    
    def load_data(self):
        """Load monthly expenditure data based on the selected year."""
        self.data_table.setRowCount(0)  # Clear the table
        selected_year = self.data_year_selector.currentText()
        
        # Get monthly and yearly totals
        monthly_totals, yearly_totals = self.db_manager.get_monthly_totals(selected_year)
        
        # Populate the data table with monthly totals
        for month in range(1, 13):
            row_count = self.data_table.rowCount()
            self.data_table.insertRow(row_count)
            self.data_table.setItem(row_count, 0, QTableWidgetItem(datetime(1900, month, 1).strftime("%B")))  # Month name
            self.data_table.setItem(row_count, 1, QTableWidgetItem(f"${monthly_totals[month]['cash']:.2f}"))
            self.data_table.setItem(row_count, 2, QTableWidgetItem(f"${monthly_totals[month]['not_cash']:.2f}"))
            self.data_table.setItem(row_count, 3, QTableWidgetItem(f"${monthly_totals[month]['total']:.2f}"))
        
        # Add yearly totals as the last row
        row_count = self.data_table.rowCount()
        self.data_table.insertRow(row_count)
        self.data_table.setItem(row_count, 0, QTableWidgetItem("Year Total"))
        self.data_table.setItem(row_count, 1, QTableWidgetItem(f"${yearly_totals['cash']:.2f}"))
        self.data_table.setItem(row_count, 2, QTableWidgetItem(f"${yearly_totals['not_cash']:.2f}"))
        self.data_table.setItem(row_count, 3, QTableWidgetItem(f"${yearly_totals['total']:.2f}"))

    def print_bills(self):
        # Create a printer object
        printer = QPrinter(QPrinter.HighResolution)

        # Create a print preview dialog
        preview_dialog = QPrintPreviewDialog(printer)
        preview_dialog.setWindowTitle("Print Preview")
        preview_dialog.setWindowModality(Qt.ApplicationModal)

        # Connect the paint request signal to a custom method
        preview_dialog.paintRequested.connect(lambda p: self.render_filtered_table_to_printer(p))

        # Show the print preview dialog
        if preview_dialog.exec_() == QPrintPreviewDialog.Accepted:
            # Open the print dialog
            print_dialog = QPrintDialog(printer)
            if print_dialog.exec_() == QPrintDialog.Accepted:
                # Proceed with printing
                self.render_filtered_table_to_printer(printer)
    
    def render_filtered_table_to_printer(self, printer):
        from PyQt5.QtGui import QPainter, QFont
        
        if not hasattr(self, 'bill_table'):
            # Show an error message if the bill_table doesn't exist
            QMessageBox.critical(self, "Print Error", "The bill table is not available for printing.")
            return

        # Create a painter to handle rendering
        painter = QPainter(printer)

        # Set up page dimensions and margins
        margin = 85
        page_rect = printer.pageRect()
        x, y = margin, margin

        # Set up the font
        font = QFont() 
        font.setPointSize(10)  # Set the font size to 10 for the table
        painter.setFont(font)  # Apply the font to the painter

        # Render table content (filtered rows only)
        for row in range(self.bill_table.rowCount()):
            if y + 20 > page_rect.height() - margin:
                printer.newPage()
                y = margin  # Reset y for the new page

            date = self.bill_table.item(row, 0).text()
            name = self.bill_table.item(row, 1).text()
            price = self.bill_table.item(row, 2).text()

            painter.drawText(x, y, date)
            painter.drawText(x + 525, y, name)
            painter.drawText(x + 4250, y, price)
            y += 135
    
    def setup_page(self):
        printer = QPrinter()
        page_setup_dialog = QPageSetupDialog(printer, self)
        page_setup_dialog.exec_()
    
    def filter_by_date_range(self):
        """Filter the bill table by date range."""
        if not hasattr(self, 'bill_table'):
            return  # Exit early if bill_table doesn't exist yet
            
        if not hasattr(self, 'year_selector'):
            return  # Exit early if year_selector doesn't exist yet
            
        start_date, end_date = DateHelper.parse_date_range(
            self.start_date_input.text(), 
            self.end_date_input.text()
        )
        
        if not start_date or not end_date:
            # If invalid date range, show all bills
            self.load_bills()
            return
            
        # Load bills within the date range
        self.bill_table.setRowCount(0)  # Clear the table
        selected_year = self.year_selector.currentText()
        
        bills = self.db_manager.get_bills(
            selected_year, 
            start_date, 
            end_date
        )
        
        # Populate the table with the filtered bills
        for bill in bills:
            row_count = self.bill_table.rowCount()
            self.bill_table.insertRow(row_count)
            self.bill_table.setItem(row_count, 0, QTableWidgetItem(bill[0]))
            self.bill_table.setItem(row_count, 1, QTableWidgetItem(bill[1]))
            self.bill_table.setItem(row_count, 2, QTableWidgetItem(bill[2]))

    def init_delete_page(self):
        """Initialize the Delete Page tab for removing bills."""
        self.delete_page = QWidget()
        self.delete_layout = QVBoxLayout()
        self.delete_page.setLayout(self.delete_layout)

        # Section: Search Bills
        self.delete_layout.addWidget(UIHelper.create_section_label("Search Bills by Date"))
        
        # Search by date
        self.search_input = UIHelper.create_date_input()
        self.delete_layout.addWidget(self.search_input)

        self.search_button = UIHelper.create_button("Search", self.search_by_date)
        self.delete_layout.addWidget(self.search_button)
        
        UIHelper.add_section_spacing(self.delete_layout)
        
        # Section: Sort Options
        self.delete_layout.addWidget(UIHelper.create_section_label("Sort Options"))

        # Sorting buttons
        sort_buttons_layout = QHBoxLayout()

        self.sort_asc_button = UIHelper.create_button("Sort Ascending", lambda: self.sort_delete_table("asc"))
        sort_buttons_layout.addWidget(self.sort_asc_button)

        self.sort_desc_button = UIHelper.create_button("Sort Descending", lambda: self.sort_delete_table("desc"))
        sort_buttons_layout.addWidget(self.sort_desc_button)

        self.delete_layout.addLayout(sort_buttons_layout)
        
        UIHelper.add_section_spacing(self.delete_layout)
        
        # Section: Actions
        self.delete_layout.addWidget(UIHelper.create_section_label("Actions"))

        # Show All Bills and Delete buttons
        buttons_layout = QHBoxLayout()

        self.show_all_button = UIHelper.create_button("Show All Bills", self.load_delete_table)
        buttons_layout.addWidget(self.show_all_button)

        self.delete_button = UIHelper.create_button("Delete Selected", self.delete_selected_row)
        buttons_layout.addWidget(self.delete_button)

        self.delete_layout.addLayout(buttons_layout)
        
        UIHelper.add_section_spacing(self.delete_layout)
        
        # Section: Database Selection
        self.delete_layout.addWidget(UIHelper.create_section_label("Select Year"))

        # Database selection dropdown
        self.delete_year_selector = QComboBox()
        for i in range(self.year_selector.count()):
            year = self.year_selector.itemText(i)
            if year != "Present Database":
                self.delete_year_selector.addItem(year)
        self.delete_year_selector.currentIndexChanged.connect(self.load_delete_table)
        self.delete_layout.addWidget(self.delete_year_selector)
        
        UIHelper.add_section_spacing(self.delete_layout)
        
        # Section: Bills Table
        self.delete_layout.addWidget(UIHelper.create_section_label("Bills"))

        # Table to display bills
        self.delete_table = UIHelper.create_table(3, ["Date", "Name", "Price"])
        self.delete_layout.addWidget(self.delete_table)

    def load_delete_table(self):
        self.delete_table.setRowCount(0)
        selected_year = self.delete_year_selector.currentText()
        conn = sqlite3.connect(f"bills_{selected_year}.db")
        cursor = conn.execute("SELECT date, name, price FROM bills")
        for row in cursor:
            row_count = self.delete_table.rowCount()
            self.delete_table.insertRow(row_count)
            self.delete_table.setItem(row_count, 0, QTableWidgetItem(row[0]))
            self.delete_table.setItem(row_count, 1, QTableWidgetItem(row[1]))
            self.delete_table.setItem(row_count, 2, QTableWidgetItem(row[2]))
        conn.close()

    def search_by_date(self):
        try:
            date_formats = ["%m/%d/%y", "%m/%d/%Y"]
            
            def parse_date(date_text):
                for date_format in date_formats:
                    try:
                        return datetime.strptime(date_text, date_format).strftime("%m/%d/%Y")
                    except ValueError:
                        continue
                raise ValueError("Invalid date format")
            
            date_text = parse_date(self.search_input.text())

            # Convert the text inputs to datetime objects
            date = datetime.strptime(date_text, "%m/%d/%Y")
        except ValueError as e:
            # If invalid date or conversion error occurs, show all entries in the database        
            # Load all bills (no filtering)
            QMessageBox.warning(self, "Input Error", "Invalid date format. Please use MM/dd/yyyy.")
            return

        self.delete_table.setRowCount(0)
        selected_year = self.delete_year_selector.currentText()
        conn = sqlite3.connect(f"bills_{selected_year}.db")
        cursor = conn.execute("SELECT date, name, price FROM bills WHERE date = ?", (date.strftime("%m/%d/%Y"),))
        for row in cursor:
            row_count = self.delete_table.rowCount()
            self.delete_table.insertRow(row_count)
            self.delete_table.setItem(row_count, 0, QTableWidgetItem(row[0]))
            self.delete_table.setItem(row_count, 1, QTableWidgetItem(row[1]))
            self.delete_table.setItem(row_count, 2, QTableWidgetItem(row[2]))
        conn.close()

    def delete_selected_row(self):
        """Delete the selected row from the database."""
        selected_row = self.delete_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, UIHelper.translate("Selection Error"), 
                               UIHelper.translate("No row selected."))
            return
            
        date = self.delete_table.item(selected_row, 0).text()
        name = self.delete_table.item(selected_row, 1).text()
        price = self.delete_table.item(selected_row, 2).text()
        
        selected_year = self.delete_year_selector.currentText()
        
        # Delete the bill using the database manager
        success = self.db_manager.delete_bill(selected_year, date, name, price)
        
        if success:
            self.delete_table.removeRow(selected_row)
        else:
            QMessageBox.critical(self, UIHelper.translate("Error"), 
                                UIHelper.translate("Failed to delete bill. Please try again."))

    def sort_delete_table(self, order):
        rows = []
        for row in range(self.delete_table.rowCount()):
            date_item = self.delete_table.item(row, 0)
            name_item = self.delete_table.item(row, 1)
            price_item = self.delete_table.item(row, 2)

            if date_item and name_item and price_item:
                date = datetime.strptime(date_item.text(), "%m/%d/%Y")
                price = float(price_item.text().replace("$", ""))
                name = name_item.text()
                rows.append((date, price, name, row))

        rows.sort(key=lambda x: (x[0], -x[1], x[2]), reverse=order == "desc")

        self.delete_table.setRowCount(0)
        for date, price, name, _ in rows:
            row_count = self.delete_table.rowCount()
            self.delete_table.insertRow(row_count)
            self.delete_table.setItem(row_count, 0, QTableWidgetItem(date.strftime("%m/%d/%Y")))
            self.delete_table.setItem(row_count, 1, QTableWidgetItem(name))
            self.delete_table.setItem(row_count, 2, QTableWidgetItem(f"${price:.2f}"))

    def update_widget_translations(self, parent_widget):
        """Recursively update translations of all child widgets.
        
        Args:
            parent_widget: The parent widget to update
        """
        for child in parent_widget.findChildren(QWidget):
            # Update QPushButton text
            if isinstance(child, QPushButton) and child.property("original_text"):
                child.setText(UIHelper.translate(child.property("original_text")))
                
            # Update QLabel text
            elif isinstance(child, QLabel) and child.property("original_text"):
                child.setText(UIHelper.translate(child.property("original_text")))
                
            # Update QLineEdit placeholder
            elif isinstance(child, QLineEdit) and child.property("original_placeholder"):
                child.setPlaceholderText(UIHelper.translate(child.property("original_placeholder")))
                
            # Recursively update child widgets
            if child.children():
                self.update_widget_translations(child)

    def load_names_into_trie(self):
        # Load names from unique_names.json and insert them into the trie
        try:
            with open('unique_names.json', 'r') as file:
                names = json.load(file)
            for name in names:
                self.trie.insert(name)
        except FileNotFoundError:
            # Create the file if it doesn't exist
            with open('unique_names.json', 'w') as file:
                json.dump([], file)

    def init_print_page(self):
        """Initialize the Print Page tab with filter and display options."""
        self.print_page = QWidget()
        self.print_layout = QVBoxLayout()
        self.print_page.setLayout(self.print_layout)

        # Section: Date range filter
        self.print_layout.addWidget(UIHelper.create_section_label("Filter Bills by Date Range"))
        
        # Date Range Inputs
        date_range_layout = QHBoxLayout()
        
        self.start_date_input = UIHelper.create_date_input()
        date_range_layout.addWidget(self.start_date_input)
        
        self.end_date_input = UIHelper.create_date_input()
        date_range_layout.addWidget(self.end_date_input)
        
        self.print_layout.addLayout(date_range_layout)
        
        # Filter button
        self.filter_button = UIHelper.create_button("Filter by Date Range", self.filter_by_date_range)
        self.print_layout.addWidget(self.filter_button)
        
        UIHelper.add_section_spacing(self.print_layout)
        
        # Section: Sort options
        self.print_layout.addWidget(UIHelper.create_section_label("Sort Options"))
        
        # Sort buttons
        sort_buttons_layout = QHBoxLayout()
        
        self.sort_asc_button = UIHelper.create_button("Sort by Date (Ascending)", lambda: self.sort_table("asc"))
        sort_buttons_layout.addWidget(self.sort_asc_button)
        
        self.sort_desc_button = UIHelper.create_button("Sort by Date (Descending)", lambda: self.sort_table("desc"))
        sort_buttons_layout.addWidget(self.sort_desc_button)
        
        self.print_layout.addLayout(sort_buttons_layout)
        
        UIHelper.add_section_spacing(self.print_layout)
        
        # Section: Actions
        self.print_layout.addWidget(UIHelper.create_section_label("Actions"))
        
        # Print and Show All Bills buttons
        buttons_layout = QHBoxLayout()
        
        self.print_button = UIHelper.create_button("Print Bills", self.print_bills)
        buttons_layout.addWidget(self.print_button)
        
        self.show_all_button = UIHelper.create_button("Show All Bills", self.load_bills)
        buttons_layout.addWidget(self.show_all_button)
        
        self.print_layout.addLayout(buttons_layout)
        
        UIHelper.add_section_spacing(self.print_layout)
        
        # Section: Database Selection
        self.print_layout.addWidget(UIHelper.create_section_label("Select Year"))
        
        # Database selection dropdown
        self.year_selector = QComboBox()
        self.year_selector.addItem("Present Database")
        self.year_selector.currentIndexChanged.connect(self.load_bills)
        self.print_layout.addWidget(self.year_selector)
        
        UIHelper.add_section_spacing(self.print_layout)
        
        # Section: Bills Table
        self.print_layout.addWidget(UIHelper.create_section_label("Bills"))
        
        # Table to display bills
        self.bill_table = UIHelper.create_table(3, ["Date", "Name", "Price"])
        self.print_layout.addWidget(self.bill_table)
    
    def show_autocomplete_suggestions(self):
        """Show autocomplete suggestions for bill names."""
        query = self.name_input.text()
        
        if len(query) < 2:
            self.suggestions_list.clear()
            self.suggestions_list.setFixedHeight(0)  # Hide when not needed
            return
            
        suggestions = self.trie.get_suggestions(query)
        
        if suggestions:
            self.suggestions_list.clear()
            self.suggestions_list.addItems(suggestions)
            # Adjust height based on number of suggestions (up to 5 visible)
            item_height = 25
            suggestion_count = min(5, len(suggestions))
            self.suggestions_list.setFixedHeight(suggestion_count * item_height)
        else:
            self.suggestions_list.clear()
            self.suggestions_list.setFixedHeight(0)  # Hide when no suggestions
    
    def select_suggestion(self, item):
        """Select a suggestion from the autocomplete list."""
        self.name_input.setText(item.text())
        self.suggestions_list.clear()
        self.suggestions_list.setFixedHeight(0)  # Hide after selection
    
    def toggle_category(self, category, checked):
        """Toggle a category on or off."""
        if checked and category not in self.selected_categories:
            self.selected_categories.append(category)
        elif not checked and category in self.selected_categories:
            self.selected_categories.remove(category)
            
        self.update_name_input()
    
    def show_calendar_dialog(self):
        """Show a dialog with calendar widget for date selection."""
        dialog = QDialog(self)
        dialog.setWindowTitle(UIHelper.translate("Select Date"))
        dialog.setFixedSize(300, 300)
        
        layout = QVBoxLayout()
        dialog.setLayout(layout)
        
        calendar = QCalendarWidget()
        calendar.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        layout.addWidget(calendar)
        
        # Button to accept selection
        select_btn = QPushButton(UIHelper.translate("Select"))
        select_btn.clicked.connect(lambda: (self.date_input.setText(calendar.selectedDate().toString("MM/dd/yyyy")), dialog.accept()))
        layout.addWidget(select_btn)
        
        dialog.exec_()
    
    def clear_photo(self):
        """Clear the selected photo."""
        self.selected_image_path = None
        self.image_preview.clear()
        self.show_notification(UIHelper.translate("Photo cleared"), "info")
    
    def perform_global_search(self):
        """Perform a global search across all bills."""
        search_text = self.global_search.text().lower()
        if not search_text:
            return
            
        # If on dashboard, update the recent bills table with search results
        if self.tab_widget.currentIndex() == 0:
            self.recent_bills_table.setRowCount(0)
            
            # Search in all years
            all_bills = []
            years = self.db_manager.get_existing_databases()
            
            # Add bills from present database
            present_bills = self.db_manager.get_bills()
            all_bills.extend(present_bills)
            
            # Add bills from year-specific databases
            for year in years:
                year_bills = self.db_manager.get_bills(year)
                all_bills.extend(year_bills)
            
            # Filter bills by search text
            filtered_bills = [bill for bill in all_bills if 
                             search_text in bill[0].lower() or  # Date
                             search_text in bill[1].lower() or  # Name
                             search_text in bill[2].lower()]    # Price
            
            # Add filtered bills to table (limit to 10)
            max_bills = min(10, len(filtered_bills))
            for i in range(max_bills):
                bill = filtered_bills[i]
                row_count = self.recent_bills_table.rowCount()
                self.recent_bills_table.insertRow(row_count)
                self.recent_bills_table.setItem(row_count, 0, QTableWidgetItem(bill[0]))
                self.recent_bills_table.setItem(row_count, 1, QTableWidgetItem(bill[1]))
                self.recent_bills_table.setItem(row_count, 2, QTableWidgetItem(bill[2]))

    def init_notification_system(self):
        """Initialize the notification system for user feedback."""
        self.notification_area = QLabel("")
        self.notification_area.setObjectName("notification-area")
        self.notification_area.setAlignment(Qt.AlignCenter)
        self.notification_area.setFixedHeight(0)  # Hidden by default
        self.notification_timer = QTimer(self)
        self.notification_timer.timeout.connect(self.hide_notification)
        
        # Add to the main window
        layout = QVBoxLayout()
        layout.addWidget(self.notification_area)
        layout.addWidget(self.tab_widget)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create a central widget to hold the layout
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        
    def show_notification(self, message, type="info", duration=3000):
        """Show a notification to the user.
        
        Args:
            message: The notification message to display
            type: The type of notification (info, success, warning, error)
            duration: How long to show the notification (in milliseconds)
        """
        # Set notification style based on type
        if type == "success":
            self.notification_area.setStyleSheet("background-color: #d4edda; color: #155724; border-bottom: 1px solid #c3e6cb;")
        elif type == "warning":
            self.notification_area.setStyleSheet("background-color: #fff3cd; color: #856404; border-bottom: 1px solid #ffeeba;")
        elif type == "error":
            self.notification_area.setStyleSheet("background-color: #f8d7da; color: #721c24; border-bottom: 1px solid #f5c6cb;")
        else:  # info
            self.notification_area.setStyleSheet("background-color: #d1ecf1; color: #0c5460; border-bottom: 1px solid #bee5eb;")
        
        # Set message and show
        self.notification_area.setText(message)
        self.notification_area.setFixedHeight(40)
        
        # Start timer to hide notification
        self.notification_timer.start(duration)
    
    def hide_notification(self):
        """Hide the notification area."""
        self.notification_area.setFixedHeight(0)
        self.notification_timer.stop()
    
    def on_manage_tab_changed(self, index):
        """Handle changing between Bills and Photos tabs."""
        if index == 0:  # Bills tab
            self.load_manage_bills()
        else:  # Photos tab
            self.load_manage_photos()
    
    def load_manage_bills(self):
        """Load bills into the manage bills table."""
        self.manage_bills_table.setRowCount(0)
        selected_year = self.manage_year_selector.currentText()
        
        bills = self.db_manager.get_bills(selected_year)
        
        for bill in bills:
            row_count = self.manage_bills_table.rowCount()
            self.manage_bills_table.insertRow(row_count)
            self.manage_bills_table.setItem(row_count, 0, QTableWidgetItem(bill[0]))
            self.manage_bills_table.setItem(row_count, 1, QTableWidgetItem(bill[1]))
            self.manage_bills_table.setItem(row_count, 2, QTableWidgetItem(bill[2]))
            
            # Add checkbox for selection
            checkbox = QCheckBox()
            self.manage_bills_table.setCellWidget(row_count, 3, checkbox)
    
    def filter_manage_bills(self):
        """Filter bills in the manage view by date range and category."""
        start_date = self.manage_start_date.text()
        end_date = self.manage_end_date.text()
        selected_year = self.manage_year_selector.currentText()
        selected_category = self.category_filter.currentText()
        
        # Get date-filtered bills
        if start_date and end_date:
            start_date, end_date = DateHelper.parse_date_range(start_date, end_date)
            if start_date and end_date:
                bills = self.db_manager.get_bills(selected_year, start_date, end_date)
            else:
                # Invalid date format, show all bills
                bills = self.db_manager.get_bills(selected_year)
                self.show_notification(UIHelper.translate("Invalid date format. Showing all bills."), "warning")
        else:
            # No date range, show all bills
            bills = self.db_manager.get_bills(selected_year)
        
        # Filter by category
        if selected_category != UIHelper.translate("All Categories"):
            bills = [bill for bill in bills if f"({selected_category})" in bill[1]]
        
        # Update table
        self.manage_bills_table.setRowCount(0)
        for bill in bills:
            row_count = self.manage_bills_table.rowCount()
            self.manage_bills_table.insertRow(row_count)
            self.manage_bills_table.setItem(row_count, 0, QTableWidgetItem(bill[0]))
            self.manage_bills_table.setItem(row_count, 1, QTableWidgetItem(bill[1]))
            self.manage_bills_table.setItem(row_count, 2, QTableWidgetItem(bill[2]))
            
            # Add checkbox for selection
            checkbox = QCheckBox()
            self.manage_bills_table.setCellWidget(row_count, 3, checkbox)
    
    def delete_selected_bills(self):
        """Delete bills selected with checkboxes."""
        selected_rows = []
        
        # Get all selected rows
        for row in range(self.manage_bills_table.rowCount()):
            checkbox = self.manage_bills_table.cellWidget(row, 3)
            if checkbox and checkbox.isChecked():
                selected_rows.append(row)
        
        if not selected_rows:
            self.show_notification(UIHelper.translate("No bills selected."), "warning")
            return
        
        # Confirm deletion
        result = QMessageBox.question(
            self,
            UIHelper.translate("Confirm Deletion"),
            UIHelper.translate(f"Delete {len(selected_rows)} selected bills?"),
            QMessageBox.Yes | QMessageBox.No
        )
        
        if result != QMessageBox.Yes:
            return
        
        # Delete selected rows
        selected_year = self.manage_year_selector.currentText()
        deleted_count = 0
        
        # Delete in reverse order to avoid index shifting
        for row in sorted(selected_rows, reverse=True):
            date = self.manage_bills_table.item(row, 0).text()
            name = self.manage_bills_table.item(row, 1).text()
            price = self.manage_bills_table.item(row, 2).text()
            
            success = self.db_manager.delete_bill(selected_year, date, name, price)
            
            if success:
                deleted_count += 1
                self.manage_bills_table.removeRow(row)
            
        # Show success notification
        if deleted_count > 0:
            self.show_notification(
                UIHelper.translate(f"Successfully deleted {deleted_count} bills."),
                "success"
            )
        else:
            self.show_notification(
                UIHelper.translate("Failed to delete bills. Please try again."),
                "error"
            )
    
    def load_manage_photos(self):
        """Load photos into the manage photos view."""
        # Clear existing photos
        self.clear_layout(self.photos_scroll_layout)
        
        # Get selected year
        selected_year = None
        if hasattr(self, 'manage_year_selector') and self.manage_year_selector.count() > 0:
            selected_year = self.manage_year_selector.currentText()
        
        # Get all bill images
        bill_images = self.db_manager.get_bill_images(selected_year)
        
        # Create a grid layout for photos
        photo_grid = QGridLayout()
        self.photos_scroll_layout.addLayout(photo_grid)
        
        # Add images to the grid
        row, col = 0, 0
        max_cols = 3  # Show 3 photos per row
        
        for date, image_filename in bill_images:
            if image_filename:
                image_path = os.path.join("bill_images", image_filename)
                if os.path.exists(image_path):
                    # Create a card for each photo
                    photo_card = QWidget()
                    photo_card.setObjectName("photo-card")
                    card_layout = QVBoxLayout()
                    photo_card.setLayout(card_layout)
                    
                    # Add date label
                    date_label = QLabel(f"{UIHelper.translate('Date')}: {date}")
                    date_label.setAlignment(Qt.AlignCenter)
                    card_layout.addWidget(date_label)
                    
                    # Add image
                    image_label = QLabel()
                    pixmap = QPixmap(image_path)
                    image_label.setPixmap(pixmap.scaled(250, 250, Qt.KeepAspectRatio))
                    image_label.setAlignment(Qt.AlignCenter)
                    card_layout.addWidget(image_label)
                    
                    # Add to grid
                    photo_grid.addWidget(photo_card, row, col)
                    
                    # Move to next position
                    col += 1
                    if col >= max_cols:
                        col = 0
                        row += 1
    
    def filter_manage_photos(self):
        """Filter photos by date range."""
        start_date = self.photo_start_date.text()
        end_date = self.photo_end_date.text()
        
        if start_date and end_date:
            start_date, end_date = DateHelper.parse_date_range(start_date, end_date)
            if not start_date or not end_date:
                self.show_notification(UIHelper.translate("Invalid date format."), "warning")
                return
                
            # Clear existing photos
            self.clear_layout(self.photos_scroll_layout)
            
            # Get selected year
            selected_year = None
            if hasattr(self, 'manage_year_selector') and self.manage_year_selector.count() > 0:
                selected_year = self.manage_year_selector.currentText()
            
            # Get filtered bill images
            bill_images = self.db_manager.get_bill_images(selected_year, start_date, end_date)
            
            # Create a grid layout for photos
            photo_grid = QGridLayout()
            self.photos_scroll_layout.addLayout(photo_grid)
            
            # Add images to the grid
            row, col = 0, 0
            max_cols = 3
            
            for date, image_filename in bill_images:
                if image_filename:
                    image_path = os.path.join("bill_images", image_filename)
                    if os.path.exists(image_path):
                        # Create a card for each photo
                        photo_card = QWidget()
                        photo_card.setObjectName("photo-card")
                        card_layout = QVBoxLayout()
                        photo_card.setLayout(card_layout)
                        
                        # Add date label
                        date_label = QLabel(f"{UIHelper.translate('Date')}: {date}")
                        date_label.setAlignment(Qt.AlignCenter)
                        card_layout.addWidget(date_label)
                        
                        # Add image
                        image_label = QLabel()
                        pixmap = QPixmap(image_path)
                        image_label.setPixmap(pixmap.scaled(250, 250, Qt.KeepAspectRatio))
                        image_label.setAlignment(Qt.AlignCenter)
                        card_layout.addWidget(image_label)
                        
                        # Add to grid
                        photo_grid.addWidget(photo_card, row, col)
                        
                        # Move to next position
                        col += 1
                        if col >= max_cols:
                            col = 0
                            row += 1
        else:
            self.show_notification(UIHelper.translate("Please enter both start and end dates."), "warning")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BillTracker()
    window.show()
    sys.exit(app.exec_())