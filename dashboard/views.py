from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import logout, get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Teacher, Student, Course, Assignment, Submission
from .forms import TeacherForm, StudentForm, CourseForm, AssignmentForm, AdminCreationForm, AdminChangeForm,TeacherStudentForm,TeacherCourseForm
from .models import Teacher, Student, Course, Assignment, Submission, CourseMaterial, UserProfile
from .forms import TeacherForm, StudentForm, CourseForm, AssignmentForm, AdminCreationForm, AdminChangeForm,TeacherStudentForm,TeacherCourseForm, CourseMaterialForm
from django.db.models import Count, Avg
from datetime import datetime, timedelta
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
import pyotp
import qrcode
import io
import base64

User = get_user_model()

# -----------------------------
# Role-based access check
# -----------------------------
def is_admin(user):
    return user.is_authenticated and getattr(user, 'role', None) == 'admin'

# -----------------------------
# Logout View
# -----------------------------
def custom_logout(request):
    logout(request)
    return redirect('login')

# -----------------------------
# Dashboard View
# -----------------------------
@login_required
def dashboard(request):
    if request.user.role == 'admin':
        context = {
            'teacher_count': Teacher.objects.count(),
            'student_count': Student.objects.count(),
            'course_count': Course.objects.count(),
            'admin_count': User.objects.filter(role='admin').count(),
        }
        return render(request, 'dashboard/index.html', context)
    elif request.user.role == 'teacher':
        return teacher_dashboard(request)
    else:
        # Handle student role or others
        return redirect('login')
# -----------------------------
# Admin Views
# -----------------------------
@user_passes_test(is_admin)
def admin_list(request):
    admins = User.objects.filter(role='admin').order_by('date_joined')
    return render(request, 'dashboard/admin_list.html', {'admins': admins})

@user_passes_test(is_admin)
def create_admin_user(request):
    if request.method == 'POST':
        form = AdminCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'admin'
            user.is_staff = True
            user.save()
            messages.success(request, 'Admin user created successfully!')
            return redirect('dashboard:admin_list')
    else:
        form = AdminCreationForm()
    return render(request, 'dashboard/admin_form.html', {'form': form})

@user_passes_test(is_admin)
def edit_admin(request, id):
    admin = get_object_or_404(User, id=id, role='admin')
    if request.method == 'POST':
        form = AdminChangeForm(request.POST, instance=admin)
        if form.is_valid():
            user = form.save(commit=False)
            new_password = request.POST.get('new_password')
            if new_password:
                user.set_password(new_password)
            user.save()
            messages.success(request, 'Admin updated successfully!')
            return redirect('dashboard:admin_list')
    else:
        form = AdminChangeForm(instance=admin)
    return render(request, 'dashboard/admin_form.html', {
        'form': form,
        'title': 'Edit Admin',
        'admin_id': id
    })

@user_passes_test(is_admin)
def delete_admin(request, id):
    admin = get_object_or_404(User, id=id, role='admin')
    if admin != request.user:
        admin.delete()
        messages.success(request, 'Admin deleted successfully!')
    else:
        messages.error(request, 'You cannot delete yourself!')
    return redirect('dashboard:admin_list')

# -----------------------------
# Teacher Views
# -----------------------------
@login_required
def teacher_list(request):
    teachers = Teacher.objects.select_related('user').all()
    return render(request, 'dashboard/teacher_list.html', {
        'teachers': teachers,
        'title': 'Teachers Management'
    })

@login_required
def teacher_create(request):
    return edit_teacher(request)

@login_required
def edit_teacher(request, id=None):
    teacher = get_object_or_404(Teacher, id=id) if id else None
    if request.method == 'POST':
        form = TeacherForm(request.POST, instance=teacher)
        if form.is_valid():
            teacher = form.save()
            messages.success(request, f'Teacher {"updated" if id else "created"} successfully!')
            if '_addanother' in request.POST:
                return redirect('dashboard:teacher_create')
            elif '_continue' in request.POST:
                return redirect('dashboard:edit_teacher', teacher.id)
            return redirect('dashboard:teacher_list')
    else:
        form = TeacherForm(instance=teacher)
    return render(request, 'dashboard/teacher_form.html', {
        'form': form,
        'title': 'Edit Teacher' if id else 'Add Teacher'
    })

