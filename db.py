# labmanagement/db.py
import os
import pyodbc

def get_connection():
    """
    Reads DB config from environment variables and returns a pyodbc connection.
    Environment variables:
      DB_SERVER, DB_NAME, DB_DRIVER, DB_USER, DB_PASS
    If DB_USER/DB_PASS are not set, it uses Trusted_Connection=yes (Windows auth).
    """
    server = os.environ.get("DB_SERVER", "DESKTOP-R8GUBNB\\SQLEXPRESS01")
    database = os.environ.get("DB_NAME", "Lmss_4")
    driver = os.environ.get("DB_DRIVER", "ODBC Driver 17 for SQL Server")
    db_user = os.environ.get("DB_USER")
    db_pass = os.environ.get("DB_PASS")

    if db_user and db_pass:
        auth = f"UID={db_user};PWD={db_pass};"
    else:
        auth = "Trusted_Connection=yes;"

    conn_str = f"DRIVER={{{driver}}};SERVER={server};DATABASE={database};{auth}"

    try:
        conn = pyodbc.connect(conn_str, autocommit=False)
        # print("Connected to SQL Server")
        return conn
    except Exception as e:
        # For production, log this error instead of printing
        print("Database connection failed:", e)
        raise
