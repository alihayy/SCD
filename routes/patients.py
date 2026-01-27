# routes/patients.py
from flask import Blueprint, render_template, request, jsonify, send_file
from models.patient_model import Patient
from io import BytesIO
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from datetime import datetime
import logging
from abc import ABC, abstractmethod
import json
from db import get_connection  # ADD THIS IMPORT

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

patients_bp = Blueprint('patients', __name__, template_folder='../templates')

# ---------------------------------------
# FACTORY PATTERN - Response Factory
# ---------------------------------------
class ResponseFactory:
    @staticmethod
    def create_response(response_type, data=None, message=None, errors=None, metadata=None):
        """Factory method to create standardized API responses"""
        base_response = {
            "timestamp": datetime.now().isoformat(),
            "success": response_type == "success",
            "version": "1.0"
        }
        
        if response_type == "success":
            if data is not None:
                base_response["data"] = data
            if message:
                base_response["message"] = message
            if metadata:
                base_response["metadata"] = metadata
                
        elif response_type == "error":
            if errors:
                base_response["errors"] = errors if isinstance(errors, list) else [errors]
            if message:
                base_response["message"] = message
                
        else:  # info response
            base_response["message"] = message or "Request processed"
            if data is not None:
                base_response["data"] = data
        
        return base_response

# ---------------------------------------
# STRATEGY PATTERN - PDF Generation Strategies
# ---------------------------------------
class PDFGenerationStrategy(ABC):
    """Abstract base class for PDF generation strategies"""
    
    @abstractmethod
    def generate(self, patient_data, buffer):
        pass

class ReceiptPDFStrategy(PDFGenerationStrategy):
    """Strategy for generating receipt PDFs"""
    
    def generate(self, patient_data, buffer):
        try:
            doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=20, bottomMargin=20)
            elements = []
            styles = getSampleStyleSheet()
            styles['Normal'].fontSize = 11

            # Header Section
            elements.extend(self._create_header(styles))
            
            # Patient Information Section
            elements.extend(self._create_patient_info(patient_data, styles))
            
            # Tests Details Section
            elements.extend(self._create_tests_section(patient_data, styles))
            
            # Footer Section
            elements.extend(self._create_footer(styles))
            
            doc.build(elements)
            buffer.seek(0)
            return {"success": True, "buffer": buffer}
            
        except Exception as e:
            logger.error(f"PDF generation error: {str(e)}")
            return {"success": False, "error": str(e)}

    def _create_header(self, styles):
        """Create PDF header with logo and clinic info"""
        elements = []
        
        logo_path = "static/logo.png"
        try:
            logo_img = Image(logo_path, 1.2 * inch, 1.2 * inch)
        except:
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
            colWidths=[1.4 * inch, A4[0] - (1.4 * inch + 60)]
        )

        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.Color(0, 0.4, 0.4)),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))

        elements.append(header_table)
        elements.append(Spacer(1, 18))
        return elements

    def _create_patient_info(self, patient_data, styles):
        """Create patient information section"""
        elements = []
        
        patient_info = [
            ["MR No:", patient_data.get("mr_no", ""), "Reg Date:", patient_data.get("reg_date", "")],
            ["Name:", patient_data.get("name", ""), "Reporting Date:", patient_data.get("reporting_date", "")],
            ["Gender:", patient_data.get("gender", ""), "Age:", str(patient_data.get("age", ""))],
            ["Doctor:", patient_data.get("doctor", ""), "Amount:", f"₹{patient_data.get('amount', '')}"],
        ]

        info_table = Table(patient_info, colWidths=[90, 180, 90, A4[0] - (90 + 180 + 90 + 60)])
        info_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ]))

        elements.append(info_table)
        elements.append(Spacer(1, 12))
        return elements

    def _create_tests_section(self, patient_data, styles):
        """Create tests information section"""
        elements = []
        
        tests_text = patient_data.get("tests", "")
        tests_paragraph = Paragraph(f"<b>Tests Investigations:</b><br/>{tests_text}", styles['Normal'])
        elements.append(tests_paragraph)
        elements.append(Spacer(1, 12))
        
        return elements

    def _create_footer(self, styles):
        """Create PDF footer"""
        elements = []
        
        footer_text = """
        <b><i>Thank you for choosing Citi Lab & Diagnostic Centre</i></b><br/>
        <i>For any queries, please contact: 0301-5225117</i><br/>
        <i>This is a computer generated receipt</i>
        """
        
        footer_paragraph = Paragraph(footer_text, styles['Normal'])
        elements.append(Spacer(1, 20))
        elements.append(footer_paragraph)
        
        return elements

