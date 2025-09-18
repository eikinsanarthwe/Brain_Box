from django.db import models
from django.conf import settings
# -----------------------------
# User Profile Model (for profile pictures and 2FA)
# -----------------------------
class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    bio = models.TextField(blank=True, null=True, verbose_name="Bio/Description")
    two_factor_enabled = models.BooleanField(default=False)
    two_factor_secret = models.CharField(max_length=32, null=True, blank=True)
    theme_preference = models.CharField(max_length=10, default='light', choices=[
        ('light', 'Light'),
        ('dark', 'Dark'),
        ('auto', 'Auto (System)')
    ])

    def __str__(self):
        return f"{self.user.username}'s Profile"

# -----------------------------
# Teacher Model
# -----------------------------
class Teacher(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    specialty = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, blank=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username

# -----------------------------
# Student Model
# -----------------------------
class Student(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    enrollment_id = models.CharField(max_length=20, unique=True)
    courses = models.ManyToManyField('Course', related_name='students')
    semester = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.enrollment_id})"

    class Meta:
        verbose_name = "Student"
        verbose_name_plural = "Students"

# -----------------------------
# Course Model
# -----------------------------
class Course(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    teachers = models.ManyToManyField(Teacher)
    credit = models.IntegerField(default=3)  # Add this field
    created_at = models.DateTimeField(auto_now_add=True)
    # Add this field

    def __str__(self):
        return f"{self.code} - {self.name}"

# -----------------------------
# Assignment Model
# -----------------------------
# C:\Users\ASUS\Brain_Box\dashboard\models.py

class Assignment(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]
    students = models.ManyToManyField(Student)
    title = models.CharField(max_length=200)
    description = models.TextField()
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        limit_choices_to={'role': 'teacher'},
        on_delete=models.CASCADE
    )
    due_date = models.DateTimeField()
    max_points = models.PositiveIntegerField(default=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')  # Add this field
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.course.code}"
# -----------------------------
# Submission Model
# -----------------------------
class Submission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    submitted_file = models.FileField(upload_to='submissions/%Y/%m/%d/')
    submitted_at = models.DateTimeField(auto_now_add=True)
    grade = models.PositiveIntegerField(null=True, blank=True)
    feedback = models.TextField(blank=True)
    is_late = models.BooleanField(default=False)

    class Meta:
        unique_together = ('assignment', 'student')
        ordering = ['-submitted_at']

    def save(self, *args, **kwargs):
        if self.assignment.due_date and self.submitted_at:
            self.is_late = self.submitted_at > self.assignment.due_date
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student}'s submission for {self.assignment}"


# -----------------------------
# Course Material Model
# -----------------------------
class CourseMaterial(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='materials')  # Note the related_name
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='course_materials/%Y/%m/%d/')
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        limit_choices_to={'role': 'teacher'},
        on_delete=models.CASCADE
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.course.code}"

    class Meta:
        ordering = ['-uploaded_at']


# Message Model
# -----------------------------
class Message(models.Model):
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='sent_messages',
        on_delete=models.CASCADE
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='received_messages',
        on_delete=models.CASCADE
    )
    subject = models.CharField(max_length=200)
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    sent_at = models.DateTimeField(auto_now_add=True)
    parent_message = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='replies'
    )

    class Meta:
        ordering = ['-sent_at']

    def __str__(self):
        return f"{self.subject} - {self.sender} to {self.recipient}"

    def mark_as_read(self):
        self.is_read = True
        self.save()
