import json
from PyQt5.QtWidgets import (
    QMainWindow, QTabWidget
)

from trie import Trie;
import sqlite3

class BillTracker(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Bill Tracker')
        self.setGeometry(100, 100, 800, 800)

        # Set up tab widget
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        self.predefined_order = self.load_categories()  # Changed from category_order
        self.selected_categories = []
        
        # Initialize pages
        self.init_print_page()
        self.init_bill_page()
        self.init_settings_page()
        self.init_data_page()
        self.init_delete_page()
        

        # Add pages to tab widget
        self.tab_widget.addTab(self.bill_page, "Bill Entry")
        self.tab_widget.addTab(self.print_page, "Print Page")
        self.tab_widget.addTab(self.delete_page, "Delete Page")
        self.tab_widget.addTab(self.data_page, "Data")
        self.tab_widget.addTab(self.settings_page, "Settings")
        

        # SQLite connection
        self.conn = sqlite3.connect(':memory:') # use :memory: for in-memory database
        self.create_table()
        self.load_existing_databases()
        self.load_bills()
        self.load_present_bills()

        #apply stylesheet
        self.apply_styles()

        self.update_settings_page()

        # Initialize the trie for name suggestions
        self.trie = Trie()
        self.load_names_into_trie()

        self.init_photos_page()
        self.tab_widget.addTab(self.photos_page, "Photos")
    
    def load_names_into_trie(self):
        # Load names from unique_names.json and insert them into the trie
        with open('../unique_names.json', 'r') as file:
            names = json.load(file)
        for name in names:
            self.trie.insert(name)