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
            return redirect('dashboard:student_dashboard') # Redirect to student dashboard
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

def signup_view(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Log the user in immediately after signup
            login(request, user)
            # Redirect to the appropriate dashboard based on the user's role
            if user.role == 'admin':
                return redirect('dashboard:dashboard')
            elif user.role == 'teacher':
                return redirect('dashboard:teacher_dashboard')
            else: # Student
                return redirect('dashboard:student_dashboard')
    else:
        form = SignupForm()
    return render(request, 'accounts/signup.html', {'form': form})

@login_required
def admin_home(request):
    # For admin users, redirect to the dashboard app
    if request.user.role == 'admin':
        return redirect('dashboard:dashboard')
    # If a non-admin gets here, redirect to the appropriate page
    elif request.user.role == 'teacher':
        return redirect('dashboard:teacher_dashboard')
    else:
        return redirect('dashboard:student_dashboard')

@login_required
def teacher_home(request):
    # For teacher users, redirect to the teacher dashboard
    if request.user.role == 'teacher':
        return redirect('dashboard:teacher_dashboard')
    # If a non-teacher gets here, redirect to the appropriate page
    elif request.user.role == 'admin':
        return redirect('dashboard:dashboard')
    else:
        return redirect('dashboard:student_dashboard')

@login_required
def student_home(request):
    # This function is now simplified to handle redirects based on role.
    if request.user.role == 'student':
        return redirect('dashboard:student_dashboard')
    elif request.user.role == 'admin':
        return redirect('dashboard:dashboard')
    elif request.user.role == 'teacher':
        return redirect('dashboard:teacher_dashboard')
    # This `else` block is unlikely to be reached if all roles are handled above.
    return redirect('login')
