from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # --- ADMIN DASHBOARD AND MANAGEMENT ---
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
    path('courses/<int:id>/delete/', views.delete_course, name='delete_course'),
    path('courses/<int:id>/edit/', views.edit_course, name='edit_course'),

    # Assignments (Admin)
    path('assignments/', views.assignment_list, name='assignment_list'),
    path('assignments/add/', views.assignment_create, name='assignment_create'),
    path('assignments/<int:id>/edit/', views.edit_assignment, name='edit_assignment'),
    path('assignments/<int:id>/delete/', views.delete_assignment, name='delete_assignment'),

    # --- TEACHER DASHBOARD AND FUNCTIONS ---
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),

    # Teacher Courses
    path('teacher/courses/', views.teacher_courses, name='teacher_courses'),
    path('teacher/courses/add/', views.teacher_course_create, name='teacher_course_create'),
    path('teacher/courses/<int:course_id>/', views.teacher_course_detail, name='teacher_course_detail'),
    # Teacher edit course - separate view
    path('teacher/course/<int:id>/edit/', views.teacher_edit_course, name='teacher_edit_course'),
    path('teacher/courses/<int:course_id>/delete/', views.delete_course, name='teacher_course_delete'),

    # Course Modules (NEW)
    path('teacher/courses/<int:course_id>/modules/', views.course_modules, name='course_modules'),
    path('teacher/courses/<int:course_id>/modules/add/', views.add_course_module, name='add_course_module'),

    # Teacher Assignments
    path('teacher/assignments/', views.teacher_assignments, name='teacher_assignments'),
    path('teacher/assignments/add/', views.teacher_assignment_create, name='teacher_assignment_create'),
    path('teacher/assignments/<int:id>/', views.teacher_assignment_detail, name='teacher_assignment_detail'),
    path('teacher/assignments/<int:id>/edit/', views.edit_assignment, name='teacher_edit_assignment'),
    path('teacher/grade/<int:submission_id>/', views.grade_submission, name='grade_submission'),

    # Assignment Submission
    path('teacher/submission/<int:submission_id>/details/', views.submission_details, name='submission_details'),
    path('teacher/assignments/<int:assignment_id>/download-all/', views.download_all_submissions, name='download_all_submissions'),

    # Teacher Students
    path('teacher/students/', views.teacher_students, name='teacher_students'),
    path('teacher/course/<int:course_id>/add-student/', views.add_student_to_course, name='add_student_to_course'),
    path('teacher/course/<int:course_id>/remove-student/<int:student_id>/', views.remove_student_from_course, name='remove_student_from_course'),

    # Progress Tracking
    path('teacher/student-progress/<int:course_id>/', views.teacher_student_progress, name='teacher_student_progress'),
    path('teacher/progress-track/', views.teacher_progress_track, name='teacher_progress_track'),
    path('teacher/send-progress-reminder/', views.send_progress_reminder, name='send_progress_reminder'),
    path('teacher/progress/update/<int:progress_id>/', views.update_student_progress, name='update_student_progress'), # NEW

    # Teacher Settings
    path('teacher/settings/', views.teacher_settings, name='teacher_settings'),
    path('teacher/settings/profile/', views.teacher_profile_settings, name='teacher_profile_settings'),
    path('teacher/settings/appearance/', views.teacher_appearance_settings, name='teacher_appearance_settings'),
    path('teacher/settings/security/', views.teacher_security_settings, name='teacher_security_settings'),

    # Student Settings
    path('student/settings/', views.student_settings, name='student_settings'),
    path('student/settings/profile/', views.student_profile_settings, name='student_profile_settings'),
    path('student/settings/appearance/', views.student_appearance_settings, name='student_appearance_settings'),
    path('student/settings/security/', views.student_security_settings, name='student_security_settings'),



    # --- STUDENT DASHBOARD AND FUNCTIONS ---
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/courses/', views.student_courses, name='student_courses'),
    path('student/courses/<int:course_id>/', views.student_course_detail, name='student_course_detail'),
    path('student/course-catalog/', views.course_catalog, name='course_catalog'),
      path('student/material/<int:material_id>/download/',
         views.download_course_material,
         name='download_course_material'),

    # Student Assignments
    path('student/assignments/', views.student_assignments, name='student_assignments'),
    path('student/assignments/<int:assignment_id>/', views.student_assignment_detail, name='student_assignment_detail'),
    # Updated to the new assignment submission path/name:
    path('student/assignments/<int:assignment_id>/submit/', views.student_assignment_submit, name='student_assignment_submit'),

    # Additional Student URLs
    path('student/profile/', views.student_profile, name='student_profile'),
    path('student/settings/', views.student_settings, name='student_settings'),
    path('student/progress/', views.student_progress, name='student_progress'),
    path('student/messages/', views.student_messages, name='student_messages'),
    path('student/aboutus/', views.student_aboutus, name='student_aboutus'),

    # --- SHARED/COMMON URLs ---

    # Course Materials
    path('teacher/courses/<int:course_id>/materials/', views.teacher_course_materials, name='teacher_course_materials'),
    path('teacher/courses/<int:course_id>/materials/add/', views.add_course_material, name='add_course_material'),
    path('teacher/courses/materials/<int:material_id>/delete/', views.delete_course_material, name='delete_course_material'),
    path('student/courses/<int:course_id>/materials/', views.student_course_materials, name='student_course_materials'),

    # Settings (Admin/Shared)
    path('settings/', views.admin_settings, name='admin_settings'),
    path('settings/profile/', views.profile_settings, name='profile_settings'),
    path('settings/appearance/', views.appearance_settings, name='appearance_settings'),
    path('settings/security/', views.security_settings, name='security_settings'),
    path('settings/security/generate-qr/', views.generate_qr_code, name='generate_qr_code'),

    # Theme Update
    path('update-theme/', views.update_theme_preference, name='update_theme'),

    # Messaging
    path('messages/', views.message_list, name='message_list'),
    path('messages/compose/', views.message_compose, name='message_compose'),
    path('messages/compose/<int:recipient_id>/', views.message_compose, name='message_compose_to'),
    path('messages/<int:message_id>/', views.message_detail, name='message_detail'),
    path('messages/<int:message_id>/delete/', views.message_delete, name='message_delete'),
    path('messages/unread-count/', views.get_unread_count, name='unread_count'),

    # Student Messages
    path('student/messages/', views.student_messages, name='student_messages'),
    path('student/messages/sent/', views.student_sent_messages, name='student_sent_messages'),
    path('student/messages/compose/', views.student_compose_message, name='student_compose_message'),
    path('student/messages/<int:message_id>/', views.student_message_detail, name='student_message_detail'),
    path('student/messages/<int:message_id>/delete/', views.student_delete_message, name='student_delete_message'),
    path('student/messages/<int:message_id>/read/', views.mark_message_read, name='mark_message_read'),

    # Teacher Messages
    path('teacher/messages/', views.teacher_messages, name='teacher_messages'),
    path('teacher/messages/sent/', views.teacher_sent_messages, name='teacher_sent_messages'),
    path('teacher/messages/compose/', views.teacher_compose_message, name='teacher_compose_message'),
    path('teacher/messages/<int:message_id>/', views.teacher_message_detail, name='teacher_message_detail'),
    path('teacher/messages/<int:message_id>/delete/', views.teacher_delete_message, name='teacher_delete_message'),
    path('teacher/messages/<int:message_id>/read/', views.teacher_mark_message_read, name='teacher_mark_message_read'),

    # Admin Messages
    path('admin/messages/', views.admin_messages, name='admin_messages'),
    path('admin/messages/sent/', views.admin_sent_messages, name='admin_sent_messages'),
    path('admin/messages/compose/', views.admin_compose_message, name='admin_compose_message'),
    path('admin/messages/<int:message_id>/', views.admin_message_detail, name='admin_message_detail'),
    path('admin/messages/<int:message_id>/delete/', views.admin_delete_message, name='admin_delete_message'),
    path('admin/messages/<int:message_id>/read/', views.admin_mark_message_read, name='admin_mark_message_read'),
]
