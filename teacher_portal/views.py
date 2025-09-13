from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.db.models import Count, Q
from django.core.exceptions import ValidationError, PermissionDenied
from django.utils import timezone
from django.contrib import messages
from django.db import transaction
from datetime import date


@login_required
def role_redirect(request):
    user = request.user
    if user.role == 'admin':
        return redirect('dashboard:dashboard')  # admin dashboard
    elif user.role == 'teacher':
        return redirect('teacher_portal:dashboard')  # teacher dashboard
    elif user.role == 'student':
        return redirect('student_portal:dashboard')  # if you have one
    else:
        return redirect('login')  # fallback



from .models import (
    Course,
    Assignment,
    Student,
    Grade,
    Submission,
    ActivityLog,  # Add this import
    Notification  # Add this import
)

from .models import Course, Assignment, Student, Grade, Submission
from .forms import StudentForm, CourseForm, AssignmentForm, GradeSubmissionForm

User = get_user_model()


# ===================== DASHBOARD =====================

@login_required
def teacher_dashboard(request):
    return render(request, 'teacher_portal/dashboard.html')

@login_required
def dashboard(request):
    if not request.user.is_staff:
        return HttpResponseForbidden("Only teachers can access the dashboard")

    # Get teacher's courses (limited to 5 most recent)
    teacher_courses = Course.objects.filter(
        teacher=request.user
    ).order_by('-created_at')[:5]

    # Get statistics
    course_count = Course.objects.filter(teacher=request.user).count()
    student_count = Student.objects.filter(
        enrolled_courses__teacher=request.user
    ).distinct().count()

    total_assignments = Assignment.objects.filter(
        course__teacher=request.user
    ).count()

    assignments_to_grade = Submission.objects.filter(
        assignment__course__teacher=request.user,
        is_graded=False
    ).count()

    # Get upcoming deadlines (next 7 days)
    upcoming_deadlines = Assignment.objects.filter(
        course__teacher=request.user,
        due_date__gte=timezone.now(),
        due_date__lte=timezone.now() + timezone.timedelta(days=7)
    ).order_by('due_date')[:5]

    # Annotate with days remaining
    for assignment in upcoming_deadlines:
        assignment.days_remaining = (assignment.due_date - timezone.now()).days

    # Get recent activities (most recent 10)
    recent_activities = ActivityLog.objects.filter(
        user=request.user
    ).order_by('-timestamp')[:10]

    # Get unread notification count
    notification_count = Notification.objects.filter(
        user=request.user,
        read=False
    ).count()

    context = {
        'teacher_courses': teacher_courses,
        'course_count': course_count,
        'student_count': student_count,
        'total_assignments': total_assignments,
        'assignments_to_grade': assignments_to_grade,
        'upcoming_deadlines': upcoming_deadlines,
        'recent_activities': recent_activities,
        'notification_count': notification_count,
    }

    return render(request, 'teacher_portal/dashboard.html', context)


# ===================== COURSES =====================
def course_list(request):
    courses = Course.objects.all()
    return render(request, 'teacher_portal/course_list.html', {'courses': courses})


@login_required
def course_create(request):
    if not request.user.is_staff:
        return HttpResponseForbidden("Only teachers can create courses.")

    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            course.teacher = request.user
            try:
                course.save()
                return redirect('course_list')
            except ValidationError as e:
                for field, errors in e.message_dict.items():
                    for error in errors:
                        form.add_error(field, error)
    else:
        form = CourseForm()

    return render(request, 'teacher_portal/course_form.html', {
        'form': form,
        'title': 'Add Course'
    })


