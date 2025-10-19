from django.contrib import admin
from .models import Organization, OrganizationMembership, MenuCategory, MenuItem, UserMenuPermission


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'status', 'subscription_plan', 'max_employees', 'created_at')
    list_filter = ('status', 'subscription_plan', 'created_at')
    search_fields = ('name', 'email', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone', 'website')
        }),
        ('Address', {
            'fields': ('address_line1', 'address_line2', 'city', 'state', 'postal_code', 'country'),
            'classes': ('collapse',)
        }),
        ('Settings', {
            'fields': ('logo', 'status', 'subscription_plan', 'max_employees')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )


@admin.register(OrganizationMembership)
class OrganizationMembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'organization', 'is_admin', 'is_active', 'joined_at')
    list_filter = ('is_admin', 'is_active', 'joined_at', 'organization')
    search_fields = ('user__username', 'user__email', 'organization__name')
    readonly_fields = ('joined_at',)
    
    fieldsets = (
        ('Membership Information', {
            'fields': ('user', 'organization', 'is_admin', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('joined_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(MenuCategory)
class MenuCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon', 'order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)
    ordering = ('order', 'name')


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'parent', 'visibility', 'order', 'is_active')
    list_filter = ('category', 'visibility', 'is_active', 'is_external')
    search_fields = ('title', 'url_name', 'url_path')
    ordering = ('category__order', 'order', 'title')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'category', 'parent', 'order')
        }),
        ('Link Configuration', {
            'fields': ('url_name', 'url_path', 'icon', 'description', 'target', 'is_external')
        }),
        ('Visibility & Permissions', {
            'fields': ('visibility', 'required_permissions', 'organizations')
        }),
        ('Status', {
            'fields': ('is_active', 'is_divider')
        }),
    )
    
    filter_horizontal = ('organizations',)


@admin.register(UserMenuPermission)
class UserMenuPermissionAdmin(admin.ModelAdmin):
    list_display = ('user', 'menu_item', 'can_view', 'can_edit', 'granted_at')
    list_filter = ('can_view', 'can_edit', 'granted_at')
    search_fields = ('user__username', 'menu_item__title')
    readonly_fields = ('granted_at',)


# Note: Additional models like DynamicTable, TableColumn, RoleTablePermission,
# RoleColumnPermission, UserTablePreference can also be registered here similarly.
from .models import DynamicTable, TableColumn, RoleTablePermission, RoleColumnPermission, UserTablePreference


admin.site.register(DynamicTable)


admin.site.register(TableColumn)

admin.site.register(RoleTablePermission)


admin.site.register(RoleColumnPermission)

admin.site.register(UserTablePreference)
