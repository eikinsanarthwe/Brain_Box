from django.db import models
from django.conf import settings
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError

class Profile(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    image = models.CharField(
        max_length=255,
        default='default_profile.png',
        help_text="Path to profile image (relative to static files)"
    )
    bio = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()

class Course(models.Model):
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='taught_courses',
        limit_choices_to={'is_staff': True}
    )
    code = models.CharField(max_length=10, unique=True)
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    students = models.ManyToManyField(
        'Student',
        related_name='enrolled_courses',
        blank=True
    )

    class Meta:
        ordering = ['code']
        verbose_name_plural = "Courses"
        permissions = [
            ('view_all_courses', 'Can view all courses'),
        ]

    def __str__(self):
        return f"{self.code} - {self.title}"

    def clean(self):
        if hasattr(self, 'teacher') and self.teacher and not self.teacher.is_staff:
            raise ValidationError("The assigned teacher must be a staff member.")

class Student(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="student_profile",
        limit_choices_to={"is_staff": False},
    )
    enrollment_date = models.DateField(default=timezone.now)

    class Meta:
        ordering = ["user__last_name", "user__first_name"]

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.user.username})"

class Assignment(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='assignments'
    )
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    due_date = models.DateTimeField(null=True, blank=True)
    total_points = models.PositiveIntegerField(default=100)
    created_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    attachment = models.FileField(upload_to='assignment_files/', blank=True, null=True)
    grade = models.CharField(max_length=10, blank=True, null=True)
    feedback = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-due_date']
        permissions = [
            ('view_all_assignments', 'Can view all assignments'),
        ]

    def __str__(self):
        return f"{self.title} ({self.course.code})"

    @property
    def is_past_due(self):
        if self.due_date is None:
            return False
        return timezone.now() > self.due_date

    @property
    def days_remaining(self):
        if not self.due_date:
            return None
        delta = self.due_date - timezone.now()
        return delta.days

    @property
    def submission_status(self):
        total = self.course.students.count()
        submitted = self.submissions.count()
        return f"{submitted}/{total}"

    @property
    def grading_status(self):
        graded = self.submissions.filter(is_graded=True).count()
        total = self.submissions.count()
        return f"{graded}/{total}" if total > 0 else "0/0"

    def get_submission_status_class(self):
        submitted = self.submissions.count()
        total = self.course.students.count()
        if submitted == total:
            return "bg-success"
        elif submitted > total / 2:
            return "bg-warning"
        return "bg-danger"

    def clean(self):
        if self.due_date and self.due_date < timezone.now():
            raise ValidationError("Due date cannot be in the past")
        if self.pk:
            original = Assignment.objects.get(pk=self.pk)
            if original.status == 'archived' and self.status != 'archived':
                raise ValidationError("Archived assignments cannot be changed back to draft/published")

    def publish(self):
        if self.status != 'published':
            self.status = 'published'
            self.save()

    def archive(self):
        if self.status != 'archived':
            self.status = 'archived'
            self.save()

class Submission(models.Model):
    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name='submissions'
    )
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='submissions'
    )
    submitted_date = models.DateTimeField(default=timezone.now)
    file = models.FileField(
        upload_to='submissions/%Y/%m/%d/',
        blank=True,
        null=True
    )
    grade = models.PositiveIntegerField(null=True, blank=True)
    is_graded = models.BooleanField(default=False)
    feedback = models.TextField(blank=True)

    class Meta:
        ordering = ['-submitted_date']
        unique_together = ['assignment', 'student']

    def __str__(self):
        return f"{self.student} - {self.assignment}"

    @property
    def late_submission(self):
        if self.assignment.due_date is None:
            return False
        return self.submitted_date > self.assignment.due_date

    def clean(self):
        if not self.student.enrolled_courses.filter(id=self.assignment.course.id).exists():
            raise ValidationError("Student must be enrolled in the course")

class Grade(models.Model):
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='grades'
    )
    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name='grades'
    )
    value = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Grade value (e.g., 85.50)"
    )
    feedback = models.TextField(blank=True)
    graded_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('student', 'assignment')
        ordering = ["student__user__first_name", "student__user__last_name"]
        permissions = [
            ('view_all_grades', 'Can view all grades'),
        ]

    def __str__(self):
        return f"{self.student} - {self.assignment}: {self.value}"

class NotificationManager(models.Manager):
    def unread(self, user):
        return self.filter(user=user, read=False)

    def mark_as_read(self, user):
        return self.filter(user=user, read=False).update(read=True)

class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField()
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    url = models.URLField(blank=True, null=True)

    objects = NotificationManager()

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.user.username}: {self.message[:50]}"

class ActivityLog(models.Model):
    ACTION_CHOICES = [
        ('course_create', 'Course Created'),
        ('course_update', 'Course Updated'),
        ('assignment_create', 'Assignment Created'),
        ('assignment_submit', 'Assignment Submitted'),
        ('grade_submit', 'Grade Submitted'),
        ('student_add', 'Student Added'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    object_type = models.CharField(max_length=50)
    object_id = models.PositiveIntegerField()
    object_name = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.get_action_display()} - {self.object_name}"
