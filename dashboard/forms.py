from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from .models import Teacher, Student, Course, Assignment,CourseMaterial,Message,UserProfile,CourseModule, StudentProgress
from django.db.models import Q

User = get_user_model()

# ---------------- Admin Creation ---------------- #

class AdminCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email address'})
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter username'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Create password'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirm password'})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'admin'
        if commit:
            user.save()
        return user

# ---------------- Admin Update ---------------- #

class AdminChangeForm(forms.ModelForm):
    new_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Leave blank to keep current password'}),
        help_text="Leave blank to keep current password"
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter username'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email address'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last name'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop('password', None)

# ---------------- Teacher Form ---------------- #

class TeacherForm(forms.ModelForm):
    username = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(required=False, widget=forms.PasswordInput(attrs={'class': 'form-control'}), help_text="Leave blank to generate a random password")
    specialty = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    phone = forms.CharField(max_length=20, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = Teacher
        fields = ['specialty', 'phone']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and self.instance.user:
            self.fields['username'].initial = self.instance.user.username
            self.fields['password'].help_text = "Leave blank to keep current password"
        else:
            self.fields['password'].required = True

    def save(self, commit=True):
        teacher = super().save(commit=False)
        username = self.cleaned_data['username']
        password = self.cleaned_data['password']

        if not self.instance.pk:
            if not password:  # If no password entered, generate one
                password = User.objects.make_random_password()
            user = User.objects.create_user(username=username, password=password)
            user.role = 'teacher'
            user.save()
            teacher.user = user
        else:
            user = self.instance.user
            if user.username != username:
                user.username = username
            if password:
                user.set_password(password)
            user.save()

        if commit:
            teacher.save()
        return teacher

# ---------------- Student Form ---------------- #
# ---------------- Student Form ---------------- #
class StudentForm(forms.ModelForm):
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text="Leave blank to generate a random password"
    )

    class Meta:
        model = Student
        fields = ['enrollment_id', 'semester']  # course is handled separately
        widgets = {
            'enrollment_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter enrollment ID'
            }),
            'semester': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'placeholder': 'Enter semester'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Dynamically add courses field (not in Student model)
        courses = Course.objects.all()
        course_choices = [(course.id, f"{course.code} - {course.name}") for course in courses]

        self.fields['courses'] = forms.MultipleChoiceField(
            choices=course_choices,
            widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
            required=False,
            label="Courses"
        )

        if self.instance.pk and self.instance.user:
            # Pre-fill username
            self.fields['username'].initial = self.instance.user.username
            self.fields['password'].help_text = "Leave blank to keep current password"

            # Pre-fill selected courses
            if self.instance.courses.exists():
                self.fields['courses'].initial = [
                    course.id for course in self.instance.courses.all()
                ]

    def save(self, commit=True):
        student = super().save(commit=False)
        username = self.cleaned_data['username']
        password = self.cleaned_data.get('password')
        selected_course_ids = self.cleaned_data.get('courses', [])

        if not self.instance.pk:
            # New student
            if not password:
                password = User.objects.make_random_password()
            user = User.objects.create_user(username=username, password=password)
            user.role = 'student'
            user.save()
            student.user = user
        else:
            # Existing student
            user = self.instance.user
            if user.username != username:
                user.username = username
            if password:
                user.set_password(password)
            user.save()

        if commit:
            student.save()
            # Save courses
            if selected_course_ids:
                student.courses.set(Course.objects.filter(id__in=selected_course_ids))
            else:
                student.courses.clear()

        return student

#------------- Course Form ---------------- #

# In your CourseForm class in forms.py
class CourseForm(forms.ModelForm):
    # Add a clear image field
    clear_image = forms.BooleanField(required=False, widget=forms.CheckboxInput())

    class Meta:
        model = Course
        fields = ['code', 'name', 'description', 'teachers', 'image']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. CS101'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Intro to CS'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Course description...'}),
            'teachers': forms.SelectMultiple(attrs={'class': 'form-control select2-multiple', 'data-placeholder': 'Select teachers...'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['teachers'].queryset = Teacher.objects.all()

        # Make image field not required
        self.fields['image'].required = False

        # Hide the clear_image field as we'll handle it in the template
        self.fields['clear_image'].widget = forms.HiddenInput()

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Handle image clearing
        if self.cleaned_data.get('clear_image'):
            if instance.image:
                instance.image.delete(save=False)
            instance.image = None

        if commit:
            instance.save()
            self.save_m2m()

        return instance
class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ['title', 'description', 'due_date', 'course', 'max_points', 'status', 'students']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter assignment title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Detailed assignment description...'}),
            'due_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'course': forms.Select(attrs={'class': 'form-control'}),
            'max_points': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Maximum score (e.g. 100)', 'min': 1}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'students': forms.SelectMultiple(attrs={'class': 'form-control select2-multiple', 'data-placeholder': 'Select students...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Filter courses and students based on teacher
        if hasattr(self, 'initial') and 'user' in self.initial:
            user = self.initial['user']
            if user.role == 'teacher':
                try:
                    teacher = Teacher.objects.get(user=user)
                    # Get courses taught by this teacher
                    self.fields['course'].queryset = Course.objects.filter(teachers=teacher)

                    # Get students enrolled in teacher's courses
                    teacher_courses = Course.objects.filter(teachers=teacher)
                    self.fields['students'].queryset = Student.objects.filter(courses__in=teacher_courses).distinct()

                except Teacher.DoesNotExist:
                    self.fields['course'].queryset = Course.objects.none()
                    self.fields['students'].queryset = Student.objects.none()
        else:
            # Default querysets for admin users
            self.fields['course'].queryset = Course.objects.all()
            self.fields['students'].queryset = Student.objects.all()
class TeacherStudentForm(forms.ModelForm):
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter username'})
    )
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter password'}),
        help_text="Enter password for the student"
    )
    # Override the course field to be a ChoiceField
    course = forms.ChoiceField(
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Course*"
    )

    class Meta:
        model = Student
        fields = ['enrollment_id', 'course', 'semester']
        widgets = {
            'enrollment_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter enrollment ID'}),
            'semester': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'placeholder': 'Enter semester'})
        }

    def __init__(self, *args, **kwargs):
        # Extract teacher from kwargs before calling super
        self.teacher = kwargs.pop('teacher', None)
        super().__init__(*args, **kwargs)

        # Get course choices for the current teacher
        if self.teacher:
            try:
                courses = Course.objects.filter(teachers=self.teacher)
                course_choices = [(course.name, f"{course.code} - {course.name}") for course in courses]
                self.fields['course'].choices = [('', '---------')] + course_choices
            except Exception as e:
                print(f"DEBUG: Error getting courses: {e}")
                self.fields['course'].choices = [('', '---------')]
        else:
            self.fields['course'].choices = [('', '---------')]

    def save(self, commit=True):
        student = super().save(commit=False)
        username = self.cleaned_data['username']
        password = self.cleaned_data['password']

        # Create user account
        user = User.objects.create_user(username=username, password=password)
        user.role = 'student'
        user.save()

        student.user = user

        if commit:
            student.save()
        return student
