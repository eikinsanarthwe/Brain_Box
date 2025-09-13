from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from .forms import LoginForm
from django.contrib.auth.decorators import login_required
from .forms import SignupForm
from django.contrib.auth import logout


def login_view(request):
    form = LoginForm(request, data=request.POST or None)
    if form.is_valid():
        user = form.get_user()
        login(request, user)
        if user.role == 'admin':
            return redirect('dashboard:dashboard')  # Redirect to dashboard index
        elif user.role == 'teacher':
            return redirect('teacher_home')
        elif user.role == 'student':
            return redirect('student_home')
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')



@login_required
def admin_home(request):
    return render(request, 'dashboard/admin_home.html')

@login_required
def teacher_home(request):
    return render(request, 'accounts/teacher_home.html')

@login_required
def student_home(request):
    return render(request, 'accounts/student_home.html')

def test_view(request):
    return render(request, 'accounts/test.html')

def signup_view(request):
    form = SignupForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('login')  # Redirect to login after signup
    return render(request, 'accounts/signup.html', {'form': form})


