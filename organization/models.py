from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator

User = get_user_model()


class Organization(models.Model):
    """
    Organization model for multi-tenant SaaS
    Each organization is a separate tenant with its own data
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
    ]
    
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(blank=True, null=True)
    
    # Contact Information
    email = models.EmailField()
    phone = models.CharField(
        max_length=15,
        validators=[RegexValidator(regex=r'^\+?1?\d{9,15}$')],
        blank=True,
        null=True
    )
    website = models.URLField(blank=True, null=True)
    
    # Address
    address_line1 = models.CharField(max_length=255, blank=True, null=True)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    
    # Organization Settings
    logo = models.ImageField(upload_to='organization_logos/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Subscription & Billing
    subscription_plan = models.CharField(max_length=50, default='basic')
    max_employees = models.PositiveIntegerField(default=10)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_organizations')
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    @property
    def admin_users(self):
        """Get all admin users for this organization"""
        return User.objects.filter(
            organizationmembership__organization=self,
            organizationmembership__is_admin=True
        )
    
    @property
    def employee_count(self):
        """Get total number of employees in this organization"""
        return User.objects.filter(
            organizationmembership__organization=self,
            role='employee'
        ).count()


class OrganizationMembership(models.Model):
    """
    Model to manage user-organization relationships
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organizationmembership')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='members')
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'organization']
        ordering = ['-joined_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.organization.name}"


class MenuCategory(models.Model):
    """
    Menu categories for organizing menu items
    """
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, blank=True, null=True, help_text="Icon class (e.g., 'ri-dashboard-line')")
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = 'Menu Categories'
    
    def __str__(self):
        return self.name


class MenuItem(models.Model):
    """
    Individual menu items for dynamic sidebar
    """
    TARGET_CHOICES = [
        ('_self', 'Same Window'),
        ('_blank', 'New Window'),
    ]
    
    VISIBILITY_CHOICES = [
        ('all', 'All Users'),
        ('super_admin', 'Super Admin Only'),
        ('organization_admin', 'Organization Admin Only'),
        ('employee', 'Employee Only'),
        ('custom', 'Custom Permissions'),
    ]
    
    # Basic Information
    title = models.CharField(max_length=100)
    url_name = models.CharField(max_length=200, blank=True, null=True, help_text="Django URL name")
    url_path = models.CharField(max_length=200, blank=True, null=True, help_text="Direct URL path")
    icon = models.CharField(max_length=50, blank=True, null=True, help_text="Icon class (e.g., 'ri-user-line')")
    description = models.TextField(blank=True, null=True)
    
    # Menu Structure
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    category = models.ForeignKey(MenuCategory, on_delete=models.CASCADE, related_name='menu_items')
    order = models.PositiveIntegerField(default=0)
    
    # Visibility and Permissions
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='all')
    required_permissions = models.JSONField(default=list, blank=True, help_text="List of required permissions")
    organizations = models.ManyToManyField(Organization, blank=True, help_text="Organizations that can see this menu")
    
    # Link Properties
    target = models.CharField(max_length=10, choices=TARGET_CHOICES, default='_self')
    is_external = models.BooleanField(default=False, help_text="External link")
    
    # Status
    is_active = models.BooleanField(default=True)
    is_divider = models.BooleanField(default=False, help_text="Show as divider line")
    
    class Meta:
        ordering = ['category__order', 'order', 'title']
    
    def __str__(self):
        return f"{self.category.name} - {self.title}"
    
    @property
    def has_children(self):
        return self.children.filter(is_active=True).exists()
    
    @property
    def get_url(self):
        """Get the URL for this menu item"""
        if self.url_name:
            return f"url '{self.url_name}'"
        elif self.url_path:
            return f"'{self.url_path}'"
        return '#'
    
    def is_visible_to_user(self, user, organization=None):
        """Check if this menu item is visible to the given user"""
        if not self.is_active:
            return False
        
        # Check visibility based on user role
        if self.visibility == 'super_admin' and not user.is_super_admin:
            return False
        elif self.visibility == 'organization_admin' and not user.is_organization_admin:
            return False
        elif self.visibility == 'employee' and not user.is_employee:
            return False
        
        # Check organization-specific visibility
        if self.organizations.exists() and organization:
            if not self.organizations.filter(id=organization.id).exists():
                return False
        
        # Check custom permissions
        if self.visibility == 'custom' and self.required_permissions:
            # Add custom permission logic here
            pass
        
        return True


