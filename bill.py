from functools import partial
import json
from datetime import datetime
import os

from PyQt5.QtWidgets import (
    QPushButton, QTableWidgetItem, QLabel, QMessageBox, QHBoxLayout, QFileDialog
)

from PyQt5.QtPrintSupport import QPrinter, QPrintDialog, QPrintPreviewDialog, QPageSetupDialog
from PyQt5.QtGui import QPixmap

from PyQt5.QtCore import Qt
import sqlite3
import shutil

category_order = ["Mortgage", "Food", "Gas", "Mechanic", "Work Clothes", "Materials", "Miscellaneous", "Doctor", "Equipment & Rent", "Cash"]

def select_photo(self):
    options = QFileDialog.Options()
    file_path, _ = QFileDialog.getOpenFileName(self, "Select Bill Image", "", "Images (*.png *.jpg *.jpeg *.bmp);;All Files (*)", options=options)
    
    if file_path:
        self.selected_image_path = file_path
        self.image_preview.setPixmap(QPixmap(file_path))  # Show image preview

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
    query = "SELECT date, name, price FROM bills"
    cursor = self.conn.execute(query)
    
    for row in cursor:
        row_count = self.present_bill_table.rowCount()
        self.present_bill_table.insertRow(row_count)
        self.present_bill_table.setItem(row_count, 0, QTableWidgetItem(row[0]))
        self.present_bill_table.setItem(row_count, 1, QTableWidgetItem(row[1]))
        self.present_bill_table.setItem(row_count, 2, QTableWidgetItem(row[2]))

def load_all_photos(self):
    self.clear_layout(self.scroll_layout)  # Clear previous images

    query = "SELECT date, image FROM bills WHERE image IS NOT NULL"
    cursor = self.conn.execute(query)

    for row in cursor:
        date, image_filename = row
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

def filter_photos_by_date(self):
    try:
        date_formats = ["%m/%d/%y", "%m/%d/%Y"]

        def parse_date(date_text):
            for date_format in date_formats:
                try:
                    return datetime.strptime(date_text, date_format).strftime("%m/%d/%Y")
                except ValueError:
                    continue
            raise ValueError("Invalid date format")
        
        start_date = parse_date(self.photo_start_date_input.text())
        end_date = parse_date(self.photo_end_date_input.text())

        # Convert the text inputs to datetime objects
        start_date = datetime.strptime(start_date, "%m/%d/%Y")
        end_date = datetime.strptime(end_date, "%m/%d/%Y")
    except ValueError:
        # If invalid date range or conversion error occurs, show all entries in the database        
        # Load all bills (no filtering)
        self.load_all_photos()
        return

    self.clear_layout(self.scroll_layout)  # Clear existing images

    query = "SELECT date, image FROM bills WHERE image IS NOT NULL AND date BETWEEN ? AND ?"
    cursor = self.conn.execute(query, (start_date.strftime("%m/%d/%Y"), end_date.strftime("%m/%d/%Y")))

    for row in cursor:
        date, image_filename = row
        if image_filename:
            image_path = os.path.join("bill_images", image_filename)
            if os.path.exists(image_path):
                self.add_image_to_photos_page(date, image_path)

def load_existing_databases(self):
    # Scan the current directory
    for file in os.listdir('.'):
        if file.startswith('bills_') and file.endswith('.db'):
            year = file[6:10]
            if year.isdigit():
                # Update the Main Page year selector
                if year not in [self.year_selector.itemText(i) for i in range(self.year_selector.count())]:
                    self.year_selector.addItem(year)
                
                # Update the Data Page year selector
                if year not in [self.data_year_selector.itemText(i) for i in range(self.data_year_selector.count())]:
                    self.data_year_selector.addItem(year)
                
                # Update the Delete Page year selector
                if year not in [self.delete_year_selector.itemText(i) for i in range(self.delete_year_selector.count())]:
                    self.delete_year_selector.addItem(year)

def sort_table(self, order):
    rows = []
    for row in range(self.bill_table.rowCount()):
        date_item = self.bill_table.item(row, 0)
        name_item = self.bill_table.item(row, 1)
        price_item = self.bill_table.item(row, 2)
        
        if date_item and name_item and price_item:
            date = datetime.strptime(date_item.text(), "%m/%d/%Y")
            price = float(price_item.text().replace("$", ""))
            name = name_item.text()
            rows.append((date, price, name, row))  # Include the original row index

    # Sort rows by date (desc/asc), price (desc), and name (alphabetically)
    rows.sort(key=lambda x: (x[0], -x[1], x[2]), reverse=order=="desc")

    # Clear and repopulate the table
    self.bill_table.setRowCount(0)
    for date, price, name, _ in rows:
        row_count = self.bill_table.rowCount()
        self.bill_table.insertRow(row_count)
        self.bill_table.setItem(row_count, 0, QTableWidgetItem(date.strftime("%m/%d/%Y")))
        self.bill_table.setItem(row_count, 1, QTableWidgetItem(name))
        self.bill_table.setItem(row_count, 2, QTableWidgetItem(f"${price:.2f}"))

