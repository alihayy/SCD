# routes/patients.py
from flask import Blueprint, render_template, request, jsonify, send_file
from models.patient_model import Patient
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

patients_bp = Blueprint('patients', __name__, template_folder='../templates')


# -----------------------------
# 1️⃣ Patients Home Page
# -----------------------------
@patients_bp.route('/', methods=['GET'])
def patients_home():
    """Render patients list page."""
    patients = Patient.get_all_patients()
    return render_template('patients.html', patients=patients)


# -----------------------------
# 2️⃣ Add Patient Route
# -----------------------------
@patients_bp.route('/add', methods=['POST'])
def add_patient_route():
    """Add new patient record and return MR number."""
    try:
        reg_date = request.form.get('reg_date')
        reporting_date = request.form.get('reporting_date')
        name = request.form.get('name')
        gender = request.form.get('gender')
        age = request.form.get('age')
        doctor = request.form.get('doctor')
        tests = request.form.get('tests')
        amount = request.form.get('amount')

        # Type conversions
        age = int(age) if age and age.isdigit() else None
        try:
            amount = float(amount) if amount else None
        except ValueError:
            amount = None

        mr_no = Patient.add_patient(reg_date, reporting_date, name, gender, age, doctor, tests, amount)

        if mr_no is None:
            return jsonify({"success": False, "message": "Failed to add patient"}), 500

        return jsonify({"success": True, "message": "Patient added successfully", "mr_no": mr_no})

    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500


# -----------------------------
# 3️⃣ Generate PDF Receipt
# -----------------------------
@patients_bp.route('/<int:mr_no>/receipt')
def generate_pdf(mr_no):
    """Generate a PDF receipt for the patient."""
    patients = Patient.get_all_patients()
    patient = next((p for p in patients if p.get('mr_no') == mr_no), None)

    if not patient:
        return "Patient not found", 404

    # PDF setup
    buffer = BytesIO()
    page_width, page_height = A4
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=20, bottomMargin=20)
    elements = []
    styles = getSampleStyleSheet()
    styles['Normal'].fontSize = 11

    # ---------------- HEADER ----------------
    logo_path = "static/logo.png"  # Make sure this exists
    try:
        logo_img = Image(logo_path, 1.2 * inch, 1.2 * inch)
    except Exception:
        logo_img = Spacer(1.2 * inch, 1.2 * inch)

    header_table = Table(
        [[
            logo_img,
  Paragraph(
    "<b><font size='16' color='white'>CITI LAB & DIAGNOSTIC CENTRE</font></b><br/>"
    "<font color='white'>"
    "<u><b>______________________________________________</b></u><br/>"
    "Opposite: C.M.H Muzaffarabad Azad Kashmir<br/>"
    "Cell: 0301-5225117 | Ph: 05822-447698"
    "</font>",
    styles['Normal']
)


        ]],
        colWidths=[1.4 * inch, page_width - (1.4 * inch + 60)]  # match total width to A4 usable area
    )

    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.Color(0, 0.4, 0.4)),  # teal-green background
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 18))

    # ---------------- PATIENT INFO TABLE ----------------
    patient_data = [
        ["MR No:", patient.get("mr_no", ""), "Reg Date:", patient.get("reg_date", "")],
        ["Name:", patient.get("name", ""), "Reporting Date:", patient.get("reporting_date", "")],
        ["Gender:", patient.get("gender", ""), "Age:", str(patient.get("age", ""))],
        ["Doctor:", patient.get("doctor", ""), "Amount:", f"{patient.get('amount', '')} PKR"],
        ["Tests:", patient.get("tests", ""), "", ""]
    ]

    # Match width to header
    patient_table = Table(patient_data, colWidths=[90, 180, 90, page_width - (90 + 180 + 90 + 60)])
    patient_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(patient_table)

    # ---------------- BUILD PDF ----------------
    doc.build(elements)
    buffer.seek(0)
    filename = f"receipt_{patient.get('mr_no', '')}.pdf"
    return send_file(buffer, as_attachment=False, download_name=filename, mimetype='application/pdf')
# -----------------------------
# 4️⃣ View Saved Patients List
# -----------------------------
@patients_bp.route('/saved', methods=['GET'])
def saved_patients():
    """Show all saved patients list."""
    patients = Patient.get_all_patients()
    return render_template('saved_patients.html', patients=patients)
