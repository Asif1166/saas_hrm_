from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from organization.models import Organization, OrganizationMembership
from hrm.models import Branch, Department, Designation, EmployeeRole, Employee
from datetime import date, timedelta

User = get_user_model()


class Command(BaseCommand):
    help = 'Create sample employee data for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--organization-id',
            type=int,
            help='Organization ID to create sample data for',
            required=True
        )

    def handle(self, *args, **options):
        org_id = options['organization_id']
        
        try:
            organization = Organization.objects.get(id=org_id)
        except Organization.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Organization with ID {org_id} does not exist!')
            )
            return

        try:
            with transaction.atomic():
                # Create sample branch
                branch, created = Branch.objects.get_or_create(
                    organization=organization,
                    code='BR001',
                    defaults={
                        'name': 'Head Office',
                        'description': 'Main office branch',
                        'city': 'Dhaka',
                        'country': 'Bangladesh',
                        'is_active': True
                    }
                )
                if created:
                    self.stdout.write(f'Created branch: {branch.name}')

                # Create sample department
                department, created = Department.objects.get_or_create(
                    organization=organization,
                    code='IT001',
                    defaults={
                        'name': 'Information Technology',
                        'description': 'IT Department',
                        'branch': branch,
                        'is_active': True
                    }
                )
                if created:
                    self.stdout.write(f'Created department: {department.name}')

                # Create sample designation
                designation, created = Designation.objects.get_or_create(
                    organization=organization,
                    code='DEV001',
                    defaults={
                        'name': 'Software Developer',
                        'description': 'Software development role',
                        'level': 3,
                        'department': department,
                        'is_active': True
                    }
                )
                if created:
                    self.stdout.write(f'Created designation: {designation.name}')

                # Create sample employee role
                employee_role, created = EmployeeRole.objects.get_or_create(
                    organization=organization,
                    code='DEV',
                    defaults={
                        'name': 'Developer',
                        'description': 'Software developer role',
                        'permissions': {'can_view_code': True, 'can_commit': True},
                        'is_active': True
                    }
                )
                if created:
                    self.stdout.write(f'Created employee role: {employee_role.name}')

                # Create sample employee
                employee_username = 'john_doe'
                if not User.objects.filter(username=employee_username).exists():
                    # Create user account
                    user = User.objects.create_user(
                        username=employee_username,
                        email='john.doe@example.com',
                        password='employee123',
                        first_name='John',
                        last_name='Doe',
                        role='employee',
                        is_active=True
                    )

                    # Create employee profile
                    employee = Employee.objects.create(
                        user=user,
                        employee_id='EMP001',
                        organization=organization,
                        branch=branch,
                        department=department,
                        designation=designation,
                        employee_role=employee_role,
                        first_name='John',
                        last_name='Doe',
                        gender='male',
                        date_of_birth=date(1990, 5, 15),
                        personal_email='john.doe@example.com',
                        personal_phone='+8801234567890',
                        current_address='123 Main Street, Dhaka',
                        employment_status='active',
                        hire_date=date.today() - timedelta(days=365),
                        basic_salary=50000.00,
                        gross_salary=60000.00,
                        emergency_contact_name='Jane Doe',
                        emergency_contact_phone='+8809876543210',
                        emergency_contact_relationship='Spouse',
                        skills='Python, Django, JavaScript, React',
                        is_active=True
                    )

                    # Create organization membership
                    OrganizationMembership.objects.create(
                        user=user,
                        organization=organization,
                        is_admin=False,
                        is_active=True
                    )

                    self.stdout.write(
                        self.style.SUCCESS(f'Created employee: {employee.full_name}')
                    )
                    self.stdout.write(
                        self.style.SUCCESS(f'Username: {employee_username}')
                    )
                    self.stdout.write(
                        self.style.SUCCESS(f'Password: employee123')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'Employee with username {employee_username} already exists!')
                    )

                # Create another sample employee
                employee_username2 = 'jane_smith'
                if not User.objects.filter(username=employee_username2).exists():
                    # Create user account
                    user2 = User.objects.create_user(
                        username=employee_username2,
                        email='jane.smith@example.com',
                        password='employee123',
                        first_name='Jane',
                        last_name='Smith',
                        role='employee',
                        is_active=True
                    )

                    # Create employee profile
                    employee2 = Employee.objects.create(
                        user=user2,
                        employee_id='EMP002',
                        organization=organization,
                        branch=branch,
                        department=department,
                        designation=designation,
                        employee_role=employee_role,
                        first_name='Jane',
                        last_name='Smith',
                        gender='female',
                        date_of_birth=date(1992, 8, 20),
                        personal_email='jane.smith@example.com',
                        personal_phone='+8801234567891',
                        current_address='456 Oak Avenue, Dhaka',
                        employment_status='active',
                        hire_date=date.today() - timedelta(days=200),
                        basic_salary=45000.00,
                        gross_salary=55000.00,
                        emergency_contact_name='John Smith',
                        emergency_contact_phone='+8809876543211',
                        emergency_contact_relationship='Brother',
                        skills='Python, Django, UI/UX Design',
                        is_active=True
                    )

                    # Create organization membership
                    OrganizationMembership.objects.create(
                        user=user2,
                        organization=organization,
                        is_admin=False,
                        is_active=True
                    )

                    self.stdout.write(
                        self.style.SUCCESS(f'Created employee: {employee2.full_name}')
                    )
                    self.stdout.write(
                        self.style.SUCCESS(f'Username: {employee_username2}')
                    )
                    self.stdout.write(
                        self.style.SUCCESS(f'Password: employee123')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'Employee with username {employee_username2} already exists!')
                    )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating sample data: {str(e)}')
            )