class DetailedReportPDFStrategy(PDFGenerationStrategy):
    """Strategy for generating detailed report PDFs (extensible for future)"""
    
    def generate(self, patient_data, buffer):
        # Implementation for detailed reports
        # This can be extended later for comprehensive lab reports
        return ReceiptPDFStrategy().generate(patient_data, buffer)

# ---------------------------------------
# NEW: LAB REPORT PDF STRATEGY
# ---------------------------------------
class LabReportPDFStrategy(PDFGenerationStrategy):
    """Strategy for generating detailed lab reports with ranges"""
    
    def generate(self, patient_data, buffer):
        try:
            doc = SimpleDocTemplate(buffer, pagesize=A4, 
                                   rightMargin=30, leftMargin=30, 
                                   topMargin=20, bottomMargin=20)
            elements = []
            styles = getSampleStyleSheet()
            
            # Header - SAME AS RECEIPT
            elements.extend(self._create_header(styles))
            
            # Patient Information - SAME AS RECEIPT
            elements.extend(self._create_patient_info(patient_data, styles))
            
            # Test Results Section - NEW WITH RANGES
            elements.extend(self._create_test_results(patient_data, styles))
            
            # Interpretation Section - NEW
            elements.extend(self._create_interpretation_section(styles))
            
            # Footer - SAME AS RECEIPT
            elements.extend(self._create_footer(styles))
            
            doc.build(elements)
            buffer.seek(0)
            return {"success": True, "buffer": buffer}
            
        except Exception as e:
            logger.error(f"Lab report PDF error: {str(e)}")
            return {"success": False, "error": str(e)}

    def _create_header(self, styles):
        """SAME HEADER LOGIC AS RECEIPT"""
        elements = []
        
        logo_path = "static/logo.png"
        try:
            logo_img = Image(logo_path, 1.2 * inch, 1.2 * inch)
        except:
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
            colWidths=[1.4 * inch, A4[0] - (1.4 * inch + 60)]
        )

        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.Color(0, 0.4, 0.4)),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))

        elements.append(header_table)
        elements.append(Spacer(1, 18))
        return elements

    def _create_patient_info(self, patient_data, styles):
        """SAME PATIENT INFO AS RECEIPT"""
        elements = []
        
        patient_info = [
            ["MR No:", patient_data.get("mr_no", ""), "Reg Date:", patient_data.get("reg_date", "")],
            ["Name:", patient_data.get("name", ""), "Reporting Date:", patient_data.get("reporting_date", "")],
            ["Gender:", patient_data.get("gender", ""), "Age:", str(patient_data.get("age", ""))],
            ["Doctor:", patient_data.get("doctor", ""), "Amount:", f"₹{patient_data.get('amount', '')}"],
        ]

        info_table = Table(patient_info, colWidths=[90, 180, 90, A4[0] - (90 + 180 + 90 + 60)])
        info_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ]))

        elements.append(info_table)
        elements.append(Spacer(1, 12))
        return elements

    def _create_test_results(self, patient_data, styles):
        """NEW: Create test results with gender-specific ranges"""
        elements = []
        
        # Title
        title = Paragraph(
            "<b><font size='14' color='#006D5B'>LABORATORY TEST REPORT</font></b>",
            styles['Heading2']
        )
        elements.append(title)
        elements.append(Spacer(1, 12))
        
        # Test results table with sample data
        gender = patient_data.get('gender', 'Male')
        
        # Sample test data - This would come from database in real implementation
        test_data = [
            ["Test", "Result", f"Normal Range ({gender})", "Units", "Status"],
            ["Hemoglobin (Hb)", "14.2", "Male: 13.5-17.5, Female: 12.0-15.5", "g/dL", "Normal"],
            ["WBC Count", "7.8", "4.5-11.0", "x10³/µL", "Normal"],
            ["Blood Glucose (Fasting)", "92", "70-100", "mg/dL", "Normal"],
            ["Serum Creatinine", "0.9", f"Male: 0.7-1.3, Female: 0.6-1.1", "mg/dL", "Normal"],
            ["Total Cholesterol", "185", "< 200", "mg/dL", "Normal"],
        ]
        
        test_table = Table(test_data, colWidths=[180, 80, 150, 60, 80])
        test_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0, 0.4, 0.4)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))

        elements.append(test_table)
        elements.append(Spacer(1, 20))
        
        return elements

    def _create_interpretation_section(self, styles):
        """Create interpretation/comment section"""
        elements = []
        
        interpretation_title = Paragraph(
            "<b><font size='12' color='#006D5B'>INTERPRETATION & COMMENTS:</font></b>",
            styles['Heading3']
        )
        elements.append(interpretation_title)
        elements.append(Spacer(1, 8))
        
        interpretation_text = Paragraph(
            "1. All test results are within normal reference ranges.<br/>"
            "2. Normal ranges are gender-specific as indicated.<br/>"
            "3. Please consult your physician for clinical correlation.<br/>"
            "4. For any queries, contact the laboratory at 0301-5225117.",
            styles['Normal']
        )
        elements.append(interpretation_text)
        elements.append(Spacer(1, 15))
        
        return elements

    def _create_footer(self, styles):
        """SAME FOOTER AS RECEIPT"""
        elements = []
        
        footer_text = """
        <b><i>Thank you for choosing Citi Lab & Diagnostic Centre</i></b><br/>
        <i>For any queries, please contact: 0301-5225117</i><br/>
        <i>This is a computer generated lab report</i>
        """
        
        footer_paragraph = Paragraph(footer_text, styles['Normal'])
        elements.append(Spacer(1, 20))
        elements.append(footer_paragraph)
        
        return elements

