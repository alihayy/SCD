from flask import Blueprint, request, jsonify
from db import get_connection
from contextlib import contextmanager
import logging
from datetime import datetime, timedelta

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

receipts_bp = Blueprint('receipts', __name__)

# ---------------------------------------
# SINGLETON PATTERN - Database Config Manager
# ---------------------------------------
class DBConfigManager:
    _instance = None
    _config = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DBConfigManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize database configuration"""
        self._config = {
            'max_receipt_amount': 1000000,  # Maximum receipt amount
            'min_receipt_amount': 1,        # Minimum receipt amount
            'max_patient_id': 999999,       # Maximum patient ID
            'default_currency': 'Rs',
            'date_format': '%Y-%m-%d %H:%M:%S',
            'receipt_timeout_seconds': 300,   # 5 minutes for receipt operations
            'default_report_due_hours': 24    # Default report due time in hours
        }
    
    def get(self, key, default=None):
        """Get configuration value"""
        return self._config.get(key, default)
    
    def set(self, key, value):
        """Set configuration value"""
        self._config[key] = value
    
    def validate_amount(self, amount):
        """Validate receipt amount against configured limits"""
        min_amount = self.get('min_receipt_amount')
        max_amount = self.get('max_receipt_amount')
        return min_amount <= amount <= max_amount
    
    def get_currency_symbol(self):
        """Get configured currency symbol"""
        return self.get('default_currency', 'Rs')
    
    def get_default_due_time(self):
        """Get default report due time"""
        hours = self.get('default_report_due_hours', 24)
        return datetime.now() + timedelta(hours=hours)

# ---------------------------------------
# REPOSITORY PATTERN Implementation (Updated for New Schema)
# ---------------------------------------
class ReceiptRepository:
    def __init__(self, db_connection_func):
        self.db_connection_func = db_connection_func
        self.config = DBConfigManager()  # Using Singleton
    
    def create(self, patient_mr_no, total_amount, report_due_time=None, test_ids=None):
        """Create a new receipt with validation"""
        errors = self._validate_receipt_data(patient_mr_no, total_amount)
        if errors:
            return {"success": False, "errors": errors}
        
        try:
            with self.db_connection_func() as conn:
                cursor = conn.cursor()
                
                # Check if patient exists
                cursor.execute("SELECT MrNo, Name FROM Patients WHERE MrNo = ?", (patient_mr_no,))
                patient_result = cursor.fetchone()
                if not patient_result:
                    return {"success": False, "errors": ["Patient not found"]}
                
                # Set default report due time if not provided
                if not report_due_time:
                    report_due_time = self.config.get_default_due_time()
                
                # Insert receipt
                cursor.execute("""
                    INSERT INTO Receipts (PatientMrNo, TotalAmount, ReportDueTime, CreatedAt) 
                    OUTPUT INSERTED.ReceiptId, INSERTED.PatientMrNo, INSERTED.TotalAmount, INSERTED.ReportDueTime, INSERTED.CreatedAt
                    VALUES (?, ?, ?, ?)
                """, (patient_mr_no, total_amount, report_due_time, datetime.now()))
                
                receipt_result = cursor.fetchone()
                receipt_id = receipt_result[0]
                
                # Link tests if provided
                if test_ids:
                    for test_id in test_ids:
                        cursor.execute("""
                            INSERT INTO Receipt_Tests (ReceiptId, TestId)
                            VALUES (?, ?)
                        """, (receipt_id, test_id))
                
                conn.commit()
                
                return {
                    "success": True, 
                    "receipt": {
                        "receipt_id": receipt_id,
                        "patient_mr_no": receipt_result[1],
                        "patient_name": patient_result[1],
                        "total_amount": float(receipt_result[2]),
                        "report_due_time": receipt_result[3].isoformat() if receipt_result[3] else None,
                        "created_at": receipt_result[4].isoformat() if receipt_result[4] else None,
                        "currency": self.config.get_currency_symbol(),
                        "formatted_total": f"{self.config.get_currency_symbol()}{float(receipt_result[2]):.2f}",
                        "test_ids": test_ids or []
                    }
                }
                
        except Exception as e:
            logger.error(f"Error creating receipt: {str(e)}")
            return {"success": False, "errors": [f"Database error: {str(e)}"]}
    
    def get_all(self):
        """Get all receipts with patient information"""
        try:
            with self.db_connection_func() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT r.ReceiptId, r.PatientMrNo, p.Name as PatientName, 
                           r.TotalAmount, r.ReportDueTime, r.CreatedAt
                    FROM Receipts r
                    LEFT JOIN Patients p ON r.PatientMrNo = p.MrNo
                    ORDER BY r.CreatedAt DESC
                """)
                
                rows = cursor.fetchall()
                receipts = []
                currency = self.config.get_currency_symbol()
                
                for row in rows:
                    receipts.append({
                        "receipt_id": row[0],
                        "patient_mr_no": row[1],
                        "patient_name": row[2] or "Unknown",
                        "total_amount": float(row[3]) if row[3] else 0.0,
                        "formatted_total": f"{currency}{float(row[3] or 0):.2f}",
                        "report_due_time": row[4].isoformat() if row[4] else None,
                        "created_at": row[5].isoformat() if row[5] else None,
                        "created_date": row[5].strftime(self.config.get('date_format')) if row[5] else "Unknown",
                        "is_overdue": row[4] and row[4] < datetime.now()  # Check if report is overdue
                    })
                
                return {"success": True, "receipts": receipts, "count": len(receipts)}
                
        except Exception as e:
            logger.error(f"Error fetching receipts: {str(e)}")
            return {"success": False, "errors": [f"Database error: {str(e)}"]}
    
    def get_by_id(self, receipt_id):
        """Get receipt by ID with test details"""
        try:
            with self.db_connection_func() as conn:
                cursor = conn.cursor()
                
                # Get receipt basic info
                cursor.execute("""
                    SELECT r.ReceiptId, r.PatientMrNo, p.Name as PatientName, 
                           r.TotalAmount, r.ReportDueTime, r.CreatedAt
                    FROM Receipts r
                    LEFT JOIN Patients p ON r.PatientMrNo = p.MrNo
                    WHERE r.ReceiptId = ?
                """, (receipt_id,))
                
                receipt_row = cursor.fetchone()
                if not receipt_row:
                    return {"success": False, "errors": ["Receipt not found"]}
                
                # Get associated tests
                cursor.execute("""
                    SELECT t.TestId, t.TestName, t.Price
                    FROM Receipt_Tests rt
                    JOIN Tests t ON rt.TestId = t.TestId
                    WHERE rt.ReceiptId = ?
                """, (receipt_id,))
                
                test_rows = cursor.fetchall()
                tests = []
                for test_row in test_rows:
                    tests.append({
                        "test_id": test_row[0],
                        "test_name": test_row[1],
                        "price": float(test_row[2]) if test_row[2] else 0.0
                    })
                
                receipt = {
                    "receipt_id": receipt_row[0],
                    "patient_mr_no": receipt_row[1],
                    "patient_name": receipt_row[2] or "Unknown",
                    "total_amount": float(receipt_row[3]) if receipt_row[3] else 0.0,
                    "formatted_total": f"{self.config.get_currency_symbol()}{float(receipt_row[3] or 0):.2f}",
                    "report_due_time": receipt_row[4].isoformat() if receipt_row[4] else None,
                    "created_at": receipt_row[5].isoformat() if receipt_row[5] else None,
                    "tests": tests,
                    "is_overdue": receipt_row[4] and receipt_row[4] < datetime.now()
                }
                
                return {"success": True, "receipt": receipt}
                
        except Exception as e:
            logger.error(f"Error fetching receipt {receipt_id}: {str(e)}")
            return {"success": False, "errors": [f"Database error: {str(e)}"]}
    
    def get_receipts_by_patient(self, patient_mr_no):
        """Get all receipts for a specific patient"""
        try:
            with self.db_connection_func() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT r.ReceiptId, r.PatientMrNo, p.Name as PatientName, 
                           r.TotalAmount, r.ReportDueTime, r.CreatedAt
                    FROM Receipts r
                    LEFT JOIN Patients p ON r.PatientMrNo = p.MrNo
                    WHERE r.PatientMrNo = ?
                    ORDER BY r.CreatedAt DESC
                """, (patient_mr_no,))
                
                rows = cursor.fetchall()
                receipts = []
                currency = self.config.get_currency_symbol()
                
                for row in rows:
                    receipts.append({
                        "receipt_id": row[0],
                        "patient_mr_no": row[1],
                        "patient_name": row[2] or "Unknown",
                        "total_amount": float(row[3]) if row[3] else 0.0,
                        "formatted_total": f"{currency}{float(row[3] or 0):.2f}",
                        "report_due_time": row[4].isoformat() if row[4] else None,
                        "created_at": row[5].isoformat() if row[5] else None,
                        "is_overdue": row[4] and row[4] < datetime.now()
                    })
                
                return {"success": True, "receipts": receipts, "count": len(receipts)}
                
        except Exception as e:
            logger.error(f"Error fetching patient receipts: {str(e)}")
            return {"success": False, "errors": [f"Database error: {str(e)}"]}
    
    def get_receipts_summary(self):
        """Get receipts summary statistics"""
        try:
            with self.db_connection_func() as conn:
                cursor = conn.cursor()
                
                # Total receipts count
                cursor.execute("SELECT COUNT(*) FROM Receipts")
                total_receipts = cursor.fetchone()[0]
                
                # Total amount
                cursor.execute("SELECT SUM(TotalAmount) FROM Receipts")
                total_amount = cursor.fetchone()[0] or 0
                
                # Today's receipts
                cursor.execute("SELECT COUNT(*), SUM(TotalAmount) FROM Receipts WHERE CAST(CreatedAt AS DATE) = CAST(GETDATE() AS DATE)")
                today_result = cursor.fetchone()
                today_receipts = today_result[0] or 0
                today_amount = today_result[1] or 0
                
                # Overdue reports
                cursor.execute("SELECT COUNT(*) FROM Receipts WHERE ReportDueTime < GETDATE()")
                overdue_reports = cursor.fetchone()[0] or 0
                
                return {
                    "success": True,
                    "summary": {
                        "total_receipts": total_receipts,
                        "total_amount": float(total_amount),
                        "formatted_total_amount": f"{self.config.get_currency_symbol()}{float(total_amount):.2f}",
                        "today_receipts": today_receipts,
                        "today_amount": float(today_amount),
                        "formatted_today_amount": f"{self.config.get_currency_symbol()}{float(today_amount):.2f}",
                        "overdue_reports": overdue_reports,
                        "currency": self.config.get_currency_symbol()
                    }
                }
                
        except Exception as e:
            logger.error(f"Error fetching receipts summary: {str(e)}")
            return {"success": False, "errors": [f"Database error: {str(e)}"]}
    
    def get_available_tests(self):
        """Get all available tests from master data"""
        try:
            with self.db_connection_func() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT TestId, TestName, Price 
                    FROM Tests 
                    ORDER BY TestName
                """)
                
                rows = cursor.fetchall()
                tests = []
                currency = self.config.get_currency_symbol()
                
                for row in rows:
                    tests.append({
                        "test_id": row[0],
                        "test_name": row[1],
                        "price": float(row[2]) if row[2] else 0.0,
                        "formatted_price": f"{currency}{float(row[2] or 0):.2f}"
                    })
                
                return {"success": True, "tests": tests, "count": len(tests)}
                
        except Exception as e:
            logger.error(f"Error fetching tests: {str(e)}")
            return {"success": False, "errors": [f"Database error: {str(e)}"]}
    
    def _validate_receipt_data(self, patient_mr_no, total_amount):
        """Validate receipt data using Singleton config"""
        errors = []
        
        # Patient MR No validation
        if not patient_mr_no:
            errors.append("Patient MR Number is required")
        else:
            try:
                patient_mr_no_int = int(patient_mr_no)
                if patient_mr_no_int <= 0:
                    errors.append("Patient MR Number must be a positive integer")
                elif patient_mr_no_int > self.config.get('max_patient_id'):
                    errors.append("Patient MR Number seems invalid")
            except (ValueError, TypeError):
                errors.append("Patient MR Number must be a valid integer")
        
        # Total amount validation using Singleton config
        if total_amount is None:
            errors.append("Total amount is required")
        else:
            try:
                total_float = float(total_amount)
                if not self.config.validate_amount(total_float):
                    min_amt = self.config.get('min_receipt_amount')
                    max_amt = self.config.get('max_receipt_amount')
                    errors.append(f"Total amount must be between {self.config.get_currency_symbol()}{min_amt} and {self.config.get_currency_symbol()}{max_amt}")
            except (ValueError, TypeError):
                errors.append("Total amount must be a valid number")
        
        return errors

