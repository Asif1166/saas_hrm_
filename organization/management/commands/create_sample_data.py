from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from organization.models import (
    Organization, OrganizationMembership, MenuCategory, MenuItem,
    DynamicTable, TableColumn, RoleTablePermission, RoleColumnPermission
)
from hrm.models import Branch, Department, Designation, EmployeeRole, Employee
from datetime import date, timedelta
import random

User = get_user_model()


class Command(BaseCommand):
    help = 'Create sample data for testing dynamic table implementation'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample data for dynamic table testing...')
        
        with transaction.atomic():
            # Create super admin user
            super_admin = self.create_super_admin()
            
            # Create menu categories and items
            self.create_menu_structure()
            
            # Create sample organizations
            organizations = self.create_sample_organizations(super_admin)
            
            # Create dynamic table configurations
            self.setup_dynamic_tables()
            
            # Create HRM data for each organization
            for org in organizations:
                self.create_organization_data(org)
            
            self.stdout.write(
                self.style.SUCCESS('Successfully created sample data!')
            )
    
    def create_super_admin(self):
        """Create super admin user"""
        super_admin, created = User.objects.get_or_create(
            username='superadmin',
            defaults={
                'email': 'superadmin@example.com',
                'first_name': 'Super',
                'last_name': 'Admin',
                'role': 'super_admin',
                'is_active': True,
                'is_staff': True,
                'is_superuser': True
            }
        )
        
        if created:
            super_admin.set_password('admin123')
            super_admin.save()
            self.stdout.write(f'Created super admin: {super_admin.username}')
        
        return super_admin
    
    def create_menu_structure(self):
        """Create menu categories and items"""
        # Create menu categories
        categories = [
            {'name': 'Dashboard', 'icon': 'ri-dashboard-line', 'order': 1},
            {'name': 'HR Management', 'icon': 'ri-team-line', 'order': 2},
            {'name': 'Employee Management', 'icon': 'ri-user-line', 'order': 3},
            {'name': 'Payroll', 'icon': 'ri-money-dollar-circle-line', 'order': 4},
            {'name': 'Reports', 'icon': 'ri-bar-chart-line', 'order': 5},
            {'name': 'Settings', 'icon': 'ri-settings-line', 'order': 6},
        ]
        
        created_categories = {}
        for cat_data in categories:
            category, created = MenuCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults={
                    'icon': cat_data['icon'],
                    'order': cat_data['order'],
                    'is_active': True
                }
            )
            created_categories[cat_data['name']] = category
            if created:
                self.stdout.write(f'Created menu category: {category.name}')
        
        # Create menu items
        menu_items = [
            # Dashboard
            {'title': 'Dashboard', 'url_name': 'organization:dashboard', 'icon': 'ri-dashboard-line', 'category': 'Dashboard', 'visibility': 'all', 'order': 1},
            
            # HR Management
            {'title': 'HR Dashboard', 'url_name': 'hrm:dashboard', 'icon': 'ri-dashboard-line', 'category': 'HR Management', 'visibility': 'organization_admin', 'order': 1},
            {'title': 'Branches', 'url_name': 'hrm:branch_list', 'icon': 'ri-building-line', 'category': 'HR Management', 'visibility': 'organization_admin', 'order': 2},
            {'title': 'Departments', 'url_name': 'hrm:department_list', 'icon': 'ri-building-2-line', 'category': 'HR Management', 'visibility': 'organization_admin', 'order': 3},
            {'title': 'Designations', 'url_name': 'hrm:designation_list', 'icon': 'ri-award-line', 'category': 'HR Management', 'visibility': 'organization_admin', 'order': 4},
            {'title': 'Employee Roles', 'url_name': 'hrm:employee_role_list', 'icon': 'ri-shield-user-line', 'category': 'HR Management', 'visibility': 'organization_admin', 'order': 5},
            
            # Employee Management
            {'title': 'All Employees', 'url_name': 'hrm:employee_list', 'icon': 'ri-team-line', 'category': 'Employee Management', 'visibility': 'all', 'order': 1},
            {'title': 'Add Employee', 'url_name': 'hrm:create_employee', 'icon': 'ri-user-add-line', 'category': 'Employee Management', 'visibility': 'organization_admin', 'order': 2},
            {'title': 'Attendance', 'url_name': 'hrm:attendance_list', 'icon': 'ri-time-line', 'category': 'Employee Management', 'visibility': 'all', 'order': 3},
            {'title': 'Leave Requests', 'url_name': 'hrm:leave_list', 'icon': 'ri-calendar-line', 'category': 'Employee Management', 'visibility': 'all', 'order': 4},
            {'title': 'My Profile', 'url_name': 'hrm:employee_dashboard', 'icon': 'ri-user-line', 'category': 'Employee Management', 'visibility': 'employee', 'order': 5},
            
            # Payroll
            {'title': 'Payroll Dashboard', 'url_name': 'payroll:dashboard', 'icon': 'ri-money-dollar-circle-line', 'category': 'Payroll', 'visibility': 'organization_admin', 'order': 1},
            {'title': 'Salary Management', 'url_name': 'payroll:salary_list', 'icon': 'ri-money-dollar-box-line', 'category': 'Payroll', 'visibility': 'organization_admin', 'order': 2},
            
            # Reports
            {'title': 'Employee Reports', 'url_name': 'reports:employee_reports', 'icon': 'ri-file-chart-line', 'category': 'Reports', 'visibility': 'organization_admin', 'order': 1},
            {'title': 'Attendance Reports', 'url_name': 'reports:attendance_reports', 'icon': 'ri-file-list-line', 'category': 'Reports', 'visibility': 'all', 'order': 2},
            
            # Settings
            {'title': 'Organization Settings', 'url_name': 'organization:settings', 'icon': 'ri-settings-3-line', 'category': 'Settings', 'visibility': 'organization_admin', 'order': 1},
            {'title': 'Table Configuration', 'url_name': 'organization:dynamic_table_config', 'icon': 'ri-table-line', 'category': 'Settings', 'visibility': 'organization_admin', 'order': 2},
        ]
        
        for item_data in menu_items:
            menu_item, created = MenuItem.objects.get_or_create(
                title=item_data['title'],
                defaults={
                    'category': created_categories[item_data['category']],
                    'url_name': item_data['url_name'],
                    'icon': item_data['icon'],
                    'visibility': item_data['visibility'],
                    'order': item_data['order'],
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(f'Created menu item: {menu_item.title}')
    
    def create_sample_organizations(self, super_admin):
        """Create sample organizations"""
        organizations = []
        
        org_data = [
            {
                'name': 'TechCorp Solutions',
                'email': 'admin@techcorp.com',
                'phone': '+1-555-0101',
                'website': 'https://techcorp.com',
                'city': 'San Francisco',
                'state': 'California',
                'country': 'USA',
                'subscription_plan': 'premium',
                'max_employees': 100
            },
            {
                'name': 'Global Manufacturing Ltd',
                'email': 'hr@globalmfg.com',
                'phone': '+1-555-0202',
                'website': 'https://globalmfg.com',
                'city': 'Detroit',
                'state': 'Michigan',
                'country': 'USA',
                'subscription_plan': 'enterprise',
                'max_employees': 500
            },
            {
                'name': 'Creative Agency Inc',
                'email': 'info@creativeagency.com',
                'phone': '+1-555-0303',
                'website': 'https://creativeagency.com',
                'city': 'New York',
                'state': 'New York',
                'country': 'USA',
                'subscription_plan': 'basic',
                'max_employees': 50
            }
        ]
        
        for i, org_info in enumerate(org_data):
            org, created = Organization.objects.get_or_create(
                name=org_info['name'],
                defaults={
                    'slug': f'org-{i+1}',
                    'email': org_info['email'],
                    'phone': org_info['phone'],
                    'website': org_info['website'],
                    'city': org_info['city'],
                    'state': org_info['state'],
                    'country': org_info['country'],
                    'subscription_plan': org_info['subscription_plan'],
                    'max_employees': org_info['max_employees'],
                    'created_by': super_admin
                }
            )
            
            if created:
                # Create organization admin user
                admin_username = f'admin_{org.slug}'
                admin_user, created = User.objects.get_or_create(
                    username=admin_username,
                    defaults={
                        'email': org_info['email'],
                        'first_name': 'Organization',
                        'last_name': 'Admin',
                        'role': 'organization_admin',
                        'is_active': True
                    }
                )
                
                if created:
                    admin_user.set_password('admin123')
                    admin_user.save()
                
                # Create organization membership
                OrganizationMembership.objects.get_or_create(
                    user=admin_user,
                    organization=org,
                    defaults={
                        'is_admin': True,
                        'is_active': True
                    }
                )
                
                self.stdout.write(f'Created organization: {org.name}')
                organizations.append(org)
        
        return organizations
    
    def setup_dynamic_tables(self):
        """Setup dynamic table configurations"""
        # Create employee list table if not exists
        employee_table, created = DynamicTable.objects.get_or_create(
            name='employee_list',
            defaults={
                'table_type': 'employee_list',
                'display_name': 'Employee List',
                'description': 'Dynamic employee list with role-based column permissions',
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(f'Created table: {employee_table.display_name}')
        
        # Create columns if not exists
        employee_columns = [
            {'field_name': 'id', 'display_name': 'ID', 'column_type': 'number', 'order': 1, 'is_sortable': True, 'default_visible': True, 'width': '60px'},
            {'field_name': 'employee_id', 'display_name': 'Employee ID', 'column_type': 'text', 'order': 2, 'is_sortable': True, 'default_visible': True, 'width': '120px'},
            {'field_name': 'profile_picture', 'display_name': 'Photo', 'column_type': 'image', 'order': 3, 'is_sortable': False, 'default_visible': True, 'width': '80px'},
            {'field_name': 'full_name', 'display_name': 'Name', 'column_type': 'text', 'order': 4, 'is_sortable': True, 'default_visible': True, 'width': '200px'},
            {'field_name': 'department', 'display_name': 'Department', 'column_type': 'foreign_key', 'order': 5, 'is_sortable': True, 'default_visible': True, 'width': '150px', 'is_filterable': True},
            {'field_name': 'designation', 'display_name': 'Designation', 'column_type': 'foreign_key', 'order': 6, 'is_sortable': True, 'default_visible': True, 'width': '150px', 'is_filterable': True},
            {'field_name': 'employee_role', 'display_name': 'Role', 'column_type': 'foreign_key', 'order': 7, 'is_sortable': True, 'default_visible': True, 'width': '120px', 'is_filterable': True},
            {'field_name': 'personal_phone', 'display_name': 'Phone', 'column_type': 'phone', 'order': 8, 'is_sortable': False, 'default_visible': True, 'width': '130px'},
            {'field_name': 'user.email', 'display_name': 'Email', 'column_type': 'email', 'order': 9, 'is_sortable': True, 'default_visible': True, 'width': '200px'},
            {'field_name': 'current_address', 'display_name': 'Address', 'column_type': 'text', 'order': 10, 'is_sortable': False, 'default_visible': False, 'width': '250px'},
            {'field_name': 'employment_status', 'display_name': 'Status', 'column_type': 'text', 'order': 11, 'is_sortable': True, 'default_visible': True, 'width': '120px', 'is_filterable': True},
            {'field_name': 'hire_date', 'display_name': 'Hire Date', 'column_type': 'date', 'order': 12, 'is_sortable': True, 'default_visible': False, 'width': '120px'},
            {'field_name': 'basic_salary', 'display_name': 'Basic Salary', 'column_type': 'number', 'order': 13, 'is_sortable': True, 'default_visible': False, 'width': '120px'},
            {'field_name': 'branch', 'display_name': 'Branch', 'column_type': 'foreign_key', 'order': 14, 'is_sortable': True, 'default_visible': False, 'width': '120px', 'is_filterable': True},
            {'field_name': 'reporting_manager', 'display_name': 'Manager', 'column_type': 'foreign_key', 'order': 15, 'is_sortable': True, 'default_visible': False, 'width': '150px'},
        ]
        
        for col_data in employee_columns:
            column, created = TableColumn.objects.get_or_create(
                table=employee_table,
                field_name=col_data['field_name'],
                defaults={
                    'display_name': col_data['display_name'],
                    'column_type': col_data['column_type'],
                    'order': col_data['order'],
                    'is_sortable': col_data['is_sortable'],
                    'default_visible': col_data['default_visible'],
                    'width': col_data.get('width', ''),
                    'is_filterable': col_data.get('is_filterable', False),
                    'is_active': True
                }
            )
            
            if created:
                self.stdout.write(f'  Created column: {column.display_name}')
    
    def create_organization_data(self, organization):
        """Create HRM data for organization"""
        self.stdout.write(f'Creating data for {organization.name}...')
        
        # Create branches
        branches = []
        branch_names = ['Main Office', 'Branch Office', 'Remote Office']
        for i, branch_name in enumerate(branch_names):
            branch, created = Branch.objects.get_or_create(
                organization=organization,
                code=f'BR{i+1:03d}',
                defaults={
                    'name': branch_name,
                    'city': organization.city,
                    'state': organization.state,
                    'country': organization.country,
                    'is_active': True
                }
            )
            branches.append(branch)
        
        # Create departments
        departments = []
        dept_names = ['Human Resources', 'Information Technology', 'Finance', 'Marketing', 'Operations']
        for i, dept_name in enumerate(dept_names):
            department, created = Department.objects.get_or_create(
                organization=organization,
                code=f'DEP{i+1:03d}',
                defaults={
                    'name': dept_name,
                    'branch': branches[i % len(branches)],
                    'is_active': True
                }
            )
            departments.append(department)
        
        # Create designations
        designations = []
        designation_data = [
            {'name': 'Manager', 'level': 5},
            {'name': 'Senior Executive', 'level': 4},
            {'name': 'Executive', 'level': 3},
            {'name': 'Associate', 'level': 2},
            {'name': 'Trainee', 'level': 1},
        ]
        
        for i, desig_data in enumerate(designation_data):
            designation, created = Designation.objects.get_or_create(
                organization=organization,
                code=f'DES{i+1:03d}',
                defaults={
                    'name': desig_data['name'],
                    'level': desig_data['level'],
                    'department': departments[i % len(departments)],
                    'is_active': True
                }
            )
            designations.append(designation)
        
        # Create employee roles
        roles = []
        role_data = [
            {'name': 'HR Manager', 'permissions': {'employee_view': True, 'employee_edit': True, 'salary_view': True}},
            {'name': 'Department Manager', 'permissions': {'employee_view': True, 'employee_edit': False, 'salary_view': False}},
            {'name': 'Team Lead', 'permissions': {'employee_view': True, 'employee_edit': False, 'salary_view': False}},
            {'name': 'Employee', 'permissions': {'employee_view': False, 'employee_edit': False, 'salary_view': False}},
        ]
        
        for i, role_data_item in enumerate(role_data):
            role, created = EmployeeRole.objects.get_or_create(
                organization=organization,
                code=f'ROL{i+1:03d}',
                defaults={
                    'name': role_data_item['name'],
                    'permissions': role_data_item['permissions'],
                    'is_active': True
                }
            )
            roles.append(role)
        
        # Setup role permissions for dynamic tables
        self.setup_role_permissions(organization, roles)
        
        # Create employees
        self.create_sample_employees(organization, branches, departments, designations, roles)
    
    def setup_role_permissions(self, organization, roles):
        """Setup role permissions for dynamic tables"""
        try:
            table = DynamicTable.objects.get(name='employee_list')
            columns = TableColumn.objects.filter(table=table, is_active=True)
            
            for role in roles:
                # Setup table permissions
                table_permissions = [
                    ('view', True),
                    ('edit', role.name in ['HR Manager']),
                    ('delete', role.name in ['HR Manager']),
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
                
                # Setup column permissions
                for column in columns:
                    # Default permissions based on role
                    can_view = True
                    can_edit = role.name in ['HR Manager']
                    can_hide = role.name in ['HR Manager']
                    
                    # Sensitive columns - restrict access
                    sensitive_fields = ['basic_salary', 'personal_phone', 'current_address']
                    if column.field_name in sensitive_fields:
                        can_view = role.name in ['HR Manager', 'Department Manager']
                        can_edit = role.name in ['HR Manager']
                    
                    # Manager-specific columns
                    if column.field_name in ['reporting_manager']:
                        can_view = role.name in ['HR Manager', 'Department Manager']
                    
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
            
            self.stdout.write(f'  Set up permissions for {len(roles)} roles')
            
        except DynamicTable.DoesNotExist:
            self.stdout.write('  Dynamic table not found, skipping permissions setup')
    
    def create_sample_employees(self, organization, branches, departments, designations, roles):
        """Create sample employees"""
        employee_data = [
            {
                'username': 'john.doe',
                'email': 'john.doe@example.com',
                'first_name': 'John',
                'last_name': 'Doe',
                'employee_id': f'EMP{organization.id}001',
                'role': 'HR Manager',
                'department': 'Human Resources',
                'designation': 'Manager',
                'branch': 'Main Office',
                'personal_phone': '+1-555-1001',
                'basic_salary': 75000,
                'hire_date': date.today() - timedelta(days=365*2)
            },
            {
                'username': 'jane.smith',
                'email': 'jane.smith@example.com',
                'first_name': 'Jane',
                'last_name': 'Smith',
                'employee_id': f'EMP{organization.id}002',
                'role': 'Department Manager',
                'department': 'Information Technology',
                'designation': 'Manager',
                'branch': 'Main Office',
                'personal_phone': '+1-555-1002',
                'basic_salary': 70000,
                'hire_date': date.today() - timedelta(days=365*3)
            },
            {
                'username': 'mike.johnson',
                'email': 'mike.johnson@example.com',
                'first_name': 'Mike',
                'last_name': 'Johnson',
                'employee_id': f'EMP{organization.id}003',
                'role': 'Team Lead',
                'department': 'Information Technology',
                'designation': 'Senior Executive',
                'branch': 'Branch Office',
                'personal_phone': '+1-555-1003',
                'basic_salary': 55000,
                'hire_date': date.today() - timedelta(days=365*1)
            },
            {
                'username': 'sarah.wilson',
                'email': 'sarah.wilson@example.com',
                'first_name': 'Sarah',
                'last_name': 'Wilson',
                'employee_id': f'EMP{organization.id}004',
                'role': 'Employee',
                'department': 'Marketing',
                'designation': 'Executive',
                'branch': 'Main Office',
                'personal_phone': '+1-555-1004',
                'basic_salary': 45000,
                'hire_date': date.today() - timedelta(days=180)
            },
            {
                'username': 'david.brown',
                'email': 'david.brown@example.com',
                'first_name': 'David',
                'last_name': 'Brown',
                'employee_id': f'EMP{organization.id}005',
                'role': 'Employee',
                'department': 'Finance',
                'designation': 'Associate',
                'branch': 'Remote Office',
                'personal_phone': '+1-555-1005',
                'basic_salary': 40000,
                'hire_date': date.today() - timedelta(days=90)
            },
            {
                'username': 'lisa.garcia',
                'email': 'lisa.garcia@example.com',
                'first_name': 'Lisa',
                'last_name': 'Garcia',
                'employee_id': f'EMP{organization.id}006',
                'role': 'Employee',
                'department': 'Operations',
                'designation': 'Trainee',
                'branch': 'Main Office',
                'personal_phone': '+1-555-1006',
                'basic_salary': 35000,
                'hire_date': date.today() - timedelta(days=30)
            }
        ]
        
        created_employees = []
        for emp_data in employee_data:
            # Create unique username for this organization
            unique_username = f"{emp_data['username']}_{organization.slug}"
            
            # Create user account
            user, created = User.objects.get_or_create(
                username=unique_username,
                defaults={
                    'email': emp_data['email'],
                    'first_name': emp_data['first_name'],
                    'last_name': emp_data['last_name'],
                    'role': 'employee',
                    'is_active': True
                }
            )
            
            if created:
                user.set_password('employee123')
                user.save()
            
            # Create employee profile
            employee, created = Employee.objects.get_or_create(
                employee_id=emp_data['employee_id'],
                organization=organization,
                defaults={
                    'user': user,
                    'first_name': emp_data['first_name'],
                    'last_name': emp_data['last_name'],
                    'employee_role': next((r for r in roles if r.name == emp_data['role']), roles[-1]),
                    'department': next((d for d in departments if d.name == emp_data['department']), departments[0]),
                    'designation': next((d for d in designations if d.name == emp_data['designation']), designations[0]),
                    'branch': next((b for b in branches if b.name == emp_data['branch']), branches[0]),
                    'personal_phone': emp_data['personal_phone'],
                    'personal_email': emp_data['email'],
                    'basic_salary': emp_data['basic_salary'],
                    'hire_date': emp_data['hire_date'],
                    'current_address': f'123 Main St, {organization.city}, {organization.state}',
                    'employment_status': 'active',
                    'is_active': True
                }
            )
            
            if created:
                # Create organization membership
                OrganizationMembership.objects.get_or_create(
                    user=user,
                    organization=organization,
                    defaults={
                        'is_admin': False,
                        'is_active': True
                    }
                )
                created_employees.append(employee)
        
        self.stdout.write(f'  Created {len(created_employees)} employees')
        
        # Set up reporting relationships
        if len(created_employees) >= 3:
            # HR Manager reports to no one (top level)
            # Department Manager reports to HR Manager
            created_employees[1].reporting_manager = created_employees[0]
            created_employees[1].save()
            
            # Team Lead reports to Department Manager
            created_employees[2].reporting_manager = created_employees[1]
            created_employees[2].save()
            
            # Employees report to Team Lead or Department Manager
            for i in range(3, len(created_employees)):
                if i % 2 == 0:
                    created_employees[i].reporting_manager = created_employees[2]  # Team Lead
                else:
                    created_employees[i].reporting_manager = created_employees[1]  # Department Manager
                created_employees[i].save()
        
        return created_employees
