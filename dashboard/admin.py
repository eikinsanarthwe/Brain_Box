from django.contrib import admin
from django.contrib.auth import get_user_model
from django import forms
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Count, Avg
from django.http import HttpResponse
import csv
from datetime import datetime

User = get_user_model()

from .models import Teacher, Student, Course, Assignment, Submission, CourseMaterial

# -----------------------------
# Assignment Form with Teacher Validation
# -----------------------------
class AssignmentAdminForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = '__all__'

    def clean_teacher(self):
        teacher = self.cleaned_data.get('teacher')
        if teacher and not hasattr(teacher, 'teacher'):
            raise forms.ValidationError("The selected user must be a registered teacher")
        return teacher

    def clean_due_date(self):
        due_date = self.cleaned_data.get('due_date')
        if due_date and due_date < timezone.now():
            raise forms.ValidationError("Due date cannot be in the past")
        return due_date

# -----------------------------
# Submission Form with Grade Validation
# -----------------------------
class SubmissionAdminForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = '__all__'

    def clean_grade(self):
        grade = self.cleaned_data.get('grade')
        assignment = self.cleaned_data.get('assignment')

        if grade is not None:
            if grade < 0:
                raise forms.ValidationError("Grade cannot be negative")
            if assignment and grade > assignment.max_points:
                raise forms.ValidationError(f"Grade cannot exceed maximum points ({assignment.max_points})")

        return grade

# -----------------------------
# Custom Filters
# -----------------------------
class TeacherFilter(admin.SimpleListFilter):
    title = 'Teacher'
    parameter_name = 'teacher'

    def lookups(self, request, model_admin):
        teachers = Teacher.objects.select_related('user').all()
        return [(t.user.id, f"{t.user.get_full_name()} ({t.specialty})") for t in teachers]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(teacher__id=self.value())
        return queryset

class CourseFilter(admin.SimpleListFilter):
    title = 'Course'
    parameter_name = 'course'

    def lookups(self, request, model_admin):
        return [(c.id, f"{c.code} - {c.name}") for c in Course.objects.all()]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(course__id=self.value())
        return queryset

class SemesterFilter(admin.SimpleListFilter):
    title = 'Semester'
    parameter_name = 'semester'

    def lookups(self, request, model_admin):
        semesters = Student.objects.values_list('semester', flat=True).distinct().order_by('semester')
        return [(sem, f"Semester {sem}") for sem in semesters if sem]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(semester=self.value())
        return queryset

# -----------------------------
# Export Actions
# -----------------------------
def export_to_csv(modeladmin, request, queryset):
    meta = modeladmin.model._meta
    field_names = [field.name for field in meta.fields]

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename={meta.verbose_name_plural}.csv'

    writer = csv.writer(response)
    writer.writerow(field_names)

    for obj in queryset:
        row = [getattr(obj, field) for field in field_names]
        writer.writerow(row)

    return response

export_to_csv.short_description = "Export selected to CSV"

# -----------------------------
# Teacher Admin
# -----------------------------
@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ['user', 'specialty', 'phone', 'user_email', 'courses_count', 'assignments_count']
    search_fields = ['user__first_name', 'user__last_name', 'specialty', 'phone']
    list_filter = ['specialty']
    raw_id_fields = ['user']
    actions = [export_to_csv]

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'
    user_email.admin_order_field = 'user__email'

    def courses_count(self, obj):
        count = obj.course_set.count()
        return format_html('<span class="badge bg-primary">{}</span>', count)
    courses_count.short_description = 'Courses'

    def assignments_count(self, obj):
        count = Assignment.objects.filter(teacher=obj.user).count()
        return format_html('<span class="badge bg-info">{}</span>', count)
    assignments_count.short_description = 'Assignments'

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            courses_count=Count('course')
        )

