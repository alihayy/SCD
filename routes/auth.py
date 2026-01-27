# routes/auth.py - Sirf login function update karein
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, flash
from db import get_connection
import secrets
from datetime import datetime, timedelta
import re

auth_bp = Blueprint("auth", __name__)

# Password reset tokens storage (temporary - use database in production)
password_reset_tokens = {}

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
    # Get username and password
    if request.is_json:
        data = request.get_json()
        username = data.get("username", "").strip()
        password = data.get("password", "").strip()
        is_ajax = True
    else:
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    print(f"🔑 Login attempt: username='{username}'")
    print(f"📝 Password entered: '{password}'")

    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Try with IsActive column first, if error, try without it
        try:
            cursor.execute(
                "SELECT UserId, Username, Password, Role, FullName FROM Users WHERE Username = ? AND IsActive = 1",
                (username,)
            )
        except:
            # If IsActive column doesn't exist, try without it
            cursor.execute(
                "SELECT UserId, Username, Password, Role, FullName FROM Users WHERE Username = ?",
                (username,)
            )
        
        row = cursor.fetchone()

        if row:
            # Convert to dict for safe access
            columns = [column[0] for column in cursor.description]
            user = dict(zip(columns, row))
            print(f"✅ User found: {user['Username']}, Role: {user['Role']}")
            print(f"📊 Stored password: {user['Password'][:50]}...")

            stored_password = user['Password']
            
            # CHECK 1: Try direct comparison first (for plain text passwords)
            if stored_password == password:
                print("🎉 Login successful (plain text match)!")
                
                # Set session
                session['user_id'] = user['UserId']
                session['username'] = user['Username']
                session['role'] = user['Role']
                session['fullname'] = user['FullName']
                
                # Role-based redirect
                redirect_urls = {
                    'Admin': '/dashboard/admin',
                    'Receptionist': '/dashboard/reception',
                    'Technician': '/dashboard/technician',
                    'Pathologist': '/dashboard/pathologist'
                }
                
                redirect_url = redirect_urls.get(user['Role'], '/dashboard')
                
                if is_ajax:
                    return jsonify({
                        'success': True, 
                        'message': 'Login successful!', 
                        'redirect_url': redirect_url,
                        'user': {
                            'username': user['Username'],
                            'role': user['Role'],
                            'fullname': user['FullName']
                        }
                    })
                return redirect(redirect_url)
            
            # CHECK 2: Try hashed password check
            elif stored_password.startswith('pbkdf2:sha256:'):
                print("Trying hashed password check...")
                if check_password_hash(stored_password, password):
                    print("🎉 Login successful (hashed password match)!")
                    
                    # Set session
                    session['user_id'] = user['UserId']
                    session['username'] = user['Username']
                    session['role'] = user['Role']
                    session['fullname'] = user['FullName']
                    
                    # Role-based redirect
                    redirect_urls = {
                        'Admin': '/dashboard/admin',
                        'Receptionist': '/dashboard/reception',
                        'Technician': '/dashboard/technician',
                        'Pathologist': '/dashboard/pathologist'
                    }
                    
                    redirect_url = redirect_urls.get(user['Role'], '/dashboard')
                    
                    if is_ajax:
                        return jsonify({
                            'success': True, 
                            'message': 'Login successful!', 
                            'redirect_url': redirect_url,
                            'user': {
                                'username': user['Username'],
                                'role': user['Role'],
                                'fullname': user['FullName']
                            }
                        })
                    return redirect(redirect_url)
                else:
                    print("❌ Hashed password mismatch!")
                    error_msg = 'Invalid username or password'
            else:
                print("❌ Password mismatch (neither plain nor hashed)!")
                error_msg = 'Invalid username or password'
        else:
            print("❌ User not found!")
            error_msg = 'Invalid username or password'

        # Invalid login response
        if is_ajax:
            return jsonify({'success': False, 'message': error_msg})
        flash(error_msg, 'error')
        return render_template('login.html', error=True)

    except Exception as e:
        print(f"💥 Database error during login: {e}")
        import traceback
        traceback.print_exc()
        error_msg = 'Server error. Please try again.'
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

