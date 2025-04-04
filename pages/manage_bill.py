from PyQt5.QtWidgets import (
    QVBoxLayout, QWidget, QPushButton, QHBoxLayout, QLabel, QComboBox, QTableWidget, QTabWidget
)

from PyQt5.QtGui import QIcon

from util.uiHelper import UIHelper

class manageBill:
    def init_manage_bills_page(self):
        """Initialize the Manage Bills page, combining print and delete functionality."""
        self.manage_bills_page = QWidget()
        main_layout = QVBoxLayout()
        self.manage_bills_page.setLayout(main_layout)
        
        # Create tabbed interface for different views
        view_tabs = QTabWidget()
        view_tabs.setDocumentMode(True)  # Make tabs look more modern
        
        # === Bills View ===
        bills_view = QWidget()
        bills_layout = QVBoxLayout()
        bills_view.setLayout(bills_layout)
        
        # Card for filtering
        filter_card = QWidget()
        filter_card.setObjectName("card")
        filter_layout = QVBoxLayout()
        filter_card.setLayout(filter_layout)
        
        filter_title = QLabel(UIHelper.translate("Filter Bills"))
        filter_title.setObjectName("card-title")
        filter_title.setProperty("original_text", "Filter Bills")
        filter_layout.addWidget(filter_title)
        
        # Date range with modern compact layout
        date_controls = QHBoxLayout()
        
        date_label = QLabel(UIHelper.translate("Date Range:"))
        date_label.setProperty("original_text", "Date Range:")
        date_controls.addWidget(date_label)
        
        self.manage_start_date = UIHelper.create_date_input()
        self.manage_start_date.setMaximumWidth(120)
        date_controls.addWidget(self.manage_start_date)
        
        date_to_label = QLabel(UIHelper.translate("to"))
        date_to_label.setProperty("original_text", "to")
        date_controls.addWidget(date_to_label)
        
        self.manage_end_date = UIHelper.create_date_input()
        self.manage_end_date.setMaximumWidth(120)
        date_controls.addWidget(self.manage_end_date)
        
        self.apply_filter_btn = QPushButton(UIHelper.translate("Apply"))
        self.apply_filter_btn.setProperty("original_text", "Apply")
        self.apply_filter_btn.setMaximumWidth(100)
        self.apply_filter_btn.clicked.connect(self.filter_manage_bills)
        date_controls.addWidget(self.apply_filter_btn)
        
        date_controls.addStretch()
        
        # Category filter
        category_controls = QHBoxLayout()
        
        category_label = QLabel(UIHelper.translate("Category:"))
        category_label.setProperty("original_text", "Category:")
        category_controls.addWidget(category_label)
        
        self.category_filter = QComboBox()
        self.category_filter.addItem(UIHelper.translate("All Categories"))
        for category in self.categories:
            self.category_filter.addItem(category)
        self.category_filter.currentIndexChanged.connect(self.filter_manage_bills)
        category_controls.addWidget(self.category_filter)
        
        # Year selection
        year_label = QLabel(UIHelper.translate("Year:"))
        year_label.setProperty("original_text", "Year:")
        category_controls.addWidget(year_label)
        
        self.manage_year_selector = QComboBox()
        self.manage_year_selector.addItem("Present Database")
        self.manage_year_selector.currentIndexChanged.connect(self.load_manage_bills)
        category_controls.addWidget(self.manage_year_selector)
        
        category_controls.addStretch()
        
        filter_layout.addLayout(date_controls)
        filter_layout.addLayout(category_controls)
        bills_layout.addWidget(filter_card)
        
        # Card for bills table with actions
        bills_card = QWidget()
        bills_card.setObjectName("card")
        bills_card_layout = QVBoxLayout()
        bills_card.setLayout(bills_card_layout)
        
        # Table header with actions
        table_header = QHBoxLayout()
        
        bills_title = QLabel(UIHelper.translate("Bills"))
        bills_title.setObjectName("card-title")
        bills_title.setProperty("original_text", "Bills")
        table_header.addWidget(bills_title)
        
        # Action buttons in header
        btn_layout = QHBoxLayout()
        
        self.print_selected_btn = QPushButton(UIHelper.translate("Print"))
        self.print_selected_btn.setProperty("original_text", "Print")
        self.print_selected_btn.setIcon(QIcon.fromTheme("document-print", QIcon()))
        self.print_selected_btn.clicked.connect(self.print_bills)
        btn_layout.addWidget(self.print_selected_btn)
        
        self.delete_selected_btn = QPushButton(UIHelper.translate("Delete"))
        self.delete_selected_btn.setProperty("original_text", "Delete")
        self.delete_selected_btn.setIcon(QIcon.fromTheme("edit-delete", QIcon()))
        self.delete_selected_btn.setObjectName("danger-button")
        self.delete_selected_btn.clicked.connect(self.delete_selected_bills)
        btn_layout.addWidget(self.delete_selected_btn)
        
        table_header.addLayout(btn_layout)
        bills_card_layout.addLayout(table_header)
        
        # Bills table with checkboxes for selection
        self.manage_bills_table = QTableWidget(0, 4)  # Date, Name, Price, Select
        headers = ["Date", "Name", "Price", ""]
        translated_headers = [UIHelper.translate(header) for header in headers]
        self.manage_bills_table.setHorizontalHeaderLabels(translated_headers)
        self.manage_bills_table.setProperty("original_headers", headers)
        self.manage_bills_table.horizontalHeader().setStretchLastSection(True)
        self.manage_bills_table.setAlternatingRowColors(True)
        self.manage_bills_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        bills_card_layout.addWidget(self.manage_bills_table)
        
        bills_layout.addWidget(bills_card)
        
        
        # Add views to the tabs
        view_tabs.addTab(bills_view, UIHelper.translate("All Bills"))
        
        main_layout.addWidget(view_tabs)
        
        # Set up selection tracking
        self.selected_bills = []
        
        # Load data when tab is shown
        view_tabs.currentChanged.connect(self.on_manage_tab_changed)