import pyodbc

def get_connection():
    try:
        conn = pyodbc.connect(
            "Driver={SQL Server};"
            "Server=DESKTOP-ONOJF0L;"          # replace localhost with your server name if needed
            "Database=Lmss;"     # replace with your actual database name
            "Trusted_Connection=yes;"    # yes for Windows Auth, no for SQL login
        )
        return conn
    except Exception as e:
        print("❌ Database connection failed:", e)
        raise