@login_required
def delete_teacher(request, id):
    teacher = get_object_or_404(Teacher, id=id)
    if teacher.user:
        teacher.user.delete()
    teacher.delete()
    messages.success(request, 'Teacher deleted successfully!')
    return redirect('dashboard:teacher_list')

# -----------------------------
# Student Views
# -----------------------------
@login_required
def student_list(request):
    students = Student.objects.select_related('user').all()
    return render(request, 'dashboard/student_list.html', {'students': students})

@user_passes_test(is_admin)
def student_create(request):
    return edit_student(request)

@user_passes_test(is_admin)
def edit_student(request, id=None):
    student = get_object_or_404(Student, id=id) if id else None
    if request.method == 'POST':
        form = StudentForm(request.POST, instance=student)
        if form.is_valid():
            student = form.save(commit=False)
            password = request.POST.get('password')
            if password:
                student.user.set_password(password)
                student.user.save()
            student.save()
            if '_addanother' in request.POST:
                messages.success(request, 'Student created successfully. You may add another student below.')
                return redirect('dashboard:student_create')
            elif '_continue' in request.POST:
                messages.success(request, 'Student updated successfully. You may edit it again below.')
                return redirect('dashboard:edit_student', student.id)
            messages.success(request, f'Student {"updated" if id else "created"} successfully!')
            return redirect('dashboard:student_list')
    else:
        form = StudentForm(instance=student)
    return render(request, 'dashboard/student_form.html', {
        'form': form,
        'title': 'Edit Student' if id else 'Add Student'
    })

@user_passes_test(is_admin)
def delete_student(request, id):
    student = get_object_or_404(Student, id=id)
    student.delete()
    messages.success(request, 'Student deleted successfully!')
    return redirect('dashboard:student_list')

# -----------------------------
# Course Views
# -----------------------------
@login_required
def course_list(request):
    courses = Course.objects.prefetch_related('teachers__user').all()
    return render(request, 'dashboard/course_list.html', {'courses': courses})

@login_required
def course_create(request):
    return edit_course(request)

@login_required
def edit_course(request, id=None):
    course = get_object_or_404(Course, id=id) if id else None
    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            course = form.save()
            messages.success(request, f'Course {"updated" if id else "created"} successfully!')
            return redirect('dashboard:course_list')
    else:
        form = CourseForm(instance=course)
    return render(request, 'dashboard/course_form.html', {
        'form': form,
        'title': 'Edit Course' if id else 'Add Course'
    })

@login_required
def delete_course(request, id):
    course = get_object_or_404(Course, id=id)
    course.delete()
    messages.success(request, 'Course deleted successfully!')
    return redirect('dashboard:course_list')

# -----------------------------
# Assignment Views
# -----------------------------
@login_required
def assignment_list(request):
    assignments = Assignment.objects.select_related('course', 'teacher').all()
    return render(request, 'dashboard/assignment_list.html', {'assignments': assignments})

@login_required
def assignment_create(request):
    if request.method == 'POST':
        form = AssignmentForm(request.POST, initial={'user': request.user})
        if form.is_valid():
            assignment = form.save(commit=False)
            # For teachers, always set themselves as the teacher
            if request.user.role == 'teacher':
                assignment.teacher = request.user
            assignment.save()
            messages.success(request, 'Assignment created successfully!')

            if request.user.role == 'teacher':
                return redirect('dashboard:teacher_assignments')
            return redirect('dashboard:assignment_list')
    else:
        form = AssignmentForm(initial={'user': request.user})

    return render(request, 'dashboard/assignment_form.html', {
        'form': form,
        'title': 'Create Assignment'
    })

@login_required
def teacher_assignment_create(request):
    if request.method == 'POST':
        form = AssignmentForm(request.POST, initial={'user': request.user})
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.teacher = request.user
            assignment.save()
            messages.success(request, 'Assignment created successfully!')
            return redirect('dashboard:teacher_assignments')
    else:
        form = AssignmentForm(initial={'user': request.user})

    return render(request, 'dashboard/assignment_form.html', {
        'form': form,
        'title': 'Create Assignment'
    })
