from django.contrib import messages
from django.shortcuts import render, redirect
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.units import inch
from results.models import CourseResult

from accounts.decorators import login_required
from accounts.models import Batch, Semester, Course, RegisteredStudent, Student
from accounts.utils import get_user_from_jwt

from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape, legal
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


@login_required
def export_course_result_pdf(request, batch_id, semester_id, course_id):
    course = Course.objects.filter(pk=course_id).first()
    if not course or not course.marks_input_status:
        messages.error(request, "Results are not finalized yet.")
        return redirect('manage_semester', batch_id=batch_id, semester_id=semester_id)

    results = CourseResult.objects.filter(course=course).select_related('student').order_by('student__student_id')

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{course.course_code}_results.pdf"'

    # Total table width here is 520pt.
    # For Legal (612pt), 46pt margins center the 520pt content perfectly.
    doc = SimpleDocTemplate(
        response,
        pagesize=legal,
        rightMargin=46, leftMargin=46, topMargin=40, bottomMargin=40
    )
    elements = []
    styles = getSampleStyleSheet()


    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], alignment=TA_CENTER)
    subtitle_style = ParagraphStyle('SubStyle', parent=styles['Heading2'], alignment=TA_CENTER)
    left_text = ParagraphStyle('LeftStyle', parent=styles['Normal'], alignment=TA_LEFT)
    right_text = ParagraphStyle('RightStyle', parent=styles['Normal'], alignment=TA_RIGHT)

    # --- Headings ---
    elements.append(Paragraph("Mawlana Bhashani Science and Technology University", title_style))
    elements.append(Paragraph("Department of Information and Communication Technology (ICT)", subtitle_style))
    elements.append(Spacer(1, 15))


    course_teacher_name = course.course_teacher.name if course.course_teacher else "N/A"

    info_data = [
        [Paragraph(f"<b>Course Teacher:</b> {course_teacher_name}", left_text),
         Paragraph(f"<b>Course Title:</b> {course.title}", right_text)],

        [Paragraph(f"<b>Course Code:</b> {course.course_code}", left_text),
         Paragraph(f"<b>Credit Hours:</b> {course.credit_hour:.2f}", right_text)],

        [Paragraph(f"<b>Session:</b> {course.batch.session}", left_text),
         Paragraph(f"<b>Semester:</b> {course.semester.name}", right_text)]
    ]


    info_table = Table(info_data, colWidths=[260, 260])
    info_table.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 12))

    data = [['Student ID', 'Name', 'CT\n(30%)', 'Attendance\n(10%)', 'Theory\n(60%)', 'Total\n(100%)', 'GPA', 'Letter']]
    for res in results:
        ct = res.ct_marks or 0.0
        att = res.attendance_marks or 0.0
        theory = res.final_theory_marks or 0.0
        total = ct + att + theory

        data.append([
            res.student.student_id,
            res.student.name,
            f"{ct:.2f}",
            f"{att:.2f}",
            f"{theory:.2f}",
            f"{total:.2f}",
            f"{res.gpa or 0.0:.2f}",
            res.letter or 'F'
        ])

    # Your original column widths: 70+130+50+75+55+60+40+40 = 520
    table = Table(data, colWidths=[70, 130, 50, 75, 55, 60, 40, 40])
    table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(table)

    doc.build(elements)
    return response


