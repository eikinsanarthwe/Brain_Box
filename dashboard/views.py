from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import logout, get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Teacher, Student, Course, Assignment, Submission
from .forms import TeacherForm, StudentForm, CourseForm, AssignmentForm, AdminCreationForm, AdminChangeForm,TeacherStudentForm,TeacherCourseForm
from django.db.models import Count, Avg
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

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
        'can_create_courses': True,  # Add this flag to control UI elements
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
    course = get_object_or_404(Course, id=course_id)
    teacher = get_object_or_404(Teacher, user=request.user)
    
    # Check if the current teacher teaches this course
    if teacher not in course.teachers.all():
        messages.error(request, "You don't have permission to view this course.")
        return redirect('dashboard:teacher_courses')
    
    # Get students enrolled in this course (using course name since it's CharField)
    students = Student.objects.filter(course=course.name).select_related('user')
    
    # Get assignments for this course created by this teacher
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