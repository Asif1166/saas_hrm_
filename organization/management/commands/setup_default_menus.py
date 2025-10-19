from django.core.management.base import BaseCommand
from organization.models import MenuCategory, MenuItem, Organization


class Command(BaseCommand):
    help = 'Setup default menu items for the system'

    def handle(self, *args, **options):
        self.stdout.write('Setting up default menu items...')
        
        # Create menu categories
        dashboard_category, created = MenuCategory.objects.get_or_create(
            name='Dashboard',
            defaults={'icon': 'fa-solid fa-tachometer-alt', 'order': 1}
        )
        if created:
            self.stdout.write(f'Created menu category: {dashboard_category.name}')
        
        hrm_category, created = MenuCategory.objects.get_or_create(
            name='Human Resources',
            defaults={'icon': 'fa-solid fa-user-tie', 'order': 2}
        )
        if created:
            self.stdout.write(f'Created menu category: {hrm_category.name}')
        
        admin_category, created = MenuCategory.objects.get_or_create(
            name='Administration',
            defaults={'icon': 'fa-solid fa-cogs', 'order': 3}
        )
        if created:
            self.stdout.write(f'Created menu category: {admin_category.name}')
        
        # Create dashboard menu items
        dashboard_items = [
            {
                'title': 'Super Admin Dashboard',
                'url_name': 'super_admin:dashboard',
                'icon': 'fa-solid fa-tachometer-alt',
                'visibility': 'super_admin',
                'order': 1
            },
            {
                'title': 'Organization Dashboard',
                'url_name': 'organization:dashboard',
                'icon': 'fa-solid fa-building',
                'visibility': 'organization_admin',
                'order': 2
            },
            {
                'title': 'Employee Dashboard',
                'url_name': 'hrm:employee_dashboard',
                'icon': 'fa-solid fa-user',
                'visibility': 'employee',
                'order': 3
            }
        ]
        
        for item_data in dashboard_items:
            item, created = MenuItem.objects.get_or_create(
                title=item_data['title'],
                category=dashboard_category,
                defaults=item_data
            )
            if created:
                self.stdout.write(f'Created menu item: {item.title}')
        
        # Create HRM menu items
        hrm_items = [
            {
                'title': 'Employee Management',
                'icon': 'fa-solid fa-users',
                'visibility': 'organization_admin',
                'order': 1,
                'children': [
                    {
                        'title': 'Add Employee',
                        'url_name': 'hrm:create_employee',
                        'icon': 'fa-solid fa-user-plus',
                        'visibility': 'organization_admin',
                        'order': 1
                    },
                    {
                        'title': 'All Employees',
                        'url_name': 'hrm:employee_list',
                        'icon': 'fa-solid fa-list',
                        'visibility': 'organization_admin',
                        'order': 2
                    },
                    {
                        'title': 'Attendance',
                        'url_name': 'hrm:attendance_list',
                        'icon': 'fa-solid fa-calendar-check',
                        'visibility': 'organization_admin',
                        'order': 3
                    }
                ]
            },
            {
                'title': 'Organizational Structure',
                'icon': 'fa-solid fa-sitemap',
                'visibility': 'organization_admin',
                'order': 2,
                'children': [
                    {
                        'title': 'Branches',
                        'url_name': 'hrm:branch_list',
                        'icon': 'fa-solid fa-building',
                        'visibility': 'organization_admin',
                        'order': 1
                    },
                    {
                        'title': 'Departments',
                        'url_name': 'hrm:department_list',
                        'icon': 'fa-solid fa-sitemap',
                        'visibility': 'organization_admin',
                        'order': 2
                    },
                    {
                        'title': 'Designations',
                        'url_name': 'hrm:designation_list',
                        'icon': 'fa-solid fa-id-badge',
                        'visibility': 'organization_admin',
                        'order': 3
                    },
                    {
                        'title': 'Employee Roles',
                        'url_name': 'hrm:employee_role_list',
                        'icon': 'fa-solid fa-user-tag',
                        'visibility': 'organization_admin',
                        'order': 4
                    }
                ]
            }
        ]
        
        for item_data in hrm_items:
            children = item_data.pop('children', [])
            item, created = MenuItem.objects.get_or_create(
                title=item_data['title'],
                category=hrm_category,
                defaults=item_data
            )
            if created:
                self.stdout.write(f'Created menu item: {item.title}')
            
            # Create children
            for child_data in children:
                child, created = MenuItem.objects.get_or_create(
                    title=child_data['title'],
                    category=hrm_category,
                    parent=item,
                    defaults=child_data
                )
                if created:
                    self.stdout.write(f'Created menu item: {child.title}')
        
        # Create admin menu items
        admin_items = [
            {
                'title': 'Menu Management',
                'icon': 'fa-solid fa-bars',
                'visibility': 'super_admin',
                'order': 1,
                'children': [
                    {
                        'title': 'Menu Categories',
                        'url_name': 'organization:menu_categories',
                        'icon': 'fa-solid fa-folder',
                        'visibility': 'super_admin',
                        'order': 1
                    },
                    {
                        'title': 'Menu Items',
                        'url_name': 'organization:menu_items',
                        'icon': 'fa-solid fa-list',
                        'visibility': 'super_admin',
                        'order': 2
                    }
                ]
            },
            {
                'title': 'Organization Management',
                'icon': 'fa-solid fa-building',
                'visibility': 'super_admin',
                'order': 2,
                'children': [
                    {
                        'title': 'All Organizations',
                        'url_name': 'super_admin:organization_list',
                        'icon': 'fa-solid fa-list',
                        'visibility': 'super_admin',
                        'order': 1
                    },
                    {
                        'title': 'Create Organization',
                        'url_name': 'super_admin:create_organization',
                        'icon': 'fa-solid fa-plus',
                        'visibility': 'super_admin',
                        'order': 2
                    }
                ]
            }
        ]
        
        for item_data in admin_items:
            children = item_data.pop('children', [])
            item, created = MenuItem.objects.get_or_create(
                title=item_data['title'],
                category=admin_category,
                defaults=item_data
            )
            if created:
                self.stdout.write(f'Created menu item: {item.title}')
            
            # Create children
            for child_data in children:
                child, created = MenuItem.objects.get_or_create(
                    title=child_data['title'],
                    category=admin_category,
                    parent=item,
                    defaults=child_data
                )
                if created:
                    self.stdout.write(f'Created menu item: {child.title}')
        
        self.stdout.write(
            self.style.SUCCESS('Successfully set up default menu items!')
        )