@login_required
def edit_assignment(request, id=None):
    assignment = get_object_or_404(Assignment, id=id) if id else None

    # Check if teacher owns this assignment
    if id and request.user.role == 'teacher' and assignment.teacher != request.user:
        messages.error(request, "You don't have permission to edit this assignment.")
        return redirect('dashboard:teacher_assignments')

    if request.method == 'POST':
        form = AssignmentForm(request.POST, instance=assignment)
        if form.is_valid():
            assignment = form.save(commit=False)
            # For teachers, always set themselves as the teacher
            if request.user.role == 'teacher':
                assignment.teacher = request.user
            assignment.save()
            form.save_m2m()  # Save many-to-many relationships if any
            messages.success(request, f'Assignment {"updated" if id else "created"} successfully!')

            if request.user.role == 'teacher':
                return redirect('dashboard:teacher_assignments')
            return redirect('dashboard:assignment_list')
    else:
        form = AssignmentForm(instance=assignment)

    return render(request, 'dashboard/assignment_form.html', {
        'form': form,
        'title': 'Edit Assignment' if id else 'Add Assignment'
    })
@login_required
def delete_assignment(request, id):
    assignment = get_object_or_404(Assignment, id=id)
    assignment.delete()
    messages.success(request, 'Assignment deleted successfully!')
    return redirect('dashboard:assignment_list')

@login_required
@user_passes_test(lambda u: u.role == 'teacher')
def teacher_dashboard(request):
    # Get the teacher object for the current user
    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        messages.error(request, "Teacher profile not found.")
        return redirect('login')

    # Get courses taught by this teacher
    courses = Course.objects.filter(teachers=teacher)

    # Get assignments created by this teacher
    assignments = Assignment.objects.filter(teacher=request.user)

    # Get recent submissions for teacher's assignments
    recent_submissions = Submission.objects.filter(
        assignment__teacher=request.user
    ).select_related('student', 'assignment').order_by('-submitted_at')[:5]

    # Calculate statistics - filter by teacher's courses
    course_names = [course.name for course in courses]
    total_students = Student.objects.filter(
        course__in=course_names
    ).distinct().count()

    # Count pending grading for this teacher's assignments
    pending_grading = Submission.objects.filter(
        assignment__teacher=request.user,
        grade__isnull=True
    ).count()

    context = {
        'teacher': teacher,
        'courses': courses,
        'assignments': assignments,
        'recent_submissions': recent_submissions,
        'total_students': total_students,
        'pending_grading': pending_grading,
        'total_assignments': assignments.count(),
        'can_create_courses': True,
    }
    return render(request, 'dashboard/teacher_dashboard.html', context)
@login_required
@user_passes_test(lambda u: u.role == 'teacher')
def teacher_assignments(request):
    # Get assignments created by this teacher
    assignments = Assignment.objects.filter(teacher=request.user)

    context = {
        'assignments': assignments,
    }
    return render(request, 'dashboard/teacher_assignments.html', context)

@login_required
@user_passes_test(lambda u: u.role == 'teacher')
def grade_submission(request, submission_id):
    submission = get_object_or_404(Submission, id=submission_id)

    # Ensure the teacher can only grade submissions for their own assignments
    if submission.assignment.teacher != request.user:
        messages.error(request, "You don't have permission to grade this submission.")
        return redirect('dashboard:teacher_dashboard')

    if request.method == 'POST':
        grade = request.POST.get('grade')
        feedback = request.POST.get('feedback')

        if grade:
            try:
                submission.grade = int(grade)
                submission.feedback = feedback
                submission.save()
                messages.success(request, 'Submission graded successfully!')
                return redirect('dashboard:teacher_assignment_detail', id=submission.assignment.id)
            except ValueError:
                messages.error(request, 'Please enter a valid grade.')

    context = {
        'submission': submission,
    }
    return render(request, 'dashboard/grade_submission.html', context)
@login_required
@user_passes_test(lambda u: u.role == 'teacher')
def teacher_courses(request):
    teacher = get_object_or_404(Teacher, user=request.user)
    courses = Course.objects.filter(teachers=teacher)

    context = {
        'courses': courses,
    }
    return render(request, 'dashboard/teacher_courses.html', context)
