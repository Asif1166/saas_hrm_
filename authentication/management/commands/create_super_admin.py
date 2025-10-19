from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()


class Command(BaseCommand):
    help = 'Create a super admin user for the HRM SaaS system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Username for the super admin',
            default='superadmin'
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Email for the super admin',
            default='admin@hrmsystem.com'
        )
        parser.add_argument(
            '--password',
            type=str,
            help='Password for the super admin',
            default='admin123'
        )
        parser.add_argument(
            '--first-name',
            type=str,
            help='First name for the super admin',
            default='Super'
        )
        parser.add_argument(
            '--last-name',
            type=str,
            help='Last name for the super admin',
            default='Admin'
        )

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']
        first_name = options['first_name']
        last_name = options['last_name']

        try:
            with transaction.atomic():
                # Check if super admin already exists
                if User.objects.filter(role='super_admin').exists():
                    self.stdout.write(
                        self.style.WARNING('Super admin user already exists!')
                    )
                    return

                # Create super admin user
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    role='super_admin',
                    is_active=True,
                    is_staff=True,
                    is_superuser=True
                )

                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully created super admin user: {username}'
                    )
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Email: {email}'
                    )
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Password: {password}'
                    )
                )
                self.stdout.write(
                    self.style.WARNING(
                        'Please change the password after first login!'
                    )
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating super admin: {str(e)}')
            )