def load_bills(self):
    self.bill_table.setRowCount(0)  # Clear the table
    selected_year = self.year_selector.currentText()
    if selected_year == "Present Database":
        query = "SELECT date, name, price FROM bills"
        cursor = self.conn.execute(query)
    else:
        conn = sqlite3.connect(f"bills_{selected_year}.db")
        cursor = conn.execute("SELECT date, name, price FROM bills")
    
    for row in cursor:
        row_count = self.bill_table.rowCount()
        self.bill_table.insertRow(row_count)
        self.bill_table.setItem(row_count, 0, QTableWidgetItem(row[0]))
        self.bill_table.setItem(row_count, 1, QTableWidgetItem(row[1]))
        self.bill_table.setItem(row_count, 2, QTableWidgetItem(row[2]))

def save_bill(self):
    if self.date_input.text():
        date_text = self.date_input.text()
        date_formats = ["%m/%d/%y", "%m/%d/%Y"]
        for date_format in date_formats:
            try:
                date = datetime.strptime(date_text, date_format).strftime("%m/%d/%Y")
                break
            except ValueError:
                continue
        else:
            QMessageBox.warning(self, "Input Error", "Invalid date format. Please use MM/dd/yyyy.")
            return
    else:
        date = self.calendar.selectedDate().toString("MM/dd/yyyy")
    
    name = self.name_input.text()
    price = self.price_input.text()

    # Check if any field is empty
    if not date or not name or not price:
        QMessageBox.warning(self, "Input Error", "Please enter date, name, and price.")
        return
    
    # Determine the year and corresponding database
    year = datetime.strptime(date, "%m/%d/%Y").year
    db_name = f"bills_{year}.db"
    conn = sqlite3.connect(db_name)
    self.create_table_in_db(conn)

    # Save to the corresponding database
    query = "INSERT INTO bills (date, name, price) VALUES (?, ?, ?)"
    conn.execute(query, (date, name, str(f"${float(price):.2f}")))
    conn.commit()
    conn.close()

    # Save to the present in-memory database
    self.conn.execute(query, (date, name, str(f"${float(price):.2f}")))
    self.conn.commit()

    # Add to table view
    row_count = self.bill_table.rowCount()
    self.bill_table.insertRow(row_count)
    self.bill_table.setItem(row_count, 0, QTableWidgetItem(date))
    self.bill_table.setItem(row_count, 1, QTableWidgetItem(name))
    self.bill_table.setItem(row_count, 2, QTableWidgetItem(f"${float(price):.2f}"))

    row_count = self.present_bill_table.rowCount()
    self.present_bill_table.insertRow(row_count)
    self.present_bill_table.setItem(row_count, 0, QTableWidgetItem(date))
    self.present_bill_table.setItem(row_count, 1, QTableWidgetItem(name))
    self.present_bill_table.setItem(row_count, 2, QTableWidgetItem(f"${float(price):.2f}"))

    # Update year selectors after saving
    self.load_existing_databases()

    # Clear selected categories and update name input
    self.selected_categories = []
    self.update_name_input()

    # Clear inputs after saving
    self.price_input.clear()
    self.name_input.clear()
    self.date_input.clear()

    # Save image (if selected)
    image_filename = None
    if self.selected_image_path:
        image_folder = "bill_images"
        os.makedirs(image_folder, exist_ok=True)  # Ensure folder exists
        image_filename = f"{date.replace('/', '-')}_{name}.jpg"  # Unique name
        dest_path = os.path.join(image_folder, image_filename)
        shutil.copy(self.selected_image_path, dest_path)  # Copy image
    else:
        image_filename = None  # No image selected

    # Store in database
    query = "INSERT INTO bills (date, name, price, image) VALUES (?, ?, ?, ?)"
    self.conn.execute(query, (date, name, f"${float(price):.2f}", image_filename))
    self.conn.commit()


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
        button = QPushButton(new_category)
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
    self.clear_layout(self.category_list_layout)

    for category in self.categories:
        category_layout = QHBoxLayout()
        category_label = QLabel(category)
        delete_button = QPushButton("Delete")
        delete_button.clicked.connect(partial(self.delete_category, category))
        category_layout.addWidget(category_label)
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
    try:
        with open("categories.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return ["Mortgage", "Food", "Gas", "Mechanic", "Work Clothes", "Materials", "Miscellaneous", "Doctor", "Equipment & Rent", "Cash"]

def save_categories(self):
    with open("categories.json", "w") as file:
        json.dump(self.categories, file)

def load_data(self):
    self.data_table.setRowCount(0)  # Clear the table
    selected_year = self.data_year_selector.currentText()

    # Determine which database to query
    if selected_year == "Present Database":
        query = "SELECT date, price, name FROM bills"
        cursor = self.conn.execute(query)
    else:
        conn = sqlite3.connect(f"bills_{selected_year}.db")
        cursor = conn.execute("SELECT date, price, name FROM bills")

    # Initialize monthly totals
    monthly_totals = {month: {"cash": 0, "not_cash": 0, "total": 0} for month in range(1, 13)}
    yearly_totals = {"cash": 0, "not_cash": 0, "total": 0}

    for row in cursor:
        date = row[0]
        price = float(row[1].replace("$", ""))  # Convert price string to float
        name = row[2]
        
        # Extract the month from the date
        month = datetime.strptime(date, "%m/%d/%Y").month

        # Determine if it's a cash transaction
        if "Cash" in name:
            monthly_totals[month]["cash"] += price
            yearly_totals["cash"] += price
        else:
            monthly_totals[month]["not_cash"] += price
            yearly_totals["not_cash"] += price

        # Update monthly and yearly totals
        monthly_totals[month]["total"] += price
        yearly_totals["total"] += price

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
    try:
        date_formats = ["%m/%d/%y", "%m/%d/%Y"]
        
        def parse_date(date_text):
            for date_format in date_formats:
                try:
                    return datetime.strptime(date_text, date_format).strftime("%m/%d/%Y")
                except ValueError:
                    continue
            raise ValueError("Invalid date format")
        
        start_date_text = parse_date(self.start_date_input.text())
        end_date_text = parse_date(self.end_date_input.text())

        # Convert the text inputs to datetime objects
        start_date = datetime.strptime(start_date_text, "%m/%d/%Y")
        end_date = datetime.strptime(end_date_text, "%m/%d/%Y")
    except ValueError as e:
        # If invalid date range or conversion error occurs, show all entries in the database        
        # Load all bills (no filtering)
        self.load_all_bills()
        return

    # Load bills within the date range
    self.bill_table.setRowCount(0)  # Clear the table
    selected_year = self.year_selector.currentText()

    if selected_year == "Present Database":
        query = "SELECT date, name, price FROM bills WHERE date BETWEEN ? AND ?"
        cursor = self.conn.execute(query, (start_date.strftime("%m/%d/%Y"), end_date.strftime("%m/%d/%Y")))
    else:
        conn = sqlite3.connect(f"bills_{selected_year}.db")
        query = "SELECT date, name, price FROM bills WHERE date BETWEEN ? AND ?"
        cursor = conn.execute(query, (start_date.strftime("%m/%d/%Y"), end_date.strftime("%m/%d/%Y")))

    # Populate the table with the filtered bills
    for row in cursor:
        row_count = self.bill_table.rowCount()
        self.bill_table.insertRow(row_count)
        self.bill_table.setItem(row_count, 0, QTableWidgetItem(row[0]))
        self.bill_table.setItem(row_count, 1, QTableWidgetItem(row[1]))
        self.bill_table.setItem(row_count, 2, QTableWidgetItem(row[2]))

def load_all_bills(self):
    # Function to load all bills if date range is invalid
    self.bill_table.setRowCount(0)  # Clear the table
    selected_year = self.year_selector.currentText()

    if selected_year == "Present Database":
        query = "SELECT date, name, price FROM bills"
        cursor = self.conn.execute(query)
    else:
        conn = sqlite3.connect(f"bills_{selected_year}.db")
        query = "SELECT date, name, price FROM bills"
        cursor = conn.execute(query)

    # Populate the table with all the bills
    for row in cursor:
        row_count = self.bill_table.rowCount()
        self.bill_table.insertRow(row_count)
        self.bill_table.setItem(row_count, 0, QTableWidgetItem(row[0]))
        self.bill_table.setItem(row_count, 1, QTableWidgetItem(row[1]))
        self.bill_table.setItem(row_count, 2, QTableWidgetItem(row[2]))

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
    selected_row = self.delete_table.currentRow()
    if selected_row < 0:
        QMessageBox.warning(self, "Selection Error", "No row selected.")
        return

    date = self.delete_table.item(selected_row, 0).text()
    name = self.delete_table.item(selected_row, 1).text()
    price = self.delete_table.item(selected_row, 2).text()

    selected_year = self.delete_year_selector.currentText()
    conn = sqlite3.connect(f"bills_{selected_year}.db")
    conn.execute("DELETE FROM bills WHERE date = ? AND name = ? AND price = ?", (date, name, price))
    conn.commit()
    conn.close()

    self.delete_table.removeRow(selected_row)

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