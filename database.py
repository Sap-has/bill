def create_table(self, conn=None):
    query = """
    CREATE TABLE IF NOT EXISTS bills (
        id INTEGER PRIMARY KEY,
        date TEXT,
        name TEXT,
        price TEXT,
        image TEXT -- stores  the image filename
    )
    """
    if conn is None:
        conn = self.conn
    conn.execute(query)
    conn.commit()