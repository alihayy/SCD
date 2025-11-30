# models/patient_model.py
import re
from db import get_connection

def _to_snake(name: str) -> str:
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)
    return s2.replace(" ", "_").lower()

class Patient:
    def __init__(self, mr_no=None, reg_date=None, reporting_date=None, name=None, gender=None, age=None, doctor=None, tests=None, amount=None):
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
    def add_patient(reg_date, reporting_date, name, gender, age, doctor, tests, amount):
        conn = get_connection()
        cursor = conn.cursor()

        insert_sql = """
        INSERT INTO Patients (RegDate, ReportingDate, Name, Gender, Age, Doctor, Tests, Amount)
        OUTPUT INSERTED.MrNo
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        cursor.execute(insert_sql, (reg_date, reporting_date, name, gender, age, doctor, tests, amount))
        inserted = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()

        if inserted:
            return int(inserted[0])
        return None

    @staticmethod
    def get_all_patients():
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT MrNo, RegDate, ReportingDate, Name, Gender, Age, Doctor, Tests, Amount FROM Patients ORDER BY MrNo DESC")
        cols = [col[0] for col in cursor.description]
        snake_cols = [_to_snake(c) for c in cols]
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        results = []
        for row in rows:
            results.append(dict(zip(snake_cols, row)))
        return results
