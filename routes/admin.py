# admin.py - COMPLETE UPDATED VERSION WITH REAL-TIME REPORTS AND FIXED TEST MANAGEMENT
from flask import Blueprint, render_template, session, redirect, url_for, jsonify, request
from db import get_connection
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import json

admin_bp = Blueprint("admin", __name__)

def get_dashboard_stats():
    """Get statistics for admin dashboard - FIXED FOR YOUR SCHEMA"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Get staff count
        cursor.execute("SELECT COUNT(*) FROM Users WHERE IsActive = 1 AND Role != 'Admin'")
        staff_count = cursor.fetchone()[0]
        
        # Get doctors count
        cursor.execute("SELECT COUNT(*) FROM Doctors WHERE IsActive = 1")
        doctors_count = cursor.fetchone()[0]
        
        # Get tests count
        cursor.execute("SELECT COUNT(*) FROM Tests WHERE IsActive = 1")
        tests_count = cursor.fetchone()[0]
        
        # Get monthly revenue - FIXED: Use Amount instead of TotalAmount
        cursor.execute("""
            SELECT ISNULL(SUM(Amount), 0) 
            FROM Patients 
            WHERE MONTH(RegDate) = MONTH(GETDATE()) 
            AND YEAR(RegDate) = YEAR(GETDATE())
        """)
        monthly_revenue = cursor.fetchone()[0] or 0
        
        # Get today's patients count
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute("SELECT COUNT(*) FROM Patients WHERE CONVERT(date, RegDate) = ?", (today,))
        today_patients = cursor.fetchone()[0] or 0
        
        # Get today's revenue - FIXED: Use Amount instead of TotalAmount
        cursor.execute("SELECT ISNULL(SUM(Amount), 0) FROM Patients WHERE CONVERT(date, RegDate) = ?", (today,))
        today_revenue = cursor.fetchone()[0] or 0
        
        return {
            'staff_count': staff_count,
            'doctors_count': doctors_count,
            'tests_count': tests_count,
            'monthly_revenue': monthly_revenue,
            'today_patients': today_patients,
            'today_revenue': today_revenue
        }
        
    except Exception as e:
        print(f"Error getting dashboard stats: {e}")
        return {
            'staff_count': 0,
            'doctors_count': 0,
            'tests_count': 0,
            'monthly_revenue': 0,
            'today_patients': 0,
            'today_revenue': 0
        }
    finally:
        cursor.close()
        conn.close()

@admin_bp.route("/admin")
def admin_dashboard():
    if session.get("role") != "Admin":
        return redirect(url_for("auth.login_page"))
    
    stats = get_dashboard_stats()
    return render_template("admin_dashboard.html", 
                         full_name=session.get('fullname'),
                         **stats)

# ===========================================
# REAL-TIME REPORTS APIs - FIXED FOR YOUR SCHEMA
# ===========================================

@admin_bp.route("/admin/api/daily-stats")
def get_daily_stats():
    """Get today's statistics - FIXED FOR YOUR SCHEMA"""
    if session.get("role") != "Admin":
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    conn = get_connection()
    cursor = conn.cursor()
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Today's patients count
        cursor.execute("SELECT COUNT(*) FROM Patients WHERE CONVERT(date, RegDate) = ?", (today,))
        today_patients = cursor.fetchone()[0] or 0
        
        # Today's revenue - FIXED: Use Amount instead of TotalAmount
        cursor.execute("SELECT ISNULL(SUM(Amount), 0) FROM Patients WHERE CONVERT(date, RegDate) = ?", (today,))
        today_revenue = cursor.fetchone()[0] or 0
        
        # Today's tests performed
        cursor.execute("SELECT Tests FROM Patients WHERE CONVERT(date, RegDate) = ?", (today,))
        today_tests_data = cursor.fetchall()
        
        test_count = 0
        for test_row in today_tests_data:
            if test_row[0]:
                tests = test_row[0].split(',')
                test_count += len(tests)
        
        # Today's patients by gender
        cursor.execute("""
            SELECT Gender, COUNT(*) 
            FROM Patients 
            WHERE CONVERT(date, RegDate) = ? 
            GROUP BY Gender
        """, (today,))
        
        gender_data = cursor.fetchall()
        gender_stats = {}
        for gender, count in gender_data:
            if gender:
                gender_stats[gender] = count
        
        return jsonify({
            'success': True,
            'date': today,
            'patients': today_patients,
            'revenue': float(today_revenue),
            'tests': test_count,
            'gender_stats': gender_stats,
            'avg_amount': round(float(today_revenue / today_patients) if today_patients > 0 else 0, 2),
            'tests_per_patient': round(test_count / today_patients, 1) if today_patients > 0 else 0
        })
        
    except Exception as e:
        print(f"Error in daily stats: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})
    finally:
        cursor.close()
        conn.close()

@admin_bp.route("/admin/api/weekly-stats")
def get_weekly_stats():
    """Get weekly statistics - FIXED FOR YOUR SCHEMA"""
    if session.get("role") != "Admin":
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    conn = get_connection()
    cursor = conn.cursor()
    try:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=6)
        
        # Get daily breakdown - FIXED: Use Amount instead of TotalAmount
        daily_data = {}
        for i in range(7):
            date = start_date + timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')
            
            cursor.execute("""
                SELECT COUNT(*), ISNULL(SUM(Amount), 0)
                FROM Patients 
                WHERE CONVERT(date, RegDate) = ?
            """, (date_str,))
            
            result = cursor.fetchone()
            patients_count = result[0] or 0 if result else 0
            revenue = float(result[1]) if result and result[1] else 0
            
            daily_data[date_str] = {
                'patients': patients_count,
                'revenue': revenue,
                'tests': 0
            }
        
        # Calculate tests for each day
        cursor.execute("""
            SELECT CONVERT(date, RegDate) as reg_date, Tests
            FROM Patients 
            WHERE CONVERT(date, RegDate) BETWEEN ? AND ?
        """, (start_date, end_date))
        
        test_data = cursor.fetchall()
        for row in test_data:
            if row and row[0] and row[1]:
                date_str = row[0].strftime('%Y-%m-%d')
                if date_str in daily_data:
                    tests = row[1].split(',')
                    daily_data[date_str]['tests'] += len(tests)
        
        # Calculate totals
        total_patients = sum(day['patients'] for day in daily_data.values())
        total_revenue = sum(day['revenue'] for day in daily_data.values())
        total_tests = sum(day['tests'] for day in daily_data.values())
        
        # Day names for chart
        day_names = []
        for i in range(7):
            day = start_date + timedelta(days=i)
            day_names.append(day.strftime('%a'))
        
        return jsonify({
            'success': True,
            'period': {
                'start': start_date.strftime('%Y-%m-%d'),
                'end': end_date.strftime('%Y-%m-%d')
            },
            'total_patients': total_patients,
            'total_revenue': total_revenue,
            'total_tests': total_tests,
            'daily_data': daily_data,
            'day_names': day_names,
            'avg_daily_patients': round(total_patients / 7, 1) if total_patients > 0 else 0,
            'avg_daily_revenue': round(total_revenue / 7, 2) if total_revenue > 0 else 0,
            'avg_daily_tests': round(total_tests / 7, 1) if total_tests > 0 else 0
        })
        
    except Exception as e:
        print(f"Error in weekly stats: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})
    finally:
        cursor.close()
        conn.close()

@admin_bp.route("/admin/api/monthly-stats")
def get_monthly_stats():
    """Get monthly statistics - FIXED FOR YOUR SCHEMA"""
    if session.get("role") != "Admin":
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    conn = get_connection()
    cursor = conn.cursor()
    try:
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        # Monthly patients and revenue - FIXED: Use Amount instead of TotalAmount
        cursor.execute("""
            SELECT COUNT(*), ISNULL(SUM(Amount), 0)
            FROM Patients 
            WHERE MONTH(RegDate) = ? AND YEAR(RegDate) = ?
        """, (current_month, current_year))
        
        result = cursor.fetchone()
        total_patients = result[0] or 0 if result else 0
        total_revenue = float(result[1]) if result and result[1] else 0
        
        # Weekly breakdown
        weeks_data = {}
        for week in range(1, 6):  # Up to 5 weeks
            weeks_data[f'Week {week}'] = {
                'patients': 0,
                'revenue': 0,
                'tests': 0
            }
        
        # Get all patients for the month - FIXED: Use Amount instead of TotalAmount
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN DATEPART(day, RegDate) BETWEEN 1 AND 7 THEN 1
                    WHEN DATEPART(day, RegDate) BETWEEN 8 AND 14 THEN 2
                    WHEN DATEPART(day, RegDate) BETWEEN 15 AND 21 THEN 3
                    WHEN DATEPART(day, RegDate) BETWEEN 22 AND 28 THEN 4
                    ELSE 5
                END as week_num,
                Amount, Tests
            FROM Patients 
            WHERE MONTH(RegDate) = ? AND YEAR(RegDate) = ?
        """, (current_month, current_year))
        
        patients_data = cursor.fetchall()
        for row in patients_data:
            if row and row[0]:
                week_num = row[0]
                week_key = f'Week {week_num}'
                
                if week_key in weeks_data:
                    weeks_data[week_key]['patients'] += 1
                    weeks_data[week_key]['revenue'] += float(row[1]) if row[1] else 0
                    if row[2]:
                        tests = row[2].split(',')
                        weeks_data[week_key]['tests'] += len(tests)
        
        # Doctor-wise revenue (Top 5) - FIXED: Use Amount instead of TotalAmount
        cursor.execute("""
            SELECT Doctor, ISNULL(SUM(Amount), 0) as revenue
            FROM Patients 
            WHERE MONTH(RegDate) = ? AND YEAR(RegDate) = ? 
                AND Doctor IS NOT NULL AND Doctor != ''
            GROUP BY Doctor
            ORDER BY revenue DESC
        """, (current_month, current_year))
        
        doctor_revenue = {}
        doctor_data = cursor.fetchall()
        for row in doctor_data[:5]:  # Top 5 doctors
            if row and row[0]:
                doctor_revenue[row[0]] = float(row[1]) if row[1] else 0
        
        # Most common tests this month
        cursor.execute("""
            SELECT Tests FROM Patients 
            WHERE MONTH(RegDate) = ? AND YEAR(RegDate) = ? 
                AND Tests IS NOT NULL AND Tests != ''
        """, (current_month, current_year))
        
        all_tests_data = cursor.fetchall()
        test_counts = {}
        for row in all_tests_data:
            if row and row[0]:
                tests = row[0].split(',')
                for test in tests:
                    test = test.strip()
                    if test:
                        test_counts[test] = test_counts.get(test, 0) + 1
        
        # Get top 5 tests
        top_tests = sorted(test_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        top_tests_dict = dict(top_tests)
        
        return jsonify({
            'success': True,
            'month': datetime.now().strftime('%B %Y'),
            'total_patients': total_patients,
            'total_revenue': total_revenue,
            'weeks_data': weeks_data,
            'doctor_revenue': doctor_revenue,
            'top_tests': top_tests_dict,
            'avg_patient_value': round(total_revenue / total_patients, 2) if total_patients > 0 else 0,
            'weeks': list(weeks_data.keys())
        })
        
    except Exception as e:
        print(f"Error in monthly stats: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})
    finally:
        cursor.close()
        conn.close()

@admin_bp.route("/admin/api/test-statistics")
def get_test_statistics():
    """Get test-wise statistics - FIXED FOR YOUR SCHEMA"""
    if session.get("role") != "Admin":
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Get all tests
        cursor.execute("SELECT TestId, TestName, Price, Category FROM Tests WHERE IsActive = 1 ORDER BY TestName")
        all_tests = cursor.fetchall()
        
        test_stats = []
        for test in all_tests:
            test_id, test_name, price, category = test
            
            # Count patients who took this test - REMOVED IsActive check from Patients
            cursor.execute("""
                SELECT COUNT(*) 
                FROM Patients 
                WHERE Tests LIKE ?
            """, (f'%{test_name}%',))
            
            patient_count = cursor.fetchone()[0] or 0
            
            # Calculate revenue from this test - FIXED: Use Amount instead of TotalAmount
            cursor.execute("""
                SELECT ISNULL(SUM(Amount), 0)
                FROM Patients 
                WHERE Tests LIKE ?
            """, (f'%{test_name}%',))
            
            total_revenue = cursor.fetchone()[0] or 0
            
            test_stats.append({
                'test_id': test_id,
                'test_name': test_name,
                'price': float(price),
                'category': category or 'General',
                'patient_count': patient_count,
                'total_revenue': float(total_revenue),
                'popularity_rank': patient_count
            })
        
        # Sort by popularity and take top 10
        test_stats.sort(key=lambda x: x['popularity_rank'], reverse=True)
        top_tests = test_stats[:10]
        
        # Calculate category distribution
        category_stats = {}
        for test in top_tests:
            category = test['category']
            category_stats[category] = category_stats.get(category, 0) + 1
        
        # Calculate summary
        total_tests_performed = sum(t['patient_count'] for t in test_stats)
        total_revenue_from_tests = sum(t['total_revenue'] for t in test_stats)
        
        return jsonify({
            'success': True,
            'top_tests': top_tests,
            'total_tests_count': len(all_tests),
            'category_stats': category_stats,
            'summary': {
                'most_popular_test': top_tests[0]['test_name'] if top_tests else 'None',
                'total_tests_performed': total_tests_performed,
                'total_revenue_from_tests': total_revenue_from_tests
            }
        })
        
    except Exception as e:
        print(f"Error in test statistics: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})
    finally:
        cursor.close()
        conn.close()

@admin_bp.route("/admin/api/doctor-statistics")
def get_doctor_statistics():
    """Get doctor-wise statistics - FIXED FOR YOUR SCHEMA"""
    if session.get("role") != "Admin":
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Get all doctors
        cursor.execute("SELECT DoctorId, Name, Specialization FROM Doctors WHERE IsActive = 1 ORDER BY Name")
        all_doctors = cursor.fetchall()
        
        doctor_stats = []
        for doctor in all_doctors:
            doctor_id, doctor_name, specialization = doctor
            
            # Count patients referred by this doctor - REMOVED IsActive check from Patients
            cursor.execute("""
                SELECT COUNT(*), ISNULL(SUM(Amount), 0)
                FROM Patients 
                WHERE Doctor = ?
            """, (doctor_name,))
            
            result = cursor.fetchone()
            patient_count = result[0] or 0 if result else 0
            total_revenue = float(result[1]) if result and result[1] else 0
            
            if patient_count > 0:  # Only include doctors with patients
                doctor_stats.append({
                    'doctor_id': doctor_id,
                    'doctor_name': doctor_name,
                    'specialization': specialization or 'General',
                    'patient_count': patient_count,
                    'total_revenue': total_revenue,
                    'avg_revenue_per_patient': round(total_revenue / patient_count, 2) if patient_count > 0 else 0
                })
        
        # Sort by revenue and take top 10
        doctor_stats.sort(key=lambda x: x['total_revenue'], reverse=True)
        top_doctors = doctor_stats[:10]
        
        # Calculate specialization distribution
        specialization_stats = {}
        for doctor in top_doctors:
            spec = doctor['specialization']
            specialization_stats[spec] = specialization_stats.get(spec, 0) + doctor['patient_count']
        
        # Calculate summary
        total_patients_referred = sum(d['patient_count'] for d in doctor_stats)
        total_revenue_from_doctors = sum(d['total_revenue'] for d in doctor_stats)
        
        return jsonify({
            'success': True,
            'top_doctors': top_doctors,
            'total_doctors_count': len(all_doctors),
            'specialization_stats': specialization_stats,
            'summary': {
                'top_earning_doctor': top_doctors[0]['doctor_name'] if top_doctors else 'None',
                'total_patients_referred': total_patients_referred,
                'total_revenue_from_doctors': total_revenue_from_doctors
            }
        })
        
    except Exception as e:
        print(f"Error in doctor statistics: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})
    finally:
        cursor.close()
        conn.close()

@admin_bp.route("/admin/api/yearly-overview")
def get_yearly_overview():
    """Get yearly overview - FIXED FOR YOUR SCHEMA"""
    if session.get("role") != "Admin":
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    conn = get_connection()
    cursor = conn.cursor()
    try:
        current_year = datetime.now().year
        
        # Monthly breakdown for current year - FIXED: Use Amount instead of TotalAmount
        monthly_data = {}
        for month in range(1, 13):
            cursor.execute("""
                SELECT COUNT(*), ISNULL(SUM(Amount), 0)
                FROM Patients 
                WHERE MONTH(RegDate) = ? AND YEAR(RegDate) = ?
            """, (month, current_year))
            
            result = cursor.fetchone()
            monthly_data[month] = {
                'patients': result[0] or 0 if result else 0,
                'revenue': float(result[1]) if result and result[1] else 0
            }
        
        # Year totals - FIXED: Use Amount instead of TotalAmount
        cursor.execute("""
            SELECT COUNT(*), ISNULL(SUM(Amount), 0)
            FROM Patients 
            WHERE YEAR(RegDate) = ?
        """, (current_year,))
        
        result = cursor.fetchone()
        yearly_total_patients = result[0] or 0 if result else 0
        yearly_total_revenue = float(result[1]) if result and result[1] else 0
        
        # Month names for chart
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        return jsonify({
            'success': True,
            'year': current_year,
            'monthly_data': monthly_data,
            'month_names': month_names,
            'yearly_total_patients': yearly_total_patients,
            'yearly_total_revenue': yearly_total_revenue,
            'avg_monthly_patients': round(yearly_total_patients / 12, 1) if yearly_total_patients > 0 else 0,
            'avg_monthly_revenue': round(yearly_total_revenue / 12, 2) if yearly_total_revenue > 0 else 0
        })
        
    except Exception as e:
        print(f"Error in yearly overview: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})
    finally:
        cursor.close()
        conn.close()

# ===========================================
# STAFF MANAGEMENT APIs
# ===========================================

@admin_bp.route("/admin/staff")
def get_staff():
    """Get all staff members"""
    if session.get("role") != "Admin":
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT UserId, Username, FullName, Role FROM Users WHERE IsActive = 1 AND Role != 'Admin' ORDER BY UserId")
        staff = cursor.fetchall()
        
        staff_list = []
        for user in staff:
            staff_list.append({
                'UserId': user[0],
                'Username': user[1],
                'FullName': user[2],
                'Role': user[3]
            })
        
        return jsonify(staff_list)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        cursor.close()
        conn.close()

@admin_bp.route("/admin/staff/add", methods=["POST"])
def add_staff():
    """Add new staff member"""
    if session.get("role") != "Admin":
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    data = request.get_json()
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Check if username already exists
        cursor.execute("SELECT UserId FROM Users WHERE Username = ?", (data['username'],))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': 'Username already exists'})
        
        # Insert new staff
        hashed_password = generate_password_hash(data['password'])
        cursor.execute(
            "INSERT INTO Users (Username, Password, Role, FullName) VALUES (?, ?, ?, ?)",
            (data['username'], hashed_password, data['role'], data['full_name'])
        )
        conn.commit()
        
        return jsonify({'success': True, 'message': 'Staff added successfully'})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)})
    finally:
        cursor.close()
        conn.close()

# ===========================================
# DOCTOR MANAGEMENT APIs
# ===========================================

@admin_bp.route("/admin/doctors")
def get_doctors():
    """Get all doctors"""
    if session.get("role") != "Admin":
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT DoctorId, Name, Specialization, ContactNumber, ConsultationFee FROM Doctors WHERE IsActive = 1 ORDER BY DoctorId")
        doctors = cursor.fetchall()
        
        doctors_list = []
        for doctor in doctors:
            doctors_list.append({
                'DoctorId': doctor[0],
                'Name': doctor[1],
                'Specialization': doctor[2],
                'ContactNumber': doctor[3],
                'ConsultationFee': float(doctor[4]) if doctor[4] else 0.0
            })
        
        return jsonify(doctors_list)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        cursor.close()
        conn.close()

@admin_bp.route("/admin/doctors/add", methods=["POST"])
def add_doctor():
    """Add new doctor"""
    if session.get("role") != "Admin":
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    data = request.get_json()
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO Doctors (Name, Specialization, ContactNumber, ConsultationFee) VALUES (?, ?, ?, ?)",
            (data['name'], data.get('specialization'), data.get('contact_number'), data.get('consultation_fee', 0))
        )
        conn.commit()
        
        return jsonify({'success': True, 'message': 'Doctor added successfully'})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)})
    finally:
        cursor.close()
        conn.close()

# ===========================================
# TEST MANAGEMENT APIs - FIXED FOR YOUR SCHEMA
# ===========================================

@admin_bp.route("/admin/tests")
def get_tests():
    """Get all tests - FIXED VERSION WITH CORRECT COLUMN NAMES"""
    if session.get("role") != "Admin":
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT 
                TestId, 
                TestName, 
                Category, 
                Price, 
                ReportingTime,
                Range_Text,
                SampleType,
                Male_Range_Min,
                Male_Range_Max,
                Female_Range_Min,
                Female_Range_Max,
                Range_Unit,
                Interpretation_Low,
                Interpretation_Normal,
                Interpretation_High,
                Sample_Type,
                Methodology,
                Turnaround_Time,
                Department
            FROM Tests 
            WHERE IsActive = 1 
            ORDER BY TestId
        """)
        tests = cursor.fetchall()
        
        tests_list = []
        for test in tests:
            tests_list.append({
                'TestId': test[0],
                'TestName': test[1],
                'Category': test[2],
                'Price': float(test[3]),
                'ReportingTime': test[4],
                'NormalRange': test[5],  # This is Range_Text in database
                'SampleType': test[6],
                'Male_Range_Min': float(test[7]) if test[7] else None,
                'Male_Range_Max': float(test[8]) if test[8] else None,
                'Female_Range_Min': float(test[9]) if test[9] else None,
                'Female_Range_Max': float(test[10]) if test[10] else None,
                'Range_Unit': test[11],
                'Interpretation_Low': test[12],
                'Interpretation_Normal': test[13],
                'Interpretation_High': test[14],
                'Sample_Type': test[15],
                'Methodology': test[16],
                'Turnaround_Time': test[17],
                'Department': test[18]
            })
        
        return jsonify(tests_list)
    except Exception as e:
        print(f"Error getting tests: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})
    finally:
        cursor.close()
        conn.close()

@admin_bp.route("/admin/tests/add", methods=["POST"])
def add_test():
    """Add new test - UPDATED FOR YOUR SCHEMA"""
    if session.get("role") != "Admin":
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    data = request.get_json()
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO Tests (
                TestName, 
                Price, 
                Category, 
                Range_Text,
                ReportingTime,
                SampleType,
                Male_Range_Min,
                Male_Range_Max,
                Female_Range_Min,
                Female_Range_Max,
                Range_Unit,
                Interpretation_Low,
                Interpretation_Normal,
                Interpretation_High,
                Sample_Type,
                Methodology,
                Turnaround_Time,
                Department,
                IsActive,
                CreatedAt
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, GETDATE())
        """, (
            data['test_name'],
            data['price'],
            data.get('category'),
            data.get('normal_range'),  # This goes to Range_Text
            data.get('reporting_time'),
            data.get('sample_type'),
            data.get('male_range_min'),
            data.get('male_range_max'),
            data.get('female_range_min'),
            data.get('female_range_max'),
            data.get('range_unit'),
            data.get('interpretation_low'),
            data.get('interpretation_normal'),
            data.get('interpretation_high'),
            data.get('sample_type'),
            data.get('methodology'),
            data.get('turnaround_time'),
            data.get('department')
        ))
        conn.commit()
        
        return jsonify({'success': True, 'message': 'Test added successfully'})
    except Exception as e:
        conn.rollback()
        print(f"Error adding test: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})
    finally:
        cursor.close()
        conn.close()

@admin_bp.route("/admin/tests/update/<int:test_id>", methods=["PUT"])
def update_test(test_id):
    """Update test - UPDATED FOR YOUR SCHEMA"""
    if session.get("role") != "Admin":
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    data = request.get_json()
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE Tests SET 
                TestName = ?, 
                Price = ?, 
                Category = ?, 
                Range_Text = ?,
                ReportingTime = ?,
                SampleType = ?,
                Male_Range_Min = ?,
                Male_Range_Max = ?,
                Female_Range_Min = ?,
                Female_Range_Max = ?,
                Range_Unit = ?,
                Interpretation_Low = ?,
                Interpretation_Normal = ?,
                Interpretation_High = ?,
                Sample_Type = ?,
                Methodology = ?,
                Turnaround_Time = ?,
                Department = ?
            WHERE TestId = ?
        """, (
            data['test_name'],
            data['price'],
            data.get('category'),
            data.get('normal_range'),  # This goes to Range_Text
            data.get('reporting_time'),
            data.get('sample_type'),
            data.get('male_range_min'),
            data.get('male_range_max'),
            data.get('female_range_min'),
            data.get('female_range_max'),
            data.get('range_unit'),
            data.get('interpretation_low'),
            data.get('interpretation_normal'),
            data.get('interpretation_high'),
            data.get('sample_type'),
            data.get('methodology'),
            data.get('turnaround_time'),
            data.get('department'),
            test_id
        ))
        conn.commit()
        
        return jsonify({'success': True, 'message': 'Test updated successfully'})
    except Exception as e:
        conn.rollback()
        print(f"Error updating test: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})
    finally:
        cursor.close()
        conn.close()

@admin_bp.route("/admin/tests/delete/<int:test_id>", methods=["DELETE"])
def delete_test(test_id):
    """Delete test (soft delete)"""
    if session.get("role") != "Admin":
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("UPDATE Tests SET IsActive = 0 WHERE TestId = ?", (test_id,))
        conn.commit()
        
        return jsonify({'success': True, 'message': 'Test deleted successfully'})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)})
    finally:
        cursor.close()
        conn.close()