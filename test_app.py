import os
import unittest
from app import create_app
from db import get_db, close_db, init_db

TEST_DB = "test_student_portal.db"

class TestStudentPortalNewSchema(unittest.TestCase):
    def setUp(self):
        if os.path.exists(TEST_DB):
            try:
                os.remove(TEST_DB)
            except Exception:
                pass

        os.environ["SQLITE_PATH"] = TEST_DB
        self.app = create_app(test_config={
            "TESTING": True,
            "DB_TYPE": "sqlite",
            "WTF_CSRF_ENABLED": False,
        })
        self.client = self.app.test_client()

        with self.app.app_context():
            init_db()
            db = get_db()
            cursor = db.cursor()

            # Insert sample teacher
            cursor.execute(
                "INSERT INTO teachers (teacher_id, full_name, email) VALUES (?, ?, ?)",
                ("101", "Dr. Sarah Connor", "sconnor@school.edu")
            )
            # Insert sample course
            cursor.execute(
                "INSERT INTO courses (course_code, title, grade_level, teacher_id, capacity) VALUES (?, ?, ?, ?, ?)",
                ("MTH101", "Advanced Mathematics", 11, "101", 30)
            )
            # Insert sample student
            cursor.execute("""
                INSERT INTO students 
                (student_id, full_name, grade, parent_name, parent_phone, date_of_birth, gender, email, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "STU2026999", "Jane Doe", 11, "John Doe", "15559999",
                "2004-01-01", "Female", "jane.doe@example.com", "Active"
            ))
            # Insert enrollment
            cursor.execute(
                "INSERT INTO enrollments (student_id, course_code, term) VALUES (?, ?, ?)",
                ("STU2026999", "MTH101", "Fall 2026")
            )
            db.commit()

    def tearDown(self):
        with self.app.app_context():
            close_db()
        if os.path.exists(TEST_DB):
            try:
                os.remove(TEST_DB)
            except Exception:
                pass

    def test_dashboard_route(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Student Enrollment Dashboard", response.data)
        self.assertIn(b"STU2026999", response.data)
        self.assertIn(b"Jane Doe", response.data)

    def test_add_student_get(self):
        response = self.client.get("/students/new")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Student Enrollment Form", response.data)

    def test_add_student_post(self):
        response = self.client.post("/students/new", data={
            "student_id": "STU2026888",
            "full_name": "Bob Smith",
            "grade": "10",
            "date_of_birth": "2005-02-15",
            "gender": "Male",
            "email": "bob.smith@example.com",
            "parent_name": "Alice Smith",
            "parent_phone": "15558888",
            "status": "Active"
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Bob Smith", response.data)
        self.assertIn(b"STU2026888", response.data)

    def test_student_detail_route(self):
        response = self.client.get("/students/STU2026999")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Jane Doe", response.data)
        self.assertIn(b"Grade 11", response.data)
        self.assertIn(b"Advanced Mathematics", response.data)

    def test_edit_student(self):
        response = self.client.post("/students/STU2026999/edit", data={
            "full_name": "Janet Doe",
            "grade": "12",
            "date_of_birth": "2004-01-01",
            "gender": "Female",
            "email": "janet.doe@example.com",
            "parent_name": "John Doe",
            "parent_phone": "15559999",
            "status": "Active"
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Janet Doe", response.data)
        self.assertIn(b"Grade 12", response.data)

    def test_courses_directory(self):
        response = self.client.get("/courses")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Advanced Mathematics", response.data)
        self.assertIn(b"Dr. Sarah Connor", response.data)

    def test_export_csv(self):
        response = self.client.get("/export/csv")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "text/csv")
        self.assertIn(b"STU2026999", response.data)
        self.assertIn(b"Jane Doe", response.data)

    def test_api_students(self):
        response = self.client.get("/api/students")
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertTrue(json_data["success"])
        self.assertGreaterEqual(json_data["count"], 1)

    def test_delete_student(self):
        response = self.client.post("/students/STU2026999/delete", follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"deleted", response.data)

if __name__ == "__main__":
    unittest.main()
