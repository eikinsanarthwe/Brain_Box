from django.urls import path
from . import views

app_name = 'dashboard'  # Add this line for URL namespacing

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
    path('teacher/progress-track/', views.teacher_progress_track, name='teacher_progress_track'),
    path('teacher/send-progress-reminder/', views.send_progress_reminder, name='send_progress_reminder'),

    # Student Dashboard URLs
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/courses/', views.student_my_courses, name='student_my_courses'),
    path('student/assignments/', views.student_assignments, name='student_assignments'),
    path('student/assignment/<int:assignment_id>/', views.student_assignment_detail, name='student_assignment_detail'),
    path('student/assignment/<int:assignment_id>/submit/', views.student_assignment_submit, name='student_assignment_submit'),  # ADD THIS LINE
    path('student/progress/', views.student_progress, name='student_progress'),
    path('student/messages/', views.student_messages, name='student_messages'),
    path('student/aboutus/', views.student_aboutus, name='student_aboutus'),
    path('student/settings/', views.student_settings, name='student_settings'),
    path('student/profile/', views.student_profile, name='student_profile'),

    # Course URLs
    path('courses/catalog/', views.course_catalog, name='course_catalog'),
    path('courses/<int:pk>/', views.course_detail, name='course_detail'),
    path('teacher/course/create/', views.teacher_course_create, name='teacher_course_create'),
    path('teacher/course/<int:course_id>/', views.teacher_course_detail, name='teacher_course_detail'),
    path('teacher/course/<int:course_id>/edit/', views.edit_course, name='edit_course'),
    path('teacher/course/<int:course_id>/materials/', views.teacher_course_materials, name='teacher_course_materials'),
    path('teacher/course/<int:course_id>/materials/add/', views.add_course_material, name='add_course_material'),
    path('teacher/course/<int:course_id>/materials/<int:material_id>/delete/', views.delete_course_material, name='delete_course_material'),
    path('student/course/<int:course_id>/materials/', views.student_course_materials, name='student_course_materials'),

    # Student Management URLs
    path('teacher/student/create/', views.teacher_student_create, name='teacher_student_create'),
    path('teacher/course/<int:course_id>/add-student/', views.add_student_to_course, name='add_student_to_course'),
    path('teacher/course/<int:course_id>/remove-student/<int:student_id>/', views.remove_student_from_course, name='remove_student_from_course'),

    # Message URLs
    path('messages/', views.message_list, name='message_list'),
    path('messages/compose/', views.message_compose, name='message_compose'),
    path('messages/compose/<int:recipient_id>/', views.message_compose, name='message_compose_to'),
    path('messages/<int:message_id>/', views.message_detail, name='message_detail'),
    path('messages/<int:message_id>/delete/', views.message_delete, name='message_delete'),
    path('messages/unread-count/', views.get_unread_count, name='get_unread_count'),

    # Settings URLs
    path('admin/settings/', views.admin_settings, name='admin_settings'),
    path('admin/settings/profile/', views.profile_settings, name='profile_settings'),
    path('admin/settings/appearance/', views.appearance_settings, name='appearance_settings'),
    path('admin/settings/security/', views.security_settings, name='security_settings'),
    path('teacher/settings/', views.teacher_settings, name='teacher_settings'),
    path('teacher/settings/profile/', views.teacher_profile_settings, name='teacher_profile_settings'),
    path('teacher/settings/appearance/', views.teacher_appearance_settings, name='teacher_appearance_settings'),
    path('teacher/settings/security/', views.teacher_security_settings, name='teacher_security_settings'),

    # API URLs
    path('api/get-teachers-by-course/', views.get_teachers_by_course, name='get_teachers_by_course'),
    path('api/update-theme/', views.update_theme_preference, name='update_theme_preference'),
    path('api/generate-qr-code/', views.generate_qr_code, name='generate_qr_code'),

    # Assignment Management URLs
    path('assignments/', views.assignment_list, name='assignment_list'),
    path('assignments/create/', views.assignment_create, name='assignment_create'),
    path('assignments/<int:id>/edit/', views.edit_assignment, name='edit_assignment'),
    path('assignments/<int:id>/delete/', views.delete_assignment, name='delete_assignment'),

    # User Management URLs
    path('admins/', views.admin_list, name='admin_list'),
    path('admins/create/', views.create_admin_user, name='create_admin_user'),
    path('admins/<int:id>/edit/', views.edit_admin, name='edit_admin'),
    path('admins/<int:id>/delete/', views.delete_admin, name='delete_admin'),
    path('teachers/<int:id>/edit/', views.edit_teacher, name='edit_teacher'),
    path('teachers/<int:id>/delete/', views.delete_teacher, name='delete_teacher'),
    path('students/<int:id>/edit/', views.edit_student, name='edit_student'),
    path('students/<int:id>/delete/', views.delete_student, name='delete_student'),

    # Course Management URLs
    path('courses/', views.course_list, name='course_list'),
    path('courses/create/', views.course_create, name='course_create'),
    path('courses/<int:id>/delete/', views.delete_course, name='delete_course'),
    


    # Logout URL
    path('logout/', views.custom_logout, name='logout'),
]
