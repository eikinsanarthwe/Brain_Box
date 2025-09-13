from django.urls import path
from . import views
from django.contrib.auth import views as auth_views




urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('admin/home/', views.admin_home, name='admin_home'),
    path('signup/', views.signup_view, name='signup'),
    path('teacher/home/', views.teacher_home, name='teacher_home'),
    path('student/home/', views.student_home, name='student_home'),
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('test/', views.test_view),
    path('logout/', views.logout_view, name='logout'),


]