# ---------------------------------------
# PDF GENERATOR CONTEXT using Strategy Pattern
# ---------------------------------------
class PDFGenerator:
    """Context class that uses PDF generation strategies"""
    
    def __init__(self, strategy: PDFGenerationStrategy = None):
        self._strategy = strategy or ReceiptPDFStrategy()

    def set_strategy(self, strategy: PDFGenerationStrategy):
        """Set the PDF generation strategy"""
        self._strategy = strategy

    def generate_pdf(self, patient_data, pdf_type="receipt"):
        """Generate PDF using the current strategy"""
        try:
            # Set strategy based on PDF type
            if pdf_type == "detailed_report":
                self.set_strategy(DetailedReportPDFStrategy())
            elif pdf_type == "lab_report":
                self.set_strategy(LabReportPDFStrategy())
            else:
                self.set_strategy(ReceiptPDFStrategy())
            
            buffer = BytesIO()
            result = self._strategy.generate(patient_data, buffer)
            
            if result["success"]:
                return {
                    "success": True,
                    "buffer": result["buffer"],
                    "filename": f"{pdf_type}_{patient_data.get('mr_no', 'unknown')}.pdf"
                }
            else:
                return {"success": False, "error": result["error"]}
                
        except Exception as e:
            logger.error(f"PDF generator error: {str(e)}")
            return {"success": False, "error": str(e)}

