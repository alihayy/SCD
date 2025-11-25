from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, flash

auth_bp = Blueprint("auth", __name__)

# Login Page
@auth_bp.route("/")
def login_page():
    return render_template("login.html")

# Login Action
@auth_bp.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]

    # Check if it's an AJAX request
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if username == "reception" and password == "Rec@123":
        session["role"] = "reception"
        
        if is_ajax:
            return jsonify({
                'success': True, 
                'message': 'Login successful',
                'redirect_url': url_for('dashboard.reception_dashboard')
            })
        else:
            return redirect(url_for("dashboard.reception_dashboard"))
    else:
        if is_ajax:
            return jsonify({
                'success': False, 
                'message': 'Invalid username or password'
            })
        else:
            # For non-AJAX requests, show error on same page
            flash('Invalid username or password', 'error')
            return render_template("login.html", error=True)

# Logout
@auth_bp.route("/logout")
def logout():
    session.pop("role", None)
    return redirect(url_for("auth.login_page"))