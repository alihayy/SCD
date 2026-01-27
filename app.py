import os
from flask import Flask, jsonify, session
from db import get_connection
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.patients import patients_bp
from routes.receipts import receipts_bp
from routes.reports import reports_bp
from routes.admin import admin_bp


app = Flask(__name__)

# Use environment variable for secret key (do NOT hardcode in production)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")

# ========================================
# DEBUG ROUTES - ADD THESE RIGHT HERE
# ========================================

@app.route("/debug/users")
def debug_users():
    """Debug route to check users in database"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT UserId, Username, Password, Role, FullName FROM Users")
        users = cursor.fetchall()
        cursor.close()
        conn.close()
        
        users_list = []
        for user in users:
            users_list.append({
                'user_id': user.UserId,
                'username': user.Username,
                'password': user.Password,
                'role': user.Role,
                'fullname': user.FullName
            })
        
        return jsonify(users_list)
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route("/debug/session")
def debug_session():
    """Debug route to check current session"""
    return jsonify(dict(session))

# ========================================
# FAVICON FIX - ADD THIS ROUTE
# ========================================
@app.route('/favicon.ico')
def favicon():
    return '', 204  # No content response to prevent 404 errors

# ========================================
# END DEBUG ROUTES
# ========================================

# REMOVE THIS LINE: Do NOT store a shared DB connection
# connection = get_connection()
# app.config["DB_CONNECTION"] = connection

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp, url_prefix="/dashboard")
app.register_blueprint(patients_bp, url_prefix="/patients")
app.register_blueprint(receipts_bp, url_prefix="/receipts")  # ADD prefix back
app.register_blueprint(reports_bp, url_prefix="/reports")
app.register_blueprint(admin_bp)

# ========================================
# ERROR HANDLERS
# ========================================
@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == "__main__":
    app.run(debug=True)