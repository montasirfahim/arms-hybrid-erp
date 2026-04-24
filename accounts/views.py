import csv
import io
import json
import secrets
import httpx
from datetime import timedelta

from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password
from rest_framework_simplejwt.tokens import RefreshToken

from .decorators import login_required
# Create your views here.
from .models import Batch, Student, Semester, User, Course, RegisteredStudent
from .utils import *

@login_required
def home_view(request):
    batches = Batch.objects.all().order_by('-session')
    context = {
        'batches': batches,
    }
    return render(request, 'accounts/home.html', context)


@login_required
def dashboard_view(request):
    user_obj = get_user_from_jwt(request)
    user = None
    if user_obj:
        user = {
            'id': user_obj.id,
            'name': user_obj.name,
            'email': user_obj.email,
            'role': user_obj.role,
            'designation': user_obj.designation,
        }

    courses_count = Course.objects.filter(course_teacher=user_obj).count() if user_obj else 0
    marks_completed = Course.objects.filter(course_teacher=user_obj, marks_input_status=True).count() if user_obj else 0
    marks_pending = courses_count - marks_completed
    batches = Batch.objects.all().order_by('-session')

    context = {
        'user_profile': user,
        'courses_count': courses_count,
        'marks_completed': marks_completed,
        'marks_pending': marks_pending,
        'batches': batches,
    }
    return render(request, 'accounts/dashboard.html', context)