@login_required
@user_passes_test(lambda u: u.role == 'teacher')
def teacher_assignment_detail(request, id):
    assignment = get_object_or_404(Assignment, id=id, teacher=request.user)
    submissions = Submission.objects.filter(assignment=assignment).select_related('student')

    context = {
        'assignment': assignment,
        'submissions': submissions,
    }
    return render(request, 'dashboard/teacher_assignment_detail.html', context)
@login_required
@user_passes_test(lambda u: u.role == 'teacher')
def teacher_students(request):
    teacher = get_object_or_404(Teacher, user=request.user)
    courses = Course.objects.filter(teachers=teacher)

    # Get students enrolled in courses taught by this teacher
    students = Student.objects.filter(
        course__in=[course.name for course in courses]
    ).select_related('user')

    context = {
        'students': students,
    }
    return render(request, 'dashboard/teacher_students.html', context)
@csrf_exempt
def get_teachers_by_course(request):
    if request.method == 'GET':
        course_id = request.GET.get('course_id')
        print(f"API called for course_id: {course_id}")

        if course_id:
            try:
                course = Course.objects.get(id=course_id)
                teachers = course.teachers.all()
                teachers_data = [{'id': teacher.user.id, 'name': str(teacher)} for teacher in teachers]
                print(f"Returning teachers: {teachers_data}")
                return JsonResponse(teachers_data, safe=False)
            except Course.DoesNotExist:
                print(f"Course with id {course_id} not found")
                return JsonResponse([], safe=False)
        else:
            print("No course_id provided")

    return JsonResponse([], safe=False)
@login_required
@user_passes_test(lambda u: u.role == 'teacher')
def teacher_course_create(request):
    if request.method == 'POST':
        form = TeacherCourseForm(request.POST)
        if form.is_valid():
            course = form.save()
            # Add the current teacher to the course
            teacher = Teacher.objects.get(user=request.user)
            course.teachers.add(teacher)
            messages.success(request, 'Course created successfully!')
            return redirect('dashboard:teacher_courses')
    else:
        form = TeacherCourseForm()

    return render(request, 'dashboard/teacher_course_form.html', {
        'form': form,
        'title': 'Create Course'
    })

@login_required
@user_passes_test(lambda u: u.role == 'teacher')
def teacher_student_create(request):
    # Get the current teacher (Teacher object, not User object)
    try:
        teacher_obj = Teacher.objects.get(user=request.user)
        print(f"DEBUG: Found teacher object: {teacher_obj}")

        # Check what courses this teacher has
        courses = Course.objects.filter(teachers=teacher_obj)
        print(f"DEBUG: Teacher has {courses.count()} courses: {list(courses)}")

    except Teacher.DoesNotExist:
        messages.error(request, "Teacher profile not found.")
        return redirect('dashboard:teacher_dashboard')

    if request.method == 'POST':
        form = TeacherStudentForm(request.POST, teacher=teacher_obj)
        if form.is_valid():
            student = form.save()
            messages.success(request, 'Student created successfully!')
            return redirect('dashboard:teacher_students')
        else:
            print(f"DEBUG: Form errors: {form.errors}")
    else:
        form = TeacherStudentForm(teacher=teacher_obj)
        print(f"DEBUG: Form course choices: {form.fields['course'].choices}")

    return render(request, 'dashboard/teacher_student_form.html', {
        'form': form,
        'title': 'Add Student'
    })

@login_required
@user_passes_test(lambda u: u.role == 'teacher')
def teacher_course_detail(request, course_id):
    # Get the course and ensure the current teacher teaches it
    course = get_object_or_404(Course.objects.prefetch_related('materials'), id=course_id)  # Add prefetch_related
    teacher = get_object_or_404(Teacher, user=request.user)

    # Check if the current teacher teaches this course
    if teacher not in course.teachers.all():
        messages.error(request, "You don't have permission to view this course.")
        return redirect('dashboard:teacher_courses')

    # Get students enrolled in this course
    students = Student.objects.filter(course=course.name).select_related('user')

    # Get assignments for this course
    assignments = Assignment.objects.filter(course=course, teacher=request.user)

    # Get assignment count and submission stats
    assignment_stats = []
    for assignment in assignments:
        submissions = Submission.objects.filter(assignment=assignment)
        graded_count = submissions.filter(grade__isnull=False).count()
        pending_count = submissions.filter(grade__isnull=True).count()

        assignment_stats.append({
            'assignment': assignment,
            'total_submissions': submissions.count(),
            'graded_count': graded_count,
            'pending_count': pending_count
        })

    context = {
        'course': course,
        'students': students,
        'assignments': assignments,
        'assignment_stats': assignment_stats,
        'teacher': teacher,
    }

    return render(request, 'dashboard/teacher_course_detail.html', context)
