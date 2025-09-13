from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import CustomUser

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

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password']
        labels = {
            'username': 'Username',
            'email': 'Email',
        }
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Enter your username'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Enter your email'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.role = 'student'  # Default role
        if commit:
            user.save()
        return user

    username = forms.CharField(
    max_length=150,
    error_messages={
        'required': 'Please enter a username.',
        'max_length': 'Username is too long.',
    },
    widget=forms.TextInput(attrs={'placeholder': 'Enter your username'})
)

