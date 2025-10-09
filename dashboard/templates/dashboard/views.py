from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import ObjectDoesNotExist
from .decorators import role_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Student, Course
import json

# --- Helper Function for Role Checking (Needed for @user_passes_test) ---
def is_student(user):
    """
    Check if the user has the 'student' role.
    Assumes your CustomUser model has an 'is_student()' method or a 'role' attribute.
    """
    # Using user.is_student() as per your original definition
    return user.is_authenticated and user.is_student()

#-----------------------------
# Admin Views
#-----------------------------

@login_required
@role_required('admin')
def assignment_form(request):
    return render(request, 'dashboard/assignment_form.html')

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
    return render(request, 'dashboard/assignment.html')





#-----------------------------
# Teacher Views
#-----------------------------



    @login_required
@role_required('teacher')
def teacher_dashboard(request):
    return render(request, 'dashboard/teacher_dashboard.html')

@login_required
@role_required('teacher')
def teacher_courses(request):
    return render(request, 'dashboard/teacher_courses.html')

@login_required
@role_required('teacher')
def teacher_assignments(request):
    return render(request, 'dashboard/teacher_assignments.html')

@login_required
@role_required('teacher')
def teacher_assignment_detail(request, id):
    return render(request, 'dashboard/teacher_assignment_detail.html')

@login_required
@role_required('teacher')
def grade_submission(request, submission_id):
    return render(request, 'dashboard/grade_submission.html')

@login_required
@role_required('teacher')
def teacher_students(request):
    return render(request, 'dashboard/teacher_students.html')

@login_required
@role_required('teacher')
def teacher_assignment_create(request):
    return render(request, 'dashboard/teacher_assignment_create.html')

#-----------------------------
# Student Views
#-----------------------------

@login_required
@user_passes_test(is_student)
def student_dashboard(request):
    """
    View for the student dashboard. Fetches enrolled courses for dashboard display.
    """
    try:
        student_instance = Student.objects.get(user=request.user)
        # Fetch all courses the student is enrolled in
        enrolled_courses = student_instance.courses.all()
    except Student.DoesNotExist:
        # If no student profile exists, pass an empty list
        enrolled_courses = []

    context = {
        'courses': enrolled_courses,
    }
    return render(request, 'dashboard/student_dashboard.html', context)

@login_required
@user_passes_test(is_student)
def student_my_courses(request):
    """
    View for the student's "My Courses" page, showing all enrolled courses.
    """
    try:
        student_instance = Student.objects.get(user=request.user)
        # Fetch all courses the student is enrolled in
        enrolled_courses = student_instance.courses.all()
    except Student.DoesNotExist:
        # If no student profile exists, pass an empty list
        enrolled_courses = []

    context = {
        'courses': enrolled_courses,
    }
    return render(request, 'dashboard/student_my_courses.html', context)

@login_required
@user_passes_test(is_student)
def student_assignments(request):
    return render(request, 'dashboard/student_assignments.html')

@login_required
@user_passes_test(is_student)
def student_progress(request):
    return render(request, 'dashboard/student_progress.html')

@login_required
@user_passes_test(is_student)
def student_messages(request):
    return render(request, 'dashboard/student_messages.html')

@login_required
@user_passes_test(is_student)
def student_aboutus(request):
    return render(request, 'dashboard/student_aboutus.html')

@login_required
@user_passes_test(is_student)
def student_settings(request):
    return render(request, 'dashboard/student_settings.html')

@login_required
@user_passes_test(is_student)
def student_profile(request):
    return render(request, 'dashboard/student_profile.html')

# Missing Course Views
@login_required
def course_catalog(request):
    return render(request, 'dashboard/course_catalog.html')

@login_required
def course_detail(request, pk):
    return render(request, 'dashboard/course_detail.html')