class TeacherCourseForm(forms.ModelForm):
    # Add clear image field
    clear_image = forms.BooleanField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = Course
        fields = ['code', 'name', 'description', 'image']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. CS101'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Intro to CS'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Course description...'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make image field not required
        self.fields['image'].required = False

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Handle image clearing - this is the crucial part
        if self.cleaned_data.get('clear_image'):
            print("DEBUG: Clearing image...")
            # Delete the current image file from storage
            if instance.image:
                # Store the path before deletion for debugging
                old_image_path = instance.image.path if instance.image else None
                print(f"DEBUG: Deleting image at: {old_image_path}")

                # Delete the file from storage
                instance.image.delete(save=False)

            # Set the image field to None/empty
            instance.image = None

        # If a new image is uploaded, it will automatically replace the old one
        # Django's FileField handles this automatically

        if commit:
            instance.save()

        return instance
# ---------------- Course Material Form ---------------- #
class CourseMaterialForm(forms.ModelForm):
    class Meta:
        model = CourseMaterial
        fields = ['title', 'description', 'file']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter material title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Description of the material...'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
        }


# ---------------- Message Form ---------------- #
class MessageForm(forms.ModelForm):
    recipient = forms.ModelChoiceField(
        queryset=User.objects.none(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Recipient"
    )

    class Meta:
        model = Message
        fields = ['recipient', 'subject', 'body']
        widgets = {
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Message subject'}),
            'body': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Type your message here...'}),
        }

    def __init__(self, *args, **kwargs):
        self.sender = kwargs.pop('sender', None)
        super().__init__(*args, **kwargs)

        if self.sender:
            if self.sender.role == 'admin':
                self.fields['recipient'].queryset = User.objects.exclude(id=self.sender.id)

            elif self.sender.role == 'teacher':
                teacher_courses = Course.objects.filter(teachers__user=self.sender)
                student_users = Student.objects.filter(
                    courses__in=teacher_courses
                ).values_list('user', flat=True)

                recipients = User.objects.filter(
                    Q(role='admin') |
                    Q(role='teacher') |
                    Q(id__in=student_users)
                ).exclude(id=self.sender.id)

                self.fields['recipient'].queryset = recipients

            elif self.sender.role == 'student':
                student = Student.objects.get(user=self.sender)

                teacher_users = Teacher.objects.filter(
                    course__in=student.courses.all()
                ).values_list('user', flat=True)

                same_course_students = Student.objects.filter(
                    courses__in=student.courses.all()
                ).values_list('user', flat=True)

                recipients = User.objects.filter(
                    Q(role='admin') |
                    Q(id__in=teacher_users) |
                    Q(id__in=same_course_students)
                ).exclude(id=self.sender.id)

                self.fields['recipient'].queryset = recipients


# ---------------- Reply Form ---------------- #
class ReplyForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['body']
        widgets = {
            'body': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Type your reply here...'}),
        }
def clean(self):
    cleaned_data = super().clean()
    print(f"Form cleaned data: {cleaned_data}")  # Debug output
    return cleaned_data
class ProfileSettingsForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    bio = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Tell us about yourself...'}))

    class Meta:
        model = UserProfile
        fields = ['profile_picture', 'bio']
        widgets = {
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if self.user:
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial = self.user.last_name
            self.fields['email'].initial = self.user.email
            if hasattr(self.user, 'userprofile'):
                self.fields['bio'].initial = self.user.userprofile.bio

    def save(self, commit=True):
        profile = super().save(commit=False)
        if self.user:
            self.user.first_name = self.cleaned_data['first_name']
            self.user.last_name = self.cleaned_data['last_name']
            self.user.email = self.cleaned_data['email']
            self.user.save()
        if commit:
            profile.save()
        return profile
class StudentProgressForm(forms.ModelForm):
    class Meta:
        model = StudentProgress
        fields = ['status', 'progress_percentage', 'notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'progress_percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 100,
                'type': 'range'  # This will create a slider
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Add notes about student progress...'
            }),
        }

class CourseModuleForm(forms.ModelForm):
    class Meta:
        model = CourseModule
        fields = ['title', 'description', 'order', 'is_required', 'estimated_duration']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'estimated_duration': forms.NumberInput(attrs={'class': 'form-control'}),
        }
