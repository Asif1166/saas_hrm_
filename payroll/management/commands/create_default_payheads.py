from django.core.management.base import BaseCommand
from hrm.models import Payhead
from organization.models import Organization
from decimal import Decimal
from django.utils import timezone

class Command(BaseCommand):
    help = 'Create default payheads for an organization'

    def add_arguments(self, parser):
        parser.add_argument('organization_id', type=int, help='Organization ID')

    def handle(self, *args, **options):
        org_id = options['organization_id']
        
        try:
            organization = Organization.objects.get(id=org_id)
            
            # Default Earnings
            earnings = [
                {
                    'name': 'Basic Salary',
                    'code': 'BASIC',
                    'short_name': 'Basic',
                    'calculation_type': 'fixed',
                    'amount': Decimal('30000.00'),
                    'display_order': 1,
                },
                {
                    'name': 'House Rent Allowance',
                    'code': 'HRA',
                    'short_name': 'HRA',
                    'calculation_type': 'percentage',
                    'percentage': Decimal('40.00'),
                    'percentage_base': 'basic',
                    'display_order': 2,
                },
                {
                    'name': 'Transport Allowance',
                    'code': 'TA',
                    'short_name': 'Transport',
                    'calculation_type': 'fixed',
                    'amount': Decimal('2000.00'),
                    'display_order': 3,
                },
                {
                    'name': 'Medical Allowance',
                    'code': 'MA',
                    'short_name': 'Medical',
                    'calculation_type': 'fixed',
                    'amount': Decimal('1500.00'),
                    'display_order': 4,
                },
                {
                    'name': 'Overtime Pay',
                    'code': 'OT',
                    'short_name': 'Overtime',
                    'calculation_type': 'overtime',
                    'overtime_rate_per_hour': Decimal('150.00'),
                    'display_order': 5,
                },
                {
                    'name': 'Special Allowance',
                    'code': 'SA',
                    'short_name': 'Special',
                    'calculation_type': 'fixed',
                    'amount': Decimal('3000.00'),
                    'display_order': 6,
                },
            ]
            
            # Default Deductions
            deductions = [
                {
                    'name': 'Provident Fund',
                    'code': 'PF',
                    'short_name': 'PF',
                    'calculation_type': 'percentage',
                    'percentage': Decimal('12.00'),
                    'percentage_base': 'basic',
                    'is_pf_applicable': True,
                    'display_order': 1,
                },
                {
                    'name': 'Employee State Insurance',
                    'code': 'ESI',
                    'short_name': 'ESI',
                    'calculation_type': 'percentage',
                    'percentage': Decimal('0.75'),
                    'percentage_base': 'gross',
                    'is_esi_applicable': True,
                    'display_order': 2,
                },
                {
                    'name': 'Professional Tax',
                    'code': 'PT',
                    'short_name': 'Prof. Tax',
                    'calculation_type': 'fixed',
                    'amount': Decimal('200.00'),
                    'display_order': 3,
                },
                {
                    'name': 'Income Tax (TDS)',
                    'code': 'TDS',
                    'short_name': 'TDS',
                    'calculation_type': 'percentage',
                    'percentage': Decimal('10.00'),
                    'percentage_base': 'gross',
                    'display_order': 4,
                },
                {
                    'name': 'Late Attendance Deduction',
                    'code': 'LATE',
                    'short_name': 'Late Deduction',
                    'calculation_type': 'custom',
                    'amount': Decimal('0.00'),
                    'display_order': 5,
                },
            ]
            
            # Create earnings
            for earning_data in earnings:
                payhead, created = Payhead.objects.get_or_create(
                    organization=organization,
                    code=earning_data['code'],
                    defaults={
                        'name': earning_data['name'],
                        'short_name': earning_data.get('short_name'),
                        'payhead_type': 'earning',
                        'calculation_type': earning_data['calculation_type'],
                        'amount': earning_data.get('amount', Decimal('0.00')),
                        'percentage': earning_data.get('percentage', Decimal('0.00')),
                        'percentage_base': earning_data.get('percentage_base', 'basic'),
                        'overtime_rate_per_hour': earning_data.get('overtime_rate_per_hour', Decimal('0.00')),
                        'display_order': earning_data['display_order'],
                        'is_active': True,
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Created earning: {payhead.name}'))
            
            # Create deductions
            for deduction_data in deductions:
                payhead, created = Payhead.objects.get_or_create(
                    organization=organization,
                    code=deduction_data['code'],
                    defaults={
                        'name': deduction_data['name'],
                        'short_name': deduction_data.get('short_name'),
                        'payhead_type': 'deduction',
                        'calculation_type': deduction_data['calculation_type'],
                        'amount': deduction_data.get('amount', Decimal('0.00')),
                        'percentage': deduction_data.get('percentage', Decimal('0.00')),
                        'percentage_base': deduction_data.get('percentage_base', 'basic'),
                        'is_pf_applicable': deduction_data.get('is_pf_applicable', False),
                        'is_esi_applicable': deduction_data.get('is_esi_applicable', False),
                        'display_order': deduction_data['display_order'],
                        'is_active': True,
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Created deduction: {payhead.name}'))
            
            self.stdout.write(self.style.SUCCESS(f'\nSuccessfully created default payheads for {organization.name}'))
            
        except Organization.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Organization with ID {org_id} not found'))