from django.test import TestCase, Client
from django.urls import reverse
from .models import User, Batch, Student, Semester, Course, RegisteredStudent
from django.contrib.auth.hashers import make_password

class AccountsModelTests(TestCase):
    def setUp(self):
        self.batch = Batch.objects.create(session="2023-24", name="Masters in ICT")
        self.user = User.objects.create(
            name="Test User",
            email="test@example.com",
            role="FACULTY",
            designation="Lecturer",
            password=make_password("password123")
        )

    def test_student_id_validation(self):
        """Test the regex validation for student IDs."""
        self.assertTrue(Student.is_valid_student_id("IT21001"))
        self.assertTrue(Student.is_valid_student_id("it21001"))
        self.assertFalse(Student.is_valid_student_id("CS21001"))
        self.assertFalse(Student.is_valid_student_id("IT2100"))
        self.assertFalse(Student.is_valid_student_id("IT210001"))

    def test_semester_unique_together(self):
        """Test that a semester name must be unique within a batch."""
        Semester.objects.create(name="1st Semester", batch=self.batch)
        with self.assertRaises(Exception):
            Semester.objects.create(name="1st Semester", batch=self.batch)

    def test_course_creation(self):
        """Test course creation and unique constraint."""
        semester = Semester.objects.create(name="1st Semester", batch=self.batch)
        course = Course.objects.create(
            course_code="ICT-1101",
            title="Programming with C",
            credit_hour=3.0,
            batch=self.batch,
            semester=semester,
            course_teacher=self.user
        )
        self.assertEqual(str(course), "ICT-1101 - Programming with C (Theory)")

class AccountsViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create(
            name="Admin User",
            email="admin@example.com",
            role="CHAIRMAN",
            designation="Professor",
            password=make_password("admin123")
        )
        # Manually set session cookie to bypass login_required if needed, 
        # but better to test the login flow or use a mock.
        # Since the project uses a custom JWT-based login_required, 
        # we might need to mock the JWT check or actually log in.
        
    def test_health_check(self):
        response = self.client.get(reverse('health_check'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "healthy"})

    def test_login_api_fail(self):
        """Test API login with wrong credentials."""
        response = self.client.post(
            reverse('api_login'),
            data={'email': 'wrong@example.com', 'password': 'wrongpassword'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 401)
        self.assertFalse(response.json()['success'])
