from django import forms
from .models import Course, Assignment,Submission,Student
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'code', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make fields required
        self.fields['title'].required = True
        self.fields['code'].required = True
        
        # Add Bootstrap classes
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
        
        # Disable code field when editing existing course
        if self.instance and self.instance.pk:
            self.fields['code'].disabled = True
            self.fields['code'].help_text = "Course code cannot be changed after creation"

    def clean_code(self):
        code = self.cleaned_data.get('code')
        # Skip validation if we're editing and code hasn't changed
        if self.instance and self.instance.pk and self.instance.code == code:
            return code
            
        if Course.objects.filter(code=code).exists():
            raise ValidationError("A course with this code already exists.")
        return code
class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ['course', 'title', 'description', 'due_date', 'total_points', 'status', 'attachment']
        widgets = {
            'course': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter assignment instructions...'
            }),
            'due_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
            'total_points': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'step': 1
            }),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }



    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make fields required
        self.fields['title'].required = True
        self.fields['description'].required = True
        self.fields['total_points'].required = True
        
        # Add help text
        self.fields['attachment'].help_text = "Upload assignment file (PDF, DOCX, etc.)"
        self.fields['status'].help_text = "Draft: Not visible to students. Published: Visible to students."

    def clean_total_points(self):
        points = self.cleaned_data.get('total_points')
        if points <= 0:
            raise ValidationError("Total points must be greater than 0")
        return points

class GradeSubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ['grade', 'feedback']
        widgets = {
            'grade': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'step': 0.5
            }),
            'feedback': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter feedback for the student...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set max points based on assignment
        if self.instance and self.instance.assignment:
            self.fields['grade'].widget.attrs['max'] = self.instance.assignment.total_points
            self.fields['grade'].help_text = f"Max points: {self.instance.assignment.total_points}"
        
        # Make feedback optional
        self.fields['feedback'].required = False

    def clean_grade(self):
        grade = self.cleaned_data.get('grade')
        if grade is not None:
            if self.instance and self.instance.assignment:
                if grade > self.instance.assignment.total_points:
                    raise ValidationError(
                        f"Grade cannot exceed maximum points ({self.instance.assignment.total_points})"
                    )
            if grade < 0:
                raise ValidationError("Grade cannot be negative")
        return grade

class StudentForm(forms.ModelForm):
    # Pull in User fields here
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)
    username = forms.CharField(max_length=150, required=True)
    password = forms.CharField(widget=forms.PasswordInput, required=True)

    class Meta:
        model = Student
        fields = ['user', 'enrollment_date']  # only Student-specific fields

    def save(self, commit=True):
        # Create User first
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
            is_staff=False  # prevent student from being staff
        )

        # Link it to Student
        student = super().save(commit=False)
        student.user = user
        if commit:
            student.save()
            self.save_m2m()  # save courses many-to-many
        return student