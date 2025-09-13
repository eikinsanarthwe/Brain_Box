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
]
