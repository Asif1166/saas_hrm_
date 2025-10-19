from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils.text import slugify
from organization.models import Organization, OrganizationMembership

User = get_user_model()


class Command(BaseCommand):
    help = 'Create a new organization with admin user'

    def add_arguments(self, parser):
        parser.add_argument('--name', type=str, help='Organization name', required=True)
        parser.add_argument('--email', type=str, help='Organization email', required=True)
        parser.add_argument('--admin-username', type=str, help='Admin username', required=True)
        parser.add_argument('--admin-email', type=str, help='Admin email', required=True)
        parser.add_argument('--admin-password', type=str, help='Admin password', required=True)
        parser.add_argument('--admin-first-name', type=str, help='Admin first name', default='')
        parser.add_argument('--admin-last-name', type=str, help='Admin last name', default='')
        parser.add_argument('--phone', type=str, help='Organization phone', default='')
        parser.add_argument('--website', type=str, help='Organization website', default='')
        parser.add_argument('--plan', type=str, help='Subscription plan', default='basic')
        parser.add_argument('--max-employees', type=int, help='Max employees', default=10)

    def handle(self, *args, **options):
        name = options['name']
        email = options['email']
        admin_username = options['admin_username']
        admin_email = options['admin_email']
        admin_password = options['admin_password']
        admin_first_name = options['admin_first_name']
        admin_last_name = options['admin_last_name']
        phone = options['phone']
        website = options['website']
        plan = options['plan']
        max_employees = options['max_employees']

        try:
            with transaction.atomic():
                # Check if organization already exists
                if Organization.objects.filter(name=name).exists():
                    self.stdout.write(
                        self.style.ERROR(f'Organization "{name}" already exists!')
                    )
                    return

                # Check if admin user already exists
                if User.objects.filter(username=admin_username).exists():
                    self.stdout.write(
                        self.style.ERROR(f'Admin user "{admin_username}" already exists!')
                    )
                    return

                # Create organization
                organization = Organization.objects.create(
                    name=name,
                    slug=slugify(name),
                    email=email,
                    phone=phone if phone else None,
                    website=website if website else None,
                    subscription_plan=plan,
                    max_employees=max_employees
                )

                # Create admin user
                admin_user = User.objects.create_user(
                    username=admin_username,
                    email=admin_email,
                    password=admin_password,
                    first_name=admin_first_name,
                    last_name=admin_last_name,
                    role='organization_admin',
                    is_active=True
                )

                # Create organization membership
                OrganizationMembership.objects.create(
                    user=admin_user,
                    organization=organization,
                    is_admin=True,
                    is_active=True
                )

                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully created organization: {name}'
                    )
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Organization Admin: {admin_username}'
                    )
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Admin Email: {admin_email}'
                    )
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Admin Password: {admin_password}'
                    )
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating organization: {str(e)}')
            )
