from django import template
from django.db import models
from django.utils.safestring import mark_safe
from ..models import MenuItem, Organization
import builtins

register = template.Library()


@register.simple_tag
def get_user_menu_items(user, organization=None):
    """Return menu items for template variable"""
    if user.is_super_admin:
        menu_items = MenuItem.objects.filter(is_active=True).select_related('category', 'parent').order_by('category__order', 'order')
    else:
        visibility_filters = []
        if user.is_organization_admin:
            visibility_filters.extend(['all', 'organization_admin'])
        if user.is_employee:
            visibility_filters.extend(['all', 'employee'])
        
        menu_items = MenuItem.objects.filter(
            is_active=True,
            visibility__in=visibility_filters
        ).select_related('category', 'parent').order_by('category__order', 'order')
        
        if organization:
            from django.db import models
            menu_items = menu_items.filter(
                models.Q(organizations__isnull=True) | 
                models.Q(organizations=organization)
            ).distinct()
    
    menu_dict = {}
    for item in menu_items:
        if item.category.name not in menu_dict:
            menu_dict[item.category.name] = {
                'category': item.category,
                'items': []
            }
        if item.is_visible_to_user(user, organization):
            menu_dict[item.category.name]['items'].append(item)
    
    return menu_dict


@register.filter
def getattr(obj, attr_name):
    """
    Get attribute from object, supporting nested attributes (e.g., 'user.email')
    """
    try:
        attrs = attr_name.split('.')
        value = obj
        for attr in attrs:
            value = builtins.getattr(value, attr, None)
            if value is None:
                return None
        return value
    except (AttributeError, TypeError):
        return None


@register.filter
def has_permission(user, permission_string):
    """
    Check if user has specific permission
    Format: 'table_name:permission_type' or 'table_name:column_name:permission_type'
    """
    try:
        parts = permission_string.split(':')
        if len(parts) == 2:
            table_name, permission_type = parts
            # Check table permission
            from organization.utils import DynamicTableManager
            return DynamicTableManager.can_user_access_table(
                user, user.organization, table_name, permission_type
            )
        elif len(parts) == 3:
            table_name, column_name, permission_type = parts
            # Check column permission
            from organization.utils import DynamicTableManager
            return DynamicTableManager.can_user_access_column(
                user, user.organization, table_name, column_name, permission_type
            )
    except Exception:
        return False
    return False


@register.filter
def get_user_table_columns(user, table_name):
    """
    Get columns that user can see for a specific table
    """
    try:
        from organization.utils import DynamicTableManager
        return DynamicTableManager.get_user_table_columns(
            user, user.organization, table_name
        )
    except Exception:
        return []


@register.filter
def get_field_value(obj, field_name):
    """
    Get field value from object with proper formatting
    """
    try:
        value = getattr(obj, field_name, None)
        
        # Handle foreign key relationships
        if hasattr(value, 'name'):
            return value.name
        elif hasattr(value, 'username'):
            return value.username
        elif hasattr(value, 'email'):
            return value.email
        
        return value
    except Exception:
        return None


@register.filter
def split(value, delimiter=','):
    """
    Split a string by delimiter
    """
    try:
        return value.split(delimiter)
    except (AttributeError, TypeError):
        return []


@register.filter
def lookup(dictionary, key):
    """
    Lookup a key in a dictionary
    """
    try:
        if hasattr(dictionary, 'get'):
            return dictionary.get(key)
        elif hasattr(dictionary, '__getitem__'):
            return dictionary[key]
        return None
    except (KeyError, TypeError):
        return None


@register.simple_tag
def get_all_organizations():
    """
    Returns all organizations for global template use
    """
    return Organization.objects.all()