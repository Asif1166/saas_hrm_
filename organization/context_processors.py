from .models import Organization, OrganizationMembership

def organization_context(request):
    """
    Context processor to make organization data available globally
    """
    context = {}
    
    if request.user.is_authenticated:
        try:
            # Get the organization for the current user through OrganizationMembership
            organization_membership = OrganizationMembership.objects.filter(
                user=request.user, 
                is_active=True
            ).first()
            
            if organization_membership:
                context['organization'] = organization_membership.organization
            else:
                context['organization'] = None
                
        except Exception as e:
            print(f"Error getting organization: {e}")
            context['organization'] = None
    
    return context