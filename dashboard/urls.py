from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Admin Management
    path('admin-users/', views.admin_list, name='admin_list'),
    path('admin-users/add/', views.create_admin_user, name='create_admin'),
    path('admin-users/<int:id>/edit/', views.edit_admin, name='edit_admin'),
    path('admin-users/<int:id>/delete/', views.delete_admin, name='delete_admin'),

    # Teachers
    path('teachers/', views.teacher_list, name='teacher_list'),
    path('teachers/add/', views.teacher_create, name='teacher_create'),
    path('teachers/<int:id>/edit/', views.edit_teacher, name='edit_teacher'),
    path('teachers/<int:id>/delete/', views.delete_teacher, name='delete_teacher'),

    # Students
    path('students/', views.student_list, name='student_list'),
    path('students/add/', views.student_create, name='student_create'),
    path('students/<int:id>/edit/', views.edit_student, name='edit_student'),
    path('students/<int:id>/delete/', views.delete_student, name='delete_student'),

    # Courses
    path('courses/', views.course_list, name='course_list'),
    path('courses/add/', views.course_create, name='course_create'),
    path('courses/<int:id>/edit/', views.edit_course, name='edit_course'),
    path('courses/<int:id>/delete/', views.delete_course, name='delete_course'),

    # Assignments
    path('assignments/', views.assignment_list, name='assignment_list'),
    path('assignments/add/', views.assignment_create, name='assignment_create'),
    path('assignments/<int:id>/edit/', views.edit_assignment, name='edit_assignment'),
    path('assignments/<int:id>/delete/', views.delete_assignment, name='delete_assignment'),

    # Teacher Dashboard URLs
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/courses/', views.teacher_courses, name='teacher_courses'),
    path('teacher/assignments/', views.teacher_assignments, name='teacher_assignments'),
    path('teacher/assignments/add/', views.teacher_assignment_create, name='teacher_assignment_create'),  # ADD THIS LINE
    path('teacher/assignments/<int:id>/', views.teacher_assignment_detail, name='teacher_assignment_detail'),
    path('teacher/grade/<int:submission_id>/', views.grade_submission, name='grade_submission'),
    path('teacher/students/', views.teacher_students, name='teacher_students'),
    # Add these to your urlpatterns list:
    # In your urls.py, ensure you have:
    path('teacher/courses/add/', views.teacher_course_create, name='teacher_course_create'),
    path('teacher/students/add/', views.teacher_student_create, name='teacher_student_create'),
    # Add these URLs to your existing urlpatterns list:
path('teacher/courses/<int:course_id>/', views.teacher_course_detail, name='teacher_course_detail'),
path('teacher/courses/<int:course_id>/remove-student/<int:student_id>/', views.remove_student_from_course, name='remove_student_from_course'),

# Course Materials URLs
path('teacher/courses/<int:course_id>/materials/', views.teacher_course_materials, name='teacher_course_materials'),
path('teacher/courses/<int:course_id>/materials/add/', views.add_course_material, name='add_course_material'),
path('teacher/courses/materials/<int:material_id>/delete/', views.delete_course_material, name='delete_course_material'),
path('student/courses/<int:course_id>/materials/', views.student_course_materials, name='student_course_materials'),
# Message URLs
path('messages/', views.message_list, name='message_list'),
path('messages/compose/', views.message_compose, name='message_compose'),
path('messages/compose/<int:recipient_id>/', views.message_compose, name='message_compose_to'),
path('messages/<int:message_id>/', views.message_detail, name='message_detail'),
path('messages/<int:message_id>/delete/', views.message_delete, name='message_delete'),
path('messages/unread-count/', views.get_unread_count, name='unread_count'),]