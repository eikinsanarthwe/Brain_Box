from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import logout, get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Teacher, Student, Assignment, Course
from .forms import TeacherForm, StudentForm, CourseForm, AssignmentForm, AdminCreationForm, AdminChangeForm

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
    context = {
        'teacher_count': Teacher.objects.count(),
        'student_count': Student.objects.count(),
        'course_count': Course.objects.count(),
        'admin_count': User.objects.filter(role='admin').count(),
    }
    return render(request, 'dashboard/index.html', context)

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
    return edit_assignment(request)

@login_required
def edit_assignment(request, id=None):
    assignment = get_object_or_404(Assignment, id=id) if id else None
    if request.method == 'POST':
        form = AssignmentForm(request.POST, instance=assignment)
        if form.is_valid():
            assignment = form.save()
            messages.success(request, f'Assignment {"updated" if id else "created"} successfully!')
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
