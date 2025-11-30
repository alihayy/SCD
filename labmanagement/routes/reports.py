from flask import Blueprint, request, jsonify, send_file
import os

reports_bp = Blueprint('reports', __name__)
UPLOAD_FOLDER = "uploads"

@reports_bp.route('/reports', methods=['POST'])
def upload_report():
    file = request.files['file']
    patient_id = request.form['patient_id']
    filename = f"report_{patient_id}.pdf"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    return jsonify({"message": "Report uploaded", "file": filename})

@reports_bp.route('/reports/<int:patient_id>', methods=['GET'])
def download_report(patient_id):
    filepath = os.path.join(UPLOAD_FOLDER, f"report_{patient_id}.pdf")
    return send_file(filepath, as_attachment=True)
