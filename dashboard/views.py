from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import logout, get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import models
from django.db.models import Count, Avg
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import render_to_string
from datetime import datetime, timedelta
import json
import pyotp
import qrcode
import io
import base64
import zipfile
from io import BytesIO
import os
from django.utils import timezone

from .models import Teacher, Student, Course, Assignment, Submission, CourseMaterial, UserProfile, Message, CourseModule, StudentProgress,MaterialDownload
from django.contrib.auth import update_session_auth_hash
from .models import Teacher, Student, Course, Assignment, Submission, CourseMaterial, UserProfile, Message, CourseModule, StudentProgress
from accounts.models import CustomUser
from .forms import (
    TeacherForm, StudentForm, CourseForm, AssignmentForm,
    AdminCreationForm, AdminChangeForm, TeacherStudentForm,
    TeacherCourseForm, CourseMaterialForm, MessageForm, ReplyForm,
    ProfileSettingsForm, CourseModuleForm, StudentProgressForm
)

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
    elif hasattr(request.user, 'student'):
        return redirect('dashboard:student_dashboard')
    else:
        return redirect('login')

# -------------------------------
# Student Dashboard Views
# -------------------------------
@login_required
def student_dashboard(request):
    if not hasattr(request.user, 'student'):
        return redirect('dashboard')

    student = get_object_or_404(Student, user=request.user)

    # Get enrolled courses
    courses = student.courses.all()

    # Get assignments (both ways depending on your model relationship)
    try:
        assignments = Assignment.objects.filter(course__in=courses, status='published').order_by('due_date')
    except:
        assignments = Assignment.objects.filter(students=student, status='published').order_by('due_date')

    # Get upcoming assignments (due in next 7 days)
    from django.utils import timezone
    from datetime import timedelta
    next_week = timezone.now() + timedelta(days=7)
    upcoming_assignments = assignments.filter(due_date__gte=timezone.now(), due_date__lte=next_week)

    # Get message counts
    unread_messages_count = Message.objects.filter(recipient=request.user, is_read=False).count()
    total_messages_count = Message.objects.filter(recipient=request.user).count()

    # Get recent submissions
    recent_submissions = Submission.objects.filter(student=student).order_by('-submitted_at')[:3]

    # Get course statistics
    total_courses = courses.count()
    submitted_assignments_count = Submission.objects.filter(student=student).count()
    graded_assignments_count = Submission.objects.filter(student=student, grade__isnull=False).count()

    context = {
        'student': student,
        'courses': courses,
        'assignments': assignments,
        'upcoming_assignments': upcoming_assignments,
        'unread_messages_count': unread_messages_count,
        'total_messages_count': total_messages_count,
        'recent_submissions': recent_submissions,
        'total_courses': total_courses,
        'submitted_assignments_count': submitted_assignments_count,
        'graded_assignments_count': graded_assignments_count,
    }
    return render(request, 'dashboard/student_dashboard.html', context)

@login_required
def student_courses(request):
    if not hasattr(request.user, 'student'):
        return redirect('dashboard')

    student = get_object_or_404(Student, user=request.user)
    courses = student.courses.all().prefetch_related('teachers')

    context = {
        'student': student,
        'courses': courses,
    }
    return render(request, 'dashboard/student_my_courses.html', context)
@login_required
def student_course_detail(request, course_id):
    if not hasattr(request.user, 'student'):
        return redirect('dashboard')

    student = get_object_or_404(Student, user=request.user)
    course = get_object_or_404(student.courses, id=course_id)
    assignments = Assignment.objects.filter(course=course, students=student)
    materials = CourseMaterial.objects.filter(course=course).order_by('-uploaded_at')[:5]

    # Get progress for this course
    try:
        progress = StudentProgress.objects.get(student=student, course=course)
    except StudentProgress.DoesNotExist:
        progress = None

    # FIX: Remove the is_required filter - count ALL materials
    total_materials = CourseMaterial.objects.filter(course=course).count()

    # FIX: Count downloads for ALL materials (remove is_required filter)
    downloaded_count = MaterialDownload.objects.filter(
        student=student,
        material__course=course
    ).count()

    progress_percentage = 0
    if total_materials > 0:
        progress_percentage = int((downloaded_count / total_materials) * 100)

    context = {
        'course': course,
        'assignments': assignments,
        'materials': materials,
        'progress': progress,
        'downloaded_count': downloaded_count,
        'total_materials': total_materials,
        'progress_percentage': progress_percentage,
    }
    return render(request, 'dashboard/student_course_detail.html', context)

@login_required
def student_assignments(request):
    """View all assignments for a student"""
    if not hasattr(request.user, 'student'):
        return redirect('dashboard')

    student = get_object_or_404(Student, user=request.user)

    # Get all published assignments for student's courses
    assignments_list = []
    assignments = Assignment.objects.filter(
        course__in=student.courses.all(),
        status='published'
    ).prefetch_related('submission_set').order_by('-due_date')

    for assignment in assignments:
        submission = assignment.submission_set.filter(student=student).first()
        is_overdue = timezone.now() > assignment.due_date and not submission

        assignments_list.append({
            'assignment': assignment,
            'submission': submission,
            'is_overdue': is_overdue
        })

    # Calculate counts
    pending_count = len([a for a in assignments_list if not a['submission'] and not a['is_overdue']])
    submitted_count = len([a for a in assignments_list if a['submission'] and not a['submission'].grade])
    graded_count = len([a for a in assignments_list if a['submission'] and a['submission'].grade])

    context = {
        'assignments': assignments_list,
        'submitted_count': submitted_count,
        'pending_count': pending_count,
        'graded_count': graded_count,
        'current_time': timezone.now(),
    }
    return render(request, 'dashboard/student_assignments.html', context)

@login_required
def student_assignment_detail(request, assignment_id):
    if not hasattr(request.user, 'student'):
        return redirect('dashboard')

    student = get_object_or_404(Student, user=request.user)
    assignment = get_object_or_404(Assignment, id=assignment_id)

    try:
        submission = Submission.objects.get(student=student, assignment=assignment)
    except Submission.DoesNotExist:
        submission = None

    # Add this line to check if assignment is overdue
    assignment.is_past_due = timezone.now() > assignment.due_date

    context = {
        'assignment': assignment,
        'submission': submission,
    }
    return render(request, 'dashboard/student_assignment_detail.html', context)

