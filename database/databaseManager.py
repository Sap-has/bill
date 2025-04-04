from datetime import datetime
import os
import shutil
import sqlite3

DATE_FORMAT = "%m/%d/%Y"
DATE_FORMATS = ["%m/%d/%y", "%m/%d/%Y"]

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