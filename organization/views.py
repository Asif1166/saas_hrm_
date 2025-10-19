from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.core.paginator import Paginator
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from .models import (
    Organization, OrganizationMembership, MenuCategory, MenuItem, UserMenuPermission,
    DynamicTable, TableColumn, RoleTablePermission, RoleColumnPermission, UserTablePreference
)
from .decorators import super_admin_required, organization_admin_required, organization_member_required
from .utils import DynamicTableManager
import json

User = get_user_model()


@login_required
@super_admin_required
def super_admin_dashboard(request):
    """
    Super Admin Dashboard - Overview of all organizations
    """
    organizations = Organization.objects.all()
    
    # Statistics
    total_organizations = organizations.count()
    active_organizations = organizations.filter(status='active').count()
    total_users = User.objects.filter(role__in=['organization_admin', 'employee']).count()
    
    # Recent organizations
    recent_organizations = organizations.order_by('-created_at')[:5]
    
    context = {
        'total_organizations': total_organizations,
        'active_organizations': active_organizations,
        'total_users': total_users,
        'recent_organizations': recent_organizations,
    }
    
    return render(request, 'super_admin/dashboard.html', context)


@login_required
@super_admin_required
def organization_list(request):
    """
    List all organizations for super admin
    """
    organizations = Organization.objects.all().order_by('-created_at')
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        organizations = organizations.filter(
            name__icontains=search_query
        ) | organizations.filter(
            email__icontains=search_query
        )
    
    # Status filter
    status_filter = request.GET.get('status')
    if status_filter:
        organizations = organizations.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(organizations, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'status_choices': Organization.STATUS_CHOICES,
    }
    
    return render(request, 'super_admin/organization_list.html', context)


@login_required
@super_admin_required
def organization_detail(request, organization_id):
    """
    View organization details
    """
    organization = get_object_or_404(Organization, id=organization_id)
    
    # Get organization members
    members = OrganizationMembership.objects.filter(
        organization=organization
    ).select_related('user').order_by('-is_admin', 'joined_at')
    
    context = {
        'organization': organization,
        'members': members,
    }
    
    return render(request, 'super_admin/organization_detail.html', context)


@login_required
@super_admin_required
def create_organization(request):
    """
    Create new organization
    """
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Create organization
                organization = Organization(
                    name=request.POST.get('name'),
                    slug=slugify(request.POST.get('name')),
                    description=request.POST.get('description'),
                    email=request.POST.get('email'),
                    phone=request.POST.get('phone'),
                    website=request.POST.get('website'),
                    address_line1=request.POST.get('address_line1'),
                    address_line2=request.POST.get('address_line2'),
                    city=request.POST.get('city'),
                    state=request.POST.get('state'),
                    postal_code=request.POST.get('postal_code'),
                    country=request.POST.get('country'),
                    subscription_plan=request.POST.get('subscription_plan', 'basic'),
                    max_employees=int(request.POST.get('max_employees', 10)),
                    created_by=request.user
                )
                organization.save()
                
                # Create organization admin user
                admin_username = request.POST.get('admin_username')
                admin_email = request.POST.get('admin_email')
                admin_password = request.POST.get('admin_password')
                admin_first_name = request.POST.get('admin_first_name')
                admin_last_name = request.POST.get('admin_last_name')
                
                if admin_username and admin_email and admin_password:
                    admin_user = User(
                        username=admin_username,
                        email=admin_email,
                        first_name=admin_first_name,
                        last_name=admin_last_name,
                        role='organization_admin',
                        is_active=True
                    )
                    admin_user.set_password(admin_password)
                    admin_user.save()
                    
                    # Create organization membership
                    OrganizationMembership.objects.create(
                        user=admin_user,
                        organization=organization,
                        is_admin=True,
                        is_active=True
                    )
                    
                    messages.success(request, f'Organization "{organization.name}" and admin user created successfully!')
                else:
                    messages.success(request, f'Organization "{organization.name}" created successfully!')
                
                return redirect('super_admin:organization_detail', organization_id=organization.id)
                
        except Exception as e:
            messages.error(request, f'Error creating organization: {str(e)}')
    
    context = {
        'subscription_plans': ['basic', 'premium', 'enterprise'],
    }
    
    return render(request, 'super_admin/create_organization.html', context)


