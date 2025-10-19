from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from organization.models import Organization, OrganizationMembership
from hrm.models import Employee

User = get_user_model()


class Command(BaseCommand):
    help = 'Show test credentials for login'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('TEST CREDENTIALS FOR DYNAMIC TABLE SYSTEM')
        self.stdout.write('='*60)
        
        # Super Admin
        try:
            super_admin = User.objects.get(username='superadmin')
            self.stdout.write(f'\n🔑 SUPER ADMIN:')
            self.stdout.write(f'   Username: {super_admin.username}')
            self.stdout.write(f'   Password: admin123')
            self.stdout.write(f'   Role: {super_admin.role}')
            self.stdout.write(f'   Access: Full system access')
        except User.DoesNotExist:
            self.stdout.write('\n❌ Super admin not found')
        
        # Organization Admins
        self.stdout.write(f'\n🏢 ORGANIZATION ADMINS:')
        organizations = Organization.objects.all()
        
        for org in organizations:
            try:
                admin_username = f'admin_{org.slug}'
                admin_user = User.objects.get(username=admin_username)
                self.stdout.write(f'\n   Organization: {org.name}')
                self.stdout.write(f'   Username: {admin_user.username}')
                self.stdout.write(f'   Password: admin123')
                self.stdout.write(f'   Email: {admin_user.email}')
                self.stdout.write(f'   Role: {admin_user.role}')
                self.stdout.write(f'   Access: Full organization access + table configuration')
            except User.DoesNotExist:
                self.stdout.write(f'\n   ❌ Admin for {org.name} not found')
        
        # Sample Employees
        self.stdout.write(f'\n👥 SAMPLE EMPLOYEES (with different roles):')
        
        for org in organizations:
            self.stdout.write(f'\n   Organization: {org.name}')
            
            # Get employees with different roles
            employees = Employee.objects.filter(
                organization=org,
                is_active=True
            ).select_related('user', 'employee_role')[:3]
            
            for emp in employees:
                self.stdout.write(f'\n   Name: {emp.full_name}')
                self.stdout.write(f'   Username: {emp.user.username}')
                self.stdout.write(f'   Password: employee123')
                self.stdout.write(f'   Role: {emp.employee_role.name if emp.employee_role else "No Role"}')
                self.stdout.write(f'   Department: {emp.department.name if emp.department else "No Department"}')
                self.stdout.write(f'   Access: Role-based table permissions')
        
        # Menu Access Information
        self.stdout.write(f'\n📋 MENU ACCESS BY ROLE:')
        self.stdout.write(f'   • Super Admin: All menus')
        self.stdout.write(f'   • Organization Admin: All organization menus + configuration')
        self.stdout.write(f'   • HR Manager: HR menus + employee management + salary view')
        self.stdout.write(f'   • Department Manager: Employee view + department management')
        self.stdout.write(f'   • Team Lead: Employee view + team management')
        self.stdout.write(f'   • Employee: Basic employee view + own profile')
        
        # Dynamic Table Features
        self.stdout.write(f'\n⚙️ DYNAMIC TABLE FEATURES:')
        self.stdout.write(f'   • Column Visibility: Toggle columns on/off')
        self.stdout.write(f'   • Role-Based Permissions: Different columns per role')
        self.stdout.write(f'   • User Preferences: Save personal column settings')
        self.stdout.write(f'   • Admin Configuration: Set permissions per role')
        self.stdout.write(f'   • Sensitive Data Protection: Salary/phone hidden by default')
        
        # Testing Instructions
        self.stdout.write(f'\n🧪 TESTING INSTRUCTIONS:')
        self.stdout.write(f'   1. Login as Organization Admin')
        self.stdout.write(f'   2. Go to Employee List to see dynamic columns')
        self.stdout.write(f'   3. Click "Configure" → "Column Permissions"')
        self.stdout.write(f'   4. Modify permissions for different roles')
        self.stdout.write(f'   5. Login as different role users to test permissions')
        self.stdout.write(f'   6. Use "Columns" dropdown to toggle visibility')
        self.stdout.write(f'   7. Save preferences to persist settings')
        
        self.stdout.write(f'\n📊 SAMPLE DATA CREATED:')
        self.stdout.write(f'   • 3 Organizations with different subscription plans')
        self.stdout.write(f'   • 18 Employees across 3 organizations (6 per org)')
        self.stdout.write(f'   • 4 Employee Roles per organization')
        self.stdout.write(f'   • 5 Departments per organization')
        self.stdout.write(f'   • 3 Branches per organization')
        self.stdout.write(f'   • Dynamic table configurations')
        self.stdout.write(f'   • Role-based column permissions')
        
        self.stdout.write(f'\n🔗 IMPORTANT URLS:')
        self.stdout.write(f'   • Login: /authentication/login/')
        self.stdout.write(f'   • Employee List: /hrm/employees/')
        self.stdout.write(f'   • Table Config: /organization/tables/employee_list/config/')
        self.stdout.write(f'   • HR Dashboard: /hrm/dashboard/')
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Ready to test the Dynamic Table System! 🚀')
        self.stdout.write('='*60 + '\n')
