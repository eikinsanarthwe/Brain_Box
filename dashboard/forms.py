from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from .models import Teacher, Student, Course, Assignment,CourseMaterial,Message
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

class StudentForm(forms.ModelForm):
    username = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(required=False, widget=forms.PasswordInput(attrs={'class': 'form-control'}), help_text="Leave blank to generate a random password")
    # Override course field for admin too
    course = forms.ChoiceField(
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Course"
    )

    class Meta:
        model = Student
        fields = ['username', 'password', 'enrollment_id', 'course', 'semester']
        widgets = {
            'enrollment_id': forms.TextInput(attrs={'class': 'form-control'}),
            'semester': forms.NumberInput(attrs={'class': 'form-control', 'min': 1})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Get all courses for admin
        courses = Course.objects.all()
        course_choices = [(course.name, f"{course.code} - {course.name}") for course in courses]
        self.fields['course'].choices = [('', '---------')] + course_choices

        if self.instance.pk and self.instance.user:
            self.fields['username'].initial = self.instance.user.username
            self.fields['password'].help_text = "Leave blank to keep current password"
        self.fields.pop('user', None)

    def save(self, commit=True):
        student = super().save(commit=False)
        username = self.cleaned_data['username']
        password = self.cleaned_data.get('password')

        if not self.instance.pk:
            if not password:  # If no password entered, generate one
                password = User.objects.make_random_password()
            user = User.objects.create_user(username=username, password=password)
            user.role = 'student'
            user.save()
            student.user = user
        else:
            user = self.instance.user
            if user.username != username:
                user.username = username
            if password:
                user.set_password(password)
            user.save()

        if commit:
            student.save()
            self.save_m2m()
        return student

# ---------------- Course Form ---------------- #

class CourseForm(forms.ModelForm):
     class Meta:
        model = Course
        fields = ['code', 'name', 'description', 'teachers']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. CS101'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Intro to CS'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Course description...'}),
            'teachers': forms.SelectMultiple(attrs={'class': 'form-control select2-multiple', 'data-placeholder': 'Select teachers...'})
        }

     def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Fix this line - use Teacher model instead of User
        self.fields['teachers'].queryset = Teacher.objects.all()  # Changed from User to Teacher
class AssignmentForm(forms.ModelForm):
     class Meta:
        model = Assignment
        fields = ['title', 'description', 'due_date', 'course', 'teacher', 'max_points']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter assignment title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Detailed assignment description...'}),
            'due_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'course': forms.Select(attrs={'class': 'form-control'}),
            'teacher': forms.Select(attrs={'class': 'form-control'}),
            'max_points': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Maximum score (e.g. 100)', 'min': 1})
        }

     def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter teachers by role - this should be User objects, not Teacher objects
        # Because the teacher field in Assignment is a ForeignKey to User, not Teacher
        self.fields['teacher'].queryset = User.objects.filter(role='teacher')  # This is correct

        # If initializing for a teacher user, set the initial value to the current user
        if 'initial' in kwargs and 'user' in kwargs['initial']:
            user = kwargs['initial']['user']
            if user.role == 'teacher':
                self.fields['teacher'].initial = user
                self.fields['teacher'].disabled = True
# In your forms.py, update the TeacherStudentForm
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
    class Meta:
        model = Course
        fields = ['code', 'name', 'description']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. CS101'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Intro to CS'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Course description...'}),
        }

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
