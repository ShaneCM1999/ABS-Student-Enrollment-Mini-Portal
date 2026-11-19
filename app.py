from operator import itemgetter
import os
import csv
import io
import re
import random
from datetime import datetime, date, timezone

try:
    import openpyxl
    _XLSX_SUPPORTED = True
except ImportError:
    _XLSX_SUPPORTED = False

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
    Response,
    abort
)
from config import Config
from db import get_db, close_db, ensure_database_exists, init_db

STATUS_CHOICES = ["Active", "Withdrawn"]
GENDER_CHOICES = ["Male", "Female"]
GRADE_CHOICES = list(range(1, 13))  # Grades 1 through 12


def run_sql(query, params=None, fetchone=False, fetchall=False, commit=False):
    """
    Executes a Raw SQL query using the current request's DB connection.
    Supports parameterized placeholders (%s for MySQL, auto-adjusted for SQLite).
    Zero ORM - 100% Raw SQL.
    """
    db = get_db()
    cursor = db.cursor()

    clean_params = None
    if params:
        clean_params = tuple(
            p.isoformat() if isinstance(p, (date, datetime)) else p
            for p in params
        )

    if Config.DB_TYPE == "sqlite":
        query = query.replace("%s", "?")

    cursor.execute(query, clean_params or ())

    result = None
    if fetchone:
        result = cursor.fetchone()
    elif fetchall:
        result = cursor.fetchall()

    if commit:
        db.commit()

    return result


def normalize_student(row):
    """Normalize a student database row for template rendering."""
    if not row:
        return None

    d = dict(row)

    # Calculate initials
    names = (d.get("full_name") or "").strip().split()

    if len(names) >= 2:
        d["initials"] = f"{names[0][0]}{names[-1][0]}".upper()
    elif len(names) == 1:
        d["initials"] = names[0][:2].upper()
    else:
        d["initials"] = "ST"

    # Convert date_of_birth
    dob = d.get("date_of_birth")

    if isinstance(dob, str):
        try:
            d["date_of_birth"] = datetime.fromisoformat(
                dob.split(" ")[0]
            ).date()
        except ValueError:
            pass

    # Convert created_at and updated_at
    for field in ["created_at", "updated_at"]:
        value = d.get(field)

        if isinstance(value, str):
            try:
                d[field] = datetime.fromisoformat(value)
            except ValueError:
                try:
                    d[field] = datetime.strptime(
                        value,
                        "%Y-%m-%d %H:%M:%S"
                    )
                except ValueError:
                    pass

    class StudentRecord(dict):
        def __getattr__(self, name):
            try:
                return self[name]
            except KeyError:
                raise AttributeError(
                    f"'StudentRecord' object has no attribute '{name}'"
                )

    return StudentRecord(d)

