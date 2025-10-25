from flask import Blueprint, request, jsonify
from db import get_connection

receipts_bp = Blueprint('receipts', __name__)

@receipts_bp.route('/receipts', methods=['POST'])
def create_receipt():
    data = request.json
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Receipts (PatientId, Total) VALUES (?, ?)",
                   (data['patient_id'], data['total']))
    conn.commit()
    return jsonify({"message": "Receipt created"})

@receipts_bp.route('/receipts', methods=['GET'])
def get_receipts():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Receipts")
    rows = cursor.fetchall()
    receipts = [{"id": row[0], "patient_id": row[1], "total": row[2]} for row in rows]
    return jsonify(receipts)
