from flask import Flask
from db import get_connection  # ✅ import connection function
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.patients import patients_bp
from routes.receipts import receipts_bp
from routes.reports import reports_bp


app = Flask(__name__)
app.secret_key = "supersecretkey"

# ✅ Initialize DB Connection
connection = get_connection()
app.config["DB_CONNECTION"] = connection

# ✅ Register Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp, url_prefix="/dashboard")
app.register_blueprint(patients_bp, url_prefix="/patients")
app.register_blueprint(receipts_bp, url_prefix="/receipts")
app.register_blueprint(reports_bp, url_prefix="/reports")


if __name__ == "__main__":
    app.run(debug=True)
