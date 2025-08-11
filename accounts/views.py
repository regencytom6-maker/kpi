from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.views.decorators.csrf import csrf_protect

@csrf_protect
def user_login(request):
    """User login view for operators and staff"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome, {user.get_full_name() or user.username}!')
            
            # Use centralized dashboard routing
            return redirect('dashboards:dashboard_home')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'accounts/login.html')

def user_logout(request):
    """User logout view"""
    logout(request)
    return redirect('accounts:login')

@login_required
def user_profile(request):
    """User profile view"""
    return render(request, 'accounts/profile.html', {'user': request.user})
