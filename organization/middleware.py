from django.utils.deprecation import MiddlewareMixin
from .models import OrganizationMembership


class OrganizationMiddleware(MiddlewareMixin):
    """
    Middleware to add organization context to requests
    """
    
    def process_request(self, request):
        # Skip for super admin and unauthenticated users
        if not request.user.is_authenticated or request.user.is_super_admin:
            request.organization = None
            return
        
        # Get user's organization
        try:
            membership = OrganizationMembership.objects.get(
                user=request.user,
                is_active=True
            )
            request.organization = membership.organization
            request.organization_membership = membership
        except OrganizationMembership.DoesNotExist:
            request.organization = None
            request.organization_membership = None
