from .models import UserProfile

def theme_context(request):
    """
    Add theme preference to all templates
    """
    if request.user.is_authenticated:
        try:
            profile = UserProfile.objects.get(user=request.user)
            return {'current_theme': profile.theme_preference}
        except UserProfile.DoesNotExist:
            # Create a UserProfile if it doesn't exist
            profile = UserProfile.objects.create(user=request.user)
            return {'current_theme': profile.theme_preference}
    return {'current_theme': 'light'}

def user_role_context(request):
    """
    Add user role information to all templates
    """
    if request.user.is_authenticated:
        return {
            'user_role': request.user.role,
            'is_admin': request.user.role == 'admin',
            'is_teacher': request.user.role == 'teacher',
            'is_student': request.user.role == 'student',
        }
    return {
        'user_role': None,
        'is_admin': False,
        'is_teacher': False,
        'is_student': False,
    }

def unread_messages_count(request):
    """
    Add unread messages count to all templates
    """
    if request.user.is_authenticated:
        try:
            from .models import Message
            unread_count = Message.objects.filter(
                recipient=request.user,
                is_read=False
            ).count()
            return {'unread_messages_count': unread_count}
        except:
            return {'unread_messages_count': 0}
    return {'unread_messages_count': 0}

def sidebar_context(request):
    """
    Add sidebar-specific context
    """
    if request.user.is_authenticated:
        try:
            from .models import Teacher, Student

            if request.user.role == 'teacher':
                teacher = Teacher.objects.get(user=request.user)
                course_count = teacher.course_set.count()
                return {
                    'teacher_course_count': course_count,
                    'teacher_profile': teacher
                }
            elif request.user.role == 'student':
                student = Student.objects.get(user=request.user)
                return {
                    'student_course_count': student.courses.count(),
                    'student_profile': student
                }
        except (Teacher.DoesNotExist, Student.DoesNotExist):
            pass

    return {}
from .models import UserProfile

def theme_context(request):
    """
    Add theme preference to all templates
    """
    if request.user.is_authenticated:
        try:
            profile = UserProfile.objects.get(user=request.user)
            # Ensure light theme is default
            if not profile.theme_preference:
                profile.theme_preference = 'light'
                profile.save()
            return {'current_theme': profile.theme_preference}
        except UserProfile.DoesNotExist:
            # Create a UserProfile with light theme as default
            profile = UserProfile.objects.create(user=request.user, theme_preference='light')
            return {'current_theme': 'light'}
    return {'current_theme': 'light'}

# Keep the other context processors as they are...
