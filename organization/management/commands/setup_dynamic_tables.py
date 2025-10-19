from django.core.management.base import BaseCommand
from organization.models import DynamicTable, TableColumn


class Command(BaseCommand):
    help = 'Setup default dynamic table configurations'

    def handle(self, *args, **options):
        self.stdout.write('Setting up dynamic table configurations...')
        
        # Create Employee List Table
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
        else:
            self.stdout.write(f'Table already exists: {employee_table.display_name}')
        
        # Define employee table columns
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
        
        # Create columns for employee table
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
            else:
                self.stdout.write(f'  Column already exists: {column.display_name}')
        
        # Create Attendance List Table
        attendance_table, created = DynamicTable.objects.get_or_create(
            name='attendance_list',
            defaults={
                'table_type': 'attendance_list',
                'display_name': 'Attendance List',
                'description': 'Dynamic attendance list with role-based column permissions',
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(f'Created table: {attendance_table.display_name}')
        
        # Create Leave List Table
        leave_table, created = DynamicTable.objects.get_or_create(
            name='leave_list',
            defaults={
                'table_type': 'leave_list',
                'display_name': 'Leave List',
                'description': 'Dynamic leave request list with role-based column permissions',
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(f'Created table: {leave_table.display_name}')
        
        self.stdout.write(
            self.style.SUCCESS('Successfully set up dynamic table configurations!')
        )
