# models/patient_model.py - UPDATED WITH EDIT AND DELETE METHODS

import re
from db import get_connection

def _to_snake(name: str) -> str:
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)
    return s2.replace(" ", "_").lower()

def validate_patient(data):
    errors = []
    required = ['reg_date', 'reporting_date', 'name', 'gender', 'age', 'doctor', 'tests', 'amount']
    
    for field in required:
        if not data.get(field):
            errors.append(f"{field} is required.")

    # Name validation
    if data.get('name') and not re.match(r'^[A-Za-z\s\.\-]+$', data['name']):
        errors.append("Name must contain only letters, spaces, dots, and hyphens.")

    # Age validation
    if data.get('age'):
        try:
            age_val = int(data['age'])
            if age_val <= 0 or age_val > 120:
                errors.append("Age must be between 1 and 120.")
        except:
            errors.append("Age must be a valid number.")

    # Gender validation
    valid_genders = ["Male", "Female", "Other"]
    if data.get('gender') not in valid_genders:
        errors.append("Invalid gender selected.")

    # Amount validation
    try:
        float(data['amount'])
    except:
        errors.append("Amount must be numeric.")

    return errors

class Patient:
    def __init__(self, mr_no=None, reg_date=None, reporting_date=None, name=None, gender=None,
                 age=None, doctor=None, tests=None, amount=None):
        self.mr_no = mr_no
        self.reg_date = reg_date
        self.reporting_date = reporting_date
        self.name = name
        self.gender = gender
        self.age = age
        self.doctor = doctor
        self.tests = tests
        self.amount = amount

    def to_dict(self):
        return {
            "mr_no": self.mr_no,
            "reg_date": self.reg_date,
            "reporting_date": self.reporting_date,
            "name": self.name,
            "gender": self.gender,
            "age": self.age,
            "doctor": self.doctor,
            "tests": self.tests,
            "amount": self.amount
        }

    @staticmethod
    def add_patient(data: dict):
        # 1. VALIDATE FIRST
        errors = validate_patient(data)
        if errors:
            return {"success": False, "errors": errors}

        conn = None
        cursor = None
        try:
            conn = get_connection()
            cursor = conn.cursor()

            query = """
                INSERT INTO Patients 
                (RegDate, ReportingDate, Name, Gender, Age, Doctor, Tests, Amount)
                OUTPUT INSERTED.MrNo
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """

            cursor.execute(query, (
                data['reg_date'],
                data['reporting_date'],
                data['name'],
                data['gender'],
                data['age'],
                data['doctor'],
                data['tests'],
                data['amount']
            ))

            inserted = cursor.fetchone()
            conn.commit()

            return {"success": True, "mr_no": inserted[0]}

        except Exception as e:
            print(f"Database Error: {str(e)}")  # Debug print
            if conn:
                conn.rollback()
            return {"success": False, "errors": [f"Database error: {str(e)}"]}

        finally:
            try:
                if cursor:
                    cursor.close()
                if conn:
                    conn.close()
            except Exception as e:
                print(f"Error closing connection: {str(e)}")

    @staticmethod
    def get_all_patients():
        conn = None
        cursor = None
        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT MrNo, RegDate, ReportingDate, Name, Gender, Age, Doctor, Tests, Amount
                FROM Patients
                ORDER BY MrNo DESC
            """)

            cols = [col[0] for col in cursor.description]
            snake_cols = [_to_snake(c) for c in cols]
            rows = cursor.fetchall()

            return [dict(zip(snake_cols, row)) for row in rows]

        except Exception as e:
            print(f"Error fetching patients: {str(e)}")  # Debug print
            return []

        finally:
            try:
                if cursor:
                    cursor.close()
                if conn:
                    conn.close()
            except Exception as e:
                print(f"Error closing connection: {str(e)}")

    # =============================================
    # NEW METHODS FOR EDIT AND DELETE FUNCTIONALITY
    # =============================================

    @staticmethod
    def update_patient(mr_no, data):
        """Update patient in database"""
        conn = None
        cursor = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Check if patient exists
            cursor.execute("SELECT * FROM Patients WHERE MrNo = ?", (mr_no,))
            if not cursor.fetchone():
                return {"success": False, "message": "Patient not found"}
            
            # Update patient
            cursor.execute("""
                UPDATE Patients 
                SET Name = ?, Age = ?, Gender = ?, Doctor = ?, Tests = ?, Amount = ?
                WHERE MrNo = ?
            """, (
                data['name'],
                data['age'], 
                data['gender'],
                data['doctor'],
                data['tests'],
                data['amount'],
                mr_no
            ))
            
            conn.commit()
            
            if cursor.rowcount > 0:
                return {"success": True, "message": "Patient updated successfully"}
            else:
                return {"success": False, "message": "No changes made"}
                
        except Exception as e:
            print(f"Database update error: {str(e)}")
            if conn:
                conn.rollback()
            return {"success": False, "message": f"Database error: {str(e)}"}
        
        finally:
            try:
                if cursor:
                    cursor.close()
                if conn:
                    conn.close()
            except Exception as e:
                print(f"Error closing connection: {str(e)}")

    @staticmethod  
    def delete_patient(mr_no):
        """Delete patient from database"""
        conn = None
        cursor = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Check if patient exists
            cursor.execute("SELECT * FROM Patients WHERE MrNo = ?", (mr_no,))
            if not cursor.fetchone():
                return {"success": False, "message": "Patient not found"}
            
            # Delete patient
            cursor.execute("DELETE FROM Patients WHERE MrNo = ?", (mr_no,))
            conn.commit()
            
            if cursor.rowcount > 0:
                return {"success": True, "message": "Patient deleted successfully"}
            else:
                return {"success": False, "message": "Failed to delete patient"}
                
        except Exception as e:
            print(f"Database delete error: {str(e)}")
            if conn:
                conn.rollback()
            return {"success": False, "message": f"Database error: {str(e)}"}
        
        finally:
            try:
                if cursor:
                    cursor.close()
                if conn:
                    conn.close()
            except Exception as e:
                print(f"Error closing connection: {str(e)}")

    @staticmethod
    def get_patient_by_mr_no(mr_no):
        """Get single patient by MR number"""
        conn = None
        cursor = None
        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT MrNo, RegDate, ReportingDate, Name, Gender, Age, Doctor, Tests, Amount
                FROM Patients 
                WHERE MrNo = ?
            """, (mr_no,))

            cols = [col[0] for col in cursor.description]
            snake_cols = [_to_snake(c) for c in cols]
            row = cursor.fetchone()

            if row:
                return dict(zip(snake_cols, row))
            else:
                return None

        except Exception as e:
            print(f"Error fetching patient: {str(e)}")
            return None

        finally:
            try:
                if cursor:
                    cursor.close()
                if conn:
                    conn.close()
            except Exception as e:
                print(f"Error closing connection: {str(e)}")

    @staticmethod
    def get_patient_statistics():
        """Get patient statistics for dashboard"""
        conn = None
        cursor = None
        try:
            conn = get_connection()
            cursor = conn.cursor()

            # Total patients count
            cursor.execute("SELECT COUNT(*) FROM Patients")
            total_patients = cursor.fetchone()[0]

            # Total revenue
            cursor.execute("SELECT SUM(Amount) FROM Patients")
            total_revenue = cursor.fetchone()[0] or 0

            # Gender distribution
            cursor.execute("SELECT Gender, COUNT(*) FROM Patients GROUP BY Gender")
            gender_distribution = {row[0]: row[1] for row in cursor.fetchall()}

            # Today's patients
            cursor.execute("SELECT COUNT(*) FROM Patients WHERE CAST(RegDate AS DATE) = CAST(GETDATE() AS DATE)")
            today_patients = cursor.fetchone()[0]

            return {
                "total_patients": total_patients,
                "total_revenue": float(total_revenue),
                "gender_distribution": gender_distribution,
                "today_patients": today_patients
            }

        except Exception as e:
            print(f"Error fetching statistics: {str(e)}")
            return {
                "total_patients": 0,
                "total_revenue": 0,
                "gender_distribution": {},
                "today_patients": 0
            }

        finally:
            try:
                if cursor:
                    cursor.close()
                if conn:
                    conn.close()
            except Exception as e:
                print(f"Error closing connection: {str(e)}")