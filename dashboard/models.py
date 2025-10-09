from django.db import models
from django.conf import settings
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from django.core.files.base import ContentFile
import random
import os
import requests
from django.utils import timezone
from django.contrib.auth.models import AbstractUser

# -----------------------------
# Custom User Model
# -----------------------------
class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)

    def __str__(self):
        # Return full name if available, otherwise username
        full_name = self.get_full_name()
        if full_name.strip():
            return full_name
        return self.username

    def is_admin(self):
        return self.role == 'admin'

    def is_teacher(self):
        return self.role == 'teacher'

    def is_student(self):
        return self.role == 'student'

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
    credit = models.IntegerField(default=3)
    created_at = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to='course_images/%Y/%m/%d/', null=True, blank=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

    def save(self, *args, **kwargs):
        # If no image is provided, generate a default one
        if not self.image:
            self.generate_default_image()
        super().save(*args, **kwargs)

    def generate_default_image(self):
        # Colors for different course categories
        colors = [
            ('#4A90E2', '#FFFFFF'),  # Blue - Programming/CS
            ('#50E3C2', '#000000'),  # Teal - Science
            ('#B8E986', '#000000'),  # Green - Math
            ('#F5A623', '#000000'),  # Orange - Humanities
            ('#D0021B', '#FFFFFF')   # Red - Other
        ]

        # Choose a random color or base it on course code
        color_index = hash(self.code) % len(colors)
        bg_color, text_color = colors[color_index]

        # Create a new image
        img = Image.new('RGB', (300, 200), color=bg_color)
        draw = ImageDraw.Draw(img)

        # Try to use a nice font if available
        try:
            # You might need to adjust the font path for your system
            font_path = "arial.ttf"
            font = ImageFont.truetype(font_path, 40)
        except:
            # Fallback to default font
            font = ImageFont.load_default()

        # Add course code text
        text = self.code
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (300 - text_width) / 2
        y = (200 - text_height) / 2

        # Draw the text
        draw.text((x, y), text, fill=text_color, font=font)

        # Add a border
        draw.rectangle([0, 0, 299, 199], outline=text_color, width=2)

        # Save to BytesIO buffer
        buffer = BytesIO()
        img.save(buffer, format='PNG')

        # Create a file name
        filename = f"course_{self.code}_{self.id or 'new'}.png"

        # Save the image to the model
        self.image.save(filename, ContentFile(buffer.getvalue()), save=False)

        buffer.close()

    def get_image_url(self):
        if self.image:
            return self.image.url
        else:
            # This fallback won't be needed if generate_default_image() always runs
            return f"/static/images/course-default-{hash(self.code) % 5 + 1}.png"

# -----------------------------
# Course Module Model
# -----------------------------
class CourseModule(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    is_required = models.BooleanField(default=True)
    estimated_duration = models.IntegerField(help_text="Estimated duration in minutes", default=0)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.course.code} - {self.title}"

# -----------------------------
# Assignment Model
# -----------------------------
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
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
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
    comments = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('assignment', 'student')
        ordering = ['-submitted_at']

    def save(self, *args, **kwargs):
        if self.assignment.due_date and self.submitted_at:
            self.is_late = self.submitted_at > self.assignment.due_date
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student}'s submission for {self.assignment}"

    def get_filename(self):
        """Get the filename without path"""
        return os.path.basename(self.submitted_file.name)

# -----------------------------
# Course Material Model
# -----------------------------
class CourseMaterial(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='materials')
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

# -----------------------------
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

# -----------------------------
# Student Progress Model
# -----------------------------
class StudentProgress(models.Model):
    PROGRESS_STATUS = (
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('needs_review', 'Needs Review'),
    )

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='progress')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='student_progress')
    module = models.ForeignKey(CourseModule, on_delete=models.CASCADE, null=True, blank=True, related_name='progress')
    status = models.CharField(max_length=20, choices=PROGRESS_STATUS, default='not_started')
    progress_percentage = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
    completed_modules = models.ManyToManyField('CourseModule', blank=True, related_name='completed_by')
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ['student', 'course', 'module']
        verbose_name_plural = 'Student Progress'

    def __str__(self):
        if self.module:
            return f"{self.student.user.username} - {self.course.name} - {self.module.title} ({self.progress_percentage}%)"
        else:
            return f"{self.student.user.username} - {self.course.name} ({self.progress_percentage}%)"

    def get_total_modules(self):
        """Get total number of modules in the course"""
        return CourseModule.objects.filter(course=self.course).count()

    def get_completed_modules_count(self):
        """Get count of completed modules"""
        return self.completed_modules.count()

    def calculate_progress_percentage(self):
        """Calculate progress percentage based on completed modules"""
        total_modules = self.get_total_modules()
        if total_modules == 0:
            return 0
        completed_count = self.get_completed_modules_count()
        return int((completed_count / total_modules) * 100)

    def save(self, *args, **kwargs):
        # Auto-calculate progress percentage if not set
        if not self.progress_percentage:
            self.progress_percentage = self.calculate_progress_percentage()

        # Update status based on progress
        if self.progress_percentage >= 90:
            self.status = 'completed'
        elif self.progress_percentage > 0:
            self.status = 'in_progress'
        else:
            self.status = 'not_started'

        super().save(*args, **kwargs)