@login_required
def detailed_course_result_pdf(request, batch_id, semester_id, course_id):
    course = Course.objects.filter(pk=course_id).first()
    if not course or not course.marks_input_status:
        messages.error(request, "Results are not finalized yet.")
        return redirect('manage_semester', batch_id=batch_id, semester_id=semester_id)

    results = CourseResult.objects.filter(course=course).select_related('student').order_by('student__student_id')

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{course.course_code}_detailed_results.pdf"'

    doc = SimpleDocTemplate(
        response,
        pagesize=legal,
        rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30
    )
    elements = []
    styles = getSampleStyleSheet()

    # 1. Custom Styles for Headings to ensure they are centered and follow margins
    heading_style = ParagraphStyle(
        'HeadingStyle',
        parent=styles['Heading1'],
        alignment=TA_CENTER,
        spaceAfter=5
    )
    sub_heading_style = ParagraphStyle(
        'SubHeadingStyle',
        parent=styles['Heading2'],
        alignment=TA_CENTER,
        fontSize=12,
        spaceAfter=12
    )
    left_text = ParagraphStyle('LeftStyle', parent=styles['Normal'], alignment=TA_LEFT)
    right_text = ParagraphStyle('RightStyle', parent=styles['Normal'], alignment=TA_RIGHT)

    # Formal Headings
    elements.append(Paragraph("Mawlana Bhashani Science and Technology University", heading_style))
    elements.append(Paragraph("Department of Information and Communication Technology (ICT)", sub_heading_style))
    elements.append(Spacer(1, 10))

    # 2. Course Details Layout (Using a Table for perfect alignment)
    course_teacher_name = course.course_teacher.name if course.course_teacher else "N/A"

    info_data = [
        [Paragraph(f"<b>Course Teacher:</b> {course_teacher_name}", left_text),
         Paragraph(f"<b>Course Title:</b> {course.title}", right_text)],

        [Paragraph(f"<b>Course Code:</b> {course.course_code}", left_text),
         Paragraph(f"<b>Credit Hours:</b> {course.credit_hour:.2f}", right_text)],

        [Paragraph(f"<b>Session:</b> {course.batch.session}", left_text),
         Paragraph(f"<b>Semester:</b> {course.semester.name}", right_text)]
    ]

    # colWidths sum to 530 to match the main data table
    info_table = Table(info_data, colWidths=[265, 265])
    info_table.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 10))

    data = [['Student ID', 'CT\n(30%)', 'Attendance\n(10%)', 'Theory(Int)\n(60%)', 'Theory(Ext)\n(60%)',
             'Theory(3rd)\n(60%)', 'Theory\n(60%)', 'Total\n(100%)', 'GPA', 'Letter']]

    for res in results:
        ct = res.ct_marks or 0.0
        att = res.attendance_marks or 0.0
        theory_int = res.theory_internal or 0.0
        theory_ext = res.theory_external or 0.0
        theory_3rd = res.theory_third_examiner if res.third_examiner_needed else None
        theory_final = res.final_theory_marks or 0.0
        total = ct + att + theory_final
        theory_3rd_str = f"{theory_3rd:.2f}" if theory_3rd is not None else "-"
        data.append([
            res.student.student_id,
            f"{ct:.2f}",
            f"{att:.2f}",
            f"{theory_int:.2f}",
            f"{theory_ext:.2f}",
            theory_3rd_str,
            f"{theory_final:.2f}",
            f"{total:.2f}",
            f"{res.gpa or 0.0:.2f}",
            res.letter or 'F'
        ])

    # Table with specific column widths
    table = Table(data, colWidths=[45, 45, 55, 65, 65, 65, 60, 45, 40, 40])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(table)

    doc.build(elements)
    return response