def course_edit(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            updated_course = form.save(commit=False)
            if not updated_course.teacher_id:
                updated_course.teacher = request.user

            if updated_course.code == course.code:
                updated_course.save()
                return redirect('course_detail', course_id=updated_course.id)

            if Course.objects.filter(code=updated_course.code).exclude(id=course_id).exists():
                form.add_error('code', 'A course with this code already exists.')
                return render(request, 'teacher_portal/course_form.html', {
                    'form': form,
                    'title': 'Edit Course'
                })

            updated_course.save()
            return redirect('course_detail', course_id=updated_course.id)
    else:
        form = CourseForm(instance=course)
    return render(request, 'teacher_portal/course_form.html', {
        'form': form,
        'title': 'Edit Course'
    })


def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    assignments = course.assignments.all()
    students = course.students.annotate(
        submission_count=Count('submissions', filter=Q(submissions__assignment__course=course)),
        graded_count=Count('submissions', filter=Q(submissions__assignment__course=course, submissions__grade__isnull=False))
    )

    return render(request, 'teacher_portal/course_detail.html', {
        'course': course,
        'assignments': assignments,
        'students': students
    })


def course_delete(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if request.method == 'POST':
        course.delete()
        return redirect('course_list')
    return render(request, 'teacher_portal/course_confirm_delete.html', {'course': course})


# ===================== ASSIGNMENTS =====================
@login_required
def assignment_list(request):
    if not request.user.is_authenticated:
        return redirect(f'/accounts/login/?next={request.path}')

    if not request.user.is_staff:
        raise PermissionDenied

    assignments = Assignment.objects.filter(
        course__teacher=request.user
    ).select_related('course').order_by('-due_date')

    assignments_with_days = []
    for assignment in assignments:
        days_remaining = (assignment.due_date - timezone.now()).days if assignment.due_date else None
        assignments_with_days.append({
            'assignment': assignment,
            'days_remaining': days_remaining
        })

    return render(request, 'teacher_portal/assignment_list.html', {
        'assignments_with_days': assignments_with_days,
        'now': timezone.now()
    })


def assignment_add(request):
    if request.method == 'POST':
        form = AssignmentForm(request.POST, request.FILES)
        if form.is_valid():
            assignment = form.save()
            return redirect('assignment_list')
    else:
        form = AssignmentForm()

    return render(request, 'teacher_portal/assignment_form.html', {
        'form': form,
        'title': 'Create Assignment'
    })



def assignment_detail(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    submissions = Submission.objects.filter(assignment=assignment)

    # Calculate days remaining
    days_remaining = None
    days_remaining_abs = None
    if assignment.due_date:
        delta = assignment.due_date.date() - date.today()
        days_remaining = delta.days
        days_remaining_abs = abs(delta.days)

    context = {
        "assignment": assignment,
        "submissions": submissions,
        "days_remaining": days_remaining,
        "days_remaining_abs": days_remaining_abs,
        "total_students": assignment.course.students.count(),
        "submitted_count": submissions.count(),
        "graded_count": submissions.filter(is_graded=True).count(),
        "submission_status": f"{submissions.count()} submitted",
        "grading_status": f"{submissions.filter(is_graded=True).count()}",
        "status_class": "bg-success" if submissions.count() > 0 else "bg-danger",
    }
    return render(request, "teacher_portal/assignment_detail.html", context)


@login_required
def assignment_edit(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id, course__teacher=request.user)

    if request.method == 'POST':
        form = AssignmentForm(request.POST, request.FILES, instance=assignment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Assignment updated successfully!')
            return redirect('assignment_detail', assignment_id=assignment.id)
    else:
        form = AssignmentForm(instance=assignment)

    return render(request, 'teacher_portal/assignment_form.html', {
        'form': form,
        'title': 'Edit Assignment',
        'assignment': assignment
    })

@login_required
def assignment_delete(request, assignment_id):
    assignment = get_object_or_404(
        Assignment,
        id=assignment_id,
        course__teacher=request.user  # ensure only the teacher who owns the course can delete
    )

    if request.method == 'POST':
        assignment.delete()
        messages.success(request, 'Assignment deleted successfully!')
        return redirect('assignment_list')

    return render(request, 'teacher_portal/assignment_confirm_delete.html', {
        'assignment': assignment,
        'title': 'Delete Assignment'
    })

def grade_submission(request, submission_id):
    submission = get_object_or_404(Submission, id=submission_id)
    if request.method == 'POST':
        form = GradeSubmissionForm(request.POST, instance=submission)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.is_graded = True
            submission.save()
            return redirect('assignment_detail', assignment_id=submission.assignment.id)
    else:
        form = GradeSubmissionForm(instance=submission)

    return render(request, 'teacher_portal/grade_submission.html', {
        'form': form,
        'submission': submission
    })
def grade_assignment(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    submissions = Submission.objects.filter(assignment=assignment)

    if request.method == "POST":
        for submission in submissions:
            grade_value = request.POST.get(f"grade_{submission.id}")
            if grade_value is not None and grade_value != "":
                submission.grade = grade_value
                submission.save()
        messages.success(request, f"Grades updated for {assignment.title}.")
        return redirect("assignment_list")

    return render(request, "teacher_portal/grade_assignment.html", {
        "assignment": assignment,
        "submissions": submissions,
    })



# ===================== STUDENTS =====================

def student_list(request):
    students = (
        Student.objects
        .select_related("user")
        .annotate(
            course_count=Count("enrolled_courses", distinct=True),
            assignment_count=Count("user__student_profile__submissions", distinct=True),
            graded_count=Count(
                "user__student_profile__submissions",
                filter=Q(user__student_profile__submissions__grade__isnull=False),
                distinct=True
            )
        )
    )

    return render(request, "teacher_portal/student_list.html", {
        "students": students,
        "can_manage": request.user.is_staff
    })

def student_manage_courses(request, student_id):
    # Get the student (linked to User)
    student = get_object_or_404(Student, id=student_id)

    # All courses
    all_courses = Course.objects.all()

    # Exclude already enrolled ones
    available_courses = all_courses.exclude(id__in=student.courses.values_list('id', flat=True))

    context = {
        "student": student,
        "available_courses": available_courses,
    }
    return render(request, "teacher_portal/student_detail.html", context)

def student_detail(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    enrolled_courses = student.enrolled_courses.all()
    available_courses = Course.objects.exclude(id__in=enrolled_courses)

    return render(request, "teacher_portal/student_detail.html", {
        "student": student,
        "enrolled_courses": enrolled_courses,
        "available_courses": available_courses,
    })




from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Student, Course

def add_student_to_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    if request.method == "POST":
        student_id = request.POST.get("student")  # match template select name
        student = get_object_or_404(Student, id=student_id)

        if course.students.filter(id=student.id).exists():
            messages.error(request, f"{student.user.get_full_name()} is already enrolled in {course.title}.")
        else:
            course.students.add(student)
            messages.success(request, f"Added {student.user.get_full_name()} to {course.title}.")

        return redirect("course_detail", course_id=course.id)

    # GET → show only students not already in this course
    students = Student.objects.exclude(id__in=course.students.values_list("id", flat=True))

    return render(request, "student_add.html", {
        "course": course,
        "students": students,
    })
def add_student_to_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    if request.method == "POST":
        student_id = request.POST.get("student_id")
        if not student_id:
            messages.error(request, "Please select a student.")
            return redirect("add_student_to_course", course_id=course.id)

        student = get_object_or_404(Student, id=student_id)

        if course.students.filter(id=student.id).exists():
            messages.error(request, f"{student.user.get_full_name()} is already enrolled.")
        else:
            course.students.add(student)
            messages.success(request, f"Added {student.user.get_full_name()} to course.")

        return redirect("course_detail", course_id=course.id)

    # Get all students not already in this course
    enrolled_student_ids = course.students.values_list('id', flat=True)
    available_students = Student.objects.exclude(id__in=enrolled_student_ids).select_related('user')

    # Debug output
    print("Available students:", available_students)  # Check console output

    return render(request, "teacher_portal/student_add.html", {
        "course": course,
        "students": available_students,
    })
def add_course_to_student(request, student_id):
    student = get_object_or_404(Student, id=student_id)

    if request.method == "POST":
        course_id = request.POST.get("course_id")
        if not course_id:
            messages.error(request, "Please select a course.")
            return redirect("add_course_to_student", student_id=student.id)

        course = get_object_or_404(Course, id=course_id)

        if student.enrolled_courses.filter(id=course.id).exists():
            messages.error(request, f"{student.user.get_full_name()} is already enrolled in {course.title}.")
        else:
            # Add both ways to maintain consistency
            student.enrolled_courses.add(course)
            course.students.add(student)
            messages.success(request, f"Added {course.title} to {student.user.get_full_name()}.")

        return redirect("student_detail", student_id=student.id)

    # Get courses not already enrolled by the student
    enrolled_course_ids = student.enrolled_courses.values_list('id', flat=True)
    courses = Course.objects.exclude(id__in=enrolled_course_ids)

    return render(request, "teacher_portal/course_add.html", {
        "student": student,
        "courses": courses,
    })

def remove_student_from_course(request, student_id, course_id):
    student = get_object_or_404(Student, id=student_id)
    course = get_object_or_404(Course, id=course_id)

    if course in student.enrolled_courses.all():
        student.enrolled_courses.remove(course)
        messages.success(request, f"Removed {student.user.get_full_name()} from {course.title}.")
    else:
        messages.error(request, f"{student.user.get_full_name()} is not enrolled in {course.title}.")

    # Redirect back to student detail (not student_manage_courses)
    return redirect("student_detail", student_id=student.id)

def student_edit(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    if request.method == 'POST':
        form = StudentForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            return redirect('student_detail', student_id=student.id)
    else:
        form = StudentForm(instance=student)
    return render(request, 'teacher_portal/student_form.html', {'form': form, 'student': student})


def student_delete(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    if request.method == 'POST':
        student.delete()
        return redirect('student_list')
    return render(request, 'teacher_portal/student_confirm_delete.html', {'student': student})


# teacher_portal/views.py
def student_create(request):
    if request.method == "POST":
        form = StudentForm(request.POST)
        if form.is_valid():
            # Create User first
            user = User.objects.create_user(
                username=form.cleaned_data["username"],
                email=form.cleaned_data["email"],
                first_name=form.cleaned_data["first_name"],
                last_name=form.cleaned_data["last_name"],
                password=form.cleaned_data["password"],
            )
            # Then create Student profile
            Student.objects.create(user=user)
            messages.success(request, "Student created successfully!")
            return redirect("student_list")
    else:
        form = StudentForm()
    return render(request, "teacher_portal/student_form.html", {
        "form": form,
        "is_edit": False,
    })
# ===================== GRADES =====================
def gradebook(request):
    grades = Grade.objects.all()
    return render(request, 'teacher_portal/gradebook.html', {'grades': grades})


# ===================== SETTINGS =====================
def teacher_settings(request):
    return render(request, 'teacher_portal/teacher_settings.html')


@login_required
def profile(request):
    return render(request, 'teacher_portal/profile.html')
