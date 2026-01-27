# dashboard.py - 
from flask import Blueprint, render_template, session, redirect, url_for

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/admin")
def admin_dashboard():
    if session.get("role") != "Admin":
        return redirect(url_for("auth.login_page"))
    return render_template("admin_dashboard.html")

@dashboard_bp.route("/reception")
def reception_dashboard():
    if session.get("role") != "Receptionist":
        return redirect(url_for("auth.login_page"))
    return render_template("reception.html")
