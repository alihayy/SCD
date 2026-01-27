# routes/receipts.py
from flask import Blueprint, request, jsonify
from db import get_connection
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

receipts_bp = Blueprint('receipts', __name__)

@receipts_bp.route('/receipts', methods=['POST'])
def create_receipt():
    """
    Create a new receipt - SIMPLIFIED (No actual functionality)
    """
    try:
        # Validate request content type
        if not request.is_json:
            return jsonify({
                "success": False,
                "errors": ["Content-Type must be application/json"]
            }), 400
        
        data = request.get_json()
        
        # Check required fields
        # Treat None or empty dict as no JSON data
        if not data or data == {}:
          return jsonify({
            "success": False,
            "errors": ["No JSON data provided"]
          }), 400

        # Support both field naming conventions
        patient_mr_no = data.get('patient_id') or data.get('patient_mr_no')
        total_amount = data.get('total') or data.get('total_amount')
        
        if not patient_mr_no:
            return jsonify({
                "success": False,
                "errors": ["Patient ID is required"]
            }), 400
        
        if not total_amount:
            return jsonify({
                "success": False,
                "errors": ["Total amount is required"]
            }), 400
        
        # Return success but no actual receipt creation
        return jsonify({
            "success": True,
            "message": "Receipt functionality has been moved to Patients Management",
            "data": {
                "note": "Please use the Patients Management page for all receipt operations"
            }
        }), 200
            
    except Exception as e:
        logger.error(f"Unexpected error in create_receipt: {str(e)}")
        return jsonify({
            "success": False,
            "errors": ["Receipt functionality has been moved to Patients Management"]
        }), 500

@receipts_bp.route('/receipts', methods=['GET'])
def get_receipts():
    """Get all receipts - SIMPLIFIED (No actual functionality)"""
    try:
        # Return empty list with message
        return jsonify({
            "success": True,
            "message": "Receipt functionality has been moved to Patients Management",
            "data": {
                "receipts": [],
                "count": 0,
                "note": "Please use the Patients Management page to view receipts"
            }
        })
            
    except Exception as e:
        logger.error(f"Unexpected error in get_receipts: {str(e)}")
        return jsonify({
            "success": False,
            "errors": ["Receipt functionality has been moved to Patients Management"]
        }), 500

@receipts_bp.route('/receipts/<int:receipt_id>', methods=['GET'])
def get_receipt(receipt_id):
    """Get specific receipt by ID - SIMPLIFIED (No actual functionality)"""
    try:
        # Validate receipt_id
        if receipt_id <= 0:
            return jsonify({
                "success": False,
                "errors": ["Receipt ID must be a positive integer"]
            }), 400
        
        # Return not found with message
        return jsonify({
            "success": False,
            "errors": ["Receipt functionality has been moved to Patients Management"],
            "message": "Please use the Patients Management page to view receipts"
        }), 404
                
    except Exception as e:
        logger.error(f"Unexpected error in get_receipt: {str(e)}")
        return jsonify({
            "success": False,
            "errors": ["Receipt functionality has been moved to Patients Management"]
        }), 500

@receipts_bp.route('/receipts/<int:receipt_id>', methods=['DELETE'])
def delete_receipt(receipt_id):
    """Delete a receipt by ID - SIMPLIFIED (No actual functionality)"""
    try:
        if receipt_id <= 0:
            return jsonify({
                "success": False,
                "errors": ["Receipt ID must be a positive integer"]
            }), 400
        
        # Return success but no actual deletion
        return jsonify({
            "success": True,
            "message": "Receipt functionality has been moved to Patients Management",
            "data": {
                "note": "Please use the Patients Management page to manage receipts"
            }
        })
            
    except Exception as e:
        logger.error(f"Error deleting receipt {receipt_id}: {str(e)}")
        return jsonify({
            "success": False,
            "errors": ["Receipt functionality has been moved to Patients Management"]
        }), 500

# Download routes - all return messages that functionality has been moved
@receipts_bp.route('/receipts/<int:receipt_id>/download-pdf', methods=['GET'])
def download_receipt_pdf(receipt_id):
    """Download single receipt as PDF - DISABLED"""
    return jsonify({
        "success": False,
        "errors": ["PDF download functionality has been moved to Patients Management"]
    }), 404

@receipts_bp.route('/receipts/download-all-pdf', methods=['GET'])
def download_all_receipts_pdf():
    """Download all receipts as PDF report - DISABLED"""
    return jsonify({
        "success": False,
        "errors": ["PDF download functionality has been moved to Patients Management"]
    }), 404

@receipts_bp.route('/receipts/export-excel', methods=['GET'])
def export_receipts_excel():
    """Export all receipts to Excel - DISABLED"""
    return jsonify({
        "success": False,
        "errors": ["Excel export functionality has been moved to Patients Management"]
    }), 404

# Health check endpoint (kept for monitoring)
@receipts_bp.route('/receipts/health', methods=['GET'])
def health_check():
    """Health check for receipts service"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            
            return jsonify({
                "success": True,
                "message": "Receipts service is available (functionality moved to Patients Management)",
                "data": {
                    "service": "receipts",
                    "status": "redirected",
                    "timestamp": datetime.now().isoformat(),
                    "note": "All receipt operations should be performed through Patients Management"
                }
            })
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            "success": False,
            "errors": ["Database connection failed"],
            "message": "Receipts service is degraded"
        }), 503

# Summary endpoint for information
@receipts_bp.route('/receipts/info', methods=['GET'])
def receipts_info():
    """Information about receipts functionality"""
    return jsonify({
        "success": True,
        "message": "Receipts Management Information",
        "data": {
            "status": "moved",
            "new_location": "Patients Management Page",
            "available_operations": [
                "Patient registration with automatic receipt generation",
                "View all patients and their receipts",
                "Download patient receipts as PDF",
                "Manage patient records and associated receipts"
            ],
            "note": "All receipt-related operations are now handled through the Patients Management interface"
        }
    })