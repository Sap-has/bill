from PyQt5.QtWidgets import (
    QVBoxLayout, QWidget, QComboBox
)

from util.uiHelper import UIHelper

class data:
    def init_data_page(self):
            """Initialize the Data tab for viewing monthly expenditure."""
            self.data_page = QWidget()
            self.data_layout = QVBoxLayout()
            self.data_page.setLayout(self.data_layout)

            # Section: Year Selection
            self.data_layout.addWidget(UIHelper.create_section_label("Select Year"))
            
            self.data_year_selector = QComboBox()
            self.data_year_selector.addItem("Present Database")
            self.data_year_selector.currentIndexChanged.connect(self.load_data)
            self.data_layout.addWidget(self.data_year_selector)
            
            UIHelper.add_section_spacing(self.data_layout)
            
            # Section: Monthly Expenditure
            self.data_layout.addWidget(UIHelper.create_section_label("Monthly Expenditure"))

            self.data_table = UIHelper.create_table(4, ["Month", "Cash", "Not Cash", "Total"])
            self.data_layout.addWidget(self.data_table)