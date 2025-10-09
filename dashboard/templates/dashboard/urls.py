from django.urls import path
from . import views

urlpatterns = [
    # Admin URLs
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

    # Teacher Assignment URLs
    path('teacher/assignments/add/', views.teacher_assignment_create, name='teacher_assignment_create'),
    path('teacher/submission/<int:submission_id>/details/', views.submission_details, name='submission_details'),
    path('teacher/assignments/<int:assignment_id>/download-all/', views.download_all_submissions, name='download_all_submissions'),

    # Teacher Progress Tracking URLs
    path('course/<int:course_id>/progress/', views.teacher_student_progress, name='teacher_student_progress'),
    path('progress/update/<int:progress_id>/', views.update_student_progress, name='update_student_progress'),
    path('course/<int:course_id>/modules/', views.course_modules, name='course_modules'),
    path('course/<int:course_id>/modules/add/', views.add_course_module, name='add_course_module'),

    # Student Dashboard URLs
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/courses/', views.student_my_courses, name='student_my_courses'),
    path('student/assignments/', views.student_assignments, name='student_assignments'),
    path('student/progress/', views.student_progress, name='student_progress'),
    path('student/messages/', views.student_messages, name='student_messages'),
    path('student/aboutus/', views.student_aboutus, name='student_aboutus'),
    path('student/settings/', views.student_settings, name='student_settings'),
    path('student/profile/', views.student_profile, name='student_profile'),

    # Course URLs
    path('courses/catalog/', views.course_catalog, name='course_catalog'),
    path('courses/<int:pk>/', views.course_detail, name='course_detail'),
]
