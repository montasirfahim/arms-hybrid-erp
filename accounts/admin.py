# Register your models here.
from django.contrib import admin
from .models import User, Batch, Student, Semester, Course, RegisteredStudent


# This allows you to add/edit students directly inside the Batch page
class StudentInline(admin.TabularInline):
    model = Student
    extra = 1 # Shows 1 empty row by default for quick adding

@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ('session', 'name', 'student_count')
    search_fields = ('session', 'name')
    inlines = [StudentInline]

    # Custom method to show how many students are in this batch
    def student_count(self, obj):
        return obj.students.count()
    student_count.short_description = 'Total Students'

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'name', 'batch', 'email')
    list_filter = ('batch',) # Adds a filter sidebar by Batch
    search_fields = ('student_id', 'name', 'email')

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'role', 'designation', 'is_verified')
    search_fields = ('name', 'email', 'role', 'designation')
    list_filter = ('role', 'is_verified')
    fields = ('name', 'email', 'role', 'designation', 'otp_code', 'otp_expiry', 'is_verified')


@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ('batch', 'name', 'committee_chairman', 'result_status')
    list_filter = ('batch', 'result_status')
    search_fields = ('name', 'committee_chairman__name')


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('course_code', 'title', 'type', 'batch', 'semester', 'course_teacher', 'marks_input_status')
    list_filter = ('type', 'batch', 'semester', 'marks_input_status')
    search_fields = ('course_code', 'title', 'course_teacher__name')

@admin.register(RegisteredStudent)
class RegisteredStudentAdmin(admin.ModelAdmin):
    list_display = ('id', 'student', 'batch', 'semester', 'status')
    list_filter = ('batch', 'semester', 'status')
    search_fields = ('student_id',)