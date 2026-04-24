"""
URL configuration for proj_arms project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from accounts import views as accounts_views
from results import views as results_views

urlpatterns = [
    path('health/', accounts_views.health_check, name='health_check'),
    path('admin/', admin.site.urls),
    path('', accounts_views.home_view, name='home'),
    path('dashboard/', accounts_views.dashboard_view, name='dashboard'),
    path('login/', accounts_views.login_view, name='login'),
    path('api/login/', accounts_views.api_login, name='api_login'),
    path('api/logout/', accounts_views.api_logout, name='api_logout'),
    path('api/ai/chat/', accounts_views.ai_proxy_view, name='ai_chat_proxy'),
    path('api/password-reset/initiate/', accounts_views.initiate_password_reset, name='initiate_password_reset'),
    path('api/password-reset/verify/', accounts_views.verify_and_reset_password, name='verify_and_reset_password'),
    path('batch/create/', accounts_views.create_batch_view, name='create_batch'),
    path('batch/<int:batch_id>/details/', accounts_views.batch_details_view, name='batch_details'),
    path('batch/<int:batch_id>/semester/<int:semester_id>/manage/', accounts_views.manage_semester_view, name='manage_semester'),
    path('batch/<int:batch_id>/semester/<int:semester_id>/registration/<int:registration_id>/delete/', accounts_views.delete_registered_student_view, name='delete_registered_student'),
    path('batch/<int:batch_id>/semester/<int:semester_id>/course/<int:course_id>/input-marks/', results_views.input_marks_view, name='input_marks'),
    path('batch/<int:batch_id>/semester/<int:semester_id>/course/<int:course_id>/export-pdf/', results_views.export_course_result_pdf, name='export_course_result_pdf'),
    path('batch/<int:batch_id>/semester/<int:semester_id>/course/<int:course_id>/export-detailed-pdf/', results_views.detailed_course_result_pdf, name='detailed_course_result_pdf'),
    path('semester/<int:semester_id>/result/<str:group>/', results_views.handle_result_type, name='export_semester_result'),
]


