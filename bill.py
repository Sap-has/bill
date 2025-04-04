from functools import partial
import json
from datetime import datetime
import sys
import os

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QGridLayout, QWidget, QPushButton, QTableWidget, QTableWidgetItem, 
    QCalendarWidget, QLineEdit, QLabel, QMessageBox, QComboBox, QHBoxLayout, QTabWidget, QListWidget, QFileDialog,
    QScrollArea, QDialog, QProgressBar, QCheckBox, QMenu
)
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog, QPrintPreviewDialog, QPageSetupDialog
from PyQt5.QtGui import QPixmap, QIcon

from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize, QTimer
import sqlite3
import shutil

from mindee import Client, product

# Define constants
DATE_FORMAT = "%m/%d/%Y"
DATE_FORMATS = ["%m/%d/%y", "%m/%d/%Y"]
DEFAULT_CATEGORIES = ["Mortgage", "Food", "Gas", "Mechanic", "Work Clothes", "Materials", "Miscellaneous", "Doctor", "Equipment & Rent", "Cash"]

# Mindee OCR Helper class
class MindeeHelper:
    """Helper class for Mindee API integration."""
    
    # Static variable to hold the API key
    api_key = None
    mindee_client = None
    
    # Track API usage
    usage_file = "mindee_usage.json"
    current_month_usage = 0
    usage_month = None
    # Monthly limit for free tier
    monthly_limit = 250
    
    @staticmethod
    def is_available():
        """Check if Mindee OCR is available (API key is set).
        
        Returns:
            bool: True if Mindee is available, False otherwise.
        """
        return MindeeHelper.api_key is not None
    
    @staticmethod
    def get_current_month():
        """Get the current month and year as a string.
        
        Returns:
            str: The current month in format 'MM-YYYY'
        """
        from datetime import datetime
        return datetime.now().strftime("%m-%Y")
    
    @staticmethod
    def load_usage_data():
        """Load API usage data from the usage file.
        
        Returns:
            tuple: (current_month_usage, usage_month)
        """
        try:
            if os.path.exists(MindeeHelper.usage_file):
                with open(MindeeHelper.usage_file, 'r') as f:
                    data = json.load(f)
                    current_month = MindeeHelper.get_current_month()
                    if data.get('month') == current_month:
                        return data.get('usage', 0), current_month
                    else:
                        # New month, reset usage
                        return 0, current_month
            else:
                # No usage file exists yet
                return 0, MindeeHelper.get_current_month()
        except Exception as e:
            print(f"Error loading usage data: {e}")
            return 0, MindeeHelper.get_current_month()
    
    @staticmethod
    def save_usage_data():
        """Save API usage data to the usage file."""
        try:
            data = {
                'month': MindeeHelper.usage_month,
                'usage': MindeeHelper.current_month_usage
            }
            with open(MindeeHelper.usage_file, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            print(f"Error saving usage data: {e}")
    
    @staticmethod
    def increment_usage():
        """Increment the API usage counter."""
        try:
            current_month = MindeeHelper.get_current_month()
            if MindeeHelper.usage_month is None or MindeeHelper.usage_month != current_month:
                # Initialize usage data for the current month
                MindeeHelper.current_month_usage, MindeeHelper.usage_month = MindeeHelper.load_usage_data()
                
            # Increment usage
            MindeeHelper.current_month_usage += 1
            
            # Save updated usage data
            MindeeHelper.save_usage_data()
        except Exception as e:
            print(f"Error incrementing usage: {e}")
    
    @staticmethod
    def get_remaining_pages():
        """Get the number of remaining pages for the current month.
        
        Returns:
            int: Number of remaining pages.
        """
        current_month = MindeeHelper.get_current_month()
        if MindeeHelper.usage_month is None or MindeeHelper.usage_month != current_month:
            # Initialize usage data for the current month
            MindeeHelper.current_month_usage, MindeeHelper.usage_month = MindeeHelper.load_usage_data()
            
        return max(0, MindeeHelper.monthly_limit - MindeeHelper.current_month_usage)
    
    @staticmethod
    def has_available_pages():
        """Check if there are available pages for the current month.
        
        Returns:
            bool: True if there are pages available, False otherwise.
        """
        return MindeeHelper.get_remaining_pages() > 0
    
    @staticmethod
    def set_api_key(api_key):
        """Set the Mindee API key.
        
        Args:
            api_key: The Mindee API key.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Import Mindee Python package
            global product
            from mindee import Client, product
            
            # Initialize the Mindee client
            client = Client(api_key)
            
            # Test the API key
            MindeeHelper.api_key = api_key
            MindeeHelper.mindee_client = client
            
            # Load usage data
            MindeeHelper.current_month_usage, MindeeHelper.usage_month = MindeeHelper.load_usage_data()
            
            return True
        except ImportError:
            print("Error: Mindee Python package is not installed.")
            return False
        except Exception as e:
            print(f"Error setting API key: {e}")
            return False
    
    @staticmethod
    def load_api_key():
        """Load the API key from the config file.
        
        Returns:
            bool: True if API key was loaded successfully, False otherwise.
        """
        try:
            if os.path.exists('mindee_api_key.txt'):
                with open('mindee_api_key.txt', 'r') as f:
                    api_key = f.read().strip()
                    if api_key:
                        return MindeeHelper.set_api_key(api_key)
            print("API key file not found or empty. Please configure your Mindee API key.")
            return False
        except Exception as e:
            print(f"Error loading Mindee API key: {e}")
            return False

# OCR Worker Thread
class MindeeWorker(QThread):
    """Worker thread for processing receipt images with Mindee API."""
    
    # Signals
    progress = pyqtSignal(int)
    finished = pyqtSignal(dict)
    
    def __init__(self, image_path):
        """Initialize the worker with the image path.
        
        Args:
            image_path: Path to the receipt image.
        """
        super().__init__()
        self.image_path = image_path
    
    def run(self):
        """Process the receipt image using Mindee API."""
        try:
            if not MindeeHelper.is_available():
                raise Exception("Mindee API key is not set")
            
            # Signal progress updates
            self.progress.emit(10)
            
            # Initialize result dictionary
            result = {
                "vendor": "",
                "date": "",
                "amount": ""
            }
            
            # Import product if needed
            from mindee import product
            
            # Open the input file
            self.progress.emit(30)
            
            # Create a receipt prediction using Mindee API
            input_doc = MindeeHelper.mindee_client.source_from_path(self.image_path)
            self.progress.emit(50)
            
            # Parse receipt using the Receipt API - use the client to parse, not the input_doc
            api_response = MindeeHelper.mindee_client.parse(product.ReceiptV5, input_doc)
            self.progress.emit(80)
            
            # Increment the API usage counter
            MindeeHelper.increment_usage()
            
            prediction = api_response.document.inference.prediction

            # Extract vendor name (supplier name in Mindee)
            if hasattr(prediction, 'supplier_name') and prediction.supplier_name:
                result["vendor"] = prediction.supplier_name.value

            # Extract date
            if hasattr(prediction, 'date') and prediction.date:
                date_value = prediction.date.value
                if isinstance(date_value, str):
                    # Parse the string into a datetime object
                    date_obj = datetime.strptime(date_value, "%Y-%m-%d")
                else:
                    # If it's already a datetime object
                    date_obj = date_value
                # Convert date to MM/DD/YYYY format
                result["date"] = date_obj.strftime("%m/%d/%Y")

            # Extract total amount
            if hasattr(prediction, 'total_amount') and prediction.total_amount:
                result["amount"] = str(prediction.total_amount.value)
            self.progress.emit(100)
            
            # Emit the result
            self.finished.emit(result)
            
        except Exception as e:
            print(f"Error in Mindee processing: {e}")
            # Emit empty result on error
            self.finished.emit({"vendor": "", "date": "", "amount": "", "error": str(e)})

class DateHelper:
    """Helper class for handling date operations."""
    
    @staticmethod
    def parse_date(date_text):
        """Parse a date from text using multiple formats.
        
        Args:
            date_text: The date text to parse.
            
        Returns:
            str: The formatted date in MM/dd/YYYY format, or None if parsing fails.
        """
        if not date_text:
            return None
            
        for date_format in DATE_FORMATS:
            try:
                return datetime.strptime(date_text, date_format).strftime(DATE_FORMAT)
            except ValueError:
                continue
        return None
    
    @staticmethod
    def parse_date_range(start_date_text, end_date_text):
        """Parse a date range from text.
        
        Args:
            start_date_text: The start date text.
            end_date_text: The end date text.
            
        Returns:
            tuple: (start_date, end_date) in MM/dd/YYYY format, or (None, None) if parsing fails.
        """
        start_date = DateHelper.parse_date(start_date_text)
        end_date = DateHelper.parse_date(end_date_text)
        
        if start_date and end_date:
            return start_date, end_date
        return None, None

class TranslationManager:
    """Manages translations for the application."""
    
    # Define translations for all text in the application
    TRANSLATIONS = {
        # Tab names
        "Bill Entry": {"es": "Entrada de Facturas"},
        "Print Page": {"es": "Página de Impresión"},
        "Delete Page": {"es": "Página de Eliminación"},
        "Data": {"es": "Datos"},
        "Settings": {"es": "Configuración"},
        "Photos": {"es": "Fotos"},
        
        # Bill Entry tab
        "Select Date": {"es": "Seleccionar Fecha"},
        "Bill Details": {"es": "Detalles de la Factura"},
        "Enter bill name": {"es": "Ingrese nombre de factura"},
        "Enter price": {"es": "Ingrese precio"},
        "Select Categories": {"es": "Seleccionar Categorías"},
        "Bill Photo": {"es": "Foto de Factura"},
        "Add Photo": {"es": "Agregar Foto"},
        "Scan Receipt": {"es": "Escanear Recibo"},
        "Save Bill": {"es": "Guardar Factura"},
        "Recent Bills": {"es": "Facturas Recientes"},
        
        # Print Page tab
        "Filter Bills by Date Range": {"es": "Filtrar Facturas por Rango de Fechas"},
        "Filter by Date Range": {"es": "Filtrar por Rango de Fechas"},
        "Sort Options": {"es": "Opciones de Ordenamiento"},
        "Sort by Date (Ascending)": {"es": "Ordenar por Fecha (Ascendente)"},
        "Sort by Date (Descending)": {"es": "Ordenar por Fecha (Descendente)"},
        "Actions": {"es": "Acciones"},
        "Print Bills": {"es": "Imprimir Facturas"},
        "Show All Bills": {"es": "Mostrar Todas las Facturas"},
        "Select Year": {"es": "Seleccionar Año"},
        "Bills": {"es": "Facturas"},
        
        # Delete Page tab
        "Search Bills by Date": {"es": "Buscar Facturas por Fecha"},
        "Search": {"es": "Buscar"},
        "Sort Ascending": {"es": "Ordenar Ascendente"},
        "Sort Descending": {"es": "Ordenar Descendente"},
        "Delete Selected": {"es": "Eliminar Seleccionado"},
        
        # Data tab
        "Monthly Expenditure": {"es": "Gastos Mensuales"},
        
        # Settings tab
        "Add New Category": {"es": "Agregar Nueva Categoría"},
        "Enter new category": {"es": "Ingrese nueva categoría"},
        "Add Category": {"es": "Agregar Categoría"},
        "Existing Categories": {"es": "Categorías Existentes"},
        "Delete": {"es": "Eliminar"},
        
        # Photos tab
        "Filter Photos by Date": {"es": "Filtrar Fotos por Fecha"},
        "Filter Photos": {"es": "Filtrar Fotos"},
        "Photo Gallery": {"es": "Galería de Fotos"},
        
        # OCR-related
        "OCR Results": {"es": "Resultados de OCR"},
        "Vendor/Name:": {"es": "Vendedor/Nombre:"},
        "Date:": {"es": "Fecha:"},
        "Amount:": {"es": "Monto:"},
        "Apply these values": {"es": "Aplicar estos valores"},
        "Edit before applying": {"es": "Editar antes de aplicar"},
        "Cancel": {"es": "Cancelar"},
        "Processing Receipt": {"es": "Procesando Recibo"},
        "Extracting information from receipt...": {"es": "Extrayendo información del recibo..."},
        "API Limit Reached": {"es": "Límite de API Alcanzado"},
        "You have reached the monthly limit of 250 pages for the Mindee API. The limit will reset at the beginning of next month.": {"es": "Has alcanzado el límite mensual de 250 páginas para la API de Mindee. El límite se restablecerá al comienzo del próximo mes."},
        "Scan a receipt using OCR. {remaining} pages remaining this month.": {"es": "Escanear un recibo usando OCR. {remaining} páginas restantes este mes."},
        "Mindee API key not set. Right-click to configure API key.": {"es": "Clave de API de Mindee no configurada. Haga clic derecho para configurar la clave de API."},
        "You have reached the monthly limit of 250 pages for the Mindee API.": {"es": "Has alcanzado el límite mensual de 250 páginas para la API de Mindee."},
        
        # Table headers
        "Date": {"es": "Fecha"},
        "Name": {"es": "Nombre"},
        "Price": {"es": "Precio"},
        "Month": {"es": "Mes"},
        "Cash": {"es": "Efectivo"},
        "Not Cash": {"es": "No Efectivo"},
        "Total": {"es": "Total"},
        "Year Total": {"es": "Total Anual"},
        
        # Messages
        "Input Error": {"es": "Error de Entrada"},
        "Please enter date, name, and price.": {"es": "Por favor ingrese fecha, nombre y precio."},
        "Invalid date format. Please use MM/dd/yyyy.": {"es": "Formato de fecha inválido. Use MM/dd/yyyy."},
        "Failed to save bill. Please try again.": {"es": "Error al guardar factura. Intente nuevamente."},
        "Selection Error": {"es": "Error de Selección"},
        "No row selected.": {"es": "Ninguna fila seleccionada."},
        "Failed to delete bill. Please try again.": {"es": "Error al eliminar factura. Intente nuevamente."},
        
        # Date placeholders
        "MM/dd/yyyy": {"es": "MM/dd/aaaa"},
        
        # Other
        "Present Database": {"es": "Base de Datos presente"},
        "Bill Tracker": {"es": "Seguimiento de Facturas"},
        "Language": {"es": "Idioma"},
        "English": {"es": "Inglés"},
        "Spanish": {"es": "Español"},
        "Error": {"es": "Error"}
    }
    
    def __init__(self):
        """Initialize the translation manager with English as default."""
        self.current_language = "en"
        
    def set_language(self, language_code):
        """Set the current language.
        
        Args:
            language_code: Two-letter language code (en, es)
        """
        if language_code in ["en", "es"]:
            self.current_language = language_code
            return True
        return False
        
    def translate(self, text):
        """Translate text to the current language.
        
        Args:
            text: The text to translate
            
        Returns:
            str: Translated text if available, otherwise the original text
        """
        if self.current_language == "en":
            return text
            
        if text in self.TRANSLATIONS and self.current_language in self.TRANSLATIONS[text]:
            return self.TRANSLATIONS[text][self.current_language]
        return text

class UIHelper:
    """Helper class for creating consistent UI components."""
    
    # Static translator instance
    translator = TranslationManager()
    
    @staticmethod
    def translate(text):
        """Translate text using the current language.
        
        Args:
            text: Text to translate
            
        Returns:
            str: Translated text
        """
        return UIHelper.translator.translate(text)
    
    @staticmethod
    def create_button(text, callback=None, height=40):
        """Create a styled button with optional callback.
        
        Args:
            text: Button text
            callback: Function to call when button is clicked
            height: Button height in pixels
            
        Returns:
            QPushButton: The created button
        """
        button = QPushButton(UIHelper.translate(text))
        button.setFixedHeight(height)
        button.setProperty("original_text", text)  # Store original text for translation updates
        if callback:
            button.clicked.connect(callback)
        return button
    
    @staticmethod
    def create_input_field(placeholder, validator=None):
        """Create a styled input field with optional validator.
        
        Args:
            placeholder: Placeholder text
            validator: Optional QValidator for input validation
            
        Returns:
            QLineEdit: The created input field
        """
        input_field = QLineEdit()
        input_field.setPlaceholderText(UIHelper.translate(placeholder))
        input_field.setProperty("original_placeholder", placeholder)  # Store original text for translation updates
        if validator:
            input_field.setValidator(validator)
        return input_field
    
    @staticmethod
    def create_date_input():
        """Create a date input field with consistent formatting.
        
        Returns:
            QLineEdit: The created date input field
        """
        date_input = QLineEdit()
        date_input.setPlaceholderText(UIHelper.translate("MM/dd/yyyy"))
        date_input.setProperty("original_placeholder", "MM/dd/yyyy")  # Store original text for translation updates
        return date_input
    
    @staticmethod
    def create_section_label(text):
        """Create a section label with consistent styling.
        
        Args:
            text: Label text
            
        Returns:
            QLabel: The created label
        """
        label = QLabel(UIHelper.translate(text))
        label.setStyleSheet("font-weight: bold; font-size: 16px; margin-top: 10px;")
        label.setProperty("original_text", text)  # Store original text for translation updates
        return label
    
    @staticmethod
    def create_table(columns, headers=None):
        """Create a styled table with specified columns.
        
        Args:
            columns: Number of columns
            headers: Optional list of column headers
            
        Returns:
            QTableWidget: The created table
        """
        table = QTableWidget(0, columns)
        if headers:
            translated_headers = [UIHelper.translate(header) for header in headers]
            table.setHorizontalHeaderLabels(translated_headers)
            table.setProperty("original_headers", headers)  # Store original headers for translation updates
        table.horizontalHeader().setStretchLastSection(True)
        table.setAlternatingRowColors(True)
        return table
    
    @staticmethod
    def add_section_spacing(layout):
        """Add consistent spacing between sections.
        
        Args:
            layout: The layout to add spacing to
        """
        spacer = QWidget()
        spacer.setFixedHeight(20)
        layout.addWidget(spacer)

class SettingsManager:
    """Handles settings and categories for the bill tracker application."""
    
    def __init__(self):
        """Initialize the settings manager."""
        pass
    
    @staticmethod
    def load_categories():
        """Load categories from the categories.json file.
        
        Returns:
            list: The list of categories.
        """
        try:
            with open("categories.json", "r") as file:
                return json.load(file)
        except FileNotFoundError:
            return DEFAULT_CATEGORIES.copy()
    
    @staticmethod
    def save_categories(categories):
        """Save categories to the categories.json file.
        
        Args:
            categories: The list of categories to save.
        """
        with open("categories.json", "w") as file:
            json.dump(categories, file)

class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end_of_word = False
        self.word = None  # Store the original word

class Trie:
    def __init__(self):
        self.root = TrieNode()
        self.words = []  # Store all words for substring search

    def insert(self, word):
        node = self.root
        for char in word.lower():
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end_of_word = True
        node.word = word  # Store the original word
        self.words.append(word)  # Add word to the list

    def search(self, prefix):
        node = self.root
        for char in prefix.lower():
            if char not in node.children:
                return []
            node = node.children[char]
        return self._find_words_from_node(node)

    def _find_words_from_node(self, node):
        words = []
        if node.is_end_of_word:
            words.append(node.word)
        for char, child_node in node.children.items():
            words.extend(self._find_words_from_node(child_node))
        return words

    def get_suggestions(self, prefix, limit=7):
        # Find words that start with the prefix
        words = self.search(prefix)
        # Find words that contain the prefix as a substring
        similar_words = [word for word in self.words if prefix.lower() in word.lower()]
        # Combine and deduplicate the results
        all_suggestions = list(dict.fromkeys(words + similar_words))
        return all_suggestions[:limit]

class DatabaseManager:
    """Handles all database operations for the bill tracker application."""
    
    def __init__(self):
        """Initialize the database manager with an in-memory database."""
        self.conn = sqlite3.connect(':memory:')  # In-memory database for current session
        self.create_tables()
    
    def create_tables(self):
        """Create the necessary tables if they don't exist."""
        query = """
        CREATE TABLE IF NOT EXISTS bills (
            id INTEGER PRIMARY KEY,
            date TEXT,
            name TEXT,
            price TEXT,
            image TEXT
        )
        """
        self.conn.execute(query)
        self.conn.commit()
    
    def get_db_connection(self, year=None):
        """Get a database connection based on the year.
        
        Args:
            year: The year to get the database for. If None, returns the in-memory database.
            
        Returns:
            sqlite3.Connection: The database connection.
        """
        if year is None or year == "Present Database":
            return self.conn
        else:
            db_name = f"bills_{year}.db"
            conn = sqlite3.connect(db_name)
            # Ensure the table exists in the year-specific database
            query = """
            CREATE TABLE IF NOT EXISTS bills (
                id INTEGER PRIMARY KEY,
                date TEXT,
                name TEXT,
                price TEXT,
                image TEXT
            )
            """
            conn.execute(query)
            conn.commit()
            return conn
    
    def save_bill(self, date, name, price, image_path=None):
        """Save a bill to both the year-specific database and in-memory database.
        
        Args:
            date: The date of the bill.
            name: The name of the bill.
            price: The price of the bill.
            image_path: The path to the bill's image, if any.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Format the price as currency
            formatted_price = f"${float(price):.2f}"
            
            # Determine the year for the database
            year = datetime.strptime(date, DATE_FORMAT).year
            db_name = f"bills_{year}.db"
            
            # Save to year-specific database
            conn = sqlite3.connect(db_name)
            self.create_tables_in_db(conn)
            
            # Save to the year-specific database
            query = "INSERT INTO bills (date, name, price) VALUES (?, ?, ?)"
            conn.execute(query, (date, name, formatted_price))
            conn.commit()
            conn.close()
            
            # Save to the in-memory database
            self.conn.execute(query, (date, name, formatted_price))
            self.conn.commit()
            
            # Handle image if provided
            image_filename = None
            if image_path:
                image_folder = "bill_images"
                os.makedirs(image_folder, exist_ok=True)
                image_filename = f"{date.replace('/', '-')}_{name}.jpg"
                dest_path = os.path.join(image_folder, image_filename)
                shutil.copy(image_path, dest_path)
                
                # Update the database with the image filename
                update_query = "UPDATE bills SET image = ? WHERE date = ? AND name = ? AND price = ?"
                self.conn.execute(update_query, (image_filename, date, name, formatted_price))
                self.conn.commit()
                
                # Also update the year-specific database
                conn = sqlite3.connect(db_name)
                conn.execute(update_query, (image_filename, date, name, formatted_price))
                conn.commit()
                conn.close()
                
            return True
        except Exception as e:
            print(f"Error saving bill: {e}")
            return False
    
    def create_tables_in_db(self, conn):
        """Create necessary tables in the provided database connection."""
        query = """
        CREATE TABLE IF NOT EXISTS bills (
            id INTEGER PRIMARY KEY,
            date TEXT,
            name TEXT,
            price TEXT,
            image TEXT
        )
        """
        conn.execute(query)
        conn.commit()
    
    def get_bills(self, year=None, start_date=None, end_date=None):
        """Get bills from the database with optional filtering.
        
        Args:
            year: The year to get bills from. If None, uses the in-memory database.
            start_date: Optional start date for filtering.
            end_date: Optional end date for filtering.
            
        Returns:
            list: List of bill tuples (date, name, price).
        """
        conn = self.get_db_connection(year)
        
        if start_date and end_date:
            query = "SELECT date, name, price FROM bills WHERE date BETWEEN ? AND ?"
            cursor = conn.execute(query, (start_date, end_date))
        else:
            query = "SELECT date, name, price FROM bills"
            cursor = conn.execute(query)
        
        bills = cursor.fetchall()
        
        # Close the connection if it's not the in-memory database
        if year is not None and year != "Present Database":
            conn.close()
            
        return bills
    
    def get_bill_images(self, year=None, start_date=None, end_date=None):
        """Get bill images from the database with optional date filtering.
        
        Args:
            year: The year to get bills from. If None, uses the in-memory database.
            start_date: Optional start date for filtering.
            end_date: Optional end date for filtering.
            
        Returns:
            list: List of tuples containing (date, image_filename).
        """
        conn = self.get_db_connection(year)
        
        if start_date and end_date:
            query = "SELECT date, image FROM bills WHERE image IS NOT NULL AND date BETWEEN ? AND ?"
            cursor = conn.execute(query, (start_date, end_date))
        else:
            query = "SELECT date, image FROM bills WHERE image IS NOT NULL"
            cursor = conn.execute(query)
            
        results = cursor.fetchall()
        
        # Close the connection if it's not the in-memory database
        if year is not None and year != "Present Database":
            conn.close()
            
        return results
    
    def delete_bill(self, year, date, name, price):
        """Delete a bill from the database.
        
        Args:
            year: The year of the database to delete from.
            date: The date of the bill.
            name: The name of the bill.
            price: The price of the bill.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            conn = sqlite3.connect(f"bills_{year}.db")
            conn.execute("DELETE FROM bills WHERE date = ? AND name = ? AND price = ?", (date, name, price))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error deleting bill: {e}")
            return False
    
    def get_existing_databases(self):
        """Get a list of existing year-specific databases.
        
        Returns:
            list: List of years for which databases exist.
        """
        years = []
        for file in os.listdir('.'):
            if file.startswith('bills_') and file.endswith('.db'):
                year = file[6:10]
                if year.isdigit():
                    years.append(year)
        return years
    
    def get_monthly_totals(self, year):
        """Calculate monthly totals for a specific year.
        
        Args:
            year: The year to calculate totals for.
            
        Returns:
            dict: Dictionary of monthly totals.
        """
        conn = self.get_db_connection(year)
        
        query = "SELECT date, price, name FROM bills"
        cursor = conn.execute(query)
        
        # Initialize monthly totals
        monthly_totals = {month: {"cash": 0, "not_cash": 0, "total": 0} for month in range(1, 13)}
        yearly_totals = {"cash": 0, "not_cash": 0, "total": 0}
        
        for row in cursor:
            date = row[0]
            price = float(row[1].replace("$", ""))
            name = row[2]
            
            # Extract the month from the date
            month = datetime.strptime(date, DATE_FORMAT).month
            
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
            
        # Close the connection if it's not the in-memory database
        if year is not None and year != "Present Database":
            conn.close()
            
        return monthly_totals, yearly_totals

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

class MindeeAPIConfigDialog(QDialog):
    """Dialog for configuring Mindee API key."""
    
    def __init__(self, parent=None):
        """Initialize the dialog for configuring Mindee API key."""
        super().__init__(parent)
        
        self.setWindowTitle(UIHelper.translate("Configure Mindee API"))
        self.setFixedWidth(500)
        
        # Create layout
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Add explanation
        info_label = QLabel(UIHelper.translate(
            "To use the Mindee Receipt OCR API, you need to enter your API key. "
            "You can get an API key by signing up at https://mindee.com."
        ))
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # API key input
        key_layout = QHBoxLayout()
        key_label = QLabel(UIHelper.translate("API Key:"))
        key_layout.addWidget(key_label)
        
        self.key_input = QLineEdit()
        if MindeeHelper.api_key:
            self.key_input.setText(MindeeHelper.api_key)
        self.key_input.setEchoMode(QLineEdit.Password)  # Hide the API key for security
        key_layout.addWidget(self.key_input)
        
        layout.addLayout(key_layout)
        
        # Show/hide API key checkbox
        self.show_key_checkbox = QCheckBox(UIHelper.translate("Show API Key"))
        self.show_key_checkbox.toggled.connect(self.toggle_key_visibility)
        layout.addWidget(self.show_key_checkbox)
        
        # Test button
        self.test_button = QPushButton(UIHelper.translate("Test API Key"))
        self.test_button.clicked.connect(self.test_api_key)
        layout.addWidget(self.test_button)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.status_label)
        
        # Add buttons
        buttons_layout = QHBoxLayout()
        
        self.save_button = QPushButton(UIHelper.translate("Save"))
        self.save_button.clicked.connect(self.save_api_key)
        buttons_layout.addWidget(self.save_button)
        
        self.cancel_button = QPushButton(UIHelper.translate("Cancel"))
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)
        
        layout.addLayout(buttons_layout)
    
    def toggle_key_visibility(self, checked):
        """Toggle the visibility of the API key input."""
        if checked:
            self.key_input.setEchoMode(QLineEdit.Normal)
        else:
            self.key_input.setEchoMode(QLineEdit.Password)
    
    def test_api_key(self):
        """Test if the specified API key works with Mindee."""
        api_key = self.key_input.text()
        
        if not api_key:
            self.status_label.setText(UIHelper.translate("Please enter an API key"))
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            return
        
        # Try to initialize the client with the API key
        try:
            # Set the API key temporarily
            client = Client(api_key=api_key)
            
            # Success
            self.status_label.setText(UIHelper.translate("API Key is valid"))
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            
        except Exception as e:
            # Failure
            self.status_label.setText(UIHelper.translate("API Key validation failed") + f": {str(e)}")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
    
    def save_api_key(self):
        """Save the Mindee API key if valid."""
        api_key = self.key_input.text()
        
        if not api_key:
            self.status_label.setText(UIHelper.translate("Please enter an API key"))
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            return
        
        # Set the API key
        if MindeeHelper.set_api_key(api_key):
            # Save the API key to a file
            try:
                with open('mindee_api_key.txt', 'w') as f:
                    f.write(api_key)
            except Exception as e:
                print(f"Error saving Mindee API key: {e}")
            
            # API key set successfully
            self.accept()
        else:
            self.status_label.setText(UIHelper.translate("Failed to set API key"))
            self.status_label.setStyleSheet("color: red; font-weight: bold;")

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
        self.apply_styles()

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
        configure_action.triggered.connect(self.show_mindee_config_dialog)
        
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

    def init_settings_page(self):
        """Initialize the Settings tab for managing categories."""
        self.settings_page = QWidget()
        self.settings_layout = QVBoxLayout()
        self.settings_page.setLayout(self.settings_layout)

        # Section: Add Category
        self.settings_layout.addWidget(UIHelper.create_section_label("Add New Category"))

        # New category input
        self.new_category_input = UIHelper.create_input_field("Enter new category")
        self.settings_layout.addWidget(self.new_category_input)

        # Add category button
        self.add_category_button = UIHelper.create_button("Add Category", self.add_new_category)
        self.settings_layout.addWidget(self.add_category_button)
        
        UIHelper.add_section_spacing(self.settings_layout)
        
        # Section: Existing Categories
        self.settings_layout.addWidget(UIHelper.create_section_label("Existing Categories"))

        # Category list layout (populated in update_settings_page)
        self.category_list_layout = QVBoxLayout()
        self.settings_layout.addLayout(self.category_list_layout)

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

    def apply_styles(self):
        """Apply stylesheet to the application for consistent styling."""
        self.setStyleSheet("""
            QWidget {
                font-size: 13px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            
            QMainWindow {
                background-color: #f5f7fa;
            }
            
            /* Tab styling */
            QTabWidget::pane {
                border: none;
                background-color: transparent;
                border-radius: 0;
            }
            
            QTabBar::tab {
                background-color: transparent;
                color: #718096;
                padding: 10px 18px;
                margin-right: 2px;
                margin-bottom: -1px;
                font-weight: bold;
                border-bottom: 3px solid transparent;
            }
            
            QTabBar::tab:selected {
                color: #3b82f6;
                border-bottom: 3px solid #3b82f6;
            }
            
            QTabBar::tab:hover:!selected {
                color: #4b5563;
                border-bottom: 3px solid #cbd5e1;
            }
            
            /* Card styling */
            #card {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #e2e8f0;
                padding: 10px;
            }
            
            #photo-card {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #e2e8f0;
                padding: 8px;
                margin: 5px;
            }
            
            #stat-card {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #e2e8f0;
                padding: 15px;
                margin: 5px;
                min-height: 80px;
            }
            
            /* Form elements */
            QLineEdit {
                padding: 8px 10px;
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                background-color: white;
                selection-background-color: #3b82f6;
                min-height: 25px;
            }
            
            QLineEdit:focus {
                border: 1px solid #3b82f6;
                outline: 0;
            }
            
            #form-group {
                background-color: transparent;
                margin-bottom: 10px;
                max-width: 400px;
            }
            
            #form-label {
                color: #4b5563;
                font-weight: bold;
                margin-bottom: 5px;
            }
            
            /* Dashboard stats */
            #stat-number {
                font-size: 24px;
                font-weight: bold;
                color: #3b82f6;
            }
            
            #card-title {
                font-size: 18px;
                font-weight: bold;
                color: #1e293b;
                margin-bottom: 15px;
            }
            
            /* Buttons styling */
            QPushButton {
                background-color: #e2e8f0;
                color: #4b5563;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
                min-height: 35px;
            }
            
            QPushButton:hover {
                background-color: #cbd5e1;
                color: #1e293b;
            }
            
            QPushButton:pressed {
                background-color: #94a3b8;
            }
            
            #primary-action {
                background-color: #3b82f6;
                color: white;
            }
            
            #primary-action:hover {
                background-color: #2563eb;
                color: white;
            }
            
            #primary-action:pressed {
                background-color: #1d4ed8;
            }
            
            #danger-button {
                background-color: #f87171;
                color: white;
            }
            
            #danger-button:hover {
                background-color: #ef4444;
            }
            
            #text-button {
                background-color: transparent;
                color: #3b82f6;
                font-weight: normal;
                border: none;
                text-decoration: underline;
                padding: 0;
                min-height: 20px;
            }
            
            #text-button:hover {
                color: #2563eb;
                background-color: transparent;
            }
            
            /* Category chips */
            #category-chip {
                background-color: #e2e8f0;
                color: #4b5563;
                border-radius: 15px;
                padding: 5px 10px;
                font-size: 12px;
                text-align: center;
                min-width: 80px;
            }
            
            #category-chip:checked {
                background-color: #3b82f6;
                color: white;
            }
            
            /* Photo preview */
            #photo-preview {
                background-color: #f1f5f9;
                border: 1px dashed #cbd5e1;
                border-radius: 4px;
            }
            
            /* Currency symbol */
            #currency-symbol {
                color: #64748b;
                font-weight: bold;
                margin-right: 0;
                padding-top: 8px;
            }
            
            /* Table styling */
            QTableWidget {
                background-color: white;
                alternate-background-color: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 4px;
                gridline-color: #e2e8f0;
            }
            
            QTableWidget::item {
                padding: 5px;
                border-bottom: 1px solid #f1f5f9;
            }
            
            QTableWidget::item:selected {
                background-color: #bfdbfe;
                color: #1e293b;
            }
            
            QHeaderView::section {
                background-color: #f1f5f9;
                color: #475569;
                padding: 8px;
                border: none;
                border-bottom: 1px solid #cbd5e1;
                font-weight: bold;
            }
            
            /* Calendar widget */
            QCalendarWidget {
                background-color: white;
                border: 1px solid #cbd5e1;
                border-radius: 4px;
            }
            
            QCalendarWidget QToolButton {
                background-color: #f1f5f9;
                color: #475569;
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                padding: 4px;
            }
            
            QCalendarWidget QMenu {
                background-color: white;
                border: 1px solid #cbd5e1;
                border-radius: 4px;
            }
            
            QCalendarWidget QAbstractItemView:enabled {
                background-color: white;
                color: #1e293b;
                selection-background-color: #3b82f6;
                selection-color: white;
            }
            
            /* Dropdown styling */
            QComboBox {
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                padding: 8px;
                background-color: white;
                min-height: 25px;
            }
            
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid #cbd5e1;
            }
            
            QComboBox QAbstractItemView {
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                selection-background-color: #3b82f6;
            }
            
            /* Scrollbars */
            QScrollBar:vertical {
                border: none;
                background: #f1f5f9;
                width: 8px;
                margin: 0px 0px 0px 0px;
            }
            
            QScrollBar::handle:vertical {
                background: #cbd5e1;
                min-height: 30px;
                border-radius: 4px;
            }
            
            QScrollBar::handle:vertical:hover {
                background: #94a3b8;
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            
            QScrollBar:horizontal {
                border: none;
                background: #f1f5f9;
                height: 8px;
                margin: 0px 0px 0px 0px;
            }
            
            QScrollBar::handle:horizontal {
                background: #cbd5e1;
                min-width: 30px;
                border-radius: 4px;
            }
            
            QScrollBar::handle:horizontal:hover {
                background: #94a3b8;
            }
            
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
            
            /* List widget */
            QListWidget {
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                background-color: white;
                selection-background-color: #bfdbfe;
                selection-color: #1e293b;
                outline: none;
            }
            
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #f1f5f9;
            }
            
            QListWidget::item:selected {
                background-color: #bfdbfe;
                color: #1e293b;
            }
            
            QListWidget::item:hover {
                background-color: #f1f5f9;
            }
            
            /* Notification area */
            #notification-area {
                font-weight: bold;
                padding: 10px;
                margin: 0px;
            }
            
            /* Checkbox styling */
            QCheckBox {
                spacing: 5px;
            }
            
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 1px solid #cbd5e1;
                border-radius: 3px;
                background-color: white;
            }
            
            QCheckBox::indicator:checked {
                background-color: #3b82f6;
                border-color: #3b82f6;
            }
            
            /* Mobile responsiveness - base styles */
            @media (max-width: 800px) {
                QLineEdit, QComboBox, QPushButton {
                    min-height: 40px;  /* Larger touch targets */
                }
                
                QTableWidget::item {
                    padding: 8px;  /* More spacing for touch */
                }
            }
        """)

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