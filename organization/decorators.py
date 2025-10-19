from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def super_admin_required(view_func):
    """
    Decorator to ensure only super admin users can access the view
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Please log in to access this page.')
            return redirect('authentication:login')
        
        if not request.user.is_super_admin:
            messages.error(request, 'Access denied. Super admin privileges required.')
            return redirect('authentication:dashboard')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def organization_admin_required(view_func):
    """
    Decorator to ensure only organization admin users can access the view
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Please log in to access this page.')
            return redirect('authentication:login')
        
        if not request.user.is_organization_admin:
            messages.error(request, 'Access denied. Organization admin privileges required.')
            return redirect('authentication:dashboard')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def employee_required(view_func):
    """
    Decorator to ensure only employee users can access the view
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Please log in to access this page.')
            return redirect('authentication:login')
        
        if not request.user.is_employee:
            messages.error(request, 'Access denied. Employee privileges required.')
            return redirect('authentication:dashboard')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def organization_member_required(view_func):
    """
    Decorator to ensure user is a member of an organization
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Please log in to access this page.')
            return redirect('authentication:login')
        
        # Super admin can access everything
        if request.user.is_super_admin:
            return view_func(request, *args, **kwargs)
        
        # Check if user is a member of any organization
        from .models import OrganizationMembership
        try:
            membership = OrganizationMembership.objects.get(
                user=request.user, 
                is_active=True
            )
            # Add organization to request for easy access
            request.organization = membership.organization
            return view_func(request, *args, **kwargs)
        except OrganizationMembership.DoesNotExist:
            messages.error(request, 'You are not associated with any organization.')
            return redirect('authentication:login')
    
    return wrapper
