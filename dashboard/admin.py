from django.contrib import admin
from django.contrib.auth import get_user_model
from django import forms
from .models import Teacher, Student, Course, Assignment, Submission

User = get_user_model()

# Custom Form for Assignment with Teacher Validation
class AssignmentAdminForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = '__all__'

    def clean_teacher(self):
        teacher = self.cleaned_data.get('teacher')
        if not hasattr(teacher, 'teacher'):
            raise forms.ValidationError("The selected user must be a registered teacher")
        return teacher

# Custom Filter for Teachers in Assignment Admin
class TeacherFilter(admin.SimpleListFilter):
    title = 'teacher'
    parameter_name = 'teacher'

    def lookups(self, request, model_admin):
        return [(t.user.id, f"{t.user.get_full_name()} ({t.specialty})") 
               for t in Teacher.objects.all()]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(teacher__id=self.value())
        return queryset

# Teacher Admin
@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ['user', 'specialty', 'phone', 'user_email']
    search_fields = ['user__first_name', 'user__last_name', 'specialty', 'phone']
    list_filter = ['specialty']
    raw_id_fields = ['user']
    fieldsets = (
        (None, {
            'fields': ('user', 'specialty')
        }),
        ('Contact Information', {
            'fields': ('phone',)
        }),
    )

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'
    user_email.admin_order_field = 'user__email'

# Student Admin
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['user', 'enrollment_id', 'course', 'semester', 'user_email']
    list_filter = ['course', 'semester']
    search_fields = ['user__first_name', 'user__last_name', 'enrollment_id']
    raw_id_fields = ['user']
    fieldsets = (
        (None, {
            'fields': ('user', 'enrollment_id')
        }),
        ('Academic Information', {
            'fields': ('course', 'semester')
        }),
    )

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'
    user_email.admin_order_field = 'user__email'

# Course Admin
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'teacher_count', 'description_short']
    list_filter = ['teachers']
    search_fields = ['code', 'name', 'description']
    filter_horizontal = ['teachers']
    fieldsets = (
        (None, {
            'fields': ('code', 'name', 'description')
        }),
        ('Instructors', {
            'fields': ('teachers',)
        }),
    )

    def teacher_count(self, obj):
        return obj.teachers.count()
    teacher_count.short_description = 'Teachers'

    def description_short(self, obj):
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_short.short_description = 'Description'

# Assignment Admin
@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    form = AssignmentAdminForm
    list_display = ('title', 'course', 'teacher_name', 'due_date', 'status_badge', 'max_points')
    list_filter = ('status', 'course', TeacherFilter)
    search_fields = ('title', 'course__name', 'teacher__username')
    date_hierarchy = 'due_date'
    filter_horizontal = ['students']
    ordering = ('-due_date',)
    list_per_page = 20
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'course')
        }),
        ('Participants', {
            'fields': ('teacher', 'students')
        }),
        ('Details', {
            'fields': ('due_date', 'max_points', 'status')
        }),
    )

    def teacher_name(self, obj):
        return obj.teacher.get_full_name()
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

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "teacher":
            kwargs["queryset"] = User.objects.filter(teacher__isnull=False)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

# Submission Admin
@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('assignment', 'student_name', 'submitted_at', 'grade_display', 'is_late_badge')
    list_filter = ('is_late', 'assignment__course')
    search_fields = ('assignment__title', 'student__user__username')
    readonly_fields = ('submitted_at',)
    raw_id_fields = ('assignment', 'student')
    list_per_page = 20
    fieldsets = (
        (None, {
            'fields': ('assignment', 'student')
        }),
        ('Submission Details', {
            'fields': ('submitted_file', 'submitted_at', 'is_late')
        }),
        ('Evaluation', {
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
        return "Not graded"
    grade_display.short_description = 'Grade'

    def is_late_badge(self, obj):
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            'danger' if obj.is_late else 'success',
            'Late' if obj.is_late else 'On Time'
        )
    is_late_badge.short_description = 'Status'