# Forgot Password Route
@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    """Handle forgot password requests"""
    try:
        # Get data from request
        if request.is_json:
            data = request.get_json()
            email = data.get('email', '').strip()
            username = data.get('username', '').strip()
        else:
            email = request.form.get('email', '').strip()
            username = request.form.get('username', '').strip()
        
        print(f"🔑 Forgot password request: email='{email}', username='{username}'")
        
        # Basic validation
        if not email or not username:
            return jsonify({
                'success': False, 
                'message': 'Please provide both email and username'
            })
        
        # Email validation regex
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, email):
            return jsonify({
                'success': False, 
                'message': 'Please enter a valid email address'
            })
        
        # Check if user exists in database
        conn = None
        cursor = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Check user with email and username
            cursor.execute(
                "SELECT UserId, Username, Email FROM Users WHERE Username = ? AND Email = ? AND IsActive = 1",
                (username, email)
            )
            row = cursor.fetchone()
            
            if row:
                # Convert to dict
                columns = [column[0] for column in cursor.description]
                user = dict(zip(columns, row))
                
                # Generate reset token
                token = secrets.token_urlsafe(32)
                expiry_time = datetime.now() + timedelta(hours=1)
                
                # Store token (in production, use database table)
                password_reset_tokens[token] = {
                    'user_id': user['UserId'],
                    'username': user['Username'],
                    'email': user['Email'],
                    'expires': expiry_time,
                    'used': False
                }
                
                print(f"✅ Generated reset token for {user['Username']}")
                
                # In production, send email here
                # For now, return success with debug info
                return jsonify({
                    'success': True, 
                    'message': 'Password reset instructions have been sent to your email.',
                    'debug_token': token  # Remove this in production
                })
            else:
                return jsonify({
                    'success': False, 
                    'message': 'No user found with provided email and username'
                })
                
        except Exception as e:
            print(f"Database error in forgot_password: {e}")
            return jsonify({
                'success': False, 
                'message': 'Database error occurred. Please try again.'
            })
        finally:
            if cursor: cursor.close()
            if conn: conn.close()
            
    except Exception as e:
        print(f"Error in forgot_password: {e}")
        return jsonify({
            'success': False, 
            'message': 'An error occurred. Please try again.'
        })

# Reset Password Page
@auth_bp.route("/reset-password/<token>", methods=["GET"])
def reset_password_page(token):
    """Show reset password page"""
    # Verify token
    token_data = password_reset_tokens.get(token)
    
    if not token_data:
        flash('Invalid or expired reset token', 'error')
        return redirect(url_for('auth.login_page'))
    
    if token_data['expires'] < datetime.now():
        flash('Reset token has expired', 'error')
        return redirect(url_for('auth.login_page'))
    
    if token_data['used']:
        flash('Reset token has already been used', 'error')
        return redirect(url_for('auth.login_page'))
    
    return render_template('reset_password.html', token=token)

# Handle Password Reset
@auth_bp.route("/reset-password/<token>", methods=["POST"])
def reset_password(token):
    """Handle password reset"""
    try:
        # Verify token
        token_data = password_reset_tokens.get(token)
        
        if not token_data:
            return jsonify({
                'success': False, 
                'message': 'Invalid or expired reset token'
            })
        
        if token_data['expires'] < datetime.now():
            return jsonify({
                'success': False, 
                'message': 'Reset token has expired'
            })
        
        if token_data['used']:
            return jsonify({
                'success': False, 
                'message': 'Reset token has already been used'
            })
        
        # Get new password from request
        if request.is_json:
            data = request.get_json()
            new_password = data.get('new_password', '').strip()
            confirm_password = data.get('confirm_password', '').strip()
        else:
            new_password = request.form.get('new_password', '').strip()
            confirm_password = request.form.get('confirm_password', '').strip()
        
        # Validate passwords
        if not new_password or not confirm_password:
            return jsonify({
                'success': False, 
                'message': 'Please fill in all fields'
            })
        
        if new_password != confirm_password:
            return jsonify({
                'success': False, 
                'message': 'Passwords do not match'
            })
        
        if len(new_password) < 6:
            return jsonify({
                'success': False, 
                'message': 'Password must be at least 6 characters long'
            })
        
        # Update password in database
        conn = None
        cursor = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Hash the new password
            hashed_password = generate_password_hash(new_password)
            
            # Update user password
            cursor.execute(
                "UPDATE Users SET Password = ? WHERE UserId = ?",
                (hashed_password, token_data['user_id'])
            )
            
            conn.commit()
            
            # Mark token as used
            token_data['used'] = True
            
            print(f"✅ Password reset successful for user ID: {token_data['user_id']}")
            
            return jsonify({
                'success': True, 
                'message': 'Password has been reset successfully! You can now login with your new password.'
            })
                
        except Exception as e:
            print(f"Database error in reset_password: {e}")
            if conn:
                conn.rollback()
            return jsonify({
                'success': False, 
                'message': 'Database error occurred. Please try again.'
            })
        finally:
            if cursor: cursor.close()
            if conn: conn.close()
            
    except Exception as e:
        print(f"Error in reset_password: {e}")
        return jsonify({
            'success': False, 
            'message': 'An error occurred. Please try again.'
        })

# Clean expired tokens (optional - can run periodically)
def clean_expired_tokens():
    """Remove expired tokens from storage"""
    current_time = datetime.now()
    expired_tokens = [
        token for token, data in password_reset_tokens.items() 
        if data['expires'] < current_time
    ]
    
    for token in expired_tokens:
        del password_reset_tokens[token]
    
    if expired_tokens:
        print(f"🧹 Cleaned {len(expired_tokens)} expired tokens")