class UserMenuPermission(models.Model):
    """
    Custom menu permissions for specific users
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='menu_permissions')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name='user_permissions')
    can_view = models.BooleanField(default=True)
    can_edit = models.BooleanField(default=False)
    granted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='granted_permissions')
    granted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'menu_item']
    
    def __str__(self):
        return f"{self.user.username} - {self.menu_item.title}"


class DynamicTable(models.Model):
    """
    Model to define dynamic tables in the system
    """
    TABLE_TYPES = [
        ('employee_list', 'Employee List'),
        ('attendance_list', 'Attendance List'),
        ('leave_list', 'Leave List'),
        ('payroll_list', 'Payroll List'),
        ('custom', 'Custom Table'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    table_type = models.CharField(max_length=50, choices=TABLE_TYPES)
    display_name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.display_name


class TableColumn(models.Model):
    """
    Model to define columns for dynamic tables
    """
    COLUMN_TYPES = [
        ('text', 'Text'),
        ('number', 'Number'),
        ('date', 'Date'),
        ('datetime', 'DateTime'),
        ('boolean', 'Boolean'),
        ('image', 'Image'),
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('url', 'URL'),
        ('json', 'JSON'),
        ('foreign_key', 'Foreign Key'),
    ]
    
    table = models.ForeignKey(DynamicTable, on_delete=models.CASCADE, related_name='columns')
    field_name = models.CharField(max_length=100, help_text="Model field name")
    display_name = models.CharField(max_length=200, help_text="Column display name")
    column_type = models.CharField(max_length=20, choices=COLUMN_TYPES, default='text')
    width = models.CharField(max_length=10, blank=True, null=True, help_text="Column width (e.g., '150px')")
    is_sortable = models.BooleanField(default=True)
    is_searchable = models.BooleanField(default=True)
    is_filterable = models.BooleanField(default=False)
    default_visible = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    css_class = models.CharField(max_length=100, blank=True, null=True)
    help_text = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['order', 'field_name']
        unique_together = ['table', 'field_name']
    
    def __str__(self):
        return f"{self.table.display_name} - {self.display_name}"


class RoleTablePermission(models.Model):
    """
    Model to define role-based permissions for table columns
    """
    PERMISSION_TYPES = [
        ('view', 'View'),
        ('edit', 'Edit'),
        ('delete', 'Delete'),
        ('export', 'Export'),
    ]
    
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='table_permissions')
    role = models.ForeignKey('hrm.EmployeeRole', on_delete=models.CASCADE, related_name='table_permissions')
    table = models.ForeignKey(DynamicTable, on_delete=models.CASCADE, related_name='role_permissions')
    permission_type = models.CharField(max_length=20, choices=PERMISSION_TYPES, default='view')
    can_access = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['organization', 'role', 'table', 'permission_type']
        ordering = ['role__name', 'table__name']
    
    def __str__(self):
        return f"{self.organization.name} - {self.role.name} - {self.table.display_name} - {self.permission_type}"


class RoleColumnPermission(models.Model):
    """
    Model to define role-based permissions for individual table columns
    """
    PERMISSION_TYPES = [
        ('view', 'View'),
        ('edit', 'Edit'),
        ('hide', 'Hide'),
    ]
    
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='column_permissions')
    role = models.ForeignKey('hrm.EmployeeRole', on_delete=models.CASCADE, related_name='column_permissions')
    table = models.ForeignKey(DynamicTable, on_delete=models.CASCADE, related_name='column_permissions')
    column = models.ForeignKey(TableColumn, on_delete=models.CASCADE, related_name='role_permissions')
    permission_type = models.CharField(max_length=20, choices=PERMISSION_TYPES, default='view')
    can_access = models.BooleanField(default=True)
    column_order = models.PositiveIntegerField(default=0, help_text="Custom order for this role")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['organization', 'role', 'table', 'column', 'permission_type']
        ordering = ['role__name', 'column_order']
    
    def __str__(self):
        return f"{self.organization.name} - {self.role.name} - {self.column.display_name} - {self.permission_type}"


class UserTablePreference(models.Model):
    """
    Model to store user-specific table preferences (column visibility, order, etc.)
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='table_preferences')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='user_table_preferences')
    table = models.ForeignKey(DynamicTable, on_delete=models.CASCADE, related_name='user_preferences')
    column_visibility = models.JSONField(default=dict, help_text="Column visibility settings")
    column_order = models.JSONField(default=list, help_text="Custom column order")
    page_size = models.PositiveIntegerField(default=20)
    saved_filters = models.JSONField(default=dict, help_text="Saved filter configurations")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'organization', 'table']
    
    def __str__(self):
        return f"{self.user.username} - {self.table.display_name}"
