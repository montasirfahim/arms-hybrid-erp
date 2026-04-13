from MySQLdb.constants.FLAG import UNIQUE, AUTO_INCREMENT
from django.db import models


# Create your models here.
class User(models.Model):
    ROLE_CHOICES = (
        ('CHAIRMAN', 'Chairman'),
        ('FACULTY', 'Faculty'),
        ('OFFICER', 'Officer'),
        ('STUDENT', 'Student'),
    )

    name = models.CharField(max_length=255, blank=False)
    email = models.EmailField(max_length=255, blank=False, null=False, unique=True)
    role = models.CharField(max_length=255, choices=ROLE_CHOICES, default='FACULTY')
    designation = models.CharField(max_length=255, blank=False, null=False)

    password = models.CharField(max_length=255, blank=False, null=False, default='123456')
    otp_code = models.CharField(max_length=6, blank=True, null=True)
    otp_expiry = models.DateTimeField(blank=True, null=True)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.email})"


class Batch(models.Model):
    session = models.CharField(max_length=7, blank=False, null=False, unique=True)
    name = models.CharField(max_length=255, blank=True, null=True, default='Masters in ICT')

    def __str__(self):
        return f"Masters Session: {self.session}"


import re


class Student(models.Model):
    student_id = models.CharField(max_length=7, primary_key=True)
    name = models.CharField(max_length=255, blank=False, null=False)
    email = models.CharField(max_length=255, blank=True, null=True)
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='students')

    GROUP_CHOISES = [
        ('Both', 'Both'),
        ('M.Sc', 'M.Sc'),
        ('M.Engg', 'M.Engg'),
    ]

    group = models.CharField(max_length=10, choices=GROUP_CHOISES, default='Both')
    

    STUDENT_ID_PATTERN = re.compile(r'^IT\d{5}$', re.IGNORECASE)

    @staticmethod
    def is_valid_student_id(student_id: str) -> bool:
        if not student_id:
            return False
        return bool(Student.STUDENT_ID_PATTERN.fullmatch(student_id.strip()))

    def __str__(self):
        return f"{self.student_id} : {self.name}"
    

class Semester(models.Model):
    NAME_CHOICES = [
        ('1st Semester', '1st Semester'),
        ('2nd Semester', '2nd Semester'),
        ('3rd Semester', '3rd Semester'),
    ]
    
    name = models.CharField(
        max_length=20, 
        choices=NAME_CHOICES, 
        blank=False, 
        null=False
    )
    
    # "Semester will be persisted" means we use SET_NULL or PROTECT
    committee_chairman = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, # Required if using SET_NULL
        related_name='chaired_semesters'
    )
    
    batch = models.ForeignKey(
        'Batch',
        on_delete=models.CASCADE,
        related_name='semesters'
    )

    result_status = models.BooleanField(blank=True, default=False)

    class Meta:
        # Ensures "1st Semester" is unique ONLY within a specific batch.
        # This allows Batch 2024 to have a "1st Semester" AND Batch 2025 to have one too.
        unique_together = ('name', 'batch')

    def __str__(self):
        return f"{self.batch.session} - {self.name}"


class Course(models.Model):
    TYPE_CHOICES = [
        ('Theory', 'Theory'),
        # ('Thesis', 'Thesis'),
        # ('Project', 'Project'),
    ]

    TARGET_CHOISES = [
        ('Both', 'Both'),
        ('M.Sc', 'M.Sc'),
        ('M.Engg', 'M.Engg'),
    ]

    course_code = models.CharField(max_length=20, blank=False, null=False)
    title = models.CharField(max_length=255, blank=False, null=False)
    credit_hour = models.FloatField(blank=False, null=False, default=3.00)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, blank=False, null=False, default='Theory')
    target_student = models.CharField(max_length=10, choices=TARGET_CHOISES, blank=False, default='Both')

    course_teacher = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='taught_courses'
    )
    
    batch = models.ForeignKey(
        Batch,
        on_delete=models.CASCADE,
        related_name='courses'
    )
    
    semester = models.ForeignKey(
        Semester,
        on_delete=models.CASCADE,
        related_name='courses'
    )
    
    marks_input_status = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('course_code', 'batch', 'semester')
    
    def __str__(self):
        return f"{self.course_code} - {self.title} ({self.type})"

class RegisteredStudent(models.Model):
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, null=False, blank=False)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, blank=False, null=False, related_name="registered_students")
    student = models.ForeignKey(Student, on_delete=models.CASCADE, blank=False, null=False)
    status = models.BooleanField(default=True) # default : registered

    def __str__(self):
        return f"{self.batch} {self.semester} {self.student}"
