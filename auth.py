from flask import Blueprint, render_template, request, redirect, url_for, session
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from validators import (
    is_valid_username,
    is_valid_password,
    is_valid_email,
    is_valid_name
)


auth_bp = Blueprint("auth", __name__)

# Login Page
@auth_bp.route("/")
def login_page():
    return render_template("login.html")

# Login Action
from flask import flash  # ✅ Make sure this is at the top

@auth_bp.route("/login", methods=["POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")

    if not username or not password:
        flash("⚠ Please enter both username and password!", "warning")
        return redirect(url_for("auth.login_page"))

    # ✅ Only check if correct
    if username == "reception" and password == "123":
        session["role"] = "reception"
        return redirect(url_for("dashboard.reception_dashboard"))
    else:
        flash("❌ Invalid username or password!", "danger")
        return redirect(url_for("auth.login_page"))


# Logout
@auth_bp.route("/logout")
def logout():
    session.pop("role", None)
    return redirect(url_for("auth.login_page"))