@login_required
def input_marks_view(request, batch_id, semester_id, course_id):
    batch = Batch.objects.filter(pk=batch_id).first()
    semester = Semester.objects.filter(pk=semester_id, batch=batch).first()
    course = Course.objects.filter(pk=course_id, batch=batch, semester=semester).first()

    if not batch or not semester or not course:
        return redirect('home')

    user_obj = get_user_from_jwt(request)
    user_id = user_obj.id if user_obj else None
    
    # Authorization check
    is_teacher = (course.course_teacher and course.course_teacher.id == user_id)
    is_chairman = (semester.committee_chairman and semester.committee_chairman.id == user_id)

    if not (is_teacher or is_chairman):
        messages.error(request, "You are not authorized to input marks for this course.")
        return redirect('manage_semester', batch_id=batch_id, semester_id=semester_id)

    results = CourseResult.objects.filter(course=course).select_related('student').order_by('student__student_id')

    if request.method == 'POST':
        if course.marks_input_status:
            messages.error(request, "This course's marks are already finalized and cannot be modified.")
            return redirect('input_marks', batch_id=batch.id, semester_id=semester.id, course_id=course.id)

        action = request.POST.get('action')
        
        if action == 'finalize_result':
            #Check if all students have all required marks
            for res in results:
                if res.ct_marks is None or res.attendance_marks is None or \
                   res.theory_internal is None or res.theory_external is None:
                    messages.error(request, f"Missing marks for student {res.student.student_id}. All marks must be provided before finalizing.")
                    return redirect('input_marks', batch_id=batch.id, semester_id=semester.id, course_id=course.id)
                
                if res.third_examiner_needed and res.theory_third_examiner is None:
                    messages.error(request, f"Third examiner marks required for student {res.student.student_id}.")
                    return redirect('input_marks', batch_id=batch.id, semester_id=semester.id, course_id=course.id)

            for res in results:
                theory_average = calculate_theory_average(res)
                res.final_theory_marks = theory_average
                total_marks = (res.ct_marks or 0.0) + (res.attendance_marks or 0.0) + theory_average
                res.gpa, res.letter = get_gpa_and_letter(total_marks)
                res.save()
            
            course.marks_input_status = True
            course.save()

            incomplete_courses = Course.objects.filter(semester=semester, marks_input_status=False).exists()
            if not incomplete_courses:
                semester.result_status = True
                semester.save()

            messages.success(request, f"Results for {course.course_code} have been finalized successfully.")
            return redirect('input_marks', batch_id=batch.id, semester_id=semester.id, course_id=course.id)

        if action == 'enroll_student':
            student_id = request.POST.get('student_id')
            student = Student.objects.filter(student_id=student_id).first()
            
            if student:
                # Check if already enrolled
                if not CourseResult.objects.filter(student=student, course=course, semester=semester).exists():
                    CourseResult.objects.create(
                        student=student,
                        course=course,
                        semester=semester
                    )
                    messages.success(request, f'Student {student.student_id} enrolled successfully.')
                else:
                    messages.warning(request, f'Student {student.student_id} is already enrolled in this course.')
            else:
                messages.error(request, 'Student not found.')
            return redirect('input_marks', batch_id=batch.id, semester_id=semester.id, course_id=course.id)

        # Default action: Update marks
        for res in results:
            if is_teacher:
                ct = request.POST.get(f'ct_{res.id}')
                att = request.POST.get(f'att_{res.id}')
                theory = request.POST.get(f'theory_{res.id}')
                try:
                    if ct not in [None, ""]:
                        res.ct_marks = float(ct)

                    if att not in [None, ""]:
                        res.attendance_marks = float(att)

                    if theory not in [None, ""]:
                        res.theory_internal = float(theory)

                    diff = 0.0
                    if res.theory_internal is not None and res.theory_external is not None:
                        diff = abs(res.theory_internal - res.theory_external)

                    if diff >= 12.0:  # third examiner marks input-able iff diff >= 12.00
                        res.third_examiner_needed = True

                except ValueError:
                    pass

            if is_chairman:
                external = request.POST.get(f'external_{res.id}')
                third = request.POST.get(f'third_{res.id}')
                try:
                    if external not in [None, ""]:
                        res.theory_external = float(external)

                    diff = 0.0
                    if res.theory_internal is not None and res.theory_external is not None:
                        diff = abs(res.theory_internal - res.theory_external)

                    if diff >= 12.0: #third examiner marks input-able iff diff >= 12.00
                        res.third_examiner_needed = True
                        if third is not None and third != "":
                            res.theory_third_examiner = float(third)
                except ValueError:
                    pass
            
            res.save()

        messages.success(request, 'Marks updated successfully.')
        return redirect('input_marks', batch_id=batch.id, semester_id=semester.id, course_id=course.id)

    # Get students registered in this semester but not yet in this course
    enrolled_student_ids = results.values_list('student_id', flat=True)
    available_students = RegisteredStudent.objects.filter(
        semester=semester
    ).exclude(
        student_id__in=enrolled_student_ids
    ).select_related('student')

    context = {
        'batch': batch,
        'semester': semester,
        'course': course,
        'results': results,
        'available_students': available_students,
        'is_teacher': is_teacher,
        'is_chairman': is_chairman,
    }
    return render(request, 'results/input_marks.html', context)



def calculate_theory_average(course_result):
    if course_result.theory_internal is None or course_result.theory_external is None:
        return None, None

    if course_result.third_examiner_needed:
        if course_result.theory_third_examiner is None:
            return None, None

        diff1 = abs(course_result.theory_internal - course_result.theory_third_examiner)
        diff2 = abs(course_result.theory_external - course_result.theory_third_examiner)

        if diff1 <= diff2:
            theory_average = (course_result.theory_third_examiner + course_result.theory_internal) / 2.0
        else:
            theory_average = (course_result.theory_third_examiner + course_result.theory_external) / 2.0

    else:
        theory_average = (course_result.theory_internal + course_result.theory_external) / 2.0

    return theory_average


def get_gpa_and_letter(total_marks):
    if total_marks < 40.0:
        return 0.00, "F"
    elif total_marks < 45.0:
        return 2.00, "D"
    elif total_marks < 50.0:
        return 2.25, "C"
    elif total_marks < 55.0:
        return 2.50, "C+"
    elif total_marks < 60.0:
        return 2.75, "B-"
    elif total_marks < 65.0:
        return 3.00, "B"
    elif total_marks < 70.0:
        return 3.25, "B+"
    elif total_marks < 75.0:
        return 3.50, "A-"
    elif total_marks < 80.0:
        return 3.75, "A"
    else:
        return 4.00, "A+"



def get_letter_from_gpa(gpa):
    if gpa >= 4.00: return 'A+'
    if gpa >= 3.75: return 'A'
    if gpa >= 3.50: return 'A-'
    if gpa >= 3.25: return 'B+'
    if gpa >= 3.00: return 'B'
    if gpa >= 2.75: return 'B-'
    if gpa >= 2.50: return 'C+'
    if gpa >= 2.25: return 'C'
    if gpa >= 2.00: return 'D'
    return 'F'


