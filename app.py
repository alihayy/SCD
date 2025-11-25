# labmanagement/app.py
import os
from flask import Flask
from db import get_connection
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.patients import patients_bp
from routes.receipts import receipts_bp
from routes.reports import reports_bp

app = Flask(__name__)

# Use environment variable for secret key (do NOT hardcode in production)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")

# Optional: store DB connection in config if you want a single shared connection (or better use pooling)
connection = get_connection()
app.config["DB_CONNECTION"] = connection

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp, url_prefix="/dashboard")
app.register_blueprint(patients_bp, url_prefix="/patients")
app.register_blueprint(receipts_bp)  # REMOVE url_prefix="/receipts" - FIXED
app.register_blueprint(reports_bp, url_prefix="/reports")

if __name__ == "__main__":
    app.run(debug=True)