@login_required
@user_passes_test(lambda u: u.role == 'teacher')
def remove_student_from_course(request, course_id, student_id):
    if request.method == 'POST':
        course = get_object_or_404(Course, id=course_id)
        student = get_object_or_404(Student, id=student_id)

        # Check if the current teacher teaches this course
        teacher = get_object_or_404(Teacher, user=request.user)
        if teacher not in course.teachers.all():
            messages.error(request, "You don't have permission to modify this course.")
            return redirect('dashboard:teacher_courses')

        # Since course is CharField, we need to handle removal differently
        # We'll set the student's course to empty string
        if student.course == course.name:
            student.course = ""
            student.save()
            messages.success(request, f'Student {student.user.username} removed from the course.')
        else:
            messages.warning(request, 'Student is not enrolled in this course.')

        return redirect('dashboard:teacher_course_detail', course_id=course_id)

    # If not POST, redirect back
    return redirect('dashboard:teacher_course_detail', course_id=course_id)

# -----------------------------
# Settings Views
# -----------------------------
@user_passes_test(is_admin)
def admin_settings(request):
    context = {
        'title': 'Admin Settings',
        'settings_options': [
            {'name': 'Profile', 'icon': 'fas fa-user', 'description': 'Update your profile information', 'url': 'dashboard:profile_settings'},
            {'name': 'Appearance', 'icon': 'fas fa-palette', 'description': 'Customize theme', 'url': 'dashboard:appearance_settings'},
            {'name': 'Security', 'icon': 'fas fa-shield-alt', 'description': 'Security settings', 'url': 'dashboard:security_settings'},
        ]
    }
    return render(request, 'dashboard/admin_settings.html', context)

@user_passes_test(is_admin)
def profile_settings(request):
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)

        # Handle profile photo upload (you'll need to add this field to your User model)
        # if 'profile_photo' in request.FILES:
        #     user.profile_photo = request.FILES['profile_photo']

        user.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('dashboard:profile_settings')

    return render(request, 'dashboard/profile_settings.html', {
        'title': 'Profile Settings'
    })

@user_passes_test(is_admin)
def appearance_settings(request):
    if request.method == 'POST':
        theme = request.POST.get('theme', 'light')

        # Save to user's profile or session
        try:
            profile, created = UserProfile.objects.get_or_create(user=request.user)
            profile.theme_preference = theme
            profile.save()
            messages.success(request, 'Appearance settings saved!')
        except:
            # Fallback to session if no profile model
            request.session['theme'] = theme
            messages.success(request, 'Appearance settings saved!')

        return redirect('dashboard:appearance_settings')

    # Get current theme preference
    current_theme = 'light'  # default
    try:
        profile = UserProfile.objects.get(user=request.user)
        current_theme = profile.theme_preference
    except:
        current_theme = request.session.get('theme', 'light')

    return render(request, 'dashboard/appearance_settings.html', {
        'title': 'Appearance Settings',
        'themes': ['light', 'dark', 'auto'],
        'current_theme': current_theme
    })

