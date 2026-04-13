from django.contrib import admin
from .models import CourseResult

@admin.register(CourseResult)
class CourseResultAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'semester', 'gpa', 'letter', 'final_theory_marks')
    list_filter = ('semester', 'course', 'letter', 'third_examiner_needed')
    search_fields = ('student__student_id', 'student__name', 'course__course_code', 'course__title')
    readonly_fields = ('final_theory_marks', 'gpa', 'letter')
    
    fieldsets = (
        ('Identification', {
            'fields': ('student', 'course', 'semester')
        }),
        ('Internal Marks', {
            'fields': ('ct_marks', 'attendance_marks', 'theory_internal')
        }),
        ('External/Third Examiner Marks', {
            'fields': ('theory_external', 'theory_third_examiner', 'third_examiner_needed')
        }),
        ('Final Computed Results', {
            'fields': ('final_theory_marks', 'gpa', 'letter')
        }),
    )
