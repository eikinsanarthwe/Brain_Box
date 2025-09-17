from django.urls import path
from . import views

urlpatterns = [
    path('admin/home/', views.admin_home, name='admin_home'),
    path('admin/courses/', views.course_list, name='admin_courses'),
    path('admin/courses/new/', views.course_form, name='admin_course_form'),
    path('admin/students/', views.student_list, name='admin_students'),
    path('admin/students/new/', views.student_form, name='admin_student_form'),
    path('admin/teachers/', views.teacher_list, name='admin_teachers'),
    path('admin/teachers/new/', views.teacher_form, name='admin_teacher_form'),
    path('admin/assignments/', views.assignment, name='admin_assignments'),
    path('admin/assignments/new/', views.assignment_form, name='admin_assignment_form'),

# Teacher Dashboard URLs
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/courses/', views.teacher_courses, name='teacher_courses'),
    path('teacher/assignments/', views.teacher_assignments, name='teacher_assignments'),
    path('teacher/assignments/<int:id>/', views.teacher_assignment_detail, name='teacher_assignment_detail'),
    path('teacher/grade/<int:submission_id>/', views.grade_submission, name='grade_submission'),
    path('teacher/students/', views.teacher_students, name='teacher_students'),

    path('assignments/add/', views.teacher_assignment_create, name='teacher_assignment_create'),]
