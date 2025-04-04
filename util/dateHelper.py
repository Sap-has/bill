from datetime import datetime

DATE_FORMAT = "%m/%d/%Y"
DATE_FORMATS = ["%m/%d/%y", "%m/%d/%Y"]

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