import json
import os

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