# ---------------------------------------
# NEW: TEST MODEL CLASS
# ---------------------------------------
class TestModel:
    """Model for laboratory tests management"""
    
    @staticmethod
    def get_all_tests_with_details():
        """Get all tests with complete details including ranges"""
        try:
            with get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                
                cursor.execute("""
                    SELECT TestId, TestName, Price, Category, 
                           Male_Range_Min, Male_Range_Max,
                           Female_Range_Min, Female_Range_Max,
                           Range_Unit, Range_Text,
                           Interpretation_Low, Interpretation_Normal, Interpretation_High
                    FROM Tests 
                    WHERE IsActive = 1 
                    ORDER BY Category, TestName
                """)
                
                tests = cursor.fetchall()
                
                # Format ranges for each test
                for test in tests:
                    test['formatted_range'] = TestModel.format_normal_range(test)
                
                return tests
                
        except Exception as e:
            logger.error(f"Error fetching tests with details: {str(e)}")
            return []
    
    @staticmethod
    def format_normal_range(test):
        """Format normal range based on gender differences"""
        if test.get('Range_Text'):
            return test['Range_Text']
        
        male_min = test.get('Male_Range_Min')
        male_max = test.get('Male_Range_Max')
        female_min = test.get('Female_Range_Min')
        female_max = test.get('Female_Range_Max')
        unit = test.get('Range_Unit', '')
        
        if male_min is not None and female_min is not None:
            if male_min == female_min and male_max == female_max:
                return f"{male_min}-{male_max} {unit}"
            else:
                return f"Male: {male_min}-{male_max} {unit}, Female: {female_min}-{female_max} {unit}"
        elif male_min is not None:
            return f"{male_min}-{male_max} {unit}"
        else:
            return "See report"
    
    @staticmethod
    def get_test_by_id(test_id):
        """Get test details by ID"""
        try:
            with get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                
                cursor.execute("""
                    SELECT * FROM Tests 
                    WHERE TestId = %s AND IsActive = 1
                """, (test_id,))
                
                return cursor.fetchone()
                
        except Exception as e:
            logger.error(f"Error getting test by ID: {str(e)}")
            return None

