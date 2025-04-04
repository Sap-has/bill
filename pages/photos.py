import os
from PyQt5.QtWidgets import (
    QVBoxLayout, QWidget, QComboBox, QHBoxLayout, QScrollArea, QLabel
)

from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

from util.uiHelper import UIHelper

class photos:
    def init_photos_page(self):
            """Initialize the Photos tab for viewing bill images."""
            self.photos_page = QWidget()
            self.photos_layout = QVBoxLayout()
            self.photos_page.setLayout(self.photos_layout)

            # Section: Database Selection
            self.photos_layout.addWidget(UIHelper.create_section_label("Select Year"))
            
            # Year selection dropdown
            self.photos_year_selector = QComboBox()
            self.photos_year_selector.addItem("Present Database")
            self.photos_year_selector.currentIndexChanged.connect(self.load_all_photos)
            self.photos_layout.addWidget(self.photos_year_selector)
            
            UIHelper.add_section_spacing(self.photos_layout)

            # Section: Filter Photos
            self.photos_layout.addWidget(UIHelper.create_section_label("Filter Photos by Date"))
            
            # Date filter inputs
            date_filter_layout = QHBoxLayout()

            self.photo_start_date_input = UIHelper.create_date_input()
            date_filter_layout.addWidget(self.photo_start_date_input)

            self.photo_end_date_input = UIHelper.create_date_input()
            date_filter_layout.addWidget(self.photo_end_date_input)

            self.filter_photos_button = UIHelper.create_button("Filter Photos", self.filter_photos_by_date)
            date_filter_layout.addWidget(self.filter_photos_button)

            self.photos_layout.addLayout(date_filter_layout)
            
            UIHelper.add_section_spacing(self.photos_layout)
            
            # Section: Photo Gallery
            self.photos_layout.addWidget(UIHelper.create_section_label("Photo Gallery"))

            # Scrollable image view
            self.scroll_area = QScrollArea()
            self.scroll_content = QWidget()
            self.scroll_layout = QVBoxLayout(self.scroll_content)
            self.scroll_area.setWidget(self.scroll_content)
            self.scroll_area.setWidgetResizable(True)
            self.photos_layout.addWidget(self.scroll_area)

            # Load images 
            self.load_all_photos()
        
    def load_all_photos(self):
        """Load all photos from the database."""
        if not hasattr(self, 'scroll_layout'):
            return  # Exit early if layout not initialized
            
        self.clear_layout(self.scroll_layout)  # Clear previous images
        
        selected_year = self.photos_year_selector.currentText() if hasattr(self, 'photos_year_selector') else None
        
        # Get all bill images
        bill_images = self.db_manager.get_bill_images(selected_year)
        
        # Add images to the photos page
        for date, image_filename in bill_images:
            if image_filename:
                image_path = os.path.join("bill_images", image_filename)
                if os.path.exists(image_path):
                    self.add_image_to_photos_page(date, image_path)
    
    def add_image_to_photos_page(self, date, image_path):
        image_label = QLabel()
        pixmap = QPixmap(image_path)
        image_label.setPixmap(pixmap.scaled(400, 400, Qt.KeepAspectRatio))
        self.scroll_layout.addWidget(QLabel(f"Date: {date}"))
        self.scroll_layout.addWidget(image_label)