@login_required
def student_submit_assignment(request, assignment_id):
    """Submit or resubmit an assignment"""
    if not hasattr(request.user, 'student'):
        return redirect('dashboard')

    assignment = get_object_or_404(Assignment, id=assignment_id, status='published')
    student = get_object_or_404(Student, user=request.user)

    if assignment.course not in student.courses.all():
        messages.error(request, "You are not enrolled in this course.")
        return redirect('dashboard:student_assignments')

    if timezone.now() > assignment.due_date:
        messages.warning(request, "This assignment is past due. You can still submit, but it will be marked as late.")

    existing_submission = Submission.objects.filter(
        assignment=assignment,
        student=student
    ).first()

    if request.method == 'POST':
        submitted_file = request.FILES.get('submitted_file')
        comments = request.POST.get('comments', '')

        if not submitted_file:
            messages.error(request, "Please select a file to upload.")
            return redirect('dashboard:student_assignment_submit', assignment_id=assignment_id)

        if submitted_file.size > 50 * 1024 * 1024:
            messages.error(request, "File size exceeds 50MB limit.")
            return redirect('dashboard:student_assignment_submit', assignment_id=assignment_id)

        allowed_extensions = ['.pdf', '.doc', '.docx', '.txt', '.mp4', '.mp3', '.wav', '.avi', '.mov', '.ppt', '.pptx']
        file_ext = os.path.splitext(submitted_file.name)[1].lower()
        if file_ext not in allowed_extensions:
            messages.error(request, f"File type {file_ext} is not allowed. Please upload a supported file type.")
            return redirect('dashboard:student_assignment_submit', assignment_id=assignment_id)

        if existing_submission:
            existing_submission.submitted_file = submitted_file
            existing_submission.comments = comments
            existing_submission.submitted_at = timezone.now()
            existing_submission.save()
            messages.success(request, "Submission updated successfully!")
        else:
            submission = Submission(
                assignment=assignment,
                student=student,
                submitted_file=submitted_file,
                comments=comments
            )
            submission.save()
            messages.success(request, "Assignment submitted successfully!")

        return redirect('dashboard:student_assignments')

    time_remaining = None
    if assignment.due_date > timezone.now():
        delta = assignment.due_date - timezone.now()
        days = delta.days
        hours = delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60

        if days > 0:
            time_remaining = f"{days} days, {hours} hours"
        elif hours > 0:
            time_remaining = f"{hours} hours, {minutes} minutes"
        else:
            time_remaining = f"{minutes} minutes"

    context = {
        'assignment': assignment,
        'existing_submission': existing_submission,
        'time_remaining': time_remaining,
    }
    return render(request, 'dashboard/student_assignment_submit.html', context)

@login_required
def student_assignment_submit(request, assignment_id):
    """Alternative submission view for URL compatibility"""
    return student_submit_assignment(request, assignment_id)

# Student Additional Views
@login_required
def student_progress(request):
    if not hasattr(request.user, 'student'):
        return redirect('dashboard')

    student = get_object_or_404(Student, user=request.user)
    submissions = Submission.objects.filter(student=student, grade__isnull=False)

    context = {
        'student': student,
        'submissions': submissions,
    }
    return render(request, 'dashboard/student_progress.html', context)

#-----------------------------
# Student Messaging Views
#-----------------------------

@login_required
def student_messages(request):
    """Student messages inbox"""
    messages_list = Message.objects.filter(recipient=request.user).order_by('-sent_at')
    unread_count = messages_list.filter(is_read=False).count()

    context = {
        'messages': messages_list,
        'unread_count': unread_count,
        'active_tab': 'inbox'
    }
    return render(request, 'dashboard/student_messages.html', context)

@login_required
def student_sent_messages(request):
    """Student sent messages"""
    sent_messages = Message.objects.filter(sender=request.user).order_by('-sent_at')

    context = {
        'messages': sent_messages,
        'active_tab': 'sent'
    }
    return render(request, 'dashboard/student_messages.html', context)

@login_required
def student_compose_message(request):
    """Compose new message"""
    if request.method == 'POST':
        recipient_username = request.POST.get('recipient')
        subject = request.POST.get('subject')
        body = request.POST.get('body')
        parent_id = request.POST.get('parent_message')

        try:
            recipient = User.objects.get(username=recipient_username)

            # Create message
            message = Message(
                sender=request.user,
                recipient=recipient,
                subject=subject,
                body=body
            )

            # If this is a reply, set parent message
            if parent_id:
                parent_message = Message.objects.get(id=parent_id)
                message.parent_message = parent_message
                # Add "Re: " to subject if not already there
                if not message.subject.startswith('Re: '):
                    message.subject = f"Re: {message.subject}"

            message.save()
            messages.success(request, 'Message sent successfully!')
            return redirect('dashboard:student_messages')

        except User.DoesNotExist:
            messages.error(request, 'Recipient not found!')
        except Exception as e:
            messages.error(request, f'Error sending message: {str(e)}')

    # Pre-fill recipient if provided in URL
    recipient_username = request.GET.get('to', '')
    parent_id = request.GET.get('reply', '')
    parent_message = None

    if parent_id:
        try:
            parent_message = Message.objects.get(id=parent_id)
            # Verify the current user is involved in this conversation
            if parent_message.recipient != request.user and parent_message.sender != request.user:
                parent_message = None
        except Message.DoesNotExist:
            parent_message = None

    context = {
        'recipient_username': recipient_username,
        'parent_message': parent_message,
        'teachers': Teacher.objects.all(),  # For recipient suggestions
        'students': Student.objects.all()   # For recipient suggestions
    }
    return render(request, 'dashboard/student_compose_message.html', context)

@login_required
def student_message_detail(request, message_id):
    """View message details and reply"""
    try:
        message = Message.objects.get(id=message_id)

        # Verify the current user is the recipient or sender
        if message.recipient != request.user and message.sender != request.user:
            messages.error(request, 'You do not have permission to view this message.')
            return redirect('dashboard:student_messages')

        # Mark as read if the current user is the recipient
        if message.recipient == request.user and not message.is_read:
            message.mark_as_read()

        # Get conversation thread
        conversation = get_message_thread(message)

    except Message.DoesNotExist:
        messages.error(request, 'Message not found.')
        return redirect('dashboard:student_messages')

    context = {
        'message': message,
        'conversation': conversation
    }
    return render(request, 'dashboard/student_message_detail.html', context)

@login_required
def student_delete_message(request, message_id):
    """Delete a message"""
    try:
        message = Message.objects.get(id=message_id)

        # Verify the current user is involved in this message
        if message.recipient != request.user and message.sender != request.user:
            messages.error(request, 'You do not have permission to delete this message.')
            return redirect('dashboard:student_messages')

        message.delete()
        messages.success(request, 'Message deleted successfully!')

    except Message.DoesNotExist:
        messages.error(request, 'Message not found.')

    return redirect('dashboard:student_messages')

@login_required
def mark_message_read(request, message_id):
    """Mark message as read (AJAX)"""
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            message = Message.objects.get(id=message_id, recipient=request.user)
            message.mark_as_read()
            return JsonResponse({'status': 'success'})
        except Message.DoesNotExist:
            return JsonResponse({'status': 'error'})
    return JsonResponse({'status': 'error'})

def get_message_thread(message):
    """Get the entire conversation thread for a message"""
    thread = []
    current_message = message

    # Go up to the original message
    while current_message.parent_message:
        current_message = current_message.parent_message

    # Get all replies in order
    thread.append(current_message)
    replies = current_message.replies.all().order_by('sent_at')
    thread.extend(replies)

    return thread

@login_required
def student_aboutus(request):
    if not hasattr(request.user, 'student'):
        return redirect('dashboard')

    return render(request, 'dashboard/student_aboutus.html')

@login_required
def student_settings(request):
    if not hasattr(request.user, 'student'):
        return redirect('dashboard')

    return render(request, 'dashboard/student_settings.html')

@login_required
@user_passes_test(lambda u: u.role == 'student')
def student_profile(request):
    """Student profile overview page"""
    if not hasattr(request.user, 'student'):
        return redirect('dashboard')

    student = get_object_or_404(Student, user=request.user)

    # Get student's courses - make sure this matches your model relationship
    courses = student.courses.all()

    # Alternative ways to get courses if the above doesn't work:
    # courses = Course.objects.filter(students=student)
    # courses = Course.objects.filter(enrolled_students=student)

    # Get recent submissions
    recent_submissions = Submission.objects.filter(student=student).order_by('-submitted_at')[:5]

    # Count statistics
    total_courses = courses.count()
    submitted_assignments = Submission.objects.filter(student=student).count()

    context = {
        'student': student,
        'courses': courses,
        'recent_submissions': recent_submissions,
        'total_courses': total_courses,
        'submitted_assignments': submitted_assignments,
    }
    return render(request, 'dashboard/student_profile.html', context)