@login_required
def batch_details_view(request, batch_id):
    batch = Batch.objects.filter(pk=batch_id).first()
    if not batch:
        return redirect('home')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add_student':
            student_id = (request.POST.get('student_id') or '').strip()
            student_name = (request.POST.get('student_name') or '').strip()
            student_email = (request.POST.get('student_email') or '').strip()
            student_group = (request.POST.get('student_group') or '').strip()

            if not student_id or not student_name:
                messages.error(request, 'Student ID and name are required.')
            elif not Student.is_valid_student_id(student_id):
                messages.error(request, 'Student ID must match ITXXXXX format.')
            elif Student.objects.filter(student_id=student_id).exists():
                messages.error(request, 'Student ID already exists.')
            elif student_group not in dict(Student.GROUP_CHOISES).keys():
                messages.error(request, 'Invalid group selected.')
            else:
                Student.objects.create(
                    student_id=student_id.upper(),
                    name=student_name,
                    email=student_email or None,
                    group=student_group,
                    batch=batch
                )
                messages.success(request, f'Student {student_name} added.')

            return redirect('batch_details', batch_id=batch.id)

        if action == 'add_bulk_students':
            csv_file = request.FILES.get('students_csv')
            if not csv_file:
                messages.error(request, 'Please upload a CSV file.')
                return redirect('batch_details', batch_id=batch.id)

            try:
                content = csv_file.read().decode('utf-8')
                reader = csv.reader(io.StringIO(content))
            except Exception:
                messages.error(request, 'Unable to read the CSV file. Ensure UTF-8 encoded CSV.')
                return redirect('batch_details', batch_id=batch.id)

            rows = list(reader)
            if not rows:
                messages.error(request, 'CSV file is empty.')
                return redirect('batch_details', batch_id=batch.id)

            header = rows[0]
            start_index = 1 if header and header[0].strip().lower() in ('id', 'student id', 'student_id') else 0
            if start_index == 1 and len(rows) == 1:
                messages.error(request, 'CSV file has header but no data rows.')
                return redirect('batch_details', batch_id=batch.id)

            parsed_students = []
            errors = []
            seen_ids = set()

            for idx, row in enumerate(rows[start_index:], start=start_index + 1):
                if not row or len(row) < 2:
                    errors.append(f'Row {idx}: required fields ID and Name are missing.')
                    continue

                sid = (row[0] or '').strip()
                name = (row[1] or '').strip()
                email = (row[2] if len(row) > 2 else '').strip() if row else ''
                group = (row[3] if len(row) > 3 else '').strip() if row else ''

                if not sid or not name:
                    errors.append(f'Row {idx}: Student ID and Name are required.')
                    continue

                sid = sid.upper()

                if not Student.is_valid_student_id(sid):
                    errors.append(f'Row {idx}: Student ID "{sid}" is invalid (use ITXXXXX).')
                    continue

                if sid in seen_ids:
                    errors.append(f'Row {idx}: Duplicate Student ID "{sid}" in file.')
                    continue

                if group and group not in dict(Student.GROUP_CHOISES).keys():
                    errors.append(f'Row {idx}: Invalid group "{group}". Must be one of {", ".join(dict(Student.GROUP_CHOISES).keys())}.')
                    continue

                seen_ids.add(sid)
                parsed_students.append({'student_id': sid, 'name': name, 'email': email, 'group': group or 'Both'})

            existing = set(Student.objects.filter(student_id__in=[s['student_id'] for s in parsed_students]).values_list('student_id', flat=True))
            for sid in existing:
                errors.append(f'Student ID "{sid}" already exists in database.')

            if errors:
                for error in errors:
                    messages.error(request, error)
            else:
                created = 0
                for student_data in parsed_students:
                    Student.objects.create(
                        student_id=student_data['student_id'],
                        name=student_data['name'],
                        email=student_data['email'] or None,
                        group=student_data['group'],
                        batch=batch
                    )
                    created += 1
                messages.success(request, f'{created} students imported successfully.')

            return redirect('batch_details', batch_id=batch.id)

        if action == 'add_semester':
            semester_name = (request.POST.get('semester_name') or '').strip()
            chairman_id = request.POST.get('chairman_id')
            result_status = request.POST.get('result_status') == 'on'

            if not semester_name:
                messages.error(request, 'Semester name is required.')
            elif batch.semesters.filter(name=semester_name).exists():
                messages.error(request, 'Semester already exists for this batch.')
            else:
                students_to_register = batch.students.all()

                if semester_name == '3rd Semester':
                    students_to_register = students_to_register.filter(group='M.Engg')

                if not students_to_register:
                    messages.error(request, 'Please add all admitted students before creating any semester')
                    return redirect('batch_details', batch_id=batch.id)

                chairman = None
                if chairman_id:
                    chairman = User.objects.filter(pk=chairman_id).first()
                semester = Semester.objects.create(
                    batch=batch,
                    name=semester_name,
                    committee_chairman=chairman,
                    result_status=result_status,
                )

                registered_count = 0
                for student in students_to_register:
                    RegisteredStudent.objects.get_or_create(
                        batch=batch,
                        semester=semester,
                        student=student
                    )
                    registered_count += 1
                    
                messages.success(request, f'Semester {semester_name} added. {registered_count} students registered.')

            return redirect('batch_details', batch_id=batch.id)

        if action == 'update_student_groups':
            # Check if second semester already exists
            if batch.semesters.filter(name='2nd Semester').exists():
                messages.error(request, "You can't update student group after second semester created.")
                return redirect('batch_details', batch_id=batch.id)

            updated_count = 0
            for student in batch.students.all():
                new_group = request.POST.get(f'group_{student.student_id}')
                if new_group and new_group != student.group:
                    if new_group in dict(Student.GROUP_CHOISES).keys():
                        student.group = new_group
                        student.save()
                        updated_count += 1
            
            if updated_count > 0:
                messages.success(request, f'Updated group for {updated_count} students.')
            else:
                messages.info(request, 'No changes were made.')
                
            return redirect('batch_details', batch_id=batch.id)

    students = batch.students.all().order_by('student_id')
    semesters = batch.semesters.exclude(name='').order_by('name')
    chairmen = User.objects.only('id', 'name').order_by('name')
    has_2nd_semester = semesters.filter(name='2nd Semester').exists()

    context = {
        'batch': batch,
        'students': students,
        'semesters': semesters,
        'chairmen': chairmen,
        'has_2nd_semester': has_2nd_semester,
    }

    return render(request, 'accounts/batch_details.html', context)

@login_required
def create_batch_view(request):
    context = {}

    if request.method == "POST":
        # Get data from the form
        session_val = (request.POST.get('session') or '').strip()
        name_val = (request.POST.get('name') or '').strip() or 'Masters in ICT'

        context.update({'session': session_val, 'name': name_val})

        # Validate required session
        if not session_val:
            messages.error(request, "Session is required.")
            return render(request, 'accounts/create_batch.html', context)

        # Check duplicate session
        if Batch.objects.filter(session=session_val).exists():
            messages.error(request, "A batch with this session already exists.")
            return render(request, 'accounts/create_batch.html', context)

        try:
            Batch.objects.create(session=session_val, name=name_val)
            messages.success(request, "Batch created successfully!")
            return redirect('home')
        except Exception as e:
            messages.error(request, "Error creating batch. Please try again.")
            context['error_detail'] = str(e)

    return render(request, 'accounts/create_batch.html', context)


