from flask import Blueprint, render_template, request, redirect, url_for, session

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

  
    if username == "reception" and password == "123":
        session["role"] = "reception"
        return redirect(url_for("dashboard.reception_dashboard"))
    else:
        return "❌ Invalid username or password"

# Logout
@auth_bp.route("/logout")
def logout():
    session.pop("role", None)
    return redirect(url_for("auth.login_page"))
