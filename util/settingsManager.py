import json

DEFAULT_CATEGORIES = ["Mortgage", "Food", "Gas", "Mechanic", "Work Clothes", "Materials", "Miscellaneous", "Doctor", "Equipment & Rent", "Cash"]

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