def seed_sample_records():
    """Seed initial demo students, teachers, courses, and enrollments if table is empty."""
    try:
        count_row = run_sql("SELECT COUNT(*) AS count FROM students", fetchone=True)
        count = count_row["count"] if count_row else 0
        if count == 0:
            students = [
                ("S1001", "Alice Nguyen",    9,  None, None, "2009-03-12", "Female", "s1001@school.test", "Active"),
                ("S1002", "Brian Okafor",    10, None, None, "2008-07-04", "Male",   "s1002@school.test", "Active"),
                ("S1003", "Carla Reyes",     11, None, None, "2007-11-19", "Female", "s1003@school.test", "Active"),
                ("S1004", "Daniel Kim",      9,  None, None, "2009-01-28", "Male",   "s1004@school.test", "Active"),
                ("S1005", "Eva Martinez",    9,  None, None, "2009-05-30", "Female", "s1005@school.test", "Active"),
                ("S1006", "Felix Turner",    10, None, None, "2008-09-15", "Male",   "s1006@school.test", "Active"),
                ("S1007", "Grace Liu",       11, None, None, "2007-02-22", "Female", "s1007@school.test", "Active"),
                ("S1008", "Henry Patel",     9,  None, None, "2009-06-11", "Male",   "s1008@school.test", "Active"),
                ("S1009", "Isla Brown",      9,  None, None, "2009-08-03", "Female", "s1009@school.test", "Active"),
                ("S1010", "James Wilson",    10, None, None, "2008-12-25", "Male",   "s1010@school.test", "Active"),
                ("S1011", "Karen Adams",     11, None, None, "2007-04-14", "Female", "s1011@school.test", "Active"),
                ("S1012", "Liam Scott",      9,  None, None, "2009-10-07", "Male",   "s1012@school.test", "Active"),
                ("S1013", "Mia Robinson",    9,  None, None, "2009-02-18", "Female", "s1013@school.test", "Active"),
                ("S1014", "Noah Carter",     10, None, None, "2008-03-29", "Male",   "s1014@school.test", "Active"),
                ("S1015", "Olivia Hall",     11, None, None, "2007-07-08", "Female", "s1015@school.test", "Active"),
                ("S1016", "Patrick Young",   9,  None, None, "2009-11-01", "Male",   "s1016@school.test", "Active"),
                ("S1017", "Quinn Harris",    9,  None, None, "2009-04-23", "Female", "s1017@school.test", "Active"),
                ("S1018", "Ryan Lewis",      10, None, None, "2008-06-16", "Male",   "s1018@school.test", "Active"),
                ("S1019", "Sara Walker",     11, None, None, "2007-09-05", "Female", "s1019@school.test", "Active"),
                ("S1020", "Tyler Allen",     9,  None, None, "2009-12-20", "Male",   "s1020@school.test", "Active"),
                ("S1021", "Uma Patel",       9,  None, None, "2009-01-09", "Female", "s1021@school.test", "Active"),
                ("S1022", "Victor Cruz",     10, None, None, "2008-05-27", "Male",   "s1022@school.test", "Active"),
                ("S1023", "Wendy Morgan",    11, None, None, "2007-03-13", "Female", "s1023@school.test", "Active"),
                ("S1024", "Xander Brooks",   9,  None, None, "2009-07-31", "Male",   "s1024@school.test", "Active"),
                ("S1025", "Yara Sanders",    9,  None, None, "2009-09-18", "Female", "s1025@school.test", "Active"),
                ("S1026", "Zack Coleman",    10, None, None, "2008-11-06", "Male",   "s1026@school.test", "Active"),
                ("S1027", "Amy Bell",        11, None, None, "2007-01-24", "Female", "s1027@school.test", "Active"),
                ("S1028", "Ben Foster",      9,  None, None, "2009-03-02", "Male",   "s1028@school.test", "Active"),
                ("S1029", "Chloe Rivera",    9,  None, None, "2009-08-14", "Female", "s1029@school.test", "Active"),
                ("S1030", "Derek Hughes",    10, None, None, "2008-04-21", "Male",   "s1030@school.test", "Active"),
                ("S1031", "Ella Price",      11, None, None, "2007-06-10", "Female", "s1031@school.test", "Active"),
                ("S1032", "Frank Flores",    9,  None, None, "2009-10-28", "Male",   "s1032@school.test", "Active"),
                ("S1033", "Gina Ross",       9,  None, None, "2009-02-05", "Female", "s1033@school.test", "Active"),
                ("S1034", "Harry Butler",    10, None, None, "2008-07-19", "Male",   "s1034@school.test", "Active"),
                ("S1035", "Irene Simmons",   11, None, None, "2007-05-03", "Female", "s1035@school.test", "Active"),
                ("S1036", "Jake Reed",       9,  None, None, "2009-12-12", "Male",   "s1036@school.test", "Active"),
                ("S1037", "Kate Barnes",     9,  None, None, "2009-04-07", "Female", "s1037@school.test", "Active"),
                ("S1038", "Leo Griffin",     10, None, None, "2008-08-30", "Male",   "s1038@school.test", "Active"),
                ("S1039", "Mara Diaz",       11, None, None, "2007-10-16", "Female", "s1039@school.test", "Active"),
                ("S1040", "Nate Hayes",      9,  None, None, "2009-06-24", "Male",   "s1040@school.test", "Active"),
            ]
            for s in students:
                run_sql("""
                    INSERT INTO students 
                    (student_id, full_name, grade, parent_name, parent_phone, date_of_birth, gender, email, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, s, commit=True)

            teachers = [
                ("1", "Sarah Collins", "sarah.collins@school.test"),
                ("2", "Ahmed Mansour", "ahmed.mansour@school.test"),
                ("3", "Priya Nair", "priya.nair@school.test"),
                ("4", "David Miller", "david.miller@school.test"),
                ("5", "Layla Hassan", "layla.hassan@school.test"),
                ("6", "John Matthews", "john.matthews@school.test"),
            ]
            for t in teachers:
                run_sql("INSERT INTO teachers (teacher_id, full_name, email) VALUES (%s, %s, %s)", t, commit=True)

            courses = [
                ("MTH101", "Algebra 1", 9, "1", 22),
                ("MTH201", "Geometry", 10, "1", 22),
                ("MTH301", "Pre-Calculus", 11, "1", 20),
                ("ENG101", "English 9", 9, "2", 24),
                ("ENG201", "English 10", 10, "2", 24),
                ("ENG301", "English 11", 11, "2", 6),
                ("SCI101", "Biology", 9, "3", 22),
                ("SCI201", "Chemistry", 10, "3", 6),
                ("SCI301", "Physics", 11, "3", 20),
                ("CSC101", "Intro to Computing", 9, "4", 18),
                ("CSC201", "Programming", 10, "4", 18),
                ("HIS101", "World History", 10, "5", 24),
                ("ART101", "Art", 9, "6", 15),
                ("PE101", "Physical Education", 9, "6", 40),
            ]
            for c in courses:
                run_sql("INSERT INTO courses (course_code, title, grade_level, teacher_id, capacity) VALUES (%s, %s, %s, %s, %s)", c, commit=True)

            enrollments = [
                ("S1001", "CSC101", "2026-T1"),
                ("S1001", "ENG101", "2026-T1"),
                ("S1001", "ART101", "2026-T1"),
                ("S1001", "SCI101", "2026-T1"),
                ("S1002", "CSC201", "2026-T1"),
                ("S1002", "SCI201", "2026-T1"),
                ("S1002", "MTH201", "2026-T1"),
                ("S1002", "PE101",  "2026-T1"),
                ("S1003", "SCI301", "2026-T1"),
                ("S1003", "ENG301", "2026-T1"),
                ("S1003", "PE101",  "2026-T1"),
                ("S1003", "MTH301", "2026-T1"),
                ("S1004", "PE101",  "2026-T1"),
                ("S1005", "CSC101", "2026-T1"),
                ("S1005", "SCI101", "2026-T1"),
                ("S1005", "ART101", "2026-T1"),
                ("S1005", "MTH101", "2026-T1"),
                ("S1006", "ENG201", "2026-T1"),
                ("S1006", "MTH201", "2026-T1"),
                ("S1006", "PE101",  "2026-T1"),
                ("S1006", "CSC201", "2026-T1"),
                ("S1007", "ENG301", "2026-T1"),
                ("S1007", "PE101",  "2026-T1"),
                ("S1007", "MTH301", "2026-T1"),
                ("S1007", "SCI301", "2026-T1"),
                ("S1008", "PE101",  "2026-T1"),
                ("S1009", "CSC101", "2026-T1"),
                ("S1009", "SCI101", "2026-T1"),
                ("S1009", "MTH101", "2026-T1"),
                ("S1009", "ART101", "2026-T1"),
                ("S1010", "MTH201", "2026-T1"),
                ("S1010", "CSC201", "2026-T1"),
                ("S1010", "ENG201", "2026-T1"),
                ("S1010", "HIS101", "2026-T1"),
                ("S1011", "ENG301", "2026-T1"),
                ("S1011", "PE101",  "2026-T1"),
                ("S1011", "SCI301", "2026-T1"),
                ("S1011", "MTH301", "2026-T1"),
                ("S1012", "PE101",  "2026-T1"),
                ("S1013", "CSC101", "2026-T1"),
                ("S1013", "PE101",  "2026-T1"),
                ("S1013", "MTH101", "2026-T1"),
                ("S1013", "SCI101", "2026-T1"),
                ("S1014", "ENG201", "2026-T1"),
                ("S1014", "PE101",  "2026-T1"),
                ("S1014", "HIS101", "2026-T1"),
                ("S1014", "MTH201", "2026-T1"),
                ("S1015", "ENG301", "2026-T1"),
                ("S1015", "SCI301", "2026-T1"),
                ("S1015", "PE101",  "2026-T1"),
                ("S1015", "MTH301", "2026-T1"),
                ("S1016", "PE101",  "2026-T1"),
                ("S1017", "PE101",  "2026-T1"),
                ("S1017", "SCI101", "2026-T1"),
                ("S1017", "ENG101", "2026-T1"),
                ("S1017", "ART101", "2026-T1"),
                ("S1018", "HIS101", "2026-T1"),
                ("S1018", "ENG201", "2026-T1"),
                ("S1018", "MTH201", "2026-T1"),
                ("S1018", "CSC201", "2026-T1"),
                ("S1019", "MTH301", "2026-T1"),
                ("S1019", "SCI301", "2026-T1"),
                ("S1019", "PE101",  "2026-T1"),
                ("S1019", "ENG301", "2026-T1"),
                ("S1020", "PE101",  "2026-T1"),
                ("S1021", "ENG101", "2026-T1"),
                ("S1021", "MTH101", "2026-T1"),
                ("S1021", "SCI101", "2026-T1"),
                ("S1021", "ART101", "2026-T1"),
                ("S1022", "SCI201", "2026-T1"),
                ("S1022", "HIS101", "2026-T1"),
                ("S1022", "ENG201", "2026-T1"),
                ("S1022", "PE101",  "2026-T1"),
                ("S1023", "SCI301", "2026-T1"),
                ("S1023", "ENG301", "2026-T1"),
                ("S1023", "PE101",  "2026-T1"),
                ("S1023", "MTH301", "2026-T1"),
                ("S1024", "PE101",  "2026-T1"),
                ("S1025", "PE101",  "2026-T1"),
                ("S1025", "SCI101", "2026-T1"),
                ("S1025", "CSC101", "2026-T1"),
                ("S1025", "ART101", "2026-T1"),
                ("S1026", "HIS101", "2026-T1"),
                ("S1026", "PE101",  "2026-T1"),
                ("S1026", "CSC201", "2026-T1"),
                ("S1026", "SCI201", "2026-T1"),
                ("S1027", "SCI301", "2026-T1"),
                ("S1027", "MTH301", "2026-T1"),
                ("S1027", "PE101",  "2026-T1"),
                ("S1028", "PE101",  "2026-T1"),
                ("S1029", "ENG101", "2026-T1"),
                ("S1029", "ART101", "2026-T1"),
                ("S1029", "MTH101", "2026-T1"),
                ("S1029", "CSC101", "2026-T1"),
                ("S1030", "ENG201", "2026-T1"),
                ("S1030", "PE101",  "2026-T1"),
                ("S1030", "CSC201", "2026-T1"),
                ("S1030", "SCI201", "2026-T1"),
                ("S1031", "MTH301", "2026-T1"),
                ("S1031", "SCI301", "2026-T1"),
                ("S1031", "PE101",  "2026-T1"),
                ("S1032", "PE101",  "2026-T1"),
                ("S1033", "MTH101", "2026-T1"),
                ("S1033", "ART101", "2026-T1"),
                ("S1033", "PE101",  "2026-T1"),
                ("S1033", "CSC101", "2026-T1"),
                ("S1034", "ENG201", "2026-T1"),
                ("S1034", "SCI201", "2026-T1"),
                ("S1034", "MTH201", "2026-T1"),
                ("S1034", "CSC201", "2026-T1"),
                ("S1035", "PE101",  "2026-T1"),
                ("S1035", "SCI301", "2026-T1"),
                ("S1035", "MTH301", "2026-T1"),
                ("S1036", "PE101",  "2026-T1"),
                ("S1037", "SCI101", "2026-T1"),
                ("S1037", "ART101", "2026-T1"),
                ("S1037", "ENG101", "2026-T1"),
                ("S1037", "PE101",  "2026-T1"),
                ("S1038", "SCI201", "2026-T1"),
                ("S1038", "CSC201", "2026-T1"),
                ("S1038", "HIS101", "2026-T1"),
                ("S1038", "PE101",  "2026-T1"),
                ("S1039", "SCI301", "2026-T1"),
                ("S1039", "PE101",  "2026-T1"),
                ("S1039", "MTH301", "2026-T1"),
                ("S1040", "PE101",  "2026-T1"),
            ]
            for e in enrollments:
                run_sql("INSERT INTO enrollments (student_id, course_code, term) VALUES (%s, %s, %s)", e, commit=True)

            print(" * Seeded sample students, teachers, courses, and enrollments.")
    except Exception as e:
        print(f"[Raw SQL Seed Notice] Table setup notice: {e}")


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)

    if test_config:
        app.config.update(test_config)
        Config.DB_TYPE = app.config.get("DB_TYPE", Config.DB_TYPE)

    app.teardown_appcontext(close_db)

    with app.app_context():
        if not app.config.get("TESTING"):
            try:
                ensure_database_exists()
                init_db("schema.sql")
                seed_sample_records()
            except Exception as e:
                print(f"[Raw SQL Setup Notice] Database ready once MySQL is connected ({e}).")

    @app.context_processor
    def inject_globals():
        return {
            "current_year": datetime.now(timezone.utc).year,
            "db_type": Config.DB_TYPE.upper(),
            "db_host": Config.MYSQL_HOST,
            "db_name": Config.MYSQL_DB,
            "status_choices": STATUS_CHOICES,
            "gender_choices": GENDER_CHOICES,
            "grade_choices": GRADE_CHOICES,
        }

    # -------------------------------------------------------------
    # WEB UI ROUTES
    # -------------------------------------------------------------

    @app.route("/")
    def index():
        query_str = request.args.get("q", "").strip()
        grade_filter = request.args.get("grade", "").strip()
        status_filter = request.args.get("status", "").strip()
        sort_by = request.args.get("sort", "name_asc")

        students = []
        total_students = active_students = withdrawn_students = total_courses = 0
        db_error = None

        try:
            # 1. Summary statistics
            stats_sql = """
                SELECT 
                    COUNT(*) AS total,
                    SUM(CASE WHEN status = 'Active' THEN 1 ELSE 0 END) AS active_cnt,
                    SUM(CASE WHEN status = 'Withdrawn' THEN 1 ELSE 0 END) AS withdrawn_cnt
                FROM students
            """
            stats = run_sql(stats_sql, fetchone=True)
            if stats:
                total_students = stats["total"] or 0
                active_students = stats["active_cnt"] or 0
                withdrawn_students = stats["withdrawn_cnt"] or 0

            # Count courses
            course_cnt_row = run_sql("SELECT COUNT(*) AS count FROM courses", fetchone=True)
            total_courses = course_cnt_row["count"] if course_cnt_row else 0

            # 2. Dynamic WHERE clauses
            where_clauses = ["1=1"]
            params = []

            if query_str:
                where_clauses.append(
                    "(student_id LIKE %s OR full_name LIKE %s OR email LIKE %s OR parent_name LIKE %s)"
                )
                p = f"%{query_str}%"
                params.extend([p, p, p, p])

            if grade_filter:
                where_clauses.append("grade = %s")
                params.append(int(grade_filter))

            if status_filter:
                where_clauses.append("status = %s")
                params.append(status_filter)

            # 3. Dynamic Sorting
            order_by = "full_name ASC"
            if sort_by == "name_desc":
                order_by = "full_name DESC"
            elif sort_by == "id_asc":
                order_by = "student_id ASC"
            elif sort_by == "grade_asc":
                order_by = "grade ASC, full_name ASC"
            elif sort_by == "grade_desc":
                order_by = "grade DESC, full_name ASC"
            elif sort_by == "created_desc":
                order_by = "created_at DESC"

            # Query with subquery for enrolled courses count
            select_sql = f"""
                SELECT s.*, 
                       (SELECT COUNT(*) FROM enrollments e WHERE e.student_id = s.student_id) AS enrolled_courses_count
                FROM students s 
                WHERE {' AND '.join(where_clauses)} 
                ORDER BY {order_by}
            """
            raw_students = run_sql(select_sql, tuple(params), fetchall=True)
            students = [normalize_student(r) for r in (raw_students or [])]

        except Exception as e:
            db_error = str(e)

        return render_template(
            "index.html",
            students=students,
            total_students=total_students,
            active_students=active_students,
            withdrawn_students=withdrawn_students,
            total_courses=total_courses,
            search_query=query_str,
            selected_grade=grade_filter,
            selected_status=status_filter,
            selected_sort=sort_by,
            db_error=db_error,
        )

    @app.route("/students/new", methods=["GET", "POST"])
    def add_student():
        suggested_id = f"STU2026{random.randint(100, 999)}"

        if request.method == "POST":
            student_id = request.form.get("student_id", "").strip().upper()
            full_name = request.form.get("full_name", "").strip()
            grade_str = request.form.get("grade", "").strip()
            dob_str = request.form.get("date_of_birth", "").strip()
            gender = request.form.get("gender", "Male").strip()
            email = request.form.get("email", "").strip().lower()
            parent_name = request.form.get("parent_name", "").strip()
            parent_phone = request.form.get("parent_phone", "").strip()
            status = request.form.get("status", "Active").strip()

            if not all([student_id, full_name, grade_str, dob_str, email]):
                flash("Please fill in all required fields (Student ID, Full Name, Grade, Date of Birth, Email).", "danger")
                return render_template("add_student.html", suggested_id=suggested_id, form_data=request.form)

            try:
                grade = int(grade_str)
                if not (1 <= grade <= 12):
                    flash("Grade must be an integer between 1 and 12.", "danger")
                    return render_template("add_student.html", suggested_id=suggested_id, form_data=request.form)
            except ValueError:
                flash("Grade must be a valid number.", "danger")
                return render_template("add_student.html", suggested_id=suggested_id, form_data=request.form)

            # Check duplicate student_id
            existing_id = run_sql("SELECT student_id FROM students WHERE student_id = %s", (student_id,), fetchone=True)
            if existing_id:
                flash(f"Student ID '{student_id}' is already registered.", "danger")
                return render_template("add_student.html", suggested_id=suggested_id, form_data=request.form)

            # Check duplicate email
            existing_email = run_sql("SELECT student_id FROM students WHERE email = %s", (email,), fetchone=True)
            if existing_email:
                flash(f"Email '{email}' is already registered for another student.", "danger")
                return render_template("add_student.html", suggested_id=suggested_id, form_data=request.form)

            try:
                insert_sql = """
                    INSERT INTO students 
                    (student_id, full_name, grade, parent_name, parent_phone, date_of_birth, gender, email, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                run_sql(insert_sql, (
                    student_id, full_name, grade, parent_name, parent_phone,
                    dob_str, gender, email, status
                ), commit=True)

                flash(f"Student {full_name} ({student_id}) enrolled successfully!", "success")
                return redirect(url_for("student_detail", student_id=student_id))
            except Exception as e:
                flash(f"Database error while saving student: {e}", "danger")
                return render_template("add_student.html", suggested_id=suggested_id, form_data=request.form)

        return render_template("add_student.html", suggested_id=suggested_id, form_data={})

    @app.route("/students/<student_id>")
    def student_detail(student_id):
        row = run_sql("SELECT * FROM students WHERE student_id = %s", (student_id,), fetchone=True)
        if not row:
            abort(404)
        student = normalize_student(row)

        # Debug (remove later)
        print("DOB:", type(student.date_of_birth), student.date_of_birth)
        print("CREATED:", type(student.created_at), student.created_at)
        print("UPDATED:", type(student.updated_at), student.updated_at)

        # Fetch enrolled courses with teacher info
        enrollments_sql = """
            SELECT e.enrollment_id, e.course_code, e.term, 
                   c.title AS course_title, c.grade_level, 
                   t.full_name AS teacher_name
            FROM enrollments e
            JOIN courses c ON e.course_code = c.course_code
            LEFT JOIN teachers t ON c.teacher_id = t.teacher_id
            WHERE e.student_id = %s
            ORDER BY c.title ASC
        """
        enrollments = run_sql(enrollments_sql, (student_id,), fetchall=True)

        # Available courses for enrollment dropdown
        available_courses = run_sql("SELECT * FROM courses ORDER BY title ASC", fetchall=True)

        return render_template(
            "student_detail.html",
            student=student,
            enrollments=enrollments or [],
            available_courses=available_courses or []
        )

    @app.route("/students/<student_id>/enroll", methods=["POST"])
    def enroll_course(student_id):
        course_code = request.form.get("course_code", "").strip()
        term = request.form.get("term", "Fall 2026").strip()

        if not course_code:
            flash("Please select a course to enroll.", "warning")
            return redirect(url_for("student_detail", student_id=student_id))

        # Check if already enrolled in this course
        existing = run_sql(
            "SELECT enrollment_id FROM enrollments WHERE student_id = %s AND course_code = %s",
            (student_id, course_code),
            fetchone=True
        )
        if existing:
            flash(f"Student is already enrolled in course {course_code}.", "warning")
            return redirect(url_for("student_detail", student_id=student_id))

        try:
            run_sql(
                "INSERT INTO enrollments (student_id, course_code, term) VALUES (%s, %s, %s)",
                (student_id, course_code, term),
                commit=True
            )
            flash(f"Enrolled successfully in course {course_code}!", "success")
        except Exception as e:
            flash(f"Error enrolling in course: {e}", "danger")

        return redirect(url_for("student_detail", student_id=student_id))

    @app.route("/students/<student_id>/unenroll/<int:enrollment_id>", methods=["POST"])
    def unenroll_course(student_id, enrollment_id):
        try:
            run_sql("DELETE FROM enrollments WHERE enrollment_id = %s AND student_id = %s", (enrollment_id, student_id), commit=True)
            flash("Course unenrollment completed.", "info")
        except Exception as e:
            flash(f"Error removing enrollment: {e}", "danger")
        return redirect(url_for("student_detail", student_id=student_id))

    @app.route("/students/<student_id>/edit", methods=["GET", "POST"])
    def edit_student(student_id):
        row = run_sql("SELECT * FROM students WHERE student_id = %s", (student_id,), fetchone=True)
        if not row:
            abort(404)
        student = normalize_student(row)

        if request.method == "POST":
            full_name = request.form.get("full_name", "").strip()
            grade_str = request.form.get("grade", "").strip()
            dob_str = request.form.get("date_of_birth", "").strip()
            gender = request.form.get("gender", "Male").strip()
            email = request.form.get("email", "").strip().lower()
            parent_name = request.form.get("parent_name", "").strip()
            parent_phone = request.form.get("parent_phone", "").strip()
            status = request.form.get("status", "Active").strip()

            if not all([full_name, grade_str, dob_str, email]):
                flash("Please fill in all required fields.", "danger")
                return render_template("edit_student.html", student=student)

            try:
                grade = int(grade_str)
                if not (1 <= grade <= 12):
                    flash("Grade must be between 1 and 12.", "danger")
                    return render_template("edit_student.html", student=student)
            except ValueError:
                flash("Grade must be a valid number.", "danger")
                return render_template("edit_student.html", student=student)

            # Check email uniqueness against other students
            conflict = run_sql(
                "SELECT student_id FROM students WHERE email = %s AND student_id != %s",
                (email, student_id),
                fetchone=True
            )
            if conflict:
                flash(f"Email '{email}' is already taken by student {conflict['student_id']}.", "danger")
                return render_template("edit_student.html", student=student)

            try:
                update_sql = """
                    UPDATE students 
                    SET full_name = %s, grade = %s, parent_name = %s, parent_phone = %s,
                        date_of_birth = %s, gender = %s, email = %s, status = %s
                    WHERE student_id = %s
                """
                run_sql(update_sql, (
                    full_name, grade, parent_name, parent_phone,
                    dob_str, gender, email, status, student_id
                ), commit=True)

                flash(f"Student {full_name} updated successfully!", "success")
                return redirect(url_for("student_detail", student_id=student_id))
            except Exception as e:
                flash(f"Error updating record: {e}", "danger")

        return render_template("edit_student.html", student=student)

    @app.route("/students/<student_id>/delete", methods=["POST"])
    def delete_student(student_id):
        row = run_sql("SELECT student_id, full_name FROM students WHERE student_id = %s", (student_id,), fetchone=True)
        if not row:
            abort(404)
        name = row["full_name"]

        try:
            run_sql("DELETE FROM students WHERE student_id = %s", (student_id,), commit=True)
            flash(f"Student record for {name} ({student_id}) and related enrollments were deleted.", "info")
        except Exception as e:
            flash(f"Error deleting record: {e}", "danger")

        return redirect(url_for("index"))

    @app.route("/courses")
    def list_courses():
        """View courses directory with assigned teachers and enrollment counts."""
        courses_sql = """
            SELECT c.*, 
                   t.full_name AS teacher_name, 
                   t.email AS teacher_email,
                   (SELECT COUNT(*) FROM enrollments e WHERE e.course_code = c.course_code) AS enrolled_count
            FROM courses c
            LEFT JOIN teachers t ON c.teacher_id = t.teacher_id
            ORDER BY c.grade_level ASC, c.title ASC
        """
        courses = run_sql(courses_sql, fetchall=True)
        return render_template("courses.html", courses=courses or [])

    @app.route("/export/csv")
    def export_csv():
        """Export all students to CSV using Raw SQL."""
        rows = run_sql("SELECT * FROM students ORDER BY grade ASC, student_id ASC", fetchall=True)
        si = io.StringIO()
        cw = csv.writer(si)
        cw.writerow([
            "Student ID", "Full Name", "Grade", "Gender", "Date of Birth", 
            "Email", "Parent Name", "Parent Phone", "Status"
        ])
        for s in (rows or []):
            item = dict(s)
            cw.writerow([
                item.get("student_id"), item.get("full_name"), item.get("grade"), item.get("gender"),
                item.get("date_of_birth"), item.get("email"), item.get("parent_name") or "",
                item.get("parent_phone") or "", item.get("status")
            ])
        
        output = si.getvalue()
        return Response(
            output,
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment;filename=students_export.csv"}
        )

    # -------------------------------------------------------------
    # REST API ENDPOINTS
    # -------------------------------------------------------------

    @app.route("/api/students", methods=["GET"])
    def api_get_students():
        rows = run_sql("SELECT * FROM students ORDER BY student_id ASC", fetchall=True)
        return jsonify({
            "success": True,
            "count": len(rows or []),
            "data": [dict(r) for r in (rows or [])]
        })

    @app.route("/api/students/<student_id>", methods=["GET"])
    def api_get_student(student_id):
        row = run_sql("SELECT * FROM students WHERE student_id = %s", (student_id,), fetchone=True)
        if not row:
            return jsonify({"success": False, "message": "Student not found"}), 404
        return jsonify({"success": True, "data": dict(row)})

    @app.route("/api/courses", methods=["GET"])
    def api_get_courses():
        rows = run_sql("SELECT * FROM courses ORDER BY course_code ASC", fetchall=True)
        return jsonify({
            "success": True,
            "count": len(rows or []),
            "data": [dict(r) for r in (rows or [])]
        })

    # -------------------------------------------------------------
    # IMPORT ROUTES
    # -------------------------------------------------------------

    def _parse_import_file(file_storage):
        """
        Parse an uploaded CSV or XLSX file into a list of dicts (one per data row).
        Returns (rows: list[dict], error: str|None).
        Column headers are normalised to lowercase + stripped.
        """
        filename = file_storage.filename.lower()
        raw_bytes = file_storage.read()

        if filename.endswith(".csv"):
            try:
                text = raw_bytes.decode("utf-8-sig")  # strip BOM if present
            except UnicodeDecodeError:
                text = raw_bytes.decode("latin-1")
            reader = csv.DictReader(io.StringIO(text))
            try:
                rows = list(reader)
            except Exception as e:
                return [], f"Could not parse CSV: {e}"
            # normalise headers
            rows = [{k.strip().lower(): (v.strip() if v else "") for k, v in row.items()} for row in rows]
            return rows, None

        elif filename.endswith(".xlsx"):
            if not _XLSX_SUPPORTED:
                return [], "Excel support requires openpyxl. Run: pip install openpyxl"
            try:
                wb = openpyxl.load_workbook(io.BytesIO(raw_bytes), read_only=True, data_only=True)
                ws = wb.active
                row_iter = iter(ws.rows)
                header_cells = next(row_iter, None)
                if not header_cells:
                    return [], "Excel file appears to be empty."
                headers = [str(c.value).strip().lower() if c.value is not None else "" for c in header_cells]
                rows = []
                for cells in row_iter:
                    vals = [str(c.value).strip() if c.value is not None else "" for c in cells]
                    rows.append(dict(zip(headers, vals)))
                wb.close()
                return rows, None
            except Exception as e:
                return [], f"Could not parse Excel file: {e}"
        else:
            return [], "Unsupported file type. Please upload a .csv or .xlsx file."
    def _generate_student_id():
        row = run_sql(
            """
            SELECT student_id
            FROM students
            ORDER BY student_id DESC
            LIMIT 1
            """,
            fetchone=True
        )

        if not row:
            return "S1001"

        try:
            latest = str(row["student_id"])

            match = re.search(r"(\d+)$", latest)

            if not match:
                return f"S{random.randint(1000,9999)}"

            next_number = int(match.group(1)) + 1

            return f"S{next_number}"

        except Exception:
            return f"S{random.randint(1000,9999)}"


    def _validate_and_import_rows(rows, on_duplicate):

        inserted = 0
        updated = 0
        skipped = 0
        errors = []

        email_re = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

        for idx, row in enumerate(rows, start=2):

            try:

                full_name = row.get("full_name", "").strip()
                grade_raw = row.get("grade", "").strip()
                dob = row.get("date_of_birth", "").strip()
                email = row.get("email", "").strip().lower()
                parent_name = row.get("parent_name", "").strip()
                parent_phone = row.get("parent_phone", "").strip()

                course_codes = [
                    c.strip().upper()
                    for c in row.get(
                        "course_codes",
                        ""
                    ).split(",")
                    if c.strip()
                ]

                if not all([
                    full_name,
                    grade_raw,
                    dob,
                    email,
                    parent_name,
                    parent_phone
                ]):
                    errors.append({
                        "row": idx,
                        "full_name": full_name,
                        "reasons": [
                            "Missing required fields"
                        ]
                    })
                    continue

                if not email_re.match(email):
                    errors.append({
                        "row": idx,
                        "full_name": full_name,
                        "reasons": [
                            "Invalid email address"
                        ]
                    })
                    continue

                try:
                    grade = int(grade_raw)

                    if grade < 1 or grade > 12:
                        raise ValueError()

                except ValueError:

                    errors.append({
                        "row": idx,
                        "full_name": full_name,
                        "reasons": [
                            "Grade must be between 1 and 12"
                        ]
                    })
                    continue

                existing = run_sql(
                    """
                    SELECT student_id
                    FROM students
                    WHERE full_name = %s
                    """,
                    (full_name,),
                    fetchone=True
                )

                if existing:

                    if on_duplicate == "update":

                        student_id = existing["student_id"]

                        run_sql(
                            """
                            UPDATE students
                            SET grade=%s,
                                parent_name=%s,
                                parent_phone=%s,
                                date_of_birth=%s,
                                email=%s
                            WHERE student_id=%s
                            """,
                            (
                                grade,
                                parent_name,
                                parent_phone,
                                dob,
                                email,
                                student_id
                            ),
                            commit=True
                        )

                        updated += 1

                    else:

                        skipped += 1

                    continue

                student_id = _generate_student_id()

                run_sql(
                    """
                    INSERT INTO students
                    (
                        student_id,
                        full_name,
                        grade,
                        parent_name,
                        parent_phone,
                        date_of_birth,
                        gender,
                        email,
                        status
                    )
                    VALUES
                    (
                        %s,%s,%s,%s,%s,%s,%s,%s,%s
                    )
                    """,
                    (
                        student_id,
                        full_name,
                        grade,
                        parent_name,
                        parent_phone,
                        dob,
                        "Male",
                        email,
                        "Active"
                    ),
                    commit=True
                )

                for course_code in course_codes:

                    course = run_sql(
                        """
                        SELECT course_code
                        FROM courses
                        WHERE course_code=%s
                        """,
                        (course_code,),
                        fetchone=True
                    )

                    if not course:
                        continue

                    run_sql(
                        """
                        INSERT INTO enrollments
                        (
                            student_id,
                            course_code,
                            term
                        )
                        VALUES
                        (
                            %s,%s,%s
                        )
                        """,
                        (
                            student_id,
                            course_code,
                            "2026-T1"
                        ),
                        commit=True
                    )

                inserted += 1

            except Exception as e:

                errors.append({
                    "row": idx,
                    "full_name": row.get(
                        "full_name",
                        ""
                    ),
                    "reasons": [str(e)]
                })

        return {
            "inserted": inserted,
            "updated": updated,
            "skipped": skipped,
            "errors": errors
        }


    @app.route("/students/import", methods=["GET", "POST"])
    def import_students():

        result = None

        if request.method == "POST":

            uploaded = request.files.get("file")

            on_duplicate = request.form.get(
                "on_duplicate",
                "skip"
            )

            if not uploaded or not uploaded.filename:

                flash(
                    "Please select a file to upload.",
                    "warning"
                )

                return redirect(request.url)

            uploaded.seek(0, 2)
            size = uploaded.tell()
            uploaded.seek(0)

            if size > 5 * 1024 * 1024:

                flash(
                    "File too large. Maximum size is 5 MB.",
                    "danger"
                )

                return redirect(request.url)

            rows, parse_error = _parse_import_file(
                uploaded
            )

            if parse_error:

                flash(
                    parse_error,
                    "danger"
                )

                return redirect(request.url)

            result = _validate_and_import_rows(
                rows,
                on_duplicate
            )

        return render_template(
            "import_students.html",
            result=result,
            xlsx_supported=_XLSX_SUPPORTED
        )


    @app.route("/students/import/template.csv")
    def import_template_csv():

        si = io.StringIO()

        writer = csv.writer(si)

        writer.writerow([
            "full_name",
            "grade",
            "date_of_birth",
            "email",
            "parent_name",
            "parent_phone",
            "course_codes"
        ])

        writer.writerow([
            "John Smith",
            "10",
            "2008-06-15",
            "john@email.com",
            "Mary Smith",
            "555123456",
            "CSC101,ENG101,MTH101"
        ])

        return Response(
            si.getvalue(),
            mimetype="text/csv",
            headers={
                "Content-Disposition":
                "attachment;filename=student_import_template.csv"
            }
        )

    @app.route("/db-status")
    def db_status():
        try:
            ver_query = "SELECT sqlite_version();" if Config.DB_TYPE == "sqlite" else "SELECT VERSION();"
            db = get_db()
            cursor = db.cursor()
            cursor.execute(ver_query)
            row = cursor.fetchone()
            version = list(dict(row).values())[0] if row else "Unknown"

            return jsonify({
                "status": "connected",
                "method": "Pure Raw SQL (PyMySQL)",
                "database_type": Config.DB_TYPE.upper(),
                "database_name": Config.MYSQL_DB if Config.DB_TYPE == "mysql" else "SQLite Local File",
                "server_version": version,
                "host": Config.MYSQL_HOST if Config.DB_TYPE == "mysql" else "localhost",
                "port": Config.MYSQL_PORT if Config.DB_TYPE == "mysql" else "N/A"
            })
        except Exception as e:
            return jsonify({
                "status": "error",
                "database_type": Config.DB_TYPE,
                "error": str(e)
            }), 500

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "True").lower() in ("true", "1", "yes")
    print(f" * Starting ABS Student Enrollment Portal on http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=debug)