@login_required
def course_catalog(request):
    """
    View for browsing available courses
    """
    courses = Course.objects.all()

    context = {
        'courses': courses,
    }
    return render(request, 'dashboard/course_catalog.html', context)

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

# ----------------------------
# Admin Messages Views
# ----------------------------

@login_required
@user_passes_test(lambda u: u.role == 'admin')
def admin_messages(request):
    """Admin messages inbox"""
    messages_list = Message.objects.filter(recipient=request.user).order_by('-sent_at')
    unread_count = messages_list.filter(is_read=False).count()

    context = {
        'messages': messages_list,
        'unread_count': unread_count,
        'active_tab': 'inbox'
    }
    return render(request, 'dashboard/admin_messages.html', context)

@login_required
@user_passes_test(lambda u: u.role == 'admin')
def admin_sent_messages(request):
    """Admin sent messages"""
    sent_messages = Message.objects.filter(sender=request.user).order_by('-sent_at')

    context = {
        'messages': sent_messages,
        'active_tab': 'sent'
    }
    return render(request, 'dashboard/admin_messages.html', context)

@login_required
@user_passes_test(lambda u: u.role == 'admin')
def admin_compose_message(request):
    """Compose new message as admin"""
    # Get all users except the current user - remove the invalid select_related
    all_users = User.objects.exclude(id=request.user.id)

    if request.method == 'POST':
        recipient_username = request.POST.get('recipient')
        subject = request.POST.get('subject')
        body = request.POST.get('body')
        parent_id = request.POST.get('parent_message')

        try:
            recipient = User.objects.get(username=recipient_username)

            # Create message
            message = Message(
                sender=request.user,
                recipient=recipient,
                subject=subject,
                body=body
            )

            # If this is a reply, set parent message
            if parent_id:
                parent_message = Message.objects.get(id=parent_id)
                message.parent_message = parent_message
                # Add "Re: " to subject if not already there
                if not message.subject.startswith('Re: '):
                    message.subject = f"Re: {message.subject}"

            message.save()
            messages.success(request, 'Message sent successfully!')
            return redirect('dashboard:admin_messages')

        except User.DoesNotExist:
            messages.error(request, 'Recipient not found!')
        except Exception as e:
            messages.error(request, f'Error sending message: {str(e)}')

    # Pre-fill recipient if provided in URL
    recipient_username = request.GET.get('to', '')
    parent_id = request.GET.get('reply', '')
    parent_message = None

    if parent_id:
        try:
            parent_message = Message.objects.get(id=parent_id)
            # Verify the current user is involved in this conversation
            if parent_message.recipient != request.user and parent_message.sender != request.user:
                parent_message = None
        except Message.DoesNotExist:
            parent_message = None

    context = {
        'recipient_username': recipient_username,
        'parent_message': parent_message,
        'all_users': all_users,
    }
    return render(request, 'dashboard/admin_compose_message.html', context)

@login_required
@user_passes_test(lambda u: u.role == 'admin')
def admin_message_detail(request, message_id):
    """View message details and reply as admin"""
    try:
        message = Message.objects.get(id=message_id)

        # Verify the current user is the recipient or sender
        if message.recipient != request.user and message.sender != request.user:
            messages.error(request, 'You do not have permission to view this message.')
            return redirect('dashboard:admin_messages')

        # Mark as read if the current user is the recipient
        if message.recipient == request.user and not message.is_read:
            message.mark_as_read()

        # Get conversation thread
        conversation = get_message_thread(message)

    except Message.DoesNotExist:
        messages.error(request, 'Message not found.')
        return redirect('dashboard:admin_messages')

    context = {
        'message': message,
        'conversation': conversation
    }
    return render(request, 'dashboard/admin_message_detail.html', context)

@login_required
@user_passes_test(lambda u: u.role == 'admin')
def admin_delete_message(request, message_id):
    """Delete a message as admin"""
    try:
        message = Message.objects.get(id=message_id)

        # Verify the current user is involved in this message
        if message.recipient != request.user and message.sender != request.user:
            messages.error(request, 'You do not have permission to delete this message.')
            return redirect('dashboard:admin_messages')

        message.delete()
        messages.success(request, 'Message deleted successfully!')

    except Message.DoesNotExist:
        messages.error(request, 'Message not found.')

    return redirect('dashboard:admin_messages')

@login_required
@user_passes_test(lambda u: u.role == 'admin')
def admin_mark_message_read(request, message_id):
    """Mark message as read (AJAX) for admin"""
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            message = Message.objects.get(id=message_id, recipient=request.user)
            message.mark_as_read()
            return JsonResponse({'status': 'success'})
        except Message.DoesNotExist:
            return JsonResponse({'status': 'error'})
    return JsonResponse({'status': 'error'})

# ----------------------------
# Teacher Messages Views
# ----------------------------
@login_required
@user_passes_test(lambda u: u.role == 'teacher')
def teacher_messages(request):
    """Teacher messages inbox"""
    messages_list = Message.objects.filter(recipient=request.user).order_by('-sent_at')
    unread_count = messages_list.filter(is_read=False).count()

    context = {
        'messages': messages_list,
        'unread_count': unread_count,
        'active_tab': 'inbox'
    }
    return render(request, 'dashboard/teacher_messages.html', context)

@login_required
@user_passes_test(lambda u: u.role == 'teacher')
def teacher_sent_messages(request):
    """Teacher sent messages"""
    sent_messages = Message.objects.filter(sender=request.user).order_by('-sent_at')

    context = {
        'messages': sent_messages,
        'active_tab': 'sent'
    }
    return render(request, 'dashboard/teacher_messages.html', context)

@login_required
@user_passes_test(lambda u: u.role == 'teacher')
def teacher_compose_message(request):
    """Compose new message as teacher"""
    # Get all users except the current user
    all_users = User.objects.exclude(id=request.user.id).select_related('teacher', 'student')

    if request.method == 'POST':
        recipient_username = request.POST.get('recipient')
        subject = request.POST.get('subject')
        body = request.POST.get('body')
        parent_id = request.POST.get('parent_message')

        try:
            recipient = User.objects.get(username=recipient_username)

            # Create message
            message = Message(
                sender=request.user,
                recipient=recipient,
                subject=subject,
                body=body
            )

            # If this is a reply, set parent message
            if parent_id:
                parent_message = Message.objects.get(id=parent_id)
                message.parent_message = parent_message
                # Add "Re: " to subject if not already there
                if not message.subject.startswith('Re: '):
                    message.subject = f"Re: {message.subject}"

            message.save()
            messages.success(request, 'Message sent successfully!')
            return redirect('dashboard:teacher_messages')

        except User.DoesNotExist:
            messages.error(request, 'Recipient not found!')
        except Exception as e:
            messages.error(request, f'Error sending message: {str(e)}')

    # Pre-fill recipient if provided in URL
    recipient_username = request.GET.get('to', '')
    parent_id = request.GET.get('reply', '')
    parent_message = None

    if parent_id:
        try:
            parent_message = Message.objects.get(id=parent_id)
            # Verify the current user is involved in this conversation
            if parent_message.recipient != request.user and parent_message.sender != request.user:
                parent_message = None
        except Message.DoesNotExist:
            parent_message = None

    context = {
        'recipient_username': recipient_username,
        'parent_message': parent_message,
        'all_users': all_users,
    }
    return render(request, 'dashboard/teacher_compose_message.html', context)

