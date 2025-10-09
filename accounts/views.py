from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from .forms import LoginForm
from django.contrib.auth.decorators import login_required
from .forms import SignupForm
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
import pyotp

def login_view(request):
    form = LoginForm(request, data=request.POST or None)
    if form.is_valid():
        user = form.get_user()
        
        # Check if 2FA is enabled for this user
        if is_2fa_enabled(user):
            # Store user ID in session for 2FA verification
            request.session['2fa_user_id'] = user.id
            request.session['2fa_username'] = user.username
            return redirect('two_factor_verify')
        else:
            login(request, user)
            if user.role == 'admin':
                return redirect('dashboard:dashboard')  # Redirect to admin dashboard
            elif user.role == 'teacher':
                return redirect('dashboard:teacher_dashboard')  # Redirect to teacher dashboard
            elif user.role == 'student':
                return redirect('student_home')
    
    return render(request, 'accounts/login.html', {'form': form})

def is_2fa_enabled(user):
    """Check if 2FA is enabled for the user"""
    try:
        from dashboard.models import UserProfile
        profile, created = UserProfile.objects.get_or_create(user=user)
        return profile.two_factor_enabled
    except:
        return False

def two_factor_verify(request):
    # Check if user came from login process
    user_id = request.session.get('2fa_user_id')
    username = request.session.get('2fa_username')
    
    if not user_id:
        messages.error(request, 'Please login first')
        return redirect('login')
    
    if request.method == 'POST':
        verification_code = request.POST.get('verification_code')
        
        if not verification_code or len(verification_code) != 6:
            messages.error(request, 'Please enter a valid 6-digit code')
            return render(request, 'accounts/two_factor_verify.html')
        
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.get(id=user_id)
            
            # Verify the 2FA code
            if verify_2fa_code(user, verification_code):
                login(request, user)
                
                # Clear the 2FA session data
                if '2fa_user_id' in request.session:
                    del request.session['2fa_user_id']
                if '2fa_username' in request.session:
                    del request.session['2fa_username']
                
                messages.success(request, 'Login successful!')
                
                # Redirect based on user role
                if user.role == 'admin':
                    return redirect('dashboard:dashboard')
                elif user.role == 'teacher':
                    return redirect('dashboard:teacher_dashboard')
                elif user.role == 'student':
                    return redirect('student_home')
            else:
                messages.error(request, 'Invalid verification code. Please try again.')
                
        except User.DoesNotExist:
            messages.error(request, 'User not found. Please login again.')
            return redirect('login')
        except Exception as e:
            messages.error(request, f'Verification failed: {str(e)}')
    
    return render(request, 'accounts/two_factor_verify.html', {
        'username': username
    })

def verify_2fa_code(user, code):
    """Verify the 2FA code using the user's secret"""
    try:
        from dashboard.models import UserProfile
        profile = UserProfile.objects.get(user=user)
        
        if not profile.two_factor_secret:
            return False
            
        totp = pyotp.TOTP(profile.two_factor_secret)
        return totp.verify(code)
    except:
        return False

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
    form = SignupForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('login')  # Redirect to login after signup
    return render(request, 'accounts/signup.html', {'form': form})