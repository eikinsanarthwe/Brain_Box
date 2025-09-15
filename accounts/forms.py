# accounts/forms.py
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model
from dashboard.models import Student

UserModel = get_user_model()

class LoginForm(AuthenticationForm):
    username = forms.CharField(label='Email / Username')
    password = forms.CharField(widget=forms.PasswordInput)

class SignupForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Enter your password'
        }),
        label='Password'
    )

    enrollment_id = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Enter your enrollment ID'})
    )

    # Remove enrollment_id from Meta fields since it's not a User field
    class Meta:
        model = UserModel
        fields = ['username', 'first_name', 'last_name', 'email', 'password']
        labels = {
            'username': 'Username',
            'email': 'Email',
            'first_name': 'First Name',
            'last_name': 'Last Name',
        }
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Enter your username'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Enter your email'}),
            'first_name': forms.TextInput(attrs={'placeholder': 'Enter your first name'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Enter your last name'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make first_name and last_name required
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True

    def save(self, commit=True):
        # Get the enrollment_id from cleaned_data before calling super().save()
        enrollment_id = self.cleaned_data.get('enrollment_id')

        # Create the user
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.role = 'student'  # Set role to student

        if commit:
            user.save()

            # CREATE THE STUDENT PROFILE
            Student.objects.create(
                user=user,
                enrollment_id=enrollment_id,
                semester=1  # Default semester
            )

        return user

    def clean_enrollment_id(self):
        enrollment_id = self.cleaned_data.get('enrollment_id')
        if enrollment_id and Student.objects.filter(enrollment_id=enrollment_id).exists():
            raise forms.ValidationError('This enrollment ID is already taken.')
        return enrollment_id
