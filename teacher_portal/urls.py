from django.urls import path
from . import views

app_name = 'teacher_portal'

urlpatterns = [
    # Dashboard
    path('dashboard/', views.teacher_dashboard, name='teacher_dashboard'),

    # Courses
    path('courses/', views.course_list, name='course_list'),
    path('courses/add/', views.course_create, name='course_create'),
    path('courses/<int:course_id>/', views.course_detail, name='course_detail'),
    path('courses/<int:course_id>/edit/', views.course_edit, name='course_edit'),
    path('courses/<int:course_id>/delete/', views.course_delete, name='course_delete'),

    # Course Student Management
    path("courses/<int:course_id>/students/add/", views.add_student_to_course, name="add_student_to_course"),
    path('courses/<int:course_id>/students/<int:student_id>/remove/', views.remove_student_from_course, name='remove_student_from_course'),

    # Assignments
    path('assignments/', views.assignment_list, name='assignment_list'),
    path('assignments/add/', views.assignment_add, name='assignment_add'),
    path('assignments/<int:assignment_id>/', views.assignment_detail, name='assignment_detail'),
    path('assignments/<int:assignment_id>/edit/', views.assignment_edit, name='assignment_edit'),
    path('assignments/<int:assignment_id>/grade/', views.grade_assignment, name='grade_assignment'),
    path('assignments/<int:assignment_id>/delete/', views.assignment_delete, name='assignment_delete'),

    # Students (CRUD)
    path('students/', views.student_list, name='student_list'),
    path('students/add/', views.student_create, name='student_add'),
    path('students/<int:student_id>/', views.student_detail, name='student_detail'),
    path('students/<int:student_id>/edit/', views.student_edit, name='student_edit'),
    path('students/<int:student_id>/delete/', views.student_delete, name='student_delete'),

    # Manage Courses for a Student
    path('students/<int:student_id>/courses/manage/', views.student_manage_courses, name='student_manage_courses'),
    path("teacher/courses/<int:course_id>/students/add/", views.add_student_to_course, name="add_student_to_course"),
    path("teacher/students/<int:student_id>/courses/add/", views.add_course_to_student, name="add_course_to_student"),
    path("students/<int:student_id>/remove_course/<int:course_id>/", views.remove_student_from_course, name="remove_student_from_course"),

    # Grades
    path('gradebook/', views.gradebook, name='gradebook'),
    #redirect
    path('redirect/', views.role_redirect, name='role_redirect'),


    # Settings and Profile
    path('settings/', views.teacher_settings, name='teacher_settings'),
    path('profile/', views.profile, name='profile'),
]
