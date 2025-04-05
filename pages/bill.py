from PyQt5.QtWidgets import (
    QVBoxLayout, QGridLayout, QWidget, QPushButton, QHBoxLayout, QListWidget, QLabel, QMainWindow
)

from PyQt5.QtGui import QIcon

from PyQt5.QtCore import Qt, QSize

from util.uiHelper import UIHelper

class bill(QMainWindow):
    def init_bill_page(self):
        """Initialize the Bill Entry tab with form and category selection."""
        self.bill_page = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        self.bill_page.setLayout(main_layout)
        
        # Bill form card
        form_card = QWidget()
        form_card.setObjectName("card")
        form_layout = QVBoxLayout()
        form_card.setLayout(form_layout)
        
        # Card title
        form_title = QLabel(UIHelper.translate("New Bill"))
        form_title.setObjectName("card-title")
        form_title.setProperty("original_text", "New Bill")
        form_layout.addWidget(form_title)
        
        # Form groups
        form_groups_layout = QHBoxLayout()
        
        # Left column - Date and details
        left_column = QVBoxLayout()
        
        # Date selection group
        date_group = QWidget()
        date_group.setObjectName("form-group")
        date_layout = QVBoxLayout()
        date_group.setLayout(date_layout)
        
        date_label = QLabel(UIHelper.translate("Date"))
        date_label.setObjectName("form-label")
        date_label.setProperty("original_text", "Date")
        date_layout.addWidget(date_label)
        
        # Date picker with calendar popup button
        date_picker_layout = QHBoxLayout()
        
        self.date_input = UIHelper.create_date_input()
        date_picker_layout.addWidget(self.date_input)
        
        calendar_btn = QPushButton()
        calendar_btn.setIcon(QIcon.fromTheme("x-office-calendar", QIcon()))
        calendar_btn.setIconSize(QSize(16, 16))
        calendar_btn.setMaximumWidth(40)
        calendar_btn.clicked.connect(self.show_calendar_dialog)
        date_picker_layout.addWidget(calendar_btn)
        
        date_layout.addLayout(date_picker_layout)
        left_column.addWidget(date_group)
        
        # Bill name group
        name_group = QWidget()
        name_group.setObjectName("form-group")
        name_layout = QVBoxLayout()
        name_group.setLayout(name_layout)
        
        name_label = QLabel(UIHelper.translate("Bill Name"))
        name_label.setObjectName("form-label")
        name_label.setProperty("original_text", "Bill Name")
        name_layout.addWidget(name_label)
        
        self.name_input = UIHelper.create_input_field("Enter bill name")
        self.name_input.textChanged.connect(self.show_autocomplete_suggestions)
        name_layout.addWidget(self.name_input)
        
        # Show suggestions only when typing
        self.suggestions_list = QListWidget()
        self.suggestions_list.setFixedHeight(0)  # Hidden initially
        self.suggestions_list.setFrameShape(QListWidget.NoFrame)
        self.suggestions_list.itemClicked.connect(self.select_suggestion)
        name_layout.addWidget(self.suggestions_list)
        
        left_column.addWidget(name_group)
        
        # Amount group
        amount_group = QWidget()
        amount_group.setObjectName("form-group")
        amount_layout = QVBoxLayout()
        amount_group.setLayout(amount_layout)
        
        amount_label = QLabel(UIHelper.translate("Amount"))
        amount_label.setObjectName("form-label")
        amount_label.setProperty("original_text", "Amount")
        amount_layout.addWidget(amount_label)
        
        amount_input_layout = QHBoxLayout()
        
        # Dollar sign prefix
        dollar_label = QLabel("$")
        dollar_label.setObjectName("currency-symbol")
        amount_input_layout.addWidget(dollar_label)
        
        self.price_input = UIHelper.create_input_field("0.00")
        amount_input_layout.addWidget(self.price_input)
        
        amount_layout.addLayout(amount_input_layout)
        left_column.addWidget(amount_group)
        
        # Add to form groups
        form_groups_layout.addLayout(left_column)
        
        # Right column - Categories and Photos
        right_column = QVBoxLayout()
        
        # Categories group
        categories_group = QWidget()
        categories_group.setObjectName("form-group")
        categories_layout = QVBoxLayout()
        categories_group.setLayout(categories_layout)
        
        categories_label = QLabel(UIHelper.translate("Categories"))
        categories_label.setObjectName("form-label")
        categories_label.setProperty("original_text", "Categories")
        categories_layout.addWidget(categories_label)
        
        # Category chips/tags in a flowing layout
        self.category_flow_widget = QWidget()
        self.category_flow_layout = QGridLayout()
        self.category_flow_layout.setHorizontalSpacing(10)
        self.category_flow_layout.setVerticalSpacing(10)
        self.category_flow_widget.setLayout(self.category_flow_layout)
        categories_layout.addWidget(self.category_flow_widget)
        
        # Create category chips
        self.category_buttons = {}
        self.categories = self.predefined_order
        
        for i, category in enumerate(self.categories):
            # Create a togglable chip button
            chip = QPushButton(category)
            chip.setObjectName("category-chip")
            chip.setCheckable(True)
            chip.setMinimumHeight(30)  # More touch-friendly
            chip.toggled.connect(lambda checked, cat=category: self.toggle_category(cat, checked))
            
            self.category_flow_layout.addWidget(chip, i // 4, i % 4)  # 4 columns
            self.category_buttons[category] = chip
        
        right_column.addWidget(categories_group)
        
        # Photo group
        photo_group = QWidget()
        photo_group.setObjectName("form-group")
        photo_layout = QVBoxLayout()
        photo_group.setLayout(photo_layout)
        
        photo_label = QLabel(UIHelper.translate("Receipt Photo"))
        photo_label.setObjectName("form-label")
        photo_label.setProperty("original_text", "Receipt Photo")
        photo_layout.addWidget(photo_label)
        
        # Photo preview and buttons
        preview_layout = QHBoxLayout()
        
        # Image preview
        preview_container = QWidget()
        preview_container.setObjectName("photo-preview")
        preview_container.setMinimumSize(150, 150)
        preview_container.setMaximumSize(150, 150)
        
        preview_container_layout = QVBoxLayout()
        preview_container.setLayout(preview_container_layout)
        
        self.image_preview = QLabel()
        self.image_preview.setAlignment(Qt.AlignCenter)
        self.image_preview.setScaledContents(True)
        preview_container_layout.addWidget(self.image_preview)
        
        preview_layout.addWidget(preview_container)
        
        # Photo actions
        photo_actions = QVBoxLayout()
        
        # Photo buttons with icons
        self.image_button = QPushButton(UIHelper.translate("  Add Photo"))
        self.image_button.setProperty("original_text", "  Add Photo")
        self.image_button.setIcon(QIcon.fromTheme("insert-image", QIcon()))
        self.image_button.setIconSize(QSize(16, 16))
        self.image_button.clicked.connect(self.select_photo)
        photo_actions.addWidget(self.image_button)
        
        self.scan_button = QPushButton(UIHelper.translate("  Scan Receipt"))
        self.scan_button.setProperty("original_text", "  Scan Receipt")
        self.scan_button.setIcon(QIcon.fromTheme("scanner", QIcon()))
        self.scan_button.setIconSize(QSize(16, 16))
        self.scan_button.setContextMenuPolicy(Qt.CustomContextMenu)
        self.scan_button.customContextMenuRequested.connect(self.show_scan_context_menu)
        self.scan_button.clicked.connect(self.scan_receipt)
        photo_actions.addWidget(self.scan_button)
        
        # Check OCR availability and update button state
        self.update_scan_button_state()
        
        # Add a clear photo button
        self.clear_photo_btn = QPushButton(UIHelper.translate("  Clear Photo"))
        self.clear_photo_btn.setProperty("original_text", "  Clear Photo")
        self.clear_photo_btn.setIcon(QIcon.fromTheme("edit-clear", QIcon()))
        self.clear_photo_btn.setIconSize(QSize(16, 16))
        self.clear_photo_btn.clicked.connect(self.clear_photo)
        photo_actions.addWidget(self.clear_photo_btn)
        
        preview_layout.addLayout(photo_actions)
        photo_layout.addLayout(preview_layout)
        
        right_column.addWidget(photo_group)
        
        # Add to form groups
        form_groups_layout.addLayout(right_column)
        
        form_layout.addLayout(form_groups_layout)
        
        # Save button - prominent at the bottom
        save_btn_layout = QHBoxLayout()
        save_btn_layout.addStretch()
        
        self.save_button = QPushButton(UIHelper.translate("  Save Bill"))
        self.save_button.setProperty("original_text", "  Save Bill")
        self.save_button.setIcon(QIcon.fromTheme("document-save", QIcon()))
        self.save_button.setIconSize(QSize(20, 20))
        self.save_button.setMinimumSize(120, 40)  # Large, touch-friendly button
        self.save_button.setObjectName("primary-action")
        self.save_button.clicked.connect(self.save_bill)
        save_btn_layout.addWidget(self.save_button)
        
        form_layout.addLayout(save_btn_layout)
        
        main_layout.addWidget(form_card)
        
        # Recent bills card
        recent_card = QWidget()
        recent_card.setObjectName("card")
        recent_layout = QVBoxLayout()
        recent_card.setLayout(recent_layout)
        
        recent_title = QLabel(UIHelper.translate("Recent Bills"))
        recent_title.setObjectName("card-title")
        recent_title.setProperty("original_text", "Recent Bills")
        recent_layout.addWidget(recent_title)
        
        # Recent bills table
        self.present_bill_table = UIHelper.create_table(3, ["Date", "Name", "Price"])
        self.present_bill_table.setMaximumHeight(200)
        recent_layout.addWidget(self.present_bill_table)
        
        main_layout.addWidget(recent_card)