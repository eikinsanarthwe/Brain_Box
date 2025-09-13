from django.db import models
from django.conf import settings

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
    course = models.CharField(max_length=100)  # You can switch to FK if needed later
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

    def __str__(self):
        return f"{self.code} - {self.name}"

# -----------------------------
# Assignment Model
# -----------------------------
class Assignment(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
        ('graded', 'Graded'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        limit_choices_to={'role': 'teacher'},
        on_delete=models.CASCADE
    )
    students = models.ManyToManyField(Student)
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

    class Meta:
        unique_together = ('assignment', 'student')
        ordering = ['-submitted_at']

    def save(self, *args, **kwargs):
        if self.assignment.due_date and self.submitted_at:
            self.is_late = self.submitted_at > self.assignment.due_date
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student}'s submission for {self.assignment}"