# -----------------------------
# Student Admin
# -----------------------------
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['user', 'enrollment_id', 'semester', 'user_email', 'courses_count', 'submissions_count', 'average_grade']
    list_filter = ['semester', CourseFilter]
    search_fields = ['user__first_name', 'user__last_name', 'enrollment_id']
    raw_id_fields = ['user']
    filter_horizontal = ['courses']
    actions = [export_to_csv]

    def get_courses(self, obj):
        return ", ".join([c.code for c in obj.courses.all()])
    get_courses.short_description = 'Courses'

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'
    user_email.admin_order_field = 'user__email'

    def courses_count(self, obj):
        count = obj.courses.count()
        return format_html('<span class="badge bg-primary">{}</span>', count)
    courses_count.short_description = 'Courses'

    def submissions_count(self, obj):
        count = obj.submission_set.count()
        return format_html('<span class="badge bg-success">{}</span>', count)
    submissions_count.short_description = 'Submissions'

    def average_grade(self, obj):
        avg_grade = obj.submission_set.filter(grade__isnull=False).aggregate(avg=Avg('grade'))['avg']
        if avg_grade:
            return format_html('<span class="badge bg-info">{:.1f}</span>', avg_grade)
        return format_html('<span class="badge bg-secondary">N/A</span>')
    average_grade.short_description = 'Avg Grade'

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('courses', 'submission_set')

# -----------------------------
# Course Admin
# -----------------------------
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'teacher_list', 'student_count', 'assignment_count', 'description_short']
    list_filter = ['teachers']
    search_fields = ['code', 'name', 'description']
    filter_horizontal = ['teachers']
    actions = [export_to_csv]

    def teacher_list(self, obj):
        teachers = obj.teachers.all()
        if teachers:
            return ", ".join([t.user.get_full_name() for t in teachers])
        return "No teachers"
    teacher_list.short_description = 'Teachers'

    def student_count(self, obj):
        count = obj.students.count()
        return format_html('<span class="badge bg-success">{}</span>', count)
    student_count.short_description = 'Students'

    def assignment_count(self, obj):
        count = obj.assignments.count()
        return format_html('<span class="badge bg-warning">{}</span>', count)
    assignment_count.short_description = 'Assignments'

    def description_short(self, obj):
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_short.short_description = 'Description'

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('teachers', 'students').annotate(
            student_count=Count('students'),
            assignment_count=Count('assignments')
        )