@login_required
def manage_semester_view(request, batch_id, semester_id):
    batch = Batch.objects.filter(pk=batch_id).first()
    semester = Semester.objects.filter(pk=semester_id, batch=batch).first()
    
    if not batch or not semester:
        return redirect('home')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_course':
            if semester.result_status:
                messages.error(request, 'Cannot add new courses. This semester\'s results are already finalized.')
                return redirect('manage_semester', batch_id=batch.id, semester_id=semester.id)

            course_code = (request.POST.get('course_code') or '').strip()
            title = (request.POST.get('title') or '').strip()
            credit_hour = request.POST.get('credit_hour')
            course_type = (request.POST.get('course_type') or 'Theory').strip()
            target_student = (request.POST.get('target_student') or '').strip()
            teacher_id = request.POST.get('course_teacher')
            
            try:
                credit_hour = float(credit_hour) if credit_hour else 3.0
            except ValueError:
                credit_hour = 3.0
            
            if not course_code or not title or credit_hour <= 0 or not course_type or not target_student:
                messages.error(request, 'All fields are required and credit hour must be positive.')
            elif Course.objects.filter(course_code=course_code, batch=batch, semester=semester).exists():
                messages.error(request, 'Course code already exists for this semester.')
            else:
                teacher = None
                if teacher_id:
                    teacher = User.objects.filter(pk=teacher_id).first()
                
                course = Course.objects.create(
                    course_code=course_code,
                    title=title,
                    credit_hour=credit_hour,
                    type=course_type,
                    target_student=target_student,
                    course_teacher=teacher,
                    batch=batch,
                    semester=semester,
                )

                # add CourseResult records for each registered student matching target_student
                from results.models import CourseResult
                registered_students = semester.registered_students.all().select_related('student')
                
                result_count = 0
                for reg in registered_students:
                    # Logic: if course is for 'Both', all students get it.
                    # Otherwise, student group must match course target_student.
                    if target_student == 'Both' or reg.student.group == target_student or reg.student.group == 'Both':
                        CourseResult.objects.get_or_create(
                            student=reg.student,
                            course=course,
                            semester=semester
                        )
                        result_count += 1

                messages.success(request, f'Course {title} added. {result_count} result records initialized.')
            
            return redirect('manage_semester', batch_id=batch.id, semester_id=semester.id)
    
    courses = semester.courses.all().order_by('course_code')
    theory_courses = courses.filter(type='Theory')
    teachers = User.objects.only('id', 'name').order_by('name')
    
    from .models import RegisteredStudent
    registered_students = semester.registered_students.all().select_related('student').order_by('student__student_id')
    
    user_obj = get_user_from_jwt(request)
    context = {
        'batch': batch,
        'semester': semester,
        'theory_courses': theory_courses,
        'teachers': teachers,
        'registered_students': registered_students,
        'current_user_id': user_obj.id if user_obj else None,
    }
    
    return render(request, 'accounts/manage_semester.html', context)


@login_required
def delete_registered_student_view(request, batch_id, semester_id, registration_id):
    from .models import RegisteredStudent
    registration = RegisteredStudent.objects.filter(
        pk=registration_id, 
        batch_id=batch_id, 
        semester_id=semester_id
    ).first()
    
    if registration:
        student_name = registration.student.name
        registration.delete()
        messages.success(request, f'Registration for {student_name} removed.')
    else:
        messages.error(request, 'Registration record not found.')
        
    return redirect('manage_semester', batch_id=batch_id, semester_id=semester_id)


@csrf_exempt
@require_http_methods(["POST"])
async def ai_proxy_view(request):
    """
    Proxies requests from the frontend to the local FastAPI service.
    This allows the AI service to work on Render's single-port setup.
    """
    # On Local, we might still want to use the proxy if the frontend points here
    target_url = "http://127.0.0.1:8001/chat"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                target_url,
                content=request.body,
                headers={"Content-Type": "application/json"},
                timeout=60.0
            )
            return JsonResponse(response.json(), status=response.status_code)
    except Exception as e:
        import traceback
        print(f"--- AI PROXY ERROR (Target: {target_url}) ---\n{traceback.format_exc()}\n")
        return JsonResponse({
            "error": "AI backend is not available yet.",
            "details": str(e)
        }, status=503)


# Login Views
def login_view(request):
    """Render login page"""
    return render(request, 'accounts/login.html')


