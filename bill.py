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
from PyQt5.QtGui import QPixmap

from PyQt5.QtCore import Qt, QThread, pyqtSignal
import sqlite3
import shutil

# Try to import Mindee API
try:
    # from mindee import Client, PredictResponse, product
    from mindee import Client, product
    print("Mindee import successful")
    HAS_OCR = True
except ImportError as e:
    print(f"Mindee import failed: {e}")
    HAS_OCR = False

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
    
    @staticmethod
    def is_available():
        """Check if Mindee OCR is available (API key is set).
        
        Returns:
            bool: True if Mindee is available, False otherwise.
        """
        return HAS_OCR and MindeeHelper.api_key is not None
    
    @staticmethod
    def set_api_key(api_key):
        """Set the Mindee API key.
        
        Args:
            api_key: The API key to use for Mindee.
            
        Returns:
            bool: True if API key was set successfully, False otherwise.
        """
        try:
            MindeeHelper.api_key = api_key
            MindeeHelper.mindee_client = Client(api_key=api_key)
            return True
        except Exception as e:
            print(f"Error setting Mindee API key: {e}")
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
            
            # Open the input file
            self.progress.emit(30)
            
            # Create a receipt prediction using Mindee API
            input_doc = MindeeHelper.mindee_client.source_from_path(self.image_path)
            self.progress.emit(50)
            
            # Parse receipt using the Receipt API - use the client to parse, not the input_doc
            api_response = MindeeHelper.mindee_client.parse(product.ReceiptV5, input_doc)
            self.progress.emit(80)
            
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
            self.finished.emit({"vendor": "", "date": "", "amount": ""})

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
        "OCR Not Available": {"es": "OCR No Disponible"},
        "OCR functionality requires pytesseract, Pillow, and OpenCV. Please install these packages to use receipt scanning.": 
            {"es": "La funcionalidad de OCR requiere pytesseract, Pillow y OpenCV. Por favor, instale estos paquetes para usar el escaneo de recibos."},
        "Configure Tesseract Path": {"es": "Configurar Ruta de Tesseract"},
        "Set Custom Tesseract Path": {"es": "Establecer Ruta Personalizada de Tesseract"},
        "Tesseract Path:": {"es": "Ruta de Tesseract:"},
        "Select Tesseract Executable": {"es": "Seleccionar Ejecutable de Tesseract"},
        "Path validated successfully": {"es": "Ruta validada con éxito"},
        "Invalid Tesseract path": {"es": "Ruta de Tesseract inválida"},
        "Tesseract Test": {"es": "Prueba de Tesseract"},
        "Test OCR": {"es": "Probar OCR"},
        "OCR Testing Successful": {"es": "Prueba de OCR Exitosa"},
        "OCR Test Failed": {"es": "Prueba de OCR Fallida"},
        "Save": {"es": "Guardar"},
        "Tesseract Not Found": {"es": "Tesseract No Encontrado"},
        "OCR Error": {"es": "Error de OCR"},
        "Tesseract OCR not found. Right-click to configure Tesseract path.": {"es": "Tesseract OCR no encontrado. Haga clic derecho para configurar la ruta de Tesseract."},
        "Tesseract OCR is not installed or not in your PATH. Would you like to configure the Tesseract path manually?": {"es": "Tesseract OCR no está instalado o no está en su PATH. ¿Desea configurar la ruta de Tesseract manualmente?"},
        "An error occurred during OCR processing:": {"es": "Ocurrió un error durante el procesamiento OCR:"},
        "Please enter a Tesseract path": {"es": "Por favor ingrese una ruta de Tesseract"},
        "Failed to set Tesseract path": {"es": "Error al establecer la ruta de Tesseract"},
        "If Tesseract OCR is installed but not detected automatically, you can set the path to the executable manually below.": {"es": "Si Tesseract OCR está instalado pero no se detecta automáticamente, puede establecer la ruta al ejecutable manualmente a continuación."},
        
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
        
        # Categories (default)
        "Mortgage": {"es": "Mortgage"},
        "Food": {"es": "Food"},
        "Gas": {"es": "Gas"},
        "Mechanic": {"es": "Mechanic"},
        "Work Clothes": {"es": "Clothes"},
        "Materials": {"es": "Materials"},
        "Miscellaneous": {"es": "Miscellaneous"},
        "Doctor": {"es": "Doctor"},
        "Equipment & Rent": {"es": "Equipment & Rent"},
        "Cash": {"es": "Cash"},
        
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
    
    def get_bill_images(self, start_date=None, end_date=None):
        """Get bill images from the database with optional date filtering.
        
        Args:
            start_date: Optional start date for filtering.
            end_date: Optional end date for filtering.
            
        Returns:
            list: List of tuples containing (date, image_filename).
        """
        if start_date and end_date:
            query = "SELECT date, image FROM bills WHERE image IS NOT NULL AND date BETWEEN ? AND ?"
            cursor = self.conn.execute(query, (start_date, end_date))
        else:
            query = "SELECT date, image FROM bills WHERE image IS NOT NULL"
            cursor = self.conn.execute(query)
            
        return cursor.fetchall()
    
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
        """Get the dialog result.
        
        Returns:
            dict: Dictionary of OCR results with acceptance status.
        """
        return self.result

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
        self.init_print_page()
        self.init_bill_page()
        self.init_settings_page()
        self.init_data_page()
        self.init_delete_page()
        self.init_photos_page()

        # Add pages to tab widget
        self.tab_widget.addTab(self.bill_page, UIHelper.translate("Bill Entry"))
        self.tab_widget.addTab(self.print_page, UIHelper.translate("Print Page"))
        self.tab_widget.addTab(self.delete_page, UIHelper.translate("Delete Page"))
        self.tab_widget.addTab(self.data_page, UIHelper.translate("Data"))
        self.tab_widget.addTab(self.settings_page, UIHelper.translate("Settings"))
        self.tab_widget.addTab(self.photos_page, UIHelper.translate("Photos"))
        
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
    
    def setup_ocr(self):
        """Set up OCR functionality by loading Mindee API key."""
        if not HAS_OCR:
            return
        
        # Try to load the API key
        MindeeHelper.load_api_key()
    
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
        self.tab_widget.setTabText(0, UIHelper.translate("Bill Entry"))
        self.tab_widget.setTabText(1, UIHelper.translate("Print Page"))
        self.tab_widget.setTabText(2, UIHelper.translate("Delete Page"))
        self.tab_widget.setTabText(3, UIHelper.translate("Data"))
        self.tab_widget.setTabText(4, UIHelper.translate("Settings"))
        self.tab_widget.setTabText(5, UIHelper.translate("Photos"))
        
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
            
        # Update category buttons
        for category, button in self.category_buttons.items():
            button.setText(UIHelper.translate(category))

    def update_scan_button_state(self):
        """Update the scan button state based on OCR availability."""
        is_ocr_available = MindeeHelper.is_available()
        self.scan_button.setEnabled(is_ocr_available)
        
        if not is_ocr_available:
            if not HAS_OCR:
                # OCR libraries not installed
                self.scan_button.setToolTip(UIHelper.translate(
                    "OCR functionality requires Mindee API. Please install the Mindee package to use receipt scanning."
                ))
            else:
                # OCR libraries installed but API key not set
                self.scan_button.setToolTip(UIHelper.translate(
                    "Mindee API key not set. Right-click to configure API key."
                ))
    
    def show_scan_context_menu(self, position):
        """Show a context menu for the scan button with OCR configuration options."""
        menu = QMenu(self)
        
        # Add an action to configure API key
        configure_action = menu.addAction(UIHelper.translate("Configure Mindee API Key"))
        configure_action.triggered.connect(self.show_mindee_config_dialog)
        
        # Show the menu at the requested position
        menu.exec_(self.scan_button.mapToGlobal(position))
    
    def show_mindee_config_dialog(self):
        """Show the dialog for configuring Mindee API key."""
        dialog = MindeeAPIConfigDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            # Update the scan button state
            self.update_scan_button_state()
    
    def scan_receipt(self):
        """Scan a receipt using OCR to extract bill information."""
        # Check if OCR is available
        if not HAS_OCR:
            QMessageBox.warning(
                self, 
                UIHelper.translate("OCR Not Available"), 
                UIHelper.translate("OCR functionality requires Mindee API. Please install the Mindee package to use receipt scanning.")
            )
            return
        
        # Check if API key is set
        if not MindeeHelper.is_available():
            result = QMessageBox.question(
                self, 
                UIHelper.translate("API Key Not Set"), 
                UIHelper.translate("Mindee API key is not set. Would you like to configure it now?"),
                QMessageBox.Yes | QMessageBox.No
            )
                
            if result == QMessageBox.Yes:
                self.show_mindee_config_dialog()
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
        """Handle the results from OCR processing.
        
        Args:
            ocr_results: Dictionary of OCR results (vendor, date, amount)
            progress_dialog: Progress dialog to close
        """
        # Close the progress dialog
        progress_dialog.accept()
        
        # Show confirmation dialog with results
        dialog = OCRResultsDialog(self, ocr_results)
        if dialog.exec_() == QDialog.Accepted:
            result = dialog.get_result()
            
            if result["accepted"]:
                # Apply the values to the form
                if result["date"]:
                    self.date_input.setText(result["date"])
                
                if result["vendor"]:
                    self.name_input.setText(result["vendor"])
                
                if result["amount"]:
                    self.price_input.setText(result["amount"])
                
                # If edit is needed, focus on the first field that needs editing
                if result.get("edit_needed", False):
                    if not result["date"]:
                        self.date_input.setFocus()
                    elif not result["vendor"]:
                        self.name_input.setFocus()
                    elif not result["amount"]:
                        self.price_input.setFocus()
                    else:
                        # Focus on vendor field for standard editing
                        self.name_input.setFocus()
    
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
        self.clear_layout(self.scroll_layout)  # Clear previous images
        
        # Get all bill images
        bill_images = self.db_manager.get_bill_images()
        
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
        
        # Get filtered bill images
        bill_images = self.db_manager.get_bill_images(start_date, end_date)
        
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
        
        # Update the Main Page year selector
        for year in years:
            if year not in [self.year_selector.itemText(i) for i in range(self.year_selector.count())]:
                self.year_selector.addItem(year)
            
            # Update the Data Page year selector
            if year not in [self.data_year_selector.itemText(i) for i in range(self.data_year_selector.count())]:
                self.data_year_selector.addItem(year)
            
            # Update the Delete Page year selector
            if year not in [self.delete_year_selector.itemText(i) for i in range(self.delete_year_selector.count())]:
                self.delete_year_selector.addItem(year)
    
    def load_bills(self):
        """Load bills into the bill table based on the selected year."""
        self.bill_table.setRowCount(0)  # Clear the table
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
        if self.date_input.text():
            date_text = self.date_input.text()
            for date_format in DATE_FORMATS:
                try:
                    date = datetime.strptime(date_text, date_format).strftime(DATE_FORMAT)
                    break
                except ValueError:
                    continue
            else:
                QMessageBox.warning(self, UIHelper.translate("Input Error"), 
                                   UIHelper.translate("Invalid date format. Please use MM/dd/yyyy."))
                return
        else:
            date = self.calendar.selectedDate().toString("MM/dd/yyyy")
        
        name = self.name_input.text()
        price = self.price_input.text()

        # Check if any field is empty
        if not date or not name or not price:
            QMessageBox.warning(self, UIHelper.translate("Input Error"), 
                               UIHelper.translate("Please enter date, name, and price."))
            return
        
        # Save the bill using the database manager
        success = self.db_manager.save_bill(date, name, price, self.selected_image_path)
        
        if success:
            # Refresh the bill tables
            self.load_bills()
            self.load_present_bills()
            
            # Update year selectors after saving
            self.load_existing_databases()
            
            # Clear selected categories and update name input
            self.selected_categories = []
            
            # Clear inputs after saving
            self.price_input.clear()
            self.name_input.clear()
            self.date_input.clear()
            
            # Clear selected image
            self.selected_image_path = None
            self.image_preview.clear()
        else:
            QMessageBox.critical(self, UIHelper.translate("Error"), 
                                UIHelper.translate("Failed to save bill. Please try again."))
    
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
                font-size: 12px;
                font-family: Arial, sans-serif;
            }
            
            QMainWindow {
                background-color: #f8f9fa;
            }
            
            QTabWidget::pane {
                border: 1px solid #ddd;
                background-color: white;
                border-radius: 4px;
            }
            
            QTabBar::tab {
                background-color: #e9ecef;
                color: #495057;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                border: 1px solid #ddd;
                border-bottom: none;
            }
            
            QTabBar::tab:selected {
                background-color: white;
                border-bottom-color: white;
                color: #007bff;
                font-weight: bold;
            }
            
            QLineEdit {
                padding: 8px;
                border: 1px solid #ced4da;
                border-radius: 4px;
                background-color: white;
                selection-background-color: #007bff;
            }
            
            QLineEdit:focus {
                border: 1px solid #80bdff;
                outline: 0;
                /* Remove box-shadow as it's not supported in PyQt CSS */
            }
            
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
                min-height: 35px;
            }
            
            QPushButton:hover {
                background-color: #0069d9;
                cursor: pointer;
            }
            
            QPushButton:pressed {
                background-color: #0062cc;
            }
            
            QTableWidget {
                background-color: white;
                alternate-background-color: #f8f9fa;
                border: 1px solid #ddd;
                border-radius: 4px;
                gridline-color: #ddd;
            }
            
            QTableWidget::item {
                padding: 4px;
            }
            
            QTableWidget::item:selected {
                background-color: #007bff;
                color: white;
            }
            
            QHeaderView::section {
                background-color: #e9ecef;
                color: #495057;
                padding: 8px;
                border: 1px solid #ddd;
                font-weight: bold;
            }
            
            QCalendarWidget {
                background-color: white;
                border: 1px solid #ddd;
            }
            
            QCalendarWidget QToolButton {
                background-color: #e9ecef;
                color: #495057;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 4px;
            }
            
            QCalendarWidget QMenu {
                background-color: white;
                border: 1px solid #ddd;
            }
            
            QCalendarWidget QAbstractItemView:enabled {
                background-color: white;
                color: #212529;
                selection-background-color: #007bff;
                selection-color: white;
            }
            
            QComboBox {
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 8px;
                background-color: white;
            }
            
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid #ced4da;
            }
            
            QComboBox QAbstractItemView {
                border: 1px solid #ced4da;
                selection-background-color: #007bff;
            }
            
            QScrollArea {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }
            
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
                alternate-background-color: #f8f9fa;
            }
            
            QListWidget::item {
                padding: 4px;
            }
            
            QListWidget::item:selected {
                background-color: #007bff;
                color: white;
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
        with open('unique_names.json', 'r') as file:
            names = json.load(file)
        for name in names:
            self.trie.insert(name)

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
        self.bill_layout = QVBoxLayout()
        self.bill_page.setLayout(self.bill_layout)

        # Section: Date Selection
        self.bill_layout.addWidget(UIHelper.create_section_label("Select Date"))
        
        # Calendar
        self.calendar = QCalendarWidget()
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        self.bill_layout.addWidget(self.calendar)

        # Manual date input
        self.date_input = UIHelper.create_date_input()
        self.bill_layout.addWidget(self.date_input)
        
        UIHelper.add_section_spacing(self.bill_layout)
        
        # Section: Bill Details
        self.bill_layout.addWidget(UIHelper.create_section_label("Bill Details"))

        # Name input
        self.name_input = UIHelper.create_input_field("Enter bill name")
        self.name_input.textChanged.connect(self.show_autocomplete_suggestions)
        self.bill_layout.addWidget(self.name_input)

        # Autocomplete suggestions list
        self.suggestions_list = QListWidget()
        self.suggestions_list.setFixedHeight(150)
        self.suggestions_list.itemClicked.connect(self.select_suggestion)
        self.bill_layout.addWidget(self.suggestions_list)

        # Amount input
        self.price_input = UIHelper.create_input_field("Enter price")
        self.bill_layout.addWidget(self.price_input)
        
        UIHelper.add_section_spacing(self.bill_layout)
        
        # Section: Categories
        self.bill_layout.addWidget(UIHelper.create_section_label("Select Categories"))
        
        # Category buttons
        self.category_buttons = {}
        self.categories = self.predefined_order
        self.category_layout = QGridLayout()
        
        for i, category in enumerate(self.categories):
            button = UIHelper.create_button(category, partial(self.add_category, category))
            self.category_layout.addWidget(button, i // 5, i % 5)
            self.category_buttons[category] = button
            
        self.bill_layout.addLayout(self.category_layout)
        
        UIHelper.add_section_spacing(self.bill_layout)
        
        # Section: Add Photo
        self.bill_layout.addWidget(UIHelper.create_section_label("Bill Photo"))

        # Image buttons layout
        image_buttons_layout = QHBoxLayout()
        
        # Image selection button
        self.image_button = UIHelper.create_button("Add Photo", self.select_photo)
        image_buttons_layout.addWidget(self.image_button)
        
        # OCR scan button (if OCR is available)
        self.scan_button = UIHelper.create_button("Scan Receipt", self.scan_receipt)
        self.scan_button.setContextMenuPolicy(Qt.CustomContextMenu)
        self.scan_button.customContextMenuRequested.connect(self.show_scan_context_menu)
        image_buttons_layout.addWidget(self.scan_button)
        
        # Check OCR availability and update the scan button state
        self.update_scan_button_state()
        
        self.bill_layout.addLayout(image_buttons_layout)

        # Image preview
        self.image_preview = QLabel()
        self.image_preview.setFixedSize(200, 200)
        self.image_preview.setScaledContents(True)
        self.bill_layout.addWidget(self.image_preview)
        
        UIHelper.add_section_spacing(self.bill_layout)
        
        # Section: Save
        self.save_button = UIHelper.create_button("Save Bill", self.save_bill)
        self.bill_layout.addWidget(self.save_button)
        
        UIHelper.add_section_spacing(self.bill_layout)
        
        # Section: Recent Bills
        self.bill_layout.addWidget(UIHelper.create_section_label("Recent Bills"))
        
        # Table to display bills (only present database)
        self.present_bill_table = UIHelper.create_table(3, ["Date", "Name", "Price"])
        self.bill_layout.addWidget(self.present_bill_table)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BillTracker()
    window.show()
    sys.exit(app.exec_())