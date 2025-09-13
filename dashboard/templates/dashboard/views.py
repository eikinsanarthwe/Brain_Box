from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .decorators import role_required

@login_required
@role_required('admin')
def admin_home(request):
    return render(request, 'dashboard/admin_home.html')

@login_required
@role_required('admin')
def course_list(request):
    return render(request, 'dashboard/course_list.html')

@login_required
@role_required('admin')
def course_form(request):
    return render(request, 'dashboard/course_form.html')

@login_required
@role_required('admin')
def student_list(request):
    return render(request, 'dashboard/student_list.html')

@login_required
@role_required('admin')
def student_form(request):
    return render(request, 'dashboard/student_form.html')

@login_required
@role_required('admin')
def teacher_list(request):
    return render(request, 'dashboard/teacher_list.html')

@login_required
@role_required('admin')
def teacher_form(request):
    return render(request, 'dashboard/teacher_form.html')

@login_required
@role_required('admin')
def assignment(request):
    return render(request, 'dashboard/assignment.html')  # ← Add actual template