@login_required
@user_passes_test(lambda u: u.role == 'teacher')
def teacher_message_detail(request, message_id):
    """View message details and reply as teacher"""
    try:
        message = Message.objects.get(id=message_id)

        # Verify the current user is the recipient or sender
        if message.recipient != request.user and message.sender != request.user:
            messages.error(request, 'You do not have permission to view this message.')
            return redirect('dashboard:teacher_messages')

        # Mark as read if the current user is the recipient
        if message.recipient == request.user and not message.is_read:
            message.mark_as_read()

        # Get conversation thread
        conversation = get_message_thread(message)

    except Message.DoesNotExist:
        messages.error(request, 'Message not found.')
        return redirect('dashboard:teacher_messages')

    context = {
        'message': message,
        'conversation': conversation
    }
    return render(request, 'dashboard/teacher_message_detail.html', context)

@login_required
@user_passes_test(lambda u: u.role == 'teacher')
def teacher_delete_message(request, message_id):
    """Delete a message as teacher"""
    try:
        message = Message.objects.get(id=message_id)

        # Verify the current user is involved in this message
        if message.recipient != request.user and message.sender != request.user:
            messages.error(request, 'You do not have permission to delete this message.')
            return redirect('dashboard:teacher_messages')

        message.delete()
        messages.success(request, 'Message deleted successfully!')

    except Message.DoesNotExist:
        messages.error(request, 'Message not found.')

    return redirect('dashboard:teacher_messages')

@login_required
@user_passes_test(lambda u: u.role == 'teacher')
def teacher_mark_message_read(request, message_id):
    """Mark message as read (AJAX) for teacher"""
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            message = Message.objects.get(id=message_id, recipient=request.user)
            message.mark_as_read()
            return JsonResponse({'status': 'success'})
        except Message.DoesNotExist:
            return JsonResponse({'status': 'error'})
    return JsonResponse({'status': 'error'})

