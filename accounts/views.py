from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from .forms import LoginForm
from django.contrib.auth.decorators import login_required
from .forms import SignupForm
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required, user_passes_test

def login_view(request):
    form = LoginForm(request, data=request.POST or None)
    if form.is_valid():
        user = form.get_user()
        login(request, user)
        if user.role == 'admin':
            return redirect('dashboard:dashboard')  # Redirect to admin dashboard
        elif user.role == 'teacher':
            return redirect('dashboard:teacher_dashboard')  # Redirect to teacher dashboard
        elif user.role == 'student':
            return redirect('student_home')
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def admin_home(request):
    # For admin users, redirect to the dashboard app
    if request.user.role == 'admin':
        return redirect('dashboard:dashboard')
    # If somehow a non-admin gets here, redirect to appropriate page
    elif request.user.role == 'teacher':
        return redirect('dashboard:teacher_dashboard')
    else:
        return redirect('student_home')

@login_required
def teacher_home(request):
    # For teacher users, redirect to the teacher dashboard
    if request.user.role == 'teacher':
        return redirect('dashboard:teacher_dashboard')
    # If somehow a non-teacher gets here, redirect to appropriate page
    elif request.user.role == 'admin':
        return redirect('dashboard:dashboard')
    else:
        return redirect('student_home')

@login_required
def student_home(request):
    return render(request, 'accounts/student_home.html')

def test_view(request):
    return render(request, 'accounts/test.html')

def signup_view(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()  # This will create both User and Student
            login(request, user)
            return redirect('student_home')  # Redirect to student dashboard
    else:
        form = SignupForm()

    return render(request, 'accounts/signup.html', {'form': form})
