from django.db import models
from accounts.models import Student,Course,Semester
from django.core.validators import MinValueValidator, MaxValueValidator

class CourseResult(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='course_results')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='results')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='results')
    
    #internal course teacher has access on these 3 fileds to update
    ct_marks = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(30.0)],
        blank=True, null=True
    )
    attendance_marks = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(10.0)], 
        blank=True, null=True
    )
    theory_internal = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(60.0)],
        blank=True, null=True
    )

    #committee chairman has the access for these 2 fileds
    theory_external = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(60.0)],
        blank=True, null=True
    )
    theory_third_examiner = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(60.0)],
        blank=True, null=True
    ) 

    third_examiner_needed = models.BooleanField(default=False)

    final_theory_marks = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(60.0)], null=True, blank=True)
    gpa = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(4.0)], 
        blank=True, null=True
    )
    letter = models.CharField(max_length=2, null=True, blank=True)

    class Meta:
        unique_together = ('student', 'course', 'semester')

    def __str__(self):
        return f"{self.student.name} - {self.course} ({self.semester})"

