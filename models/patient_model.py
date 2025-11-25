# models/patient_model.py - UPDATE THIS FILE

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