# ---------------------------------------
# PATIENT SERVICE with Enhanced Validation
# ---------------------------------------
class PatientService:
    """Service layer for patient operations"""
    
    def __init__(self):
        self.response_factory = ResponseFactory()
        self.pdf_generator = PDFGenerator()

    def validate_patient_data(self, data):
        """Enhanced patient data validation"""
        errors = []
        
        required_fields = ['reg_date', 'reporting_date', 'name', 'gender', 'age', 'doctor', 'tests', 'amount']
        
        # Check required fields
        for field in required_fields:
            if not data.get(field):
                errors.append(f"{field.replace('_', ' ').title()} is required")

        # Name validation
        if data.get('name'):
            name = data['name'].strip()
            if len(name) < 2:
                errors.append("Name must be at least 2 characters long")
            elif len(name) > 100:
                errors.append("Name is too long (max 100 characters)")
            elif not all(c.isalpha() or c.isspace() or c in ".-" for c in name):
                errors.append("Name can only contain letters, spaces, dots, and hyphens")

        # Age validation
        if data.get('age'):
            try:
                age = int(data['age'])
                if age <= 0 or age > 120:
                    errors.append("Age must be between 1 and 120 years")
            except (ValueError, TypeError):
                errors.append("Age must be a valid number")

        # Date validation
        if data.get('reg_date') and data.get('reporting_date'):
            try:
                reg_date = datetime.strptime(data['reg_date'], '%Y-%m-%d')
                reporting_date = datetime.strptime(data['reporting_date'], '%Y-%m-%d')
                
                if reporting_date < reg_date:
                    errors.append("Reporting date cannot be before registration date")
                    
                today = datetime.today()
                if reg_date > today or reporting_date > today:
                    errors.append("Dates cannot be in the future")
                    
            except ValueError:
                errors.append("Invalid date format. Use YYYY-MM-DD")

        # Amount validation
        if data.get('amount'):
            try:
                amount = float(data['amount'])
                if amount <= 0:
                    errors.append("Amount must be greater than 0")
                if amount > 1000000:
                    errors.append("Amount seems too high. Please verify")
            except (ValueError, TypeError):
                errors.append("Amount must be a valid number")

        # Tests validation
        if data.get('tests'):
            tests = data['tests'].strip()
            if len(tests) < 5:
                errors.append("Tests description seems too short")
            if len(tests) > 1000:
                errors.append("Tests description is too long (max 1000 characters)")

        return errors

    def process_patient_addition(self, form_data):
        """Process patient addition with comprehensive validation"""
        try:
            # Prepare data
            data = {
                "reg_date": form_data.get('reg_date'),
                "reporting_date": form_data.get('reporting_date'),
                "name": form_data.get('name'),
                "gender": form_data.get('gender'),
                "age": form_data.get('age'),
                "doctor": form_data.get('doctor'),
                "tests": form_data.get('tests'),
                "amount": form_data.get('amount')
            }

            # Convert numeric fields
            if data["age"] and data["age"].isdigit():
                data["age"] = int(data["age"])

            try:
                data["amount"] = float(data["amount"]) if data["amount"] else None
            except:
                data["amount"] = None

            # Validate data
            validation_errors = self.validate_patient_data(data)
            if validation_errors:
                return self.response_factory.create_response(
                    "error",
                    errors=validation_errors,
                    message="Patient data validation failed"
                ), 400

            # Send to model
            result = Patient.add_patient(data)

            if result["success"]:
                return self.response_factory.create_response(
                    "success",
                    data={"mr_no": result["mr_no"]},
                    message="Patient added successfully",
                    metadata={"patient_name": data['name']}
                ), 201
            else:
                return self.response_factory.create_response(
                    "error",
                    errors=result.get("errors", ["Unknown error occurred"]),
                    message="Failed to add patient"
                ), 400

        except Exception as e:
            logger.error(f"Patient addition error: {str(e)}")
            return self.response_factory.create_response(
                "error",
                errors=["Internal server error"],
                message="Patient addition failed"
            ), 500

    def generate_patient_pdf(self, mr_no, pdf_type="receipt"):
        """Generate PDF for patient"""
        try:
            patients = Patient.get_all_patients()
            patient = next((p for p in patients if p.get('mr_no') == mr_no), None)

            if not patient:
                return self.response_factory.create_response(
                    "error",
                    errors=["Patient not found"],
                    message="PDF generation failed"
                ), 404

            # Generate PDF
            pdf_result = self.pdf_generator.generate_pdf(patient, pdf_type)
            
            if pdf_result["success"]:
                return send_file(
                    pdf_result["buffer"],
                    as_attachment=False,
                    download_name=pdf_result["filename"],
                    mimetype='application/pdf'
                )
            else:
                return self.response_factory.create_response(
                    "error",
                    errors=[f"PDF generation failed: {pdf_result['error']}"],
                    message="Failed to generate PDF"
                ), 500

        except Exception as e:
            logger.error(f"PDF generation route error: {str(e)}")
            return self.response_factory.create_response(
                "error",
                errors=["Internal server error"],
                message="PDF generation failed"
            ), 500

# Initialize service
patient_service = PatientService()

# ----------------------------------------
# 1️⃣ Patients Home Page
# ----------------------------------------
@patients_bp.route('/', methods=['GET'])
def patients_home():
    """Render patients home page"""
    try:
        patients = Patient.get_all_patients()
        today_date = datetime.now().strftime('%Y-%m-%d')
        
        return render_template('patients.html', 
                             patients=patients, 
                             today_date=today_date)
                             
    except Exception as e:
        logger.error(f"Patients home error: {str(e)}")
        return render_template('error.html', 
                             error_message="Failed to load patients"), 500


