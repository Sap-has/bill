from datetime import datetime
from PyQt5.QtWidgets import (
    QMainWindow, QVBoxLayout, QWidget, QPushButton, QLineEdit, QLabel, QHBoxLayout, QTableWidgetItem
)

from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize, Qt

from util.uiHelper import UIHelper

class DashboardPage(QMainWindow):
    def init_dashboard_page(self):
        """Initialize the Dashboard page with summary widgets and quick actions."""
        self.dashboard_page = QWidget()
        main_layout = QVBoxLayout()
        self.dashboard_page.setLayout(main_layout)
        
        # Welcome section with search
        welcome_card = QWidget()
        welcome_card.setObjectName("card")
        welcome_layout = QVBoxLayout()
        welcome_card.setLayout(welcome_layout)
        
        # Welcome header with search
        header_layout = QHBoxLayout()
        welcome_label = QLabel(UIHelper.translate("Welcome to Bill Tracker"))
        welcome_label.setObjectName("card-title")
        header_layout.addWidget(welcome_label)
        
        # Global search box
        self.global_search = QLineEdit()
        self.global_search.setPlaceholderText(UIHelper.translate("Search all bills..."))
        self.global_search.setProperty("original_placeholder", "Search all bills...")
        self.global_search.setMinimumWidth(200)
        self.global_search.textChanged.connect(self.perform_global_search)
        header_layout.addWidget(self.global_search)
        
        welcome_layout.addLayout(header_layout)
        
        # Quick stats summary
        stats_layout = QHBoxLayout()
        
        # Bills this month card
        bills_month_widget = QWidget()
        bills_month_widget.setObjectName("stat-card")
        bills_month_layout = QVBoxLayout()
        bills_month_widget.setLayout(bills_month_layout)
        bills_month_count = QLabel("0")
        bills_month_count.setObjectName("stat-number")
        bills_month_layout.addWidget(bills_month_count)
        bills_month_label = QLabel(UIHelper.translate("Bills This Month"))
        bills_month_label.setProperty("original_text", "Bills This Month")
        bills_month_layout.addWidget(bills_month_label)
        stats_layout.addWidget(bills_month_widget)
        
        # Total spent this month card
        total_month_widget = QWidget()
        total_month_widget.setObjectName("stat-card")
        total_month_layout = QVBoxLayout()
        total_month_widget.setLayout(total_month_layout)
        total_month_amount = QLabel("$0.00")
        total_month_amount.setObjectName("stat-number")
        total_month_layout.addWidget(total_month_amount)
        total_month_label = QLabel(UIHelper.translate("Total This Month"))
        total_month_label.setProperty("original_text", "Total This Month")
        total_month_layout.addWidget(total_month_label)
        stats_layout.addWidget(total_month_widget)
        
        # Top category this month
        top_category_widget = QWidget()
        top_category_widget.setObjectName("stat-card")
        top_category_layout = QVBoxLayout()
        top_category_widget.setLayout(top_category_layout)
        top_category_name = QLabel("--")
        top_category_name.setObjectName("stat-number")
        top_category_layout.addWidget(top_category_name)
        top_category_label = QLabel(UIHelper.translate("Top Category"))
        top_category_label.setProperty("original_text", "Top Category")
        top_category_layout.addWidget(top_category_label)
        stats_layout.addWidget(top_category_widget)
        
        welcome_layout.addLayout(stats_layout)
        main_layout.addWidget(welcome_card)
        
        # Quick Actions section
        actions_card = QWidget()
        actions_card.setObjectName("card")
        actions_layout = QVBoxLayout()
        actions_card.setLayout(actions_layout)
        
        actions_title = QLabel(UIHelper.translate("Quick Actions"))
        actions_title.setObjectName("card-title")
        actions_title.setProperty("original_text", "Quick Actions")
        actions_layout.addWidget(actions_title)
        
        # Action buttons
        action_buttons_layout = QHBoxLayout()
        
        # Add New Bill button with icon
        add_bill_btn = QPushButton("  " + UIHelper.translate("Add New Bill"))
        add_bill_btn.setProperty("original_text", "  Add New Bill")
        add_bill_btn.setIcon(QIcon.fromTheme("list-add", QIcon()))
        add_bill_btn.setIconSize(QSize(24, 24))
        add_bill_btn.setObjectName("primary-action")
        add_bill_btn.clicked.connect(lambda: self.tab_widget.setCurrentIndex(1))  # Go to Bill Entry tab
        action_buttons_layout.addWidget(add_bill_btn)
        
        # Print Reports button with icon
        print_btn = QPushButton("  " + UIHelper.translate("Print Reports"))
        print_btn.setProperty("original_text", "  Print Reports")
        print_btn.setIcon(QIcon.fromTheme("document-print", QIcon()))
        print_btn.setIconSize(QSize(24, 24))
        print_btn.clicked.connect(self.print_bills)
        action_buttons_layout.addWidget(print_btn)
        
        # View Analytics button with icon
        analytics_btn = QPushButton("  " + UIHelper.translate("View Analytics"))
        analytics_btn.setProperty("original_text", "  View Analytics")
        analytics_btn.setIcon(QIcon.fromTheme("accessories-calculator", QIcon()))
        analytics_btn.setIconSize(QSize(24, 24))
        analytics_btn.clicked.connect(lambda: self.tab_widget.setCurrentIndex(3))  # Go to Reports tab
        action_buttons_layout.addWidget(analytics_btn)
        
        actions_layout.addLayout(action_buttons_layout)
        main_layout.addWidget(actions_card)
        
        # Recent Bills section
        recent_card = QWidget()
        recent_card.setObjectName("card")
        recent_layout = QVBoxLayout()
        recent_card.setLayout(recent_layout)
        
        recent_header = QHBoxLayout()
        recent_title = QLabel(UIHelper.translate("Recent Bills"))
        recent_title.setObjectName("card-title")
        recent_title.setProperty("original_text", "Recent Bills")
        recent_header.addWidget(recent_title)
        
        view_all_btn = QPushButton(UIHelper.translate("View All"))
        view_all_btn.setProperty("original_text", "View All")
        view_all_btn.setObjectName("text-button")
        view_all_btn.clicked.connect(lambda: self.tab_widget.setCurrentIndex(2))  # Go to Manage Bills tab
        recent_header.addWidget(view_all_btn)
        
        recent_layout.addLayout(recent_header)
        
        # Recent bills table
        self.recent_bills_table = UIHelper.create_table(3, ["Date", "Name", "Price"])
        self.recent_bills_table.setMaximumHeight(200)
        recent_layout.addWidget(self.recent_bills_table)
        
        main_layout.addWidget(recent_card)
        
        # Set main layout spacing and margins
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Update dashboard stats whenever it's shown
        self.tab_widget.currentChanged.connect(self.update_dashboard_if_needed)

    def update_dashboard_if_needed(self, tab_index):
        """Update dashboard stats when dashboard tab is selected."""
        if tab_index == 0:  # Dashboard is the first tab
            self.update_dashboard_stats()
            self.update_recent_bills_table()

    def update_dashboard_stats(self):
        """Update the statistics displayed on the dashboard."""
        # Get current month stats
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        # Format dates for query
        start_date = f"{current_month:02d}/01/{current_year}"
        last_day = 30 if current_month in [4, 6, 9, 11] else 31
        if current_month == 2:
            last_day = 29 if current_year % 4 == 0 else 28
        end_date = f"{current_month:02d}/{last_day}/{current_year}"
        
        # Get bills for current month
        selected_year = str(current_year)
        monthly_bills = self.db_manager.get_bills(selected_year, start_date, end_date)
        
        # Update bills count
        bills_month_count = self.dashboard_page.findChild(QLabel, "stat-number", Qt.FindChildrenRecursively)
        if bills_month_count:
            bills_month_count.setText(str(len(monthly_bills)))
        
        # Calculate total spent
        total_amount = 0.0
        category_counts = {}
        
        for bill in monthly_bills:
            # Extract price (remove $ and convert to float)
            price_str = bill[2].replace('$', '').strip()
            try:
                price = float(price_str)
                total_amount += price
                
                # Count categories
                bill_name = bill[1]
                for category in self.categories:
                    if f"({category})" in bill_name:
                        category_counts[category] = category_counts.get(category, 0) + 1
                        break
            except ValueError:
                continue
        
        # Update total amount
        total_month_amount = self.dashboard_page.findChildren(QLabel, "stat-number")[1]
        if total_month_amount:
            total_month_amount.setText(f"${total_amount:.2f}")
        
        # Update top category
        top_category = max(category_counts.items(), key=lambda x: x[1])[0] if category_counts else "--"
        top_category_name = self.dashboard_page.findChildren(QLabel, "stat-number")[2]
        if top_category_name:
            top_category_name.setText(top_category)

    def update_recent_bills_table(self):
        """Update the recent bills table on the dashboard."""
        self.recent_bills_table.setRowCount(0)
        
        # Get the most recent bills (limit to 5)
        bills = self.db_manager.get_bills()
        recent_bills = bills[-5:] if len(bills) > 5 else bills
        
        # Add the bills to the table in reverse order (newest first)
        for bill in reversed(recent_bills):
            row_count = self.recent_bills_table.rowCount()
            self.recent_bills_table.insertRow(row_count)
            self.recent_bills_table.setItem(row_count, 0, QTableWidgetItem(bill[0]))
            self.recent_bills_table.setItem(row_count, 1, QTableWidgetItem(bill[1]))
            self.recent_bills_table.setItem(row_count, 2, QTableWidgetItem(bill[2]))