# -----------------------------
# Assignment Admin
# -----------------------------
@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    form = AssignmentAdminForm
    list_display = ['title', 'course', 'teacher_name', 'due_date', 'status_badge', 'max_points', 'submission_count', 'graded_count']
    list_filter = ['status', 'course', TeacherFilter, 'due_date']
    search_fields = ['title', 'course__name', 'teacher__username']
    date_hierarchy = 'due_date'
    filter_horizontal = ['students']
    ordering = ['-due_date']
    actions = [export_to_csv]

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'course', 'teacher')
        }),
        ('Dates & Points', {
            'fields': ('due_date', 'max_points')
        }),
        ('Status & Students', {
            'fields': ('status', 'students')
        }),
    )

    def teacher_name(self, obj):
        return obj.teacher.get_full_name() if obj.teacher else "No teacher"
    teacher_name.short_description = 'Teacher'
    teacher_name.admin_order_field = 'teacher__first_name'

    def status_badge(self, obj):
        colors = {
            'draft': 'secondary',
            'published': 'success',
            'archived': 'danger',
            'graded': 'primary'
        }
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            colors.get(obj.status, 'warning'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def submission_count(self, obj):
        count = obj.submission_set.count()
        return format_html('<span class="badge bg-info">{}</span>', count)
    submission_count.short_description = 'Submissions'

    def graded_count(self, obj):
        count = obj.submission_set.filter(grade__isnull=False).count()
        return format_html('<span class="badge bg-success">{}</span>', count)
    graded_count.short_description = 'Graded'

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "teacher":
            kwargs["queryset"] = User.objects.filter(teacher__isnull=False)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('course', 'teacher').annotate(
            submission_count=Count('submission'),
            graded_count=Count('submission', filter=models.Q(submission__grade__isnull=False))
        )

# -----------------------------
# Submission Admin
# -----------------------------
@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    form = SubmissionAdminForm
    list_display = ['assignment', 'student_name', 'submitted_at', 'grade_display', 'is_late_badge', 'grade_percentage']
    list_filter = ['is_late', 'assignment__course', 'submitted_at']
    search_fields = ['assignment__title', 'student__user__username', 'student__user__first_name', 'student__user__last_name']
    readonly_fields = ['submitted_at', 'is_late']
    raw_id_fields = ['assignment', 'student']
    ordering = ['-submitted_at']
    actions = [export_to_csv, 'export_grades']

    fieldsets = (
        ('Submission Information', {
            'fields': ('assignment', 'student', 'submitted_at', 'is_late')
        }),
        ('Submission Content', {
            'fields': ('submitted_file', 'text_content')
        }),
        ('Grading', {
            'fields': ('grade', 'feedback')
        }),
    )

    def student_name(self, obj):
        return obj.student.user.get_full_name()
    student_name.short_description = 'Student'
    student_name.admin_order_field = 'student__user__first_name'

    def grade_display(self, obj):
        if obj.grade is not None:
            return f"{obj.grade}/{obj.assignment.max_points}"
        return format_html('<span class="text-muted">Not graded</span>')
    grade_display.short_description = 'Grade'

    def grade_percentage(self, obj):
        if obj.grade is not None and obj.assignment.max_points > 0:
            percentage = (obj.grade / obj.assignment.max_points) * 100
            color = 'success' if percentage >= 70 else 'warning' if percentage >= 50 else 'danger'
            return format_html('<span class="badge bg-{}">{:.1f}%</span>', color, percentage)
        return format_html('<span class="badge bg-secondary">N/A</span>')
    grade_percentage.short_description = 'Percentage'

    def is_late_badge(self, obj):
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            'danger' if obj.is_late else 'success',
            'Late' if obj.is_late else 'On Time'
        )
    is_late_badge.short_description = 'Status'

    def export_grades(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="grades_export.csv"'

        writer = csv.writer(response)
        writer.writerow(['Student', 'Assignment', 'Course', 'Grade', 'Max Points', 'Percentage', 'Submitted At', 'Status'])

        for submission in queryset:
            percentage = ''
            if submission.grade is not None and submission.assignment.max_points > 0:
                percentage = f"{(submission.grade / submission.assignment.max_points) * 100:.1f}%"

            writer.writerow([
                submission.student.user.get_full_name(),
                submission.assignment.title,
                submission.assignment.course.code,
                submission.grade or 'N/A',
                submission.assignment.max_points,
                percentage,
                submission.submitted_at.strftime('%Y-%m-%d %H:%M'),
                'Late' if submission.is_late else 'On Time'
            ])

        return response
    export_grades.short_description = "Export selected grades to CSV"

# -----------------------------
# Course Material Admin
# -----------------------------
@admin.register(CourseMaterial)
class CourseMaterialAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'uploaded_by_name', 'uploaded_at', 'file_type', 'file_size']
    list_filter = ['course', 'uploaded_at']
    search_fields = ['title', 'course__code', 'course__name']
    readonly_fields = ['uploaded_at', 'file_size']
    raw_id_fields = ['uploaded_by']

    def uploaded_by_name(self, obj):
        return obj.uploaded_by.get_full_name()
    uploaded_by_name.short_description = 'Uploaded By'

    def file_type(self, obj):
        if obj.file:
            return obj.file.name.split('.')[-1].upper()
        return 'N/A'
    file_type.short_description = 'File Type'

    def file_size(self, obj):
        if obj.file and obj.file.size:
            size = obj.file.size
            if size < 1024:
                return f"{size} B"
            elif size < 1024 * 1024:
                return f"{size / 1024:.1f} KB"
            else:
                return f"{size / (1024 * 1024):.1f} MB"
        return "N/A"
    file_size.short_description = 'File Size'

# -----------------------------
# Custom Admin Site Header
# -----------------------------
admin.site.site_header = "Learning Management System Admin"
admin.site.site_title = "LMS Admin Portal"
admin.site.index_title = "Welcome to LMS Administration"
