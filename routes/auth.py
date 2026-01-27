from werkzeug.security import generate_password_hash, check_password_hash
from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, flash
from db import get_connection

auth_bp = Blueprint("auth", __name__)

def initialize_default_passwords():
    """
    Function to initialize default passwords when needed
    Run this once manually or during first setup
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        print("🔐 Setting up default hashed passwords...")
        
        # Hash and update passwords
        admin_hash = generate_password_hash('Imran@4200')
        reception_hash = generate_password_hash('Rec@001')
        tech_hash = generate_password_hash('Tech@123')
        
        # Update admin password
        cursor.execute(
            "UPDATE Users SET Password = ?, FullName = ? WHERE Username = 'admin' AND Role = 'Admin'",
            (admin_hash, 'System Administrator')
        )
        print("✅ Admin password set: Imran@4200")
        
        # Update reception password  
        cursor.execute(
            "UPDATE Users SET Password = ?, FullName = ? WHERE Username = 'reception' AND Role = 'Receptionist'", 
            (reception_hash, 'Reception Staff')
        )
        print("✅ Reception password set: Rec@001")
        
        # Update technician password
        cursor.execute(
            "UPDATE Users SET Password = ?, FullName = ? WHERE Username = 'technician' AND Role = 'Technician'",
            (tech_hash, 'Lab Technician')
        )
        print("✅ Technician password set: Tech@123")
        
        conn.commit()
        print("🎉 Default passwords initialized successfully!")
            
    except Exception as e:
        print(f"❌ Error initializing passwords: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@auth_bp.route("/")
def login_page():
    return render_template("login.html")

@auth_bp.route("/login", methods=["POST"])
def login():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()

    print(f"Login attempt: username='{username}'")

    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Fetch user from database
        cursor.execute(
            "SELECT UserId, Username, Password, Role, FullName FROM Users WHERE Username = ? AND IsActive = 1",
            (username,)
        )
        row = cursor.fetchone()

        if row:
            # Convert to dict for safe access
            columns = [column[0] for column in cursor.description]
            user = dict(zip(columns, row))
            print(f"User found: {user['Username']}, Role: {user['Role']}")

            # Password check with hashing
            if check_password_hash(user['Password'], password):
                # Set session
                session['user_id'] = user['UserId']
                session['username'] = user['Username']
                session['role'] = user['Role']
                session['fullname'] = user['FullName']
                print(f"Login successful for: {user['Username']}")

                # Role-based redirect
                if user['Role'] == 'Admin':
                    redirect_url = url_for('dashboard.admin_dashboard')
                elif user['Role'] == 'Receptionist':
                    redirect_url = url_for('dashboard.reception_dashboard')
                else:
                    redirect_url = url_for('dashboard.tech_dashboard')

                if is_ajax:
                    return jsonify({'success': True, 'message': 'Login successful', 'redirect_url': redirect_url})
                return redirect(redirect_url)
            else:
                error_msg = 'Incorrect password'
        else:
            error_msg = 'Username not found'

        # Invalid login response
        if is_ajax:
            return jsonify({'success': False, 'message': error_msg})
        flash(error_msg, 'error')
        return render_template('login.html', error=True)

    except Exception as e:
        print(f"Database error during login: {e}")
        error_msg = f"Database error: {e}"
        if is_ajax:
            return jsonify({'success': False, 'message': error_msg})
        flash(error_msg, 'error')
        return render_template('login.html', error=True)

    finally:
        try:
            if cursor: cursor.close()
            if conn: conn.close()
        except Exception as e:
            print(f"Error closing connection: {e}")

@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login_page"))

# Function to manually trigger password initialization
@auth_bp.route("/init-passwords")
def init_passwords():
    """
    Route to initialize passwords manually
    Access this URL once to set up passwords: http://localhost:5000/init-passwords
    """
    initialize_default_passwords()
    return "✅ Default passwords initialized! You can now login."