from PyQt5.QtCore import QThread, pyqtSignal
from datetime import datetime

from mindeeApi.mindeeHelper import MindeeHelper

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