@login_required
@super_admin_required
def update_organization(request, organization_id):
    """
    Update organization
    """
    organization = get_object_or_404(Organization, id=organization_id)
    
    if request.method == 'POST':
        try:
            organization.name = request.POST.get('name', organization.name)
            organization.description = request.POST.get('description', organization.description)
            organization.email = request.POST.get('email', organization.email)
            organization.phone = request.POST.get('phone', organization.phone)
            organization.website = request.POST.get('website', organization.website)
            organization.address_line1 = request.POST.get('address_line1', organization.address_line1)
            organization.address_line2 = request.POST.get('address_line2', organization.address_line2)
            organization.city = request.POST.get('city', organization.city)
            organization.state = request.POST.get('state', organization.state)
            organization.postal_code = request.POST.get('postal_code', organization.postal_code)
            organization.country = request.POST.get('country', organization.country)
            organization.status = request.POST.get('status', organization.status)
            organization.subscription_plan = request.POST.get('subscription_plan', organization.subscription_plan)
            organization.max_employees = int(request.POST.get('max_employees', organization.max_employees))
            
            organization.save()
            messages.success(request, 'Organization updated successfully!')
            return redirect('super_admin:organization_detail', organization_id=organization.id)
            
        except Exception as e:
            messages.error(request, f'Error updating organization: {str(e)}')
    
    context = {
        'organization': organization,
        'status_choices': Organization.STATUS_CHOICES,
        'subscription_plans': ['basic', 'premium', 'enterprise'],
    }
    
    return render(request, 'super_admin/update_organization.html', context)


@login_required
@organization_admin_required
def organization_dashboard(request):
    """
    Organization Admin Dashboard
    """
    # Get user's organization
    try:
        membership = OrganizationMembership.objects.get(
            user=request.user, 
            is_active=True
        )
        organization = membership.organization
    except OrganizationMembership.DoesNotExist:
        messages.error(request, 'You are not associated with any organization.')
        return redirect('authentication:login')
    
    # Organization statistics
    total_employees = User.objects.filter(
        organizationmembership__organization=organization,
        role='employee'
    ).count()
    
    total_departments = organization.department_set.count() if hasattr(organization, 'department_set') else 0
    
    # Recent activities (you can add more specific activities here)
    recent_employees = User.objects.filter(
        organizationmembership__organization=organization,
        role='employee'
    ).order_by('-date_joined')[:5]
    
    context = {
        'organization': organization,
        'total_employees': total_employees,
        'total_departments': total_departments,
        'recent_employees': recent_employees,
    }
    
    return render(request, 'organization/dashboard.html', context)


@login_required
def debug_user_info(request):
    """
    Debug view to check user information
    """
    from django.http import JsonResponse
    
    user = request.user
    debug_info = {
        'username': user.username,
        'role': user.role,
        'is_super_admin': user.is_super_admin,
        'is_organization_admin': user.is_organization_admin,
        'is_employee': user.is_employee,
        'is_authenticated': user.is_authenticated,
    }
    
    # Check organization membership
    try:
        membership = OrganizationMembership.objects.get(user=user, is_active=True)
        debug_info['organization'] = {
            'name': membership.organization.name,
            'is_admin': membership.is_admin,
            'is_active': membership.is_active,
        }
    except OrganizationMembership.DoesNotExist:
        debug_info['organization'] = 'No organization membership found'
    
    return JsonResponse(debug_info)


# Menu Management Views
@login_required
@super_admin_required
def menu_categories(request):
    """List all menu categories"""
    categories = MenuCategory.objects.all().order_by('order', 'name')
    
    context = {
        'categories': categories,
        'page_title': 'Menu Categories'
    }
    return render(request, 'organization/menu_categories.html', context)


@login_required
@super_admin_required
def create_menu_category(request):
    """Create a new menu category"""
    if request.method == 'POST':
        name = request.POST.get('name')
        icon = request.POST.get('icon', '')
        order = request.POST.get('order', 0)
        
        try:
            category = MenuCategory.objects.create(
                name=name,
                icon=icon,
                order=int(order) if order else 0
            )
            messages.success(request, f'Menu category "{name}" created successfully!')
            return redirect('organization:menu_categories')
        except Exception as e:
            messages.error(request, f'Error creating menu category: {str(e)}')
    
    return render(request, 'organization/create_menu_category.html')