# -----------------------------
# Student Management Views
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
            form.save_m2m()

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
@user_passes_test(lambda u: u.role == 'teacher' or u.role == 'admin')
def edit_course(request, id):
    course = get_object_or_404(Course, id=id)
    is_admin = request.user.role == 'admin'

    # Check permissions
    if not is_admin:
        try:
            teacher = get_object_or_404(Teacher, user=request.user)
            if teacher not in course.teachers.all():
                messages.error(request, "You don't have permission to edit this course.")
                return redirect('dashboard:teacher_courses')
        except:
            messages.error(request, "You don't have permission to edit courses.")
            return redirect('dashboard:teacher_courses')

    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES, instance=course)

        if form.is_valid():
            # The image removal is now handled in the form's save method
            course = form.save()
            messages.success(request, f'Course "{course.name}" updated successfully!')

            # Redirect based on user role - FIXED URL NAMES
            if is_admin:
                return redirect('dashboard:course_list')  # Changed from admin_courses
            else:
                return redirect('dashboard:teacher_course_detail', course_id=course.id)
        else:
            messages.error(request, 'Please correct the errors below.')
            print("Form errors:", form.errors)  # Debug
    else:
        form = CourseForm(instance=course)

    return render(request, 'dashboard/edit_course.html', {
        'form': form,
        'course': course
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
    """Create assignment (for admin)"""
    return edit_assignment(request)

@login_required
def edit_assignment(request, id=None):
    assignment = get_object_or_404(Assignment, id=id) if id else None

    if id and request.user.role == 'teacher' and assignment.teacher != request.user:
        messages.error(request, "You don't have permission to edit this assignment.")
        return redirect('dashboard:teacher_assignments')

    if request.method == 'POST':
        form = AssignmentForm(request.POST, instance=assignment)
        if form.is_valid():
            assignment = form.save(commit=False)
            if request.user.role == 'teacher':
                assignment.teacher = request.user
            assignment.save()
            messages.success(request, f'Assignment {"updated" if id else "created"} successfully!')
            form.save_m2m()

            if request.user.role == 'teacher':
                return redirect('dashboard:teacher_assignments')
            return redirect('dashboard:assignment_list')
        else:
            print(f"Form errors: {form.errors}")
    else:
        form = AssignmentForm(instance=assignment)

    return render(request, 'dashboard/assignment_form.html', {
        'form': form,
        'title': 'Edit Assignment' if id else 'Add Assignment'
    })

@login_required
@user_passes_test(lambda u: u.role == 'teacher')
def teacher_assignment_create(request):
    if request.method == 'POST':
        form = AssignmentForm(request.POST)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.teacher = request.user
            assignment.save()
            form.save_m2m()
            messages.success(request, 'Assignment created successfully!')
            return redirect('dashboard:teacher_assignments')
        else:
            print(f"Form errors: {form.errors}")
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = AssignmentForm(initial={'teacher': request.user})

    return render(request, 'dashboard/teacher_assignment_form.html', {
        'form': form,
        'title': 'Create Assignment',
        'action': 'create'
    })

@login_required
def delete_assignment(request, id):
    assignment = get_object_or_404(Assignment, id=id)
    assignment.delete()
    messages.success(request, 'Assignment deleted successfully!')
    return redirect('dashboard:assignment_list')

# -----------------------------
# Teacher Dashboard Views
# -----------------------------
@login_required
@user_passes_test(lambda u: u.role == 'teacher')
def teacher_dashboard(request):
    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        messages.error(request, "Teacher profile not found.")
        return redirect('login')

    try:
        profile = UserProfile.objects.get(user=request.user)
        current_theme = profile.theme_preference
    except UserProfile.DoesNotExist:
        current_theme = 'light'

    courses = Course.objects.filter(teachers=teacher)
    assignments = Assignment.objects.filter(teacher=request.user)
    recent_submissions = Submission.objects.filter(
        assignment__teacher=request.user
    ).select_related('student', 'assignment').order_by('-submitted_at')[:5]

    total_students = Student.objects.filter(courses__in=courses).distinct().count()
    pending_grading = Submission.objects.filter(
        assignment__teacher=request.user,
        grade__isnull=True
    ).count()

    # Add message counts
    unread_messages_count = Message.objects.filter(recipient=request.user, is_read=False).count()
    total_messages_count = Message.objects.filter(recipient=request.user).count()

    context = {
        'teacher': teacher,
        'courses': courses,
        'assignments': assignments,
        'recent_submissions': recent_submissions,
        'total_students': total_students,
        'pending_grading': pending_grading,
        'total_assignments': assignments.count(),
        'can_create_courses': True,
        'current_theme': current_theme,
        'unread_messages_count': unread_messages_count,
        'total_messages_count': total_messages_count,
    }
    return render(request, 'dashboard/teacher_dashboard.html', context)

@login_required
@user_passes_test(lambda u: u.role == 'teacher')
def teacher_assignments(request):
    assignments = Assignment.objects.filter(teacher=request.user)

    context = {
        'assignments': assignments,
    }
    return render(request, 'dashboard/teacher_assignments.html', context)

@login_required
@user_passes_test(lambda u: u.role == 'teacher')
def grade_submission(request, submission_id):
    submission = get_object_or_404(Submission, id=submission_id)

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

    total_students = assignment.students.count() if assignment.students.exists() else 0
    submission_count = submissions.count()
    graded_count = submissions.filter(grade__isnull=False).count()
    pending_count = total_students - submission_count

    context = {
        'assignment': assignment,
        'submissions': submissions,
        'total_students': total_students,
        'submission_count': submission_count,
        'graded_count': graded_count,
        'pending_count': pending_count,
    }
    return render(request, 'dashboard/teacher_assignment_detail.html', context)

@login_required
@user_passes_test(lambda u: u.role == 'teacher')
def teacher_students(request):
    teacher = get_object_or_404(Teacher, user=request.user)
    courses = Course.objects.filter(teachers=teacher)

    students = Student.objects.filter(
        courses__in=courses
    ).select_related('user').prefetch_related('courses').distinct()

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
        form = TeacherCourseForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.save()
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
    try:
        teacher_obj = Teacher.objects.get(user=request.user)
        courses = Course.objects.filter(teachers=teacher_obj)
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

    return render(request, 'dashboard/teacher_student_form.html', {
        'form': form,
        'title': 'Add Student'
    })

@login_required
@user_passes_test(lambda u: u.role == 'teacher')
def teacher_course_detail(request, course_id):
    course = get_object_or_404(Course.objects.prefetch_related('materials'), id=course_id)
    teacher = get_object_or_404(Teacher, user=request.user)

    if teacher not in course.teachers.all():
        messages.error(request, "You don't have permission to view this course.")
        return redirect('dashboard:teacher_courses')

    students = Student.objects.filter(courses=course).select_related('user')
    assignments = Assignment.objects.filter(course=course, teacher=request.user)

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
        teacher = get_object_or_404(Teacher, user=request.user)

        if teacher not in course.teachers.all():
            messages.error(request, "You don't have permission to modify this course.")
            return redirect('dashboard:teacher_courses')

        if course in student.courses.all():
            student.courses.remove(course)
            messages.success(request, f'Student {student.user.username} removed from the course.')
        else:
            messages.warning(request, 'Student is not enrolled in this course.')

        return redirect('dashboard:teacher_course_detail', course_id=course_id)

    return redirect('dashboard:teacher_course_detail', course_id=course_id)

@login_required
@user_passes_test(lambda u: u.role == 'teacher')
def add_student_to_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    teacher = get_object_or_404(Teacher, user=request.user)

    if teacher not in course.teachers.all():
        messages.error(request, "You don't have permission to modify this course.")
        return redirect('dashboard:teacher_courses')

    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        if student_id:
            student = get_object_or_404(Student, id=student_id)

            if course not in student.courses.all():
                student.courses.add(course)
                messages.success(request, f'Student {student.user.username} added to the course.')
            else:
                messages.warning(request, 'Student is already enrolled in this course.')

            return redirect('dashboard:teacher_course_detail', course_id=course_id)

    enrolled_students = Student.objects.filter(courses=course)
    available_students = Student.objects.exclude(id__in=enrolled_students.values('id'))

    context = {
        'course': course,
        'available_students': available_students,
    }
    return render(request, 'dashboard/add_student_to_course.html', context)

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
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ProfileSettingsForm(request.POST, request.FILES, instance=profile, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('dashboard:profile_settings')
    else:
        form = ProfileSettingsForm(instance=profile, user=request.user)

    return render(request, 'dashboard/profile_settings.html', {
        'form': form,
        'title': 'Profile Settings'
    })

@user_passes_test(is_admin)
def appearance_settings(request):
    if request.method == 'POST':
        theme = request.POST.get('theme', 'light')

        try:
            profile, created = UserProfile.objects.get_or_create(user=request.user)
            profile.theme_preference = theme
            profile.save()
            messages.success(request, 'Appearance settings saved!')
        except:
            request.session['theme'] = theme
            messages.success(request, 'Appearance settings saved!')

        return redirect('dashboard:appearance_settings')

    current_theme = 'light'
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
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')

        if current_password and new_password and 'password_change' in request.POST:
            if request.user.check_password(current_password):
                request.user.set_password(new_password)
                request.user.save()
                messages.success(request, 'Password updated successfully!')
            else:
                messages.error(request, 'Current password is incorrect')

        elif 'enable_2fa' in request.POST:
            secret = pyotp.random_base32()
            profile, created = UserProfile.objects.get_or_create(user=request.user)
            profile.two_factor_secret = secret
            profile.save()
            messages.info(request, 'Please scan the QR code with your authenticator app')

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

        elif 'disable_2fa' in request.POST:
            profile = UserProfile.objects.get(user=request.user)
            profile.two_factor_enabled = False
            profile.two_factor_secret = None
            profile.save()
            messages.success(request, 'Two-factor authentication disabled')

        return redirect('dashboard:security_settings')

    active_sessions = 1

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

    if material.uploaded_by != request.user:
        messages.error(request, "You don't have permission to delete this material.")
        return redirect('dashboard:teacher_courses')

    course_id = material.course.id
    material.delete()
    messages.success(request, 'Course material deleted successfully!')
    return redirect('dashboard:teacher_course_materials', course_id=course_id)

# Add this function to your views.py (if not exists)
@login_required
@user_passes_test(lambda u: u.role == 'student')
def student_course_materials(request, course_id):
    """View course materials with progress tracking"""
    if not hasattr(request.user, 'student'):
        return redirect('dashboard')

    student = get_object_or_404(Student, user=request.user)
    course = get_object_or_404(Course, id=course_id)

    if course not in student.courses.all():
        messages.error(request, "You are not enrolled in this course.")
        return redirect('dashboard:student_courses')

    # Get ALL materials for display
    materials = CourseMaterial.objects.filter(course=course)

    # FIX: Count ALL materials for progress calculation
    total_materials = CourseMaterial.objects.filter(course=course).count()

    # Get downloaded materials for this student (ALL materials)
    downloaded_materials = MaterialDownload.objects.filter(
        student=student,
        material__course=course
    )

    downloaded_material_ids = downloaded_materials.values_list('material_id', flat=True)
    downloaded_count = downloaded_materials.count()

    # Calculate progress percentage based on ALL materials
    progress_percentage = 0
    if total_materials > 0:
        progress_percentage = int((downloaded_count / total_materials) * 100)

    # Update progress record
    progress, created = StudentProgress.objects.get_or_create(
        student=student,
        course=course,
        defaults={
            'status': 'not_started',
            'progress_percentage': progress_percentage
        }
    )

    if not created:
        progress.progress_percentage = progress_percentage
        if progress_percentage >= 90:
            progress.status = 'completed'
        elif progress_percentage > 0:
            progress.status = 'in_progress'
        else:
            progress.status = 'not_started'
        progress.save()

    context = {
        'course': course,
        'materials': materials,
        'student': student,
        'progress': progress,
        'downloaded_material_ids': list(downloaded_material_ids),
        'downloaded_count': downloaded_count,
        'total_materials': total_materials,
        'progress_percentage': progress_percentage,
    }
    return render(request, 'dashboard/student_course_materials.html', context)

# -----------------------------
@login_required
def message_list(request):
    messages_list = Message.objects.filter(recipient=request.user).order_by('-sent_at')
    unread_count = messages_list.filter(is_read=False).count()

    if request.GET.get('preview'):
        preview_messages = messages_list[:3]
        html = render_to_string('dashboard/message_preview.html', {
            'preview_messages': preview_messages
        })
        return HttpResponse(html)

    context = {
        'messages': messages_list,
        'unread_count': unread_count,
    }
    return render(request, 'dashboard/message_list.html', context)

@login_required
def message_compose(request, recipient_id=None):
    if request.method == 'POST':
        form = MessageForm(request.POST, sender=request.user)
        print(f"Form is valid: {form.is_valid()}")
        if not form.is_valid():
            print(f"Form errors: {form.errors}")
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")

        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.save()
            print(f"Message saved: {message.id}, From: {message.sender}, To: {message.recipient}")
            messages.success(request, 'Message sent successfully!')
            return redirect('dashboard:message_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        initial = {}
        if recipient_id:
            recipient = get_object_or_404(User, id=recipient_id)
            initial['recipient'] = recipient

        form = MessageForm(initial=initial, sender=request.user)
        print(f"Recipient choices: {form.fields['recipient'].queryset.count()}")

    return render(request, 'dashboard/message_compose.html', {
        'form': form,
        'title': 'Compose Message'
    })

@login_required
def message_detail(request, message_id):
    message = get_object_or_404(Message, id=message_id)

    if message.recipient != request.user and message.sender != request.user:
        messages.error(request, "You don't have permission to view this message.")
        return redirect('dashboard:message_list')

    if message.recipient == request.user and not message.is_read:
        message.mark_as_read()

    if request.method == 'POST':
        form = ReplyForm(request.POST)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.sender = request.user
            reply.recipient = message.sender if request.user == message.recipient else message.recipient
            reply.subject = f"Re: {message.subject}"
            reply.parent_message = message
            reply.save()
            messages.success(request, 'Reply sent successfully!')
            return redirect('dashboard:message_detail', message_id=message.id)
    else:
        form = ReplyForm()

    conversation = Message.objects.filter(
        models.Q(parent_message=message) |
        models.Q(id=message.parent_message.id) if message.parent_message else models.Q(id=message.id)
    ).order_by('sent_at')

    context = {
        'message': message,
        'form': form,
        'conversation': conversation,
    }
    return render(request, 'dashboard/message_detail.html', context)

@login_required
def message_delete(request, message_id):
    message = get_object_or_404(Message, id=message_id)

    if message.recipient != request.user:
        messages.error(request, "You can only delete messages you received.")
        return redirect('dashboard:message_list')

    if request.method == 'POST':
        message.delete()
        messages.success(request, 'Message deleted successfully!')
        return redirect('dashboard:message_list')

    return render(request, 'dashboard/message_confirm_delete.html', {'message': message})

@login_required
def get_unread_count(request):
    if request.user.is_authenticated:
        unread_count = Message.objects.filter(recipient=request.user, is_read=False).count()
        return JsonResponse({'unread_count': unread_count})
    return JsonResponse({'unread_count': 0})

# -----------------------------
# Teacher Settings Views
# -----------------------------
@login_required
@user_passes_test(lambda u: u.role == 'teacher')
def teacher_settings(request):
    context = {
        'title': 'Teacher Settings',
        'settings_options': [
            {'name': 'Profile', 'icon': 'fas fa-user', 'description': 'Update your profile information', 'url': 'dashboard:teacher_profile_settings'},
            {'name': 'Appearance', 'icon': 'fas fa-palette', 'description': 'Customize theme', 'url': 'dashboard:teacher_appearance_settings'},
            {'name': 'Security', 'icon': 'fas fa-shield-alt', 'description': 'Security settings', 'url': 'dashboard:teacher_security_settings'},
        ]
    }
    return render(request, 'dashboard/teacher_settings.html', context)

@login_required
@user_passes_test(lambda u: u.role == 'teacher')
def teacher_profile_settings(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ProfileSettingsForm(request.POST, request.FILES, instance=profile, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('dashboard:teacher_profile_settings')
    else:
        form = ProfileSettingsForm(instance=profile, user=request.user)

    return render(request, 'dashboard/teacher_profile_settings.html', {
        'form': form,
        'title': 'Profile Settings'
    })

@login_required
@user_passes_test(lambda u: u.role == 'teacher')
def teacher_appearance_settings(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        theme = request.POST.get('theme', 'light')
        profile.theme_preference = theme
        profile.save()

        messages.success(request, 'Appearance settings saved!')
        return redirect('dashboard:teacher_appearance_settings')

    return render(request, 'dashboard/teacher_appearance_settings.html', {
        'title': 'Appearance Settings',
        'themes': ['light', 'dark', 'auto'],
        'current_theme': profile.theme_preference
    })

@login_required
@user_passes_test(lambda u: u.role == 'teacher')
def teacher_security_settings(request):
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')

        if current_password and new_password and 'password_change' in request.POST:
            if request.user.check_password(current_password):
                request.user.set_password(new_password)
                request.user.save()
                messages.success(request, 'Password updated successfully!')
            else:
                messages.error(request, 'Current password is incorrect')

        elif 'enable_2fa' in request.POST:
            secret = pyotp.random_base32()
            profile, created = UserProfile.objects.get_or_create(user=request.user)
            profile.two_factor_secret = secret
            profile.save()
            messages.info(request, 'Please scan the QR code with your authenticator app')

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

        elif 'disable_2fa' in request.POST:
            profile = UserProfile.objects.get(user=request.user)
            profile.two_factor_enabled = False
            profile.two_factor_secret = None
            profile.save()
            messages.success(request, 'Two-factor authentication disabled')

        return redirect('dashboard:teacher_security_settings')

    active_sessions = 1

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

# -----------------------------
# Theme and Additional Views
# -----------------------------
@login_required
@csrf_exempt
def update_theme_preference(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            theme = data.get('theme', 'light')

            if theme not in ['light', 'dark', 'auto']:
                theme = 'light'

            profile, created = UserProfile.objects.get_or_create(user=request.user)
            profile.theme_preference = theme
            profile.save()

            return JsonResponse({'status': 'success', 'theme': theme})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required
@user_passes_test(lambda u: u.role == 'teacher')
def download_all_submissions(request, assignment_id):
    """Download all submissions for an assignment as ZIP"""
    assignment = get_object_or_404(Assignment, id=assignment_id, teacher=request.user)
    submissions = Submission.objects.filter(assignment=assignment)

    if not submissions.exists():
        messages.error(request, "No submissions found to download.")
        return redirect('dashboard:teacher_assignment_detail', id=assignment_id)

    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        for submission in submissions:
            try:
                file_path = submission.submitted_file.path
                filename = f"{submission.student.user.username}_{submission.student.enrollment_id}_{os.path.basename(file_path)}"
                zip_file.write(file_path, filename)
            except Exception as e:
                continue

    zip_buffer.seek(0)

    response = HttpResponse(zip_buffer, content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="{assignment.title}_submissions.zip"'
    return response

@login_required
@user_passes_test(lambda u: u.role == 'teacher')
def submission_details(request, submission_id):
    """Get submission details for modal"""
    submission = get_object_or_404(Submission, id=submission_id)

    if submission.assignment.teacher != request.user:
        return HttpResponse("Permission denied", status=403)

    context = {
        'submission': submission,
        'assignment': submission.assignment,
    }
    return render(request, 'dashboard/submission_details_modal.html', context)

# -----------------------------
# Progress Tracking Views
# -----------------------------
@login_required
@user_passes_test(lambda u: u.role == 'teacher')
def teacher_progress_track(request):
    """Main progress tracking dashboard for teachers"""
    teacher = get_object_or_404(Teacher, user=request.user)
    courses = Course.objects.filter(teachers=teacher)

    # AUTO-CREATE PROGRESS RECORDS FOR MISSING STUDENTS
    for course in courses:
        students = Student.objects.filter(courses=course)
        for student in students:
            progress, created = StudentProgress.objects.get_or_create(
                student=student,
                course=course,
                defaults={
                    'status': 'not_started',
                    'progress_percentage': 0
                }
            )
            if created:
                print(f"DEBUG: Created progress record for {student} in {course}")

    # Filter by course if specified
    course_id = request.GET.get('course')
    selected_course = None
    if course_id:
        selected_course = get_object_or_404(Course, id=course_id, teachers=teacher)
        progress_data = StudentProgress.objects.filter(
            course=selected_course
        ).select_related('student__user', 'course')
    else:
        progress_data = StudentProgress.objects.filter(
            course__in=courses
        ).select_related('student__user', 'course')

    # Calculate overall statistics
    total_students = Student.objects.filter(courses__in=courses).distinct().count()

    if progress_data:
        average_progress = sum(p.progress_percentage for p in progress_data) // len(progress_data)
    else:
        average_progress = 0

    # Count completed courses (progress >= 90%)
    completed_courses = progress_data.filter(progress_percentage__gte=90).count()

    # Students needing attention (progress < 25%)
    need_attention = progress_data.filter(progress_percentage__lt=25)
    need_attention_count = need_attention.count()

    # Course-wise summary with proper average progress calculation
    course_summary = []
    for course in courses:
        course_progress = StudentProgress.objects.filter(course=course)
        enrolled_students = course_progress.count()

        if enrolled_students > 0:
            total_progress = sum(p.progress_percentage for p in course_progress)
            avg_progress = total_progress // enrolled_students
            completed_students = course_progress.filter(progress_percentage__gte=90).count()
        else:
            avg_progress = 0
            completed_students = 0

        course_summary.append({
            'course': course,
            'code': course.code,
            'name': course.name,
            'average_progress': avg_progress,
            'enrolled_students': enrolled_students,
            'completed_students': completed_students
        })

    context = {
        'courses': courses,
        'selected_course': selected_course,
        'progress_data': progress_data,
        'total_students': total_students,
        'total_courses': courses.count(),
        'average_progress': average_progress,
        'completed_courses': completed_courses,
        'need_attention': need_attention,
        'need_attention_count': need_attention_count,
        'course_summary': course_summary,
    }

    return render(request, 'dashboard/teacher_progress_track.html', context)

@login_required
@user_passes_test(lambda u: u.role == 'teacher')
def send_progress_reminder(request):
    """Send progress reminder to student"""
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        course_id = request.POST.get('course_id')
        custom_message = request.POST.get('message', '')

        student = get_object_or_404(Student, id=student_id)
        course = get_object_or_404(Course, id=course_id)

        progress = get_object_or_404(StudentProgress, student=student, course=course)

        if custom_message:
            message_body = custom_message
        else:
            message_body = f"""
Hello {student.user.get_full_name() or student.user.username},

This is a reminder about your progress in {course.code} - {course.name}.

Current Progress: {progress.progress_percentage}%
Status: {progress.get_status_display()}

Please continue with your course modules to stay on track.

Best regards,
{request.user.get_full_name() or request.user.username}
            """.strip()

        message = Message(
            sender=request.user,
            recipient=student.user,
            subject=f"Progress Reminder - {course.code}",
            body=message_body
        )
        message.save()

        return JsonResponse({'success': True})

    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
@user_passes_test(lambda u: u.role == 'teacher')
def teacher_student_progress(request, course_id):
    """View student progress for a specific course"""
    course = get_object_or_404(Course, id=course_id)
    teacher = get_object_or_404(Teacher, user=request.user)

    if teacher not in course.teachers.all():
        messages.error(request, "You don't have permission to view progress for this course.")
        return redirect('dashboard:teacher_courses')

    students = Student.objects.filter(courses=course)

    progress_records = []
    for student in students:
        progress, created = StudentProgress.objects.get_or_create(
            student=student,
            course=course,
            defaults={'status': 'not_started', 'progress_percentage': 0}
        )
        progress_records.append(progress)

    completed_count = sum(1 for p in progress_records if p.status == 'completed')
    in_progress_count = sum(1 for p in progress_records if p.status == 'in_progress')
    not_started_count = sum(1 for p in progress_records if p.status == 'not_started')

    context = {
        'course': course,
        'progress_records': progress_records,
        'completed_count': completed_count,
        'in_progress_count': in_progress_count,
        'not_started_count': not_started_count,
    }
    return render(request, 'dashboard/teacher_student_progress.html', context)

@login_required
@user_passes_test(lambda u: u.role == 'teacher')
def update_student_progress(request, progress_id):
    """Update individual student progress"""
    progress = get_object_or_404(StudentProgress, id=progress_id)
    teacher = get_object_or_404(Teacher, user=request.user)

    if teacher not in progress.course.teachers.all():
        messages.error(request, "You don't have permission to update this progress.")
        return redirect('dashboard:teacher_courses')

    if request.method == 'POST':
        form = StudentProgressForm(request.POST, instance=progress)
        if form.is_valid():
            form.save()
            messages.success(request, f'Progress updated for {progress.student.user.username}')
            return redirect('dashboard:teacher_student_progress', course_id=progress.course.id)
    else:
        form = StudentProgressForm(instance=progress)

    context = {
        'form': form,
        'progress': progress,
        'title': f'Update Progress - {progress.student.user.username}'
    }
    return render(request, 'dashboard/update_student_progress.html', context)

@login_required
@user_passes_test(lambda u: u.role == 'teacher')
def course_modules(request, course_id):
    """Manage course modules"""
    course = get_object_or_404(Course, id=course_id)
    teacher = get_object_or_404(Teacher, user=request.user)

    if teacher not in course.teachers.all():
        messages.error(request, "You don't have permission to manage modules for this course.")
        return redirect('dashboard:teacher_courses')

    modules = CourseModule.objects.filter(course=course).order_by('order')

    context = {
        'course': course,
        'modules': modules,
    }
    return render(request, 'dashboard/course_modules.html', context)

@login_required
@user_passes_test(lambda u: u.role == 'teacher')
def add_course_module(request, course_id):
    """Add a new module to a course"""
    course = get_object_or_404(Course, id=course_id)
    teacher = get_object_or_404(Teacher, user=request.user)

    if teacher not in course.teachers.all():
        messages.error(request, "You don't have permission to add modules to this course.")
        return redirect('dashboard:teacher_courses')

    if request.method == 'POST':
        form = CourseModuleForm(request.POST)
        if form.is_valid():
            module = form.save(commit=False)
            module.course = course
            module.save()
            messages.success(request, 'Module added successfully!')
            return redirect('dashboard:course_modules', course_id=course.id)
    else:
        form = CourseModuleForm()

    context = {
        'form': form,
        'course': course,
        'title': 'Add Course Module'
    }
    return render(request, 'dashboard/add_course_module.html', context)

# -----------------------------
# Helper Functions
# -----------------------------
def calculate_student_course_progress(student, course):
    """Calculate overall progress for a student in a course"""
    modules = CourseModule.objects.filter(course=course)
    total_modules = modules.count()

    if total_modules == 0:
        return {
            'overall_percentage': 0,
            'modules_completed': 0,
            'total_modules': 0,
            'status': 'not_started'
        }

    completed_modules = 0
    total_progress = 0

    for module in modules:
        progress, created = StudentProgress.objects.get_or_create(
            student=student,
            course=course,
            module=module,
            defaults={'status': 'not_started', 'progress_percentage': 0}
        )

        if progress.status == 'completed':
            completed_modules += 1
            total_progress += 100
        else:
            total_progress += progress.progress_percentage

    overall_percentage = total_progress / total_modules

    if overall_percentage >= 90:
        status = 'completed'
    elif overall_percentage >= 50:
        status = 'in_progress'
    else:
        status = 'not_started'

    return {
        'overall_percentage': round(overall_percentage, 1),
        'modules_completed': completed_modules,
        'total_modules': total_modules,
        'status': status
    }

@login_required
@user_passes_test(lambda u: u.role == 'student')
def download_course_material(request, material_id):
    """Download course material and track progress with error handling"""
    if not hasattr(request.user, 'student'):
        return redirect('dashboard')

    student = get_object_or_404(Student, user=request.user)
    material = get_object_or_404(CourseMaterial, id=material_id)

    # Check if student is enrolled in the course
    if material.course not in student.courses.all():
        messages.error(request, "You are not enrolled in this course.")
        return redirect('dashboard:student_courses')

    # Check if file exists
    if not material.file:
        messages.error(request, "File not found. Please contact your teacher.")
        return redirect('dashboard:student_course_materials', course_id=material.course.id)

    try:
        # Check if file physically exists
        if not material.file.storage.exists(material.file.name):
            messages.error(request, "File not found on server. Please contact your teacher.")
            return redirect('dashboard:student_course_materials', course_id=material.course.id)
    except Exception as e:
        messages.error(request, f"Error accessing file: {str(e)}")
        return redirect('dashboard:student_course_materials', course_id=material.course.id)

    # Track the download
    download, created = MaterialDownload.objects.get_or_create(
        student=student,
        material=material
    )

    # FIX: Calculate progress based on ALL materials
    total_materials = CourseMaterial.objects.filter(course=material.course).count()
    downloaded_count = MaterialDownload.objects.filter(
        student=student,
        material__course=material.course
    ).count()

    progress_percentage = 0
    if total_materials > 0:
        progress_percentage = int((downloaded_count / total_materials) * 100)

    # Update student progress
    progress, created = StudentProgress.objects.get_or_create(
        student=student,
        course=material.course,
        defaults={
            'status': 'not_started',
            'progress_percentage': progress_percentage
        }
    )

    progress.progress_percentage = progress_percentage

    # Update status based on progress
    if progress_percentage >= 90:
        progress.status = 'completed'
    elif progress_percentage > 0:
        progress.status = 'in_progress'
    else:
        progress.status = 'not_started'

    progress.save()

    try:
        # Serve the file for download
        response = HttpResponse(material.file, content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{os.path.basename(material.file.name)}"'

        # Store success message in session
        request.session['download_success'] = f'Material downloaded successfully! Your progress is now {progress_percentage}%'

        return response

    except Exception as e:
        messages.error(request, f"Error downloading file: {str(e)}")
        return redirect('dashboard:student_course_materials', course_id=material.course.id)

def update_student_progress_from_materials(student, course):
    """Update student progress based on downloaded materials"""
    # FIX: Count ALL materials
    total_materials = CourseMaterial.objects.filter(course=course).count()

    if total_materials == 0:
        return

    # Get downloaded materials count (ALL materials)
    downloaded_materials = MaterialDownload.objects.filter(
        student=student,
        material__course=course
    ).count()

    # Calculate progress percentage
    progress_percentage = int((downloaded_materials / total_materials) * 100)

    # Get or create student progress record
    progress, created = StudentProgress.objects.get_or_create(
        student=student,
        course=course,
        defaults={
            'status': 'not_started',
            'progress_percentage': progress_percentage
        }
    )

    # Update progress
    progress.progress_percentage = progress_percentage

    # Update status based on progress
    if progress_percentage >= 90:
        progress.status = 'completed'
    elif progress_percentage > 0:
        progress.status = 'in_progress'
    else:
        progress.status = 'not_started'

    progress.save()

# Student Settings Views
# -----------------------------
@login_required
@user_passes_test(lambda u: u.role == 'student')
def student_settings(request):
    context = {
        'title': 'Student Settings',
        'settings_options': [
            {'name': 'Profile', 'icon': 'fas fa-user', 'description': 'Update your profile information', 'url': 'dashboard:student_profile_settings'},
            {'name': 'Appearance', 'icon': 'fas fa-palette', 'description': 'Customize theme', 'url': 'dashboard:student_appearance_settings'},
            {'name': 'Security', 'icon': 'fas fa-shield-alt', 'description': 'Security settings', 'url': 'dashboard:student_security_settings'},
        ]
    }
    return render(request, 'dashboard/student_settings.html', context)

@login_required
@user_passes_test(lambda u: u.role == 'student')
def student_profile_settings(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    student = get_object_or_404(Student, user=request.user)

    if request.method == 'POST':
        form = ProfileSettingsForm(request.POST, request.FILES, instance=profile, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('dashboard:student_profile_settings')
    else:
        form = ProfileSettingsForm(instance=profile, user=request.user)

    return render(request, 'dashboard/student_profile_settings.html', {
        'form': form,
        'title': 'Profile Settings',
        'student': student
    })

@login_required
@user_passes_test(lambda u: u.role == 'student')
def student_appearance_settings(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        theme = request.POST.get('theme', 'light')
        profile.theme_preference = theme
        profile.save()

        messages.success(request, 'Appearance settings saved!')
        return redirect('dashboard:student_appearance_settings')

    return render(request, 'dashboard/student_appearance_settings.html', {
        'title': 'Appearance Settings',
        'themes': ['light', 'dark', 'auto'],
        'current_theme': profile.theme_preference
    })

@login_required
@user_passes_test(lambda u: u.role == 'student')
def student_security_settings(request):
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')

        if current_password and new_password and 'password_change' in request.POST:
            if request.user.check_password(current_password):
                request.user.set_password(new_password)
                request.user.save()
                update_session_auth_hash(request, request.user)  # Important to keep user logged in
                messages.success(request, 'Password updated successfully!')
            else:
                messages.error(request, 'Current password is incorrect')

        elif 'enable_2fa' in request.POST:
            secret = pyotp.random_base32()
            profile, created = UserProfile.objects.get_or_create(user=request.user)
            profile.two_factor_secret = secret
            profile.save()
            messages.info(request, 'Please scan the QR code with your authenticator app')

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

        elif 'disable_2fa' in request.POST:
            profile = UserProfile.objects.get(user=request.user)
            profile.two_factor_enabled = False
            profile.two_factor_secret = None
            profile.save()
            messages.success(request, 'Two-factor authentication disabled')

        return redirect('dashboard:student_security_settings')

    active_sessions = 1

    try:
        profile = UserProfile.objects.get(user=request.user)
        two_factor_enabled = profile.two_factor_enabled
        has_secret = bool(profile.two_factor_secret)
    except UserProfile.DoesNotExist:
        two_factor_enabled = False
        has_secret = False

    return render(request, 'dashboard/student_security_settings.html', {
        'title': 'Security Settings',
        'active_sessions': active_sessions,
        'two_factor_enabled': two_factor_enabled,
        'has_secret': has_secret
    })
