import pyodbc

def get_connection():
    try:
        conn_str = (
            "DRIVER={ODBC Driver 17 for SQL Server};"
            "SERVER=DESKTOP-ONOJF0L;"        # ✅ Your actual server name
            "DATABASE=lms;"                   # ✅ Your actual database name
            "Trusted_Connection=yes;"         # ✅ Using Windows Authentication
        )
        connection = pyodbc.connect(conn_str)
        print("✅ Connected to Microsoft SQL Server successfully.")
        return connection
    except Exception as e:
        print("❌ Database connection failed:", e)
        return None