@login_required
@super_admin_required
def menu_items(request):
    """List all menu items"""
    items = MenuItem.objects.select_related('category', 'parent').all().order_by('category__order', 'order', 'title')
    categories = MenuCategory.objects.filter(is_active=True).order_by('order')
    
    # Filter by category if specified
    category_id = request.GET.get('category')
    if category_id:
        items = items.filter(category_id=category_id)
    
    context = {
        'items': items,
        'categories': categories,
        'selected_category': category_id,
        'page_title': 'Menu Items'
    }
    return render(request, 'organization/menu_items.html', context)


@login_required
@super_admin_required
def create_menu_item(request):
    """Create a new menu item"""
    categories = MenuCategory.objects.filter(is_active=True).order_by('order')
    organizations = Organization.objects.filter(status='active')
    parent_items = MenuItem.objects.filter(is_active=True, parent__isnull=True).order_by('title')
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                title = request.POST.get('title')
                category_id = request.POST.get('category')
                category_id = int(category_id) if category_id else None

                parent_id = request.POST.get('parent')
                parent_id = int(parent_id) if parent_id else None

                url_name = request.POST.get('url_name', '')
                url_path = request.POST.get('url_path', '')
                icon = request.POST.get('icon', '')
                description = request.POST.get('description', '')
                visibility = request.POST.get('visibility', 'all')
                order = request.POST.get('order', 0)
                is_external = request.POST.get('is_external') == 'on'
                target = request.POST.get('target', '_self')
                organization_ids = request.POST.getlist('organizations')

                menu_item = MenuItem.objects.create(
                    title=title,
                    category_id=category_id,
                    parent_id=parent_id,
                    url_name=url_name,
                    url_path=url_path,
                    icon=icon,
                    description=description,
                    visibility=visibility,
                    order=int(order) if order else 0,
                    is_external=is_external,
                    target=target
                )

                if organization_ids:
                    menu_item.organizations.set(organization_ids)

                messages.success(request, f'Menu item "{title}" created successfully!')
                return redirect('organization:menu_items')

        except Exception as e:
            messages.error(request, f'Error creating menu item: {str(e)}')

    
    context = {
        'categories': categories,
        'organizations': organizations,
        'parent_items': parent_items
    }
    return render(request, 'organization/create_menu_item.html', context)


@login_required
@super_admin_required
def edit_menu_item(request, item_id):
    """Edit a menu item"""
    menu_item = get_object_or_404(MenuItem, id=item_id)
    categories = MenuCategory.objects.filter(is_active=True).order_by('order')
    organizations = Organization.objects.filter(status='active')
    parent_items = MenuItem.objects.filter(is_active=True, parent__isnull=True).exclude(id=item_id).order_by('title')
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Update menu item
                menu_item.title = request.POST.get('title')
                menu_item.category_id = request.POST.get('category')
                menu_item.parent_id = request.POST.get('parent') or None
                menu_item.url_name = request.POST.get('url_name', '')
                menu_item.url_path = request.POST.get('url_path', '')
                menu_item.icon = request.POST.get('icon', '')
                menu_item.description = request.POST.get('description', '')
                menu_item.visibility = request.POST.get('visibility', 'all')
                menu_item.order = int(request.POST.get('order', 0))
                menu_item.is_external = request.POST.get('is_external') == 'on'
                menu_item.target = request.POST.get('target', '_self')
                menu_item.is_active = request.POST.get('is_active') == 'on'
                menu_item.save()
                
                # Update organizations
                organization_ids = request.POST.getlist('organizations')
                menu_item.organizations.set(organization_ids)
                
                messages.success(request, f'Menu item "{menu_item.title}" updated successfully!')
                return redirect('organization:menu_items')
                
        except Exception as e:
            messages.error(request, f'Error updating menu item: {str(e)}')
    
    context = {
        'menu_item': menu_item,
        'categories': categories,
        'organizations': organizations,
        'parent_items': parent_items
    }
    return render(request, 'organization/edit_menu_item.html', context)