# Initialize repository and singleton
db_config = DBConfigManager()  # Singleton instance
receipt_repo = ReceiptRepository(get_connection)

# ---------------------------------------
# SIMPLIFIED ROUTES for Frontend Integration
# ---------------------------------------

@receipts_bp.route('/receipts', methods=['POST'])
def create_receipt():
    """
    Create a new receipt - SIMPLIFIED for frontend
    Expected JSON: {
        "patient_id": 123, 
        "total": 1500.00
    }
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
        if not data:
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
        
        # Use Repository Pattern
        result = receipt_repo.create(patient_mr_no, total_amount)
        
        if result["success"]:
            return jsonify({
                "success": True,
                "message": "Receipt created successfully",
                "data": {
                    "receipt": result["receipt"]
                }
            }), 201
        else:
            return jsonify({
                "success": False,
                "errors": result["errors"]
            }), 400
            
    except Exception as e:
        logger.error(f"Unexpected error in create_receipt: {str(e)}")
        return jsonify({
            "success": False,
            "errors": ["Internal server error"]
        }), 500

@receipts_bp.route('/receipts', methods=['GET'])
def get_receipts():
    """Get all receipts with patient information - SIMPLIFIED"""
    try:
        # Use Repository Pattern
        result = receipt_repo.get_all()
        
        if result["success"]:
            return jsonify({
                "success": True,
                "message": "Receipts retrieved successfully",
                "data": {
                    "receipts": result["receipts"]
                }
            })
        else:
            return jsonify({
                "success": False,
                "errors": result["errors"]
            }), 500
            
    except Exception as e:
        logger.error(f"Unexpected error in get_receipts: {str(e)}")
        return jsonify({
            "success": False,
            "errors": ["Internal server error"]
        }), 500

@receipts_bp.route('/receipts/<int:receipt_id>', methods=['GET'])
def get_receipt(receipt_id):
    """Get specific receipt by ID - SIMPLIFIED"""
    try:
        # Validate receipt_id
        if receipt_id <= 0:
            return jsonify({
                "success": False,
                "errors": ["Receipt ID must be a positive integer"]
            }), 400
        
        # Use Repository Pattern
        result = receipt_repo.get_by_id(receipt_id)
        
        if result["success"]:
            return jsonify({
                "success": True,
                "message": "Receipt retrieved successfully",
                "data": {
                    "receipt": result["receipt"]
                }
            })
        else:
            if "Receipt not found" in result["errors"]:
                return jsonify({
                    "success": False,
                    "errors": result["errors"]
                }), 404
            else:
                return jsonify({
                    "success": False,
                    "errors": result["errors"]
                }), 500
                
    except Exception as e:
        logger.error(f"Unexpected error in get_receipt: {str(e)}")
        return jsonify({
            "success": False,
            "errors": ["Internal server error"]
        }), 500

@receipts_bp.route('/receipts/<int:receipt_id>', methods=['DELETE'])
def delete_receipt(receipt_id):
    """Delete a receipt by ID - SIMPLIFIED"""
    try:
        if receipt_id <= 0:
            return jsonify({
                "success": False,
                "errors": ["Receipt ID must be a positive integer"]
            }), 400
        
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if receipt exists
            cursor.execute("SELECT ReceiptId FROM Receipts WHERE ReceiptId = ?", (receipt_id,))
            if not cursor.fetchone():
                return jsonify({
                    "success": False,
                    "errors": ["Receipt not found"]
                }), 404
            
            # Delete associated tests first (foreign key constraint)
            cursor.execute("DELETE FROM Receipt_Tests WHERE ReceiptId = ?", (receipt_id,))
            
            # Delete receipt
            cursor.execute("DELETE FROM Receipts WHERE ReceiptId = ?", (receipt_id,))
            conn.commit()
            
            return jsonify({
                "success": True,
                "message": "Receipt deleted successfully"
            })
            
    except Exception as e:
        logger.error(f"Error deleting receipt {receipt_id}: {str(e)}")
        return jsonify({
            "success": False,
            "errors": ["Failed to delete receipt"]
        }), 500

# Health check endpoint
@receipts_bp.route('/receipts/health', methods=['GET'])
def health_check():
    """Health check for receipts service"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            
            return jsonify({
                "success": True,
                "message": "Receipts service is healthy",
                "data": {
                    "service": "receipts",
                    "status": "healthy",
                    "timestamp": datetime.now().isoformat()
                }
            })
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            "success": False,
            "errors": ["Database connection failed"],
            "message": "Receipts service is degraded"
        }), 503