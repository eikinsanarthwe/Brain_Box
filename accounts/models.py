from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)

    # Add the __str__ method here
    def __str__(self):
        # Return full name if available, otherwise username
        full_name = self.get_full_name()
        if full_name.strip():
            return full_name
        return self.username

    # Optional: You can also add other methods or properties
    def is_admin(self):
        return self.role == 'admin'

    def is_teacher(self):
        return self.role == 'teacher'

    def is_student(self):
        return self.role == 'student'

# Create your models here.