@login_required
@super_admin_required
def delete_menu_item(request, item_id):
    """Delete a menu item"""
    menu_item = get_object_or_404(MenuItem, id=item_id)
    
    if request.method == 'POST':
        try:
            title = menu_item.title
            menu_item.delete()
            messages.success(request, f'Menu item "{title}" deleted successfully!')
        except Exception as e:
            messages.error(request, f'Error deleting menu item: {str(e)}')
    
    return redirect('organization:menu_items')


@login_required
@super_admin_required
def toggle_menu_item_status(request, item_id):
    """Toggle menu item active status"""
    menu_item = get_object_or_404(MenuItem, id=item_id)
    
    try:
        menu_item.is_active = not menu_item.is_active
        menu_item.save()
        
        status = "activated" if menu_item.is_active else "deactivated"
        messages.success(request, f'Menu item "{menu_item.title}" {status} successfully!')
    except Exception as e:
        messages.error(request, f'Error updating menu item status: {str(e)}')
    
    return redirect('organization:menu_items')


def get_user_menu_items(user, organization=None):
    """Get menu items visible to the current user"""
    if user.is_super_admin:
        # Super admin sees all active menu items
        menu_items = MenuItem.objects.filter(is_active=True).select_related('category', 'parent').order_by('category__order', 'order')
    else:
        # Filter based on user role and organization
        visibility_filters = []
        
        if user.is_organization_admin:
            visibility_filters.extend(['all', 'organization_admin'])
        if user.is_employee:
            visibility_filters.extend(['all', 'employee'])
        
        menu_items = MenuItem.objects.filter(
            is_active=True,
            visibility__in=visibility_filters
        ).select_related('category', 'parent').order_by('category__order', 'order')
        
        # Filter by organization if specified
        if organization:
            # Include items that are either not organization-specific or belong to this organization
            from django.db import models
            menu_items = menu_items.filter(
                models.Q(organizations__isnull=True) | 
                models.Q(organizations=organization)
            ).distinct()
    
    # Group by category
    menu_dict = {}
    for item in menu_items:
        if item.category.name not in menu_dict:
            menu_dict[item.category.name] = {
                'category': item.category,
                'items': []
            }
        
        # Check if item is visible to user
        if item.is_visible_to_user(user, organization):
            menu_dict[item.category.name]['items'].append(item)
    
    return menu_dict


# Dynamic Table Management Views
@login_required
@organization_admin_required
def dynamic_table_config(request, table_name):
    """
    Configure dynamic table settings for the organization
    """
    try:
        table = DynamicTable.objects.get(name=table_name, is_active=True)
    except DynamicTable.DoesNotExist:
        messages.error(request, 'Table configuration not found.')
        return redirect('organization:organization_dashboard')
    
    organization = request.organization
    
    # Get all roles for this organization
    from hrm.models import EmployeeRole
    roles = EmployeeRole.objects.filter(organization=organization, is_active=True)
    
    # Get table columns
    columns = TableColumn.objects.filter(table=table, is_active=True).order_by('order')
    
    # Get role permissions for this table
    table_permissions = RoleTablePermission.objects.filter(
        organization=organization,
        table=table
    ).select_related('role')
    
    column_permissions = RoleColumnPermission.objects.filter(
        organization=organization,
        table=table
    ).select_related('role', 'column')
    
    context = {
        'organization': organization,
        'table': table,
        'columns': columns,
        'roles': roles,
        'table_permissions': table_permissions,
        'column_permissions': column_permissions,
    }
    
    return render(request, 'organization/dynamic_table_config.html', context)


