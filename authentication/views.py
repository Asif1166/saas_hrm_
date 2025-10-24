from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.core.paginator import Paginator
from django.urls import reverse
from django.contrib.auth.models import User
from .models import User
from organization.models import Organization, OrganizationMembership
import json


def login_view(request):
    """
    Login view for all user types (Super Admin, Organization Admin, Employee)
    """
    if request.user.is_authenticated:
        return redirect('authentication:dashboard_redirect')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if username and password:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
                    
                    # Redirect based on user role
                    if user.is_super_admin:
                        return redirect('super_admin:dashboard')
                    elif user.is_organization_admin:
                        return redirect('organization:organization_dashboard')
                    else:
                        return redirect('hrm:employee_dashboard')
                else:
                    messages.error(request, 'Your account is inactive. Please contact support.')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Please provide both username and password.')
    
    return render(request, 'authentication/login.html')


def logout_view(request):
    """
    Logout view
    """
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('authentication:login')


@login_required
def dashboard_redirect(request):
    """
    Redirect users to appropriate dashboard based on their role
    """
    if request.user.is_super_admin:
        return redirect('super_admin:dashboard')
    elif request.user.is_organization_admin:
        return redirect('organization:organization_dashboard')
    else:
        # For employees, redirect to employee dashboard
        return redirect('hrm:employee_dashboard')


@login_required
def profile_view(request):
    """
    User profile view
    """
    user = request.user
    context = {
        'user': user,
    }
    
    # Add organization info if user is not super admin
    if not user.is_super_admin:
        try:
            membership = OrganizationMembership.objects.get(user=user, is_active=True)
            context['organization'] = membership.organization
            context['is_org_admin'] = membership.is_admin
        except OrganizationMembership.DoesNotExist:
            context['organization'] = None
    
    return render(request, 'authentication/profile.html', context)


@login_required
def update_profile(request):
    """
    Update user profile
    """
    if request.method == 'POST':
        user = request.user
        
        # Update basic user information
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.phone = request.POST.get('phone', user.phone)
        
        # Handle password change if provided
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if current_password and new_password and confirm_password:
            if user.check_password(current_password):
                if new_password == confirm_password:
                    user.set_password(new_password)
                    messages.success(request, 'Password updated successfully.')
                else:
                    messages.error(request, 'New passwords do not match.')
            else:
                messages.error(request, 'Current password is incorrect.')
        
        user.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('authentication:profile')
    
    return redirect('authentication:profile')
