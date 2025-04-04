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
        "Dashboard": {"es": "Panel Principal"},
        "Manage Bills": {"es": "Administrar Facturas"},
        "Reports": {"es": "Informes"},
        
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
        "Amount": {"es": "Monto"},
        "Bill Name": {"es": "Nombre de Factura"},
        "Categories": {"es": "Categorías"},
        "Receipt Photo": {"es": "Foto de Recibo"},
        "Clear Photo": {"es": "Borrar Foto"},
        "Select": {"es": "Seleccionar"},
        "Photo cleared": {"es": "Foto borrada"},
        "Date": {"es": "Fecha"},
        "New Bill": {"es": "Nueva Factura"},
        
        # Dashboard tab
        "Welcome to Bill Tracker": {"es": "Bienvenido al Seguimiento de Facturas"},
        "Search all bills...": {"es": "Buscar todas las facturas..."},
        "Bills This Month": {"es": "Facturas Este Mes"},
        "Total This Month": {"es": "Total Este Mes"},
        "Top Category": {"es": "Categoría Principal"},
        "Quick Actions": {"es": "Acciones Rápidas"},
        "Add New Bill": {"es": "Agregar Nueva Factura"},
        "Print Reports": {"es": "Imprimir Informes"},
        "View Analytics": {"es": "Ver Análisis"},
        "View All": {"es": "Ver Todos"},
        
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
        
        # Manage Bills tab
        "All Bills": {"es": "Todas las Facturas"},
        "Filter Bills": {"es": "Filtrar Facturas"},
        "Date Range:": {"es": "Rango de Fechas:"},
        "to": {"es": "hasta"},
        "Apply": {"es": "Aplicar"},
        
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
        "You have reached the monthly limit of 250 pages for the Mindee API. Would you like to scan the image without OCR processing?": {"es": "Has alcanzado el límite mensual de 250 páginas para la API de Mindee. ¿Deseas escanear la imagen sin procesamiento OCR?"},
        "Configure Mindee API Key": {"es": "Configurar Clave de API de Mindee"},
        "Just Scan (No OCR)": {"es": "Solo Escanear (Sin OCR)"},
        "Image scanned and saved (no OCR processing).": {"es": "Imagen escaneada y guardada (sin procesamiento OCR)."},
        "OCR Processing Error": {"es": "Error de Procesamiento OCR"},
        "Failed to extract information from receipt. The image was saved.": {"es": "No se pudo extraer información del recibo. La imagen fue guardada."},
        "Mindee API limit reached. The image was saved but no data was extracted.": {"es": "Se alcanzó el límite de la API de Mindee. La imagen fue guardada pero no se extrajo ningún dato."},
        "Configure Mindee API": {"es": "Configurar API de Mindee"},
        "To use the Mindee Receipt OCR API, you need to enter your API key. You can get an API key by signing up at https://mindee.com.": {"es": "Para usar la API OCR de Recibos de Mindee, necesitas ingresar tu clave de API. Puedes obtener una clave de API registrándote en https://mindee.com."},
        "API Key:": {"es": "Clave de API:"},
        "Show API Key": {"es": "Mostrar Clave de API"},
        "Test API Key": {"es": "Probar Clave de API"},
        "Save": {"es": "Guardar"},
        
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
        "Bill saved successfully!": {"es": "¡Factura guardada exitosamente!"},
        "Invalid date format.": {"es": "Formato de fecha inválido."},
        "Please enter both start and end dates.": {"es": "Por favor ingrese fechas de inicio y fin."},
        "API Key Not Set": {"es": "Clave de API No Configurada"},
        "Mindee API key is not set. Would you like to configure it now?": {"es": "La clave de API de Mindee no está configurada. ¿Desea configurarla ahora?"},
        "OCR Error": {"es": "Error de OCR"},
        "An error occurred during OCR processing:": {"es": "Ocurrió un error durante el procesamiento OCR:"},
        
        # Date placeholders
        "MM/dd/yyyy": {"es": "MM/dd/aaaa"},
        
        # Other
        "Present Database": {"es": "Base de Datos Presente"},
        "Bill Tracker": {"es": "Seguimiento de Facturas"},
        "Language": {"es": "Idioma"},
        "English": {"es": "Inglés"},
        "Spanish": {"es": "Español"},
        "Error": {"es": "Error"},
        "Select Receipt Image": {"es": "Seleccionar Imagen de Recibo"},
        "Select Bill Image": {"es": "Seleccionar Imagen de Factura"}
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