# ----------------------------------------
# 2️⃣ Add Patient Route (Enhanced) - FIXED VERSION
# ----------------------------------------
@patients_bp.route('/add', methods=['POST'])
def add_patient_route():
    """Add new patient with comprehensive validation - FIXED VERSION"""
    try:
        print("=== ADD PATIENT REQUEST RECEIVED ===")
        print("Form data received:", dict(request.form))
        
        # Prepare data
        data = {
            "reg_date": request.form.get('reg_date'),
            "reporting_date": request.form.get('reporting_date'),
            "name": request.form.get('name'),
            "gender": request.form.get('gender'),
            "age": request.form.get('age'),
            "doctor": request.form.get('doctor'),
            "tests": request.form.get('tests'),
            "amount": request.form.get('amount')
        }
        
        print("Processed data:", data)
        
        # Check for empty fields
        missing_fields = [field for field, value in data.items() if not value]
        if missing_fields:
            error_msg = f"Missing fields: {', '.join(missing_fields)}"
            print("Validation error:", error_msg)
            return jsonify({
                "success": False, 
                "errors": [error_msg]
            }), 400

        # Convert numeric fields
        if data["age"]:
            try:
                data["age"] = int(data["age"])
            except ValueError:
                return jsonify({
                    "success": False,
                    "errors": ["Age must be a valid number"]
                }), 400

        if data["amount"]:
            try:
                data["amount"] = float(data["amount"])
            except ValueError:
                return jsonify({
                    "success": False,
                    "errors": ["Amount must be a valid number"]
                }), 400

        print("Calling Patient.add_patient with:", data)
        
        # Send to model
        result = Patient.add_patient(data)
        print("Patient.add_patient result:", result)

        if result["success"]:
            return jsonify({
                "success": True,
                "message": "Patient added successfully",
                "mr_no": result["mr_no"]
            })
        else:
            return jsonify({
                "success": False, 
                "errors": result["errors"]
            }), 400

    except Exception as e:
        print("EXCEPTION in add_patient_route:", str(e))
        import traceback
        traceback.print_exc()
        
        return jsonify({
            "success": False, 
            "message": f"Server error: {str(e)}"
        }), 500


