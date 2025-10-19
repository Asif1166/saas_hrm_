from django.contrib.auth import get_user_model
from organization.models import (
    DynamicTable, TableColumn, RoleTablePermission, 
    RoleColumnPermission, UserTablePreference
)
from hrm.models import EmployeeRole

User = get_user_model()


class DynamicTableManager:
    """
    Utility class for managing dynamic table configurations and permissions
    """
    
    @staticmethod
    def get_user_table_columns(user, organization, table_name, role=None):
        """
        Get columns that a user can see for a specific table based on their role
        """
        try:
            table = DynamicTable.objects.get(name=table_name, is_active=True)
        except DynamicTable.DoesNotExist:
            return []
        
        # Get user's role if not provided
        if not role:
            role = DynamicTableManager.get_user_role(user, organization)
        
        # Organization admin and super admin see all columns
        if user.is_organization_admin or user.is_super_admin:
            return TableColumn.objects.filter(table=table, is_active=True).order_by('order')
        
        if not role:
            return TableColumn.objects.filter(table=table, is_active=True, default_visible=True).order_by('order')
        
        # Get role-based column permissions
        column_permissions = RoleColumnPermission.objects.filter(
            organization=organization,
            role=role,
            table=table
        ).select_related('column')
        
        # Get user preferences
        user_preferences = UserTablePreference.objects.filter(
            user=user,
            organization=organization,
            table=table
        ).first()
        
        visible_columns = []
        
        for perm in column_permissions:
            if perm.permission_type == 'view' and perm.can_access:
                column = perm.column
                if column.is_active:
                    # Check user preferences for column visibility
                    if user_preferences and user_preferences.column_visibility:
                        column_visible = user_preferences.column_visibility.get(
                            column.field_name, column.default_visible
                        )
                    else:
                        column_visible = column.default_visible
                    
                    if column_visible:
                        visible_columns.append({
                            'column': column,
                            'custom_order': perm.column_order
                        })
        
        # If no role permissions found, return default visible columns
        if not visible_columns:
            visible_columns = [
                {'column': col, 'custom_order': col.order}
                for col in TableColumn.objects.filter(
                    table=table, is_active=True, default_visible=True
                ).order_by('order')
            ]
        
        # Sort by custom order or default order
        visible_columns.sort(key=lambda x: x['custom_order'] or x['column'].order)
        
        return [item['column'] for item in visible_columns]
    
    @staticmethod
    def get_user_role(user, organization):
        """
        Get user's role in the organization
        """
        if user.is_super_admin:
            return None  # Super admin has access to everything
        
        try:
            employee_profile = user.employee_profile
            return employee_profile.employee_role
        except:
            return None
    
    @staticmethod
    def can_user_access_table(user, organization, table_name, permission_type='view'):
        """
        Check if user can access a specific table with given permission
        """
        try:
            table = DynamicTable.objects.get(name=table_name, is_active=True)
        except DynamicTable.DoesNotExist:
            return False
        
        # Super admin has access to everything
        if user.is_super_admin:
            return True
        
        # Organization admin has access to everything in their organization
        if user.is_organization_admin:
            return True
        
        # Get user's role
        role = DynamicTableManager.get_user_role(user, organization)
        
        if not role:
            return False
        
        # Check role-based table permissions
        permission = RoleTablePermission.objects.filter(
            organization=organization,
            role=role,
            table=table,
            permission_type=permission_type
        ).first()
        
        return permission and permission.can_access
    
    @staticmethod
    def can_user_access_column(user, organization, table_name, column_field_name, permission_type='view'):
        """
        Check if user can access a specific column with given permission
        """
        try:
            table = DynamicTable.objects.get(name=table_name, is_active=True)
            column = TableColumn.objects.get(table=table, field_name=column_field_name, is_active=True)
        except (DynamicTable.DoesNotExist, TableColumn.DoesNotExist):
            return False
        
        # Super admin has access to everything
        if user.is_super_admin:
            return True
        
        # Organization admin has access to all columns in their organization
        if user.is_organization_admin:
            return True
        
        # Get user's role
        role = DynamicTableManager.get_user_role(user, organization)
        
        if not role:
            return column.default_visible
        
        # Check role-based column permissions
        permission = RoleColumnPermission.objects.filter(
            organization=organization,
            role=role,
            table=table,
            column=column,
            permission_type=permission_type
        ).first()
        
        if permission:
            return permission.can_access
        
        # Fall back to default visibility
        return column.default_visible
    
    @staticmethod
    def save_user_table_preferences(user, organization, table_name, preferences):
        """
        Save user's table preferences (column visibility, order, etc.)
        """
        try:
            table = DynamicTable.objects.get(name=table_name, is_active=True)
        except DynamicTable.DoesNotExist:
            return False
        
        user_preferences, created = UserTablePreference.objects.get_or_create(
            user=user,
            organization=organization,
            table=table,
            defaults=preferences
        )
        
        if not created:
            for key, value in preferences.items():
                setattr(user_preferences, key, value)
            user_preferences.save()
        
        return True
    
    @staticmethod
    def get_user_table_preferences(user, organization, table_name):
        """
        Get user's table preferences
        """
        try:
            table = DynamicTable.objects.get(name=table_name, is_active=True)
            preferences = UserTablePreference.objects.get(
                user=user,
                organization=organization,
                table=table
            )
            return {
                'column_visibility': preferences.column_visibility,
                'column_order': preferences.column_order,
                'page_size': preferences.page_size,
                'saved_filters': preferences.saved_filters
            }
        except (DynamicTable.DoesNotExist, UserTablePreference.DoesNotExist):
            return None
    
    @staticmethod
    def setup_default_role_permissions(organization, role, table_name):
        """
        Setup default permissions for a role on a specific table
        """
        try:
            table = DynamicTable.objects.get(name=table_name, is_active=True)
        except DynamicTable.DoesNotExist:
            return False
        
        # Create default table permissions
        table_permissions = [
            ('view', True),
            ('edit', role.name.lower() in ['admin', 'manager', 'hr']),
            ('delete', role.name.lower() in ['admin', 'hr']),
            ('export', True)
        ]
        
        for perm_type, can_access in table_permissions:
            RoleTablePermission.objects.get_or_create(
                organization=organization,
                role=role,
                table=table,
                permission_type=perm_type,
                defaults={'can_access': can_access}
            )
        
        # Create default column permissions
        columns = TableColumn.objects.filter(table=table, is_active=True)
        
        for column in columns:
            # Default permissions based on column type and role
            can_view = True
            can_edit = role.name.lower() in ['admin', 'manager', 'hr']
            can_hide = role.name.lower() in ['admin', 'hr']
            
            # Sensitive columns (salary, personal info) - restrict access
            sensitive_fields = ['basic_salary', 'gross_salary', 'net_salary', 'personal_email', 'personal_phone', 'current_address']
            if column.field_name in sensitive_fields:
                can_view = role.name.lower() in ['admin', 'hr', 'manager']
                can_edit = role.name.lower() in ['admin', 'hr']
            
            permissions = [
                ('view', can_view),
                ('edit', can_edit),
                ('hide', can_hide)
            ]
            
            for perm_type, can_access in permissions:
                RoleColumnPermission.objects.get_or_create(
                    organization=organization,
                    role=role,
                    table=table,
                    column=column,
                    permission_type=perm_type,
                    defaults={
                        'can_access': can_access,
                        'column_order': column.order
                    }
                )
        
        return True
