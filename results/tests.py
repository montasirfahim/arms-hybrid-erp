from django.test import TestCase
from accounts.models import User, Batch, Student, Semester, Course
from .models import CourseResult
from .views import get_gpa_and_letter, calculate_theory_average

class ResultsLogicTests(TestCase):
    def test_gpa_calculation(self):
        """Test the GPA and Letter grade mapping."""
        # 80+ -> 4.0, A+
        gpa, letter = get_gpa_and_letter(85.0)
        self.assertEqual(gpa, 4.00)
        self.assertEqual(letter, "A+")
        
        # 75 -> 3.75, A
        gpa, letter = get_gpa_and_letter(77.0)
        self.assertEqual(gpa, 3.75)
        self.assertEqual(letter, "A")

        # < 40 -> 0.0, F
        gpa, letter = get_gpa_and_letter(39.0)
        self.assertEqual(gpa, 0.00)
        self.assertEqual(letter, "F")

    def test_theory_average_no_third_examiner(self):
        """Test average calculation when no third examiner is needed."""
        res = CourseResult(theory_internal=50.0, theory_external=54.0, third_examiner_needed=False)
        avg = calculate_theory_average(res)
        self.assertEqual(avg, 52.0)

    def test_theory_average_with_third_examiner(self):
        """
        Test average calculation when third examiner is needed.
        It should take the average of the two closest marks.
        """
        # Internal: 40, External: 55 (Diff 15 >= 12)
        # Third: 42. Closest to Internal (40). Avg = (40+42)/2 = 41
        res = CourseResult(
            theory_internal=40.0, 
            theory_external=55.0, 
            theory_third_examiner=42.0,
            third_examiner_needed=True
        )
        avg = calculate_theory_average(res)
        self.assertEqual(avg, 41.0)

        # Third: 53. Closest to External (55). Avg = (55+53)/2 = 54
        res.theory_third_examiner = 53.0
        avg = calculate_theory_average(res)
        self.assertEqual(avg, 54.0)

class ResultsModelTests(TestCase):
    def setUp(self):
        self.batch = Batch.objects.create(session="2023-24")
        self.semester = Semester.objects.create(name="1st Semester", batch=self.batch)
        self.student = Student.objects.create(student_id="IT21001", name="Test Student", batch=self.batch)
        self.course = Course.objects.create(
            course_code="ICT-1101", 
            title="Test Course", 
            batch=self.batch, 
            semester=self.semester
        )

    def test_course_result_creation(self):
        res = CourseResult.objects.create(
            student=self.student,
            course=self.course,
            semester=self.semester,
            ct_marks=25.0,
            attendance_marks=9.0,
            theory_internal=45.0,
            theory_external=47.0
        )
        self.assertEqual(res.student.name, "Test Student")
        self.assertFalse(res.third_examiner_needed)