# ----------------------------------------
# 3️⃣ NEW ROUTE: Get All Tests for Dropdown
# ----------------------------------------
@patients_bp.route('/api/tests', methods=['GET'])
def get_all_tests():
    """Get all active tests for dropdown selection"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Query to get all active tests
            cursor.execute("""
                SELECT TestId, TestName, Price, Category, NormalRange 
                FROM Tests 
                WHERE IsActive = 1 
                ORDER BY TestName
            """)
            
            tests = []
            for row in cursor.fetchall():
                tests.append({
                    'TestId': row[0],
                    'TestName': row[1],
                    'Price': float(row[2]) if row[2] else 0.0,
                    'Category': row[3],
                    'NormalRange': row[4]
                })
            
            logger.info(f"Retrieved {len(tests)} tests from database")
            
            return jsonify(tests)
            
    except Exception as e:
        logger.error(f"Error fetching tests: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to load tests"
        }), 500


# ----------------------------------------
# NEW ROUTE: Get All Tests with Details
# ----------------------------------------
@patients_bp.route('/api/tests/details', methods=['GET'])
def get_all_tests_with_details():
    """Get all tests with complete details including ranges"""
    try:
        tests = TestModel.get_all_tests_with_details()
        return jsonify(tests)
        
    except Exception as e:
        logger.error(f"Error fetching tests with details: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to load tests details"
        }), 500


# ----------------------------------------
# NEW ROUTE: Get Test by ID
# ----------------------------------------
@patients_bp.route('/api/tests/<int:test_id>', methods=['GET'])
def get_test_by_id(test_id):
    """Get test details by ID"""
    try:
        test = TestModel.get_test_by_id(test_id)
        
        if test:
            return jsonify(test)
        else:
            return jsonify({
                "success": False,
                "error": "Test not found"
            }), 404
            
    except Exception as e:
        logger.error(f"Error fetching test by ID: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to load test details"
        }), 500


# ----------------------------------------
# 4️⃣ Generate PDF Receipt (Enhanced)
# ----------------------------------------
@patients_bp.route('/<int:mr_no>/receipt')
def generate_pdf(mr_no):
    """Generate PDF receipt for patient"""
    return patient_service.generate_patient_pdf(mr_no, "receipt")


@patients_bp.route('/<int:mr_no>/detailed-report')
def generate_detailed_report(mr_no):
    """Generate detailed report for patient (extensible)"""
    return patient_service.generate_patient_pdf(mr_no, "detailed_report")


# ----------------------------------------
# NEW: Generate Lab Report PDF
# ----------------------------------------
@patients_bp.route('/<int:mr_no>/lab-report')
def generate_lab_report(mr_no):
    """Generate lab report PDF with ranges"""
    return patient_service.generate_patient_pdf(mr_no, "lab_report")


# ----------------------------------------
# 5️⃣ Saved Patients Page - FIXED VERSION
# ----------------------------------------
@patients_bp.route('/saved', methods=['GET'])
def saved_patients():
    """Render saved patients page - FIXED VERSION"""
    try:
        patients = Patient.get_all_patients()
        
        # Calculate statistics for the template
        stats = {
            'total_patients': len(patients),
            'total_revenue': sum(float(p.get('amount', 0)) for p in patients),
            'male_patients': len([p for p in patients if p.get('gender') == 'Male']),
            'female_patients': len([p for p in patients if p.get('gender') == 'Female'])
        }
        
        return render_template('saved_patients.html', 
                             patients=patients,
                             stats=stats)
                             
    except Exception as e:
        logger.error(f"Saved patients error: {str(e)}")
        return render_template('error.html', 
                             error_message="Failed to load saved patients"), 500


# ----------------------------------------
# NEW: Lab Reports Management Page
# ----------------------------------------
@patients_bp.route('/lab-reports', methods=['GET'])
def lab_reports():
    """Render lab reports management page"""
    try:
        patients = Patient.get_all_patients()
        
        return render_template('lab_reports.html', 
                             patients=patients)
                             
    except Exception as e:
        logger.error(f"Lab reports error: {str(e)}")
        return render_template('error.html', 
                             error_message="Failed to load lab reports"), 500


# ----------------------------------------
# 6️⃣ Patient Statistics API
# ----------------------------------------
@patients_bp.route('/statistics', methods=['GET'])
def get_patient_statistics():
    """Get patient statistics"""
    try:
        patients = Patient.get_all_patients()
        
        statistics = {
            "total_patients": len(patients),
            "total_revenue": sum(float(p.get('amount', 0)) for p in patients),
            "gender_distribution": {
                "male": len([p for p in patients if p.get('gender') == 'Male']),
                "female": len([p for p in patients if p.get('gender') == 'Female']),
                "other": len([p for p in patients if p.get('gender') not in ['Male', 'Female']])
            },
            "recent_patients": len([p for p in patients if p.get('reg_date') == datetime.now().strftime('%Y-%m-%d')])
        }
        
        return jsonify(
            ResponseFactory.create_response(
                "success",
                data=statistics,
                message="Patient statistics retrieved successfully"
            )
        )
        
    except Exception as e:
        logger.error(f"Statistics error: {str(e)}")
        return jsonify(
            ResponseFactory.create_response(
                "error",
                errors=["Failed to retrieve statistics"],
                message="Statistics retrieval failed"
            )
        ), 500


# ----------------------------------------
# 7️⃣ Health Check Endpoint
# ----------------------------------------
@patients_bp.route('/health', methods=['GET'])
def health_check():
    """Health check for patients service"""
    try:
        patients = Patient.get_all_patients()
        
        health_info = {
            "service": "patients",
            "status": "healthy",
            "total_patients": len(patients),
            "database_connected": True,
            "pdf_generation_available": True
        }
        
        return jsonify(
            ResponseFactory.create_response(
                "success",
                data=health_info,
                message="Patients service is healthy"
            )
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify(
            ResponseFactory.create_response(
                "error",
                errors=["Service degraded"],
                message="Patients service health check failed"
            )
        ), 500


# ----------------------------------------
# 8️⃣ UPDATE PATIENT ROUTE - ADD THIS
# ----------------------------------------
@patients_bp.route('/update/<int:mr_no>', methods=['PUT'])
def update_patient(mr_no):
    """Update patient information"""
    try:
        print(f"=== UPDATE PATIENT REQUEST FOR MR_NO: {mr_no} ===")
        
        # Get JSON data from request
        data = request.get_json()
        print("Update data received:", data)
        
        if not data:
            return jsonify({
                "success": False,
                "message": "No data provided for update"
            }), 400
        
        # Required fields validation
        required_fields = ['name', 'age', 'gender', 'doctor', 'tests', 'amount']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            return jsonify({
                "success": False,
                "message": f"Missing required fields: {', '.join(missing_fields)}"
            }), 400
        
        # Convert numeric fields
        try:
            data["age"] = int(data["age"])
            data["amount"] = float(data["amount"])
        except (ValueError, TypeError) as e:
            return jsonify({
                "success": False,
                "message": "Invalid age or amount format"
            }), 400
        
        # Update patient in database
        result = Patient.update_patient(mr_no, data)
        
        if result["success"]:
            return jsonify({
                "success": True,
                "message": "Patient updated successfully",
                "mr_no": mr_no
            })
        else:
            return jsonify({
                "success": False,
                "message": result.get("message", "Failed to update patient")
            }), 400
            
    except Exception as e:
        print(f"EXCEPTION in update_patient: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            "success": False,
            "message": f"Server error: {str(e)}"
        }), 500


# ----------------------------------------
# 9️⃣ DELETE PATIENT ROUTE - ADD THIS
# ----------------------------------------
@patients_bp.route('/delete/<int:mr_no>', methods=['DELETE'])
def delete_patient(mr_no):
    """Delete patient record"""
    try:
        print(f"=== DELETE PATIENT REQUEST FOR MR_NO: {mr_no} ===")
        
        # Delete patient from database
        result = Patient.delete_patient(mr_no)
        
        if result["success"]:
            return jsonify({
                "success": True,
                "message": "Patient deleted successfully",
                "mr_no": mr_no
            })
        else:
            return jsonify({
                "success": False,
                "message": result.get("message", "Failed to delete patient")
            }), 400
            
    except Exception as e:
        print(f"EXCEPTION in delete_patient: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            "success": False,
            "message": f"Server error: {str(e)}"
        }), 500
    
    # ----------------------------------------
# NEW: Simple Test Management Routes
# ----------------------------------------
@patients_bp.route('/tests/manage', methods=['GET'])
def manage_tests():
    """Simple page to manage test ranges"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT TestId, TestName, Price, Category, 
                       Male_Range_Min, Male_Range_Max,
                       Female_Range_Min, Female_Range_Max,
                       Range_Unit, Range_Text,
                       Interpretation_Normal
                FROM Tests 
                ORDER BY TestName
            """)
            tests = cursor.fetchall()
        
        return render_template('simple_manage_tests.html', tests=tests)
        
    except Exception as e:
        logger.error(f"Manage tests error: {str(e)}")
        return render_template('error.html', 
                             error_message="Failed to load tests"), 500


@patients_bp.route('/tests/update', methods=['POST'])
def update_test_ranges():
    """Update test ranges"""
    try:
        data = request.json
        test_id = data['test_id']
        
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE Tests SET
                    Male_Range_Min = ?,
                    Male_Range_Max = ?,
                    Female_Range_Min = ?,
                    Female_Range_Max = ?,
                    Range_Unit = ?,
                    Range_Text = ?
                WHERE TestId = ?
            """, (
                data.get('male_min') or None,
                data.get('male_max') or None,
                data.get('female_min') or None,
                data.get('female_max') or None,
                data.get('unit') or None,
                data.get('range_text') or None,
                test_id
            ))
            conn.commit()
        
        return jsonify({'success': True, 'message': 'Ranges updated successfully!'})
        
    except Exception as e:
        logger.error(f"Update test error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500