@login_required
def handle_result_type(request, semester_id, group):
    semester = Semester.objects.filter(id=semester_id).first()
    if not semester:
        return HttpResponse("Semester not found", status=404)

    if group == 'Both':
        registered_students = RegisteredStudent.objects.filter(semester=semester).select_related('student').order_by('student__student_id')
        courses = Course.objects.filter(semester=semester).order_by('course_code')
    else:
        registered_students = RegisteredStudent.objects.filter(semester=semester, student__group=group).select_related('student').order_by('student__student_id')
        courses = Course.objects.filter(semester=semester).order_by('course_code')

    return export_semester_result_sheet_pdf(semester, registered_students, courses, group)


def export_semester_result_sheet_pdf(semester, registered_students, courses, group):

    response = HttpResponse(content_type='application/pdf')
    filename = f"{semester.batch.session}_{semester.name}_{group}_results.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    num_courses = courses.count()
    # Width: courses.size * 2 + 4 inch
    width = (num_courses * 2 + 6) * inch
    width = max(width, 8*inch)
    
    # Height: as much needed to display at least 60 entry
    num_students = registered_students.count()
    display_rows = max(num_students, 60)
    height = (display_rows * 0.4 + 3) * inch # approx 0.4 inch per row + 4 inch for headers/titles

    doc = SimpleDocTemplate(
        response,
        pagesize=(width, height),
        rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30
    )
    
    elements = []
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], alignment=TA_CENTER, fontSize=18)
    subtitle_style = ParagraphStyle('SubStyle', parent=styles['Heading2'], alignment=TA_CENTER, fontSize=14)
    
    elements.append(Paragraph("Mawlana Bhashani Science and Technology University", title_style))
    elements.append(Paragraph("Department of Information and Communication Technology (ICT)", subtitle_style))
    elements.append(Paragraph(f"Semester Final Result Sheet: {semester.name} ({semester.batch.session})", subtitle_style))

    if group == 'Both':
        group = "M.Sc & M.Engg"

    elements.append(Paragraph(f"Group: {group}", subtitle_style))
    elements.append(Spacer(1, 20))

    # Table Header
    # Row 1: Student ID, Course Codes (colspan 4 each), Final (colspan 5)
    h1 = ['Student ID']
    for course in courses:
        h1.extend([course.course_code, '', '', ''])
    h1.extend(['Final', '', '', '', ''])

    # Row 2: '', MO, LG, GP, TP (for each course), CT, CE, TPS, GPA, R (for Final)
    h2 = ['']
    for _ in range(num_courses):
        h2.extend(['MO', 'LG', 'GP', 'TP'])
    h2.extend(['CT', 'CE', 'TPS', 'GPA', 'R'])

    data = [h1, h2]

    # Pre-fetch all results for this semester to avoid N+1 queries
    all_results = CourseResult.objects.filter(semester=semester).select_related('course', 'student')
    results_map = {} # (student_id, course_id) -> result
    for r in all_results:
        results_map[(r.student_id, r.course_id)] = r

    for reg in registered_students:
        student = reg.student
        row = [student.student_id]
        
        total_ct = 0.0
        total_ce = 0.0
        total_tps = 0.0
        
        for course in courses:
            res = results_map.get((student.student_id, course.id))
            if res and res.gpa is not None:
                mo = (res.ct_marks or 0) + (res.attendance_marks or 0) + (res.final_theory_marks or 0)
                lg = res.letter or 'F'
                gp = res.gpa or 0.0
                tp = gp * course.credit_hour
                
                row.extend([f"{mo:.2f}", lg, f"{gp:.2f}", f"{tp:.2f}"])
                
                total_ct += course.credit_hour
                if gp > 0:
                    total_ce += course.credit_hour
                    total_tps += tp
            else:
                row.extend(['-', '-', '-', '-'])

        
        gpa = total_tps / total_ce if total_ce > 0 else 0.0
        r_letter = get_letter_from_gpa(gpa)
        
        row.extend([f"{total_ct:.2f}", f"{total_ce:.2f}", f"{total_tps:.2f}", f"{gpa:.2f}", r_letter])
        data.append(row)

    # Column widths
    # Student ID: 1 inch (72 points)
    # Each course: 4 cols * 0.5 inch = 2 inch (144 points)
    # Final: 5 cols * 0.6 inch = 3 inch (216 points)
    col_widths = [72]
    for _ in range(num_courses):
        col_widths.extend([36, 36, 36, 36])
    col_widths.extend([43.2, 43.2, 43.2, 43.2, 43.2]) # 216 / 5 = 43.2

    table = Table(data, colWidths=col_widths, repeatRows=2)
    
    ts = TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 1), 'Times-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('SPAN', (0, 0), (0, 1)), # Span Student ID
    ])

    # Spans for courses and Final
    curr_col = 1
    for i in range(num_courses):
        ts.add('SPAN', (curr_col, 0), (curr_col + 3, 0))
        curr_col += 4
    
    ts.add('SPAN', (curr_col, 0), (curr_col + 4, 0))

    table.setStyle(ts)
    elements.append(table)

    doc.build(elements)
    return response