@user_passes_test(is_admin)
def security_settings(request):
    if request.method == 'POST':
        # Handle password change
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')

        if current_password and new_password and 'password_change' in request.POST:
            if request.user.check_password(current_password):
                request.user.set_password(new_password)
                request.user.save()
                messages.success(request, 'Password updated successfully!')
            else:
                messages.error(request, 'Current password is incorrect')

        # Handle 2FA enable
        elif 'enable_2fa' in request.POST:
            # Generate a secret key
            secret = pyotp.random_base32()
            profile, created = UserProfile.objects.get_or_create(user=request.user)
            profile.two_factor_secret = secret
            profile.save()
            messages.info(request, 'Please scan the QR code with your authenticator app')

        # Handle 2FA verification
        elif 'verify_2fa' in request.POST:
            verification_code = request.POST.get('verification_code')
            profile = UserProfile.objects.get(user=request.user)

            totp = pyotp.TOTP(profile.two_factor_secret)
            if totp.verify(verification_code):
                profile.two_factor_enabled = True
                profile.save()
                messages.success(request, 'Two-factor authentication enabled successfully!')
            else:
                messages.error(request, 'Invalid verification code')

        # Handle 2FA disable
        elif 'disable_2fa' in request.POST:
            profile = UserProfile.objects.get(user=request.user)
            profile.two_factor_enabled = False
            profile.two_factor_secret = None
            profile.save()
            messages.success(request, 'Two-factor authentication disabled')

        return redirect('dashboard:security_settings')

    # Get active sessions (simplified implementation)
    active_sessions = 1  # You would implement proper session tracking

    # Check if user has 2FA enabled
    try:
        profile = UserProfile.objects.get(user=request.user)
        two_factor_enabled = profile.two_factor_enabled
        has_secret = bool(profile.two_factor_secret)
    except UserProfile.DoesNotExist:
        two_factor_enabled = False
        has_secret = False

    return render(request, 'dashboard/security_settings.html', {
        'title': 'Security Settings',
        'active_sessions': active_sessions,
        'two_factor_enabled': two_factor_enabled,
        'has_secret': has_secret
    })

def generate_qr_code(request):
    """Generate QR code for 2FA setup"""
    profile = UserProfile.objects.get(user=request.user)
    totp = pyotp.TOTP(profile.two_factor_secret)
    provisioning_uri = totp.provisioning_uri(
        name=request.user.email,
        issuer_name="Brain Box"
    )

    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(provisioning_uri)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)

    return HttpResponse(buffer.getvalue(), content_type='image/png')

# -----------------------------
# Course Material Views
# -----------------------------
@login_required
@user_passes_test(lambda u: u.role == 'teacher')
def teacher_course_materials(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    teacher = get_object_or_404(Teacher, user=request.user)

    # Check if teacher teaches this course
    if teacher not in course.teachers.all():
        messages.error(request, "You don't have permission to view materials for this course.")
        return redirect('dashboard:teacher_courses')

    materials = CourseMaterial.objects.filter(course=course)

    context = {
        'course': course,
        'materials': materials,
    }
    return render(request, 'dashboard/teacher_course_materials.html', context)


@login_required
@user_passes_test(lambda u: u.role == 'teacher')
def add_course_material(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    teacher = get_object_or_404(Teacher, user=request.user)

    # Check if teacher teaches this course
    if teacher not in course.teachers.all():
        messages.error(request, "You don't have permission to add materials to this course.")
        return redirect('dashboard:teacher_courses')

    if request.method == 'POST':
        form = CourseMaterialForm(request.POST, request.FILES)
        if form.is_valid():
            material = form.save(commit=False)
            material.course = course
            material.uploaded_by = request.user
            material.save()
            messages.success(request, 'Course material uploaded successfully!')
            return redirect('dashboard:teacher_course_materials', course_id=course.id)
    else:
        form = CourseMaterialForm()

    context = {
        'course': course,
        'form': form,
        'title': 'Add Course Material'
    }
    return render(request, 'dashboard/add_course_material.html', context)


@login_required
@user_passes_test(lambda u: u.role == 'teacher')
def delete_course_material(request, material_id):
    material = get_object_or_404(CourseMaterial, id=material_id)

    # Check if the current user uploaded this material
    if material.uploaded_by != request.user:
        messages.error(request, "You don't have permission to delete this material.")
        return redirect('dashboard:teacher_courses')

    course_id = material.course.id
    material.delete()
    messages.success(request, 'Course material deleted successfully!')
    return redirect('dashboard:teacher_course_materials', course_id=course_id)


@login_required
@user_passes_test(lambda u: u.role == 'student')
def student_course_materials(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    student = get_object_or_404(Student, user=request.user)

    # Check if student is enrolled in this course
    if student.course != course.name:
        messages.error(request, "You are not enrolled in this course.")
        return redirect('student_home')

    materials = CourseMaterial.objects.filter(course=course)

    context = {
        'course': course,
        'materials': materials,
    }
    return render(request, 'dashboard/student_course_materials.html', context)
