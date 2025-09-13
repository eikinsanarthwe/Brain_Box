from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import (
    Course, 
    Assignment, 
    Student, 
    Submission,
    Grade,  # Add this import
    ActivityLog  # Make sure this is imported
)

# Course Activities
@receiver(post_save, sender=Course)
def log_course_activity(sender, instance, created, **kwargs):
    action = 'course_create' if created else 'course_update'
    ActivityLog.objects.create(
        user=instance.teacher,
        action=action,
        object_type='course',
        object_id=instance.id,
        object_name=instance.title
    )

# Assignment Activities
@receiver(post_save, sender=Assignment)
def log_assignment_activity(sender, instance, created, **kwargs):
    if created:
        ActivityLog.objects.create(
            user=instance.course.teacher,
            action='assignment_create',
            object_type='assignment',
            object_id=instance.id,
            object_name=instance.title
        )

# Submission Activities
@receiver(post_save, sender=Submission)
def log_submission_activity(sender, instance, created, **kwargs):
    if created:
        ActivityLog.objects.create(
            user=instance.student.user,
            action='assignment_submit',
            object_type='submission',
            object_id=instance.id,
            object_name=f"{instance.assignment.title} submission"
        )

# Grading Activities
@receiver(post_save, sender=Grade)
def log_grade_activity(sender, instance, created, **kwargs):
    if created:
        ActivityLog.objects.create(
            user=instance.assignment.course.teacher,
            action='grade_submit',
            object_type='grade',
            object_id=instance.id,
            object_name=f"Grade for {instance.assignment.title}"
        )

# Student Enrollment Activities
@receiver(post_save, sender=Student.enrolled_courses.through)
def log_student_enrollment(sender, instance, created, **kwargs):
    if created:
        ActivityLog.objects.create(
            user=instance.course.teacher,
            action='student_add',
            object_type='enrollment',
            object_id=instance.id,
            object_name=f"{instance.student.user.username} to {instance.course.title}"
        )