@login_required
@organization_admin_required
def update_table_permissions(request, table_name):
    """
    Update table permissions for roles
    """
    if request.method == 'POST':
        try:
            with transaction.atomic():
                table = DynamicTable.objects.get(name=table_name, is_active=True)
                organization = request.organization
                
                # Update table permissions
                table_permissions_data = json.loads(request.POST.get('table_permissions', '{}'))
                
                for role_id, permissions in table_permissions_data.items():
                    try:
                        from hrm.models import EmployeeRole
                        role = EmployeeRole.objects.get(id=role_id, organization=organization)
                        
                        for perm_type, can_access in permissions.items():
                            RoleTablePermission.objects.update_or_create(
                                organization=organization,
                                role=role,
                                table=table,
                                permission_type=perm_type,
                                defaults={'can_access': can_access}
                            )
                    except EmployeeRole.DoesNotExist:
                        continue
                
                # Update column permissions
                column_permissions_data = json.loads(request.POST.get('column_permissions', '{}'))
                
                for role_id, role_permissions in column_permissions_data.items():
                    try:
                        from hrm.models import EmployeeRole
                        role = EmployeeRole.objects.get(id=role_id, organization=organization)
                        
                        for column_id, permissions in role_permissions.items():
                            try:
                                column = TableColumn.objects.get(id=column_id, table=table)
                                
                                for perm_type, perm_data in permissions.items():
                                    can_access = perm_data.get('can_access', True)
                                    column_order = perm_data.get('column_order', column.order)
                                    
                                    RoleColumnPermission.objects.update_or_create(
                                        organization=organization,
                                        role=role,
                                        table=table,
                                        column=column,
                                        permission_type=perm_type,
                                        defaults={
                                            'can_access': can_access,
                                            'column_order': column_order
                                        }
                                    )
                            except TableColumn.DoesNotExist:
                                continue
                    except EmployeeRole.DoesNotExist:
                        continue
                
                messages.success(request, 'Table permissions updated successfully!')
                
        except Exception as e:
            messages.error(request, f'Error updating permissions: {str(e)}')
    
    return redirect('organization:dynamic_table_config', table_name=table_name)


@login_required
@organization_admin_required
def setup_default_permissions(request, table_name):
    """
    Setup default permissions for all roles on a table
    """
    try:
        table = DynamicTable.objects.get(name=table_name, is_active=True)
        organization = request.organization
        
        from hrm.models import EmployeeRole
        roles = EmployeeRole.objects.filter(organization=organization, is_active=True)
        
        for role in roles:
            DynamicTableManager.setup_default_role_permissions(organization, role, table_name)
        
        messages.success(request, 'Default permissions set up successfully!')
        
    except Exception as e:
        messages.error(request, f'Error setting up permissions: {str(e)}')
    
    return redirect('organization:dynamic_table_config', table_name=table_name)


@login_required
@organization_member_required
def save_table_preferences(request, table_name):
    """
    Save user's table preferences via AJAX
    """
    if request.method == 'POST':
        try:
            organization = request.organization
            preferences = {
                'column_visibility': json.loads(request.POST.get('column_visibility', '{}')),
                'column_order': json.loads(request.POST.get('column_order', '[]')),
                'page_size': int(request.POST.get('page_size', 20)),
                'saved_filters': json.loads(request.POST.get('saved_filters', '{}'))
            }
            
            success = DynamicTableManager.save_user_table_preferences(
                request.user, organization, table_name, preferences
            )
            
            if success:
                return JsonResponse({'status': 'success', 'message': 'Preferences saved successfully!'})
            else:
                return JsonResponse({'status': 'error', 'message': 'Failed to save preferences'})
                
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})


@login_required
@organization_member_required
def get_table_preferences(request, table_name):
    """
    Get user's table preferences via AJAX
    """
    try:
        organization = request.organization
        preferences = DynamicTableManager.get_user_table_preferences(
            request.user, organization, table_name
        )
        
        return JsonResponse({'status': 'success', 'preferences': preferences})
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


@login_required
@organization_member_required
def get_table_columns(request, table_name):
    """
    Get user's accessible table columns via AJAX
    """
    try:
        organization = request.organization
        columns = DynamicTableManager.get_user_table_columns(
            request.user, organization, table_name
        )
        
        columns_data = []
        for column in columns:
            columns_data.append({
                'id': column.id,
                'field_name': column.field_name,
                'display_name': column.display_name,
                'column_type': column.column_type,
                'width': column.width,
                'is_sortable': column.is_sortable,
                'is_searchable': column.is_searchable,
                'is_filterable': column.is_filterable,
                'css_class': column.css_class,
                'order': column.order
            })
        
        return JsonResponse({'status': 'success', 'columns': columns_data})
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})