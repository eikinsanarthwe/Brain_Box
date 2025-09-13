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
]