@csrf_exempt
@require_http_methods(["POST"])
def api_login(request):
    """
    API endpoint for JWT token generation
    """
    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        
        if not email or not password:
            return JsonResponse({
                'success': False,
                'message': 'Email and password are required.'
            }, status=400)
        
        # Find user by email
        user = User.objects.filter(email=email).first()
        
        if not user:
            return JsonResponse({
                'success': False,
                'message': 'Invalid email or password.'
            }, status=401)
        
        # Verify password using Django's check_password
        if not check_password(password, user.password):
            # Fallback for old SHA256 passwords
            from hashlib import sha256
            password_hash = sha256(password.encode()).hexdigest()
            if user.password != password_hash and user.password != password:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid email or password.'
                }, status=401)
            else:
                # Upgrade password to secure hash on successful login
                user.password = make_password(password)
                user.save()
        
        # Generate JWT tokens
        refresh = RefreshToken()
        refresh['user_id'] = user.id
        
        access = refresh.access_token
        access['user_id'] = user.id
        
        user_data = {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'role': user.role,
            'designation': user.designation,
        }
        
        response = JsonResponse({
            'success': True,
            'message': 'Login successful!',
            'access': str(access),
            'refresh': str(refresh),
            'user': user_data,
        }, status=200)

        # Set tokens in cookies for hybrid support (template views)
        # access_token expires in 72 hours per settings, refresh in 30 days
        response.set_cookie(
            key='access_token',
            value=str(access),
            httponly=True,
            secure=not settings.DEBUG,
            samesite='Lax',
            max_age=3 * 24 * 60 * 60 # 3 days
        )
        response.set_cookie(
            key='refresh_token',
            value=str(refresh),
            httponly=True,
            secure=not settings.DEBUG,
            samesite='Lax',
            max_age=30 * 24 * 60 * 60 # 30 days
        )
        
        return response
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data.'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_logout(request):
    """
    API endpoint for logout
    """
    try:
        response = JsonResponse({
            'success': True,
            'message': 'Logout successful!'
        }, status=200)
        
        # Clear cookies
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        
        return response
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }, status=500)


def send_brevo_email(to_email, subject, content):
    """Helper to send email via Brevo API"""
    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "accept": "application/json",
        "api-key": settings.BREVO_API_KEY,
        "content-type": "application/json"
    }
    payload = {
        "sender": {"name": settings.BREVO_SENDER_NAME, "email": settings.BREVO_SENDER_EMAIL},
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": content
    }
    try:
        with httpx.Client() as client:
            response = client.post(url, headers=headers, json=payload)
            return response.status_code < 300
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


@csrf_exempt
@require_http_methods(["POST"])
def initiate_password_reset(request):
    try:
        email = None
        if request.body:
            try:
                data = json.loads(request.body)
                email = data.get('email', '').strip()
            except json.JSONDecodeError:
                pass
        
        user_obj = get_user_from_jwt(request)
        user = None
        if user_obj:
            user = user_obj
        elif email:
            user = User.objects.filter(email=email).first()
        
        # Security: Generic response for forgot password to prevent email enumeration
        if not user:
            if email and not user_obj:
                return JsonResponse({'success': True, 'message': 'If an account exists with this email, an OTP has been sent.'})
            return JsonResponse({'success': False, 'message': 'User not found.'}, status=404)

        # Secure 6-digit OTP
        otp = "".join([str(secrets.SystemRandom().randint(0, 9)) for _ in range(6)])
        user.otp_code = otp
        user.otp_expiry = timezone.now() + timedelta(minutes=3)
        user.save()

        subject = "Your Password Reset OTP"
        content = get_password_reset_email_body(user.name, otp)
        
        if send_brevo_email(user.email, subject, content):
            msg = 'OTP sent to your email.' if user_obj else 'If an account exists with this email, an OTP has been sent.'
            return JsonResponse({'success': True, 'message': msg})
        else:
            return JsonResponse({'success': False, 'message': 'Failed to send OTP email.'}, status=500)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def verify_and_reset_password(request):
    try:
        data = json.loads(request.body)
        otp = data.get('otp', '').strip()
        new_password = data.get('new_password', '').strip()
        email = data.get('email', '').strip()
        
        if not otp or not new_password:
            return JsonResponse({'success': False, 'message': 'OTP and new password are required.'}, status=400)
            
        user_obj = get_user_from_jwt(request)
        user = None
        if user_obj:
            user = user_obj
        elif email:
            user = User.objects.filter(email=email).first()
        
        if not user:
            return JsonResponse({'success': False, 'message': 'User not found.'}, status=404)
            
        # Check OTP and expiry
        if user.otp_code != otp:
            return JsonResponse({'success': False, 'message': 'Invalid OTP.'}, status=400)
            
        if user.otp_expiry < timezone.now():
            return JsonResponse({'success': False, 'message': 'OTP has expired.'}, status=400)
            
        # Update password securely
        user.password = make_password(new_password)
        user.otp_code = None
        user.otp_expiry = None
        user.save()
        
        return JsonResponse({'success': True, 'message': 'Password reset successful!'})
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON data.'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'An error occurred: {str(e)}'}, status=500)

