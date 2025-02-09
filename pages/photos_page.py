from PyQt5.QtWidgets import (
    QVBoxLayout, QWidget, QPushButton, QLineEdit, QHBoxLayout, QScrollArea
)

class photos_page:
    def init_photos_page(self):
        self.photos_page = QWidget()
        self.photos_layout = QVBoxLayout()
        self.photos_page.setLayout(self.photos_layout)

        # Date filter inputs
        date_filter_layout = QHBoxLayout()

        self.photo_start_date_input = QLineEdit()
        self.photo_start_date_input.setPlaceholderText("Start date (MM/dd/yyyy)")
        date_filter_layout.addWidget(self.photo_start_date_input)

        self.photo_end_date_input = QLineEdit()
        self.photo_end_date_input.setPlaceholderText("End date (MM/dd/yyyy)")
        date_filter_layout.addWidget(self.photo_end_date_input)

        self.filter_photos_button = QPushButton("Filter Photos")
        self.filter_photos_button.clicked.connect(self.filter_photos_by_date)
        date_filter_layout.addWidget(self.filter_photos_button)

        self.photos_layout.addLayout(date_filter_layout)

        # Scrollable image view
        self.scroll_area = QScrollArea()
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_area.setWidget(self.scroll_content)
        self.scroll_area.setWidgetResizable(True)
        self.photos_layout.addWidget(self.scroll_area)

        self.load_all_photos()