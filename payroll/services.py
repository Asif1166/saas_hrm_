# payroll/services.py - Updated to work with your existing Payslip model

from django.utils import timezone
from decimal import Decimal
from django.db import transaction
from hrm.models import Employee, AttendanceRecord, EmployeePayhead
from .models import (
    PayrollPeriod, Payslip, SalaryStructure, 
    Payhead,  PayslipComponent
)
from django.db.models import Sum, Count, Q


class PayrollProcessor:
    def __init__(self, organization):
        self.organization = organization
    
    def calculate_employee_salary(self, employee, period):
        """Calculate salary for a single employee using Payhead system"""
        try:
            # Get attendance data
            attendance_data = self._calculate_attendance_data(employee, period)
            
            # Get base salary (basic)
            basic_salary = self._get_basic_salary(employee, period)
            
            if not basic_salary or basic_salary <= 0:
                return None, f"No basic salary configured for {employee.full_name}"
            
            # Calculate earnings and deductions using payheads
            earnings_breakdown = self._calculate_earnings(
                employee, period, basic_salary, attendance_data
            )
            
            deduction_breakdown = self._calculate_deductions(
                employee, period, basic_salary, attendance_data
            )
            
            # Calculate summary fields for existing Payslip model
            basic_amount = Decimal('0.00')
            allowances_amount = Decimal('0.00')
            overtime_amount = Decimal('0.00')
            pf_amount = Decimal('0.00')
            tax_amount = Decimal('0.00')
            late_deduction_amount = Decimal('0.00')
            other_earnings_amount = Decimal('0.00')
            other_deductions_amount = Decimal('0.00')
            
            # Categorize earnings
            for earning in earnings_breakdown:
                code = earning['payhead_code']
                amount = earning['amount']
                
                if code == 'BASIC':
                    basic_amount = amount
                elif code == 'OT':
                    overtime_amount = amount
                elif code in ['HRA', 'TA', 'MA', 'SA']:
                    allowances_amount += amount
                else:
                    other_earnings_amount += amount
            
            # Categorize deductions
            for deduction in deduction_breakdown:
                code = deduction['payhead_code']
                amount = deduction['amount']
                
                if code == 'PF':
                    pf_amount = amount
                elif code in ['TDS', 'TAX']:
                    tax_amount = amount
                elif code == 'LATE':
                    late_deduction_amount = amount
                else:
                    other_deductions_amount += amount
            
            # Calculate totals
            total_earnings = sum(e['amount'] for e in earnings_breakdown)
            total_deductions = sum(d['amount'] for d in deduction_breakdown)
            net_salary = total_earnings - total_deductions
            
            # Get or create salary structure
            salary_structure = self._get_or_create_salary_structure(
                employee, period, basic_amount
            )
            
            # Create payslip with existing model fields
            payslip = Payslip(
                organization=self.organization,
                employee=employee,
                payroll_period=period,
                salary_structure=salary_structure,
                # Earnings
                basic_salary=basic_amount,
                allowances=allowances_amount,
                overtime_pay=overtime_amount,
                bonus=Decimal('0.00'),
                other_earnings=other_earnings_amount,
                # Deductions
                provident_fund=pf_amount,
                tax_deduction=tax_amount,
                late_attendance_deduction=late_deduction_amount,
                other_deductions=other_deductions_amount,
                # Totals
                gross_salary=total_earnings,
                total_deductions=total_deductions,
                net_salary=net_salary,
                created_by=period.created_by
            )
            
            # Store detailed breakdown for saving later
            payslip._earnings_breakdown = earnings_breakdown
            payslip._deduction_breakdown = deduction_breakdown
            
            return payslip, None
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return None, f"Error calculating salary for {employee.full_name}: {str(e)}"
    
    def _get_basic_salary(self, employee, period):
        """Get basic salary from employee payheads or organization default"""
        try:
            # Check employee-specific payhead
            employee_payhead = EmployeePayhead.objects.filter(
                organization=self.organization,
                employee=employee,
                payhead__code='BASIC',
                payhead__is_active=True,
                is_active=True,
                effective_from__lte=period.end_date
            ).filter(
                Q(effective_to__isnull=True) | Q(effective_to__gte=period.start_date)
            ).order_by('-effective_from').first()
            
            if employee_payhead and employee_payhead.amount > 0:
                return employee_payhead.amount
            
            # Check organization payhead
            basic_payhead = Payhead.objects.filter(
                organization=self.organization,
                code='BASIC',
                is_active=True
            ).first()
            
            if basic_payhead and basic_payhead.amount > 0:
                return basic_payhead.amount
            
            # Fallback to salary structure
            salary_structure = SalaryStructure.objects.filter(
                employee=employee,
                effective_date__lte=period.end_date,
                is_active=True
            ).order_by('-effective_date').first()
            
            if salary_structure:
                return salary_structure.basic_salary
            
            return Decimal('0.00')
            
        except Exception as e:
            print(f"Error getting basic salary: {str(e)}")
            return Decimal('0.00')
    
    def _calculate_earnings(self, employee, period, basic_salary, attendance_data):
        """Calculate all earning components"""
        earnings = []
        
        # Get employee payheads
        employee_payheads = EmployeePayhead.objects.filter(
            organization=self.organization,
            employee=employee,
            payhead__payhead_type='earning',
            payhead__is_active=True,
            is_active=True,
            effective_from__lte=period.end_date
        ).filter(
            Q(effective_to__isnull=True) | Q(effective_to__gte=period.start_date)
        ).select_related('payhead').order_by('payhead__display_order')
        
        # If no employee payheads, use organization defaults
        if not employee_payheads.exists():
            org_payheads = Payhead.objects.filter(
                organization=self.organization,
                payhead_type='earning',
                is_active=True
            ).order_by('display_order')
            
            for payhead in org_payheads:
                amount = self._calculate_payhead_amount(
                    payhead, None, basic_salary, attendance_data
                )
                earnings.append({
                    'payhead_id': payhead.id,
                    'payhead_code': payhead.code,
                    'payhead_name': payhead.name,
                    'calculation_type': payhead.calculation_type,
                    'amount': amount
                })
        else:
            for emp_payhead in employee_payheads:
                amount = emp_payhead.get_effective_amount(
                    base_amount=basic_salary,
                    attendance_hours=attendance_data.get('total_working_hours', 0),
                    overtime_hours=attendance_data.get('total_overtime_hours', 0),
                    production_units=0
                )
                earnings.append({
                    'payhead_id': emp_payhead.payhead.id,
                    'payhead_code': emp_payhead.payhead.code,
                    'payhead_name': emp_payhead.payhead.name,
                    'calculation_type': emp_payhead.payhead.calculation_type,
                    'amount': amount
                })
        
        return earnings
    
    def _calculate_deductions(self, employee, period, basic_salary, attendance_data):
        """Calculate all deduction components"""
        deductions = []
        
        # Get employee payheads
        employee_payheads = EmployeePayhead.objects.filter(
            organization=self.organization,
            employee=employee,
            payhead__payhead_type='deduction',
            payhead__is_active=True,
            is_active=True,
            effective_from__lte=period.end_date
        ).filter(
            Q(effective_to__isnull=True) | Q(effective_to__gte=period.start_date)
        ).select_related('payhead').order_by('payhead__display_order')
        
        # If no employee payheads, use organization defaults
        if not employee_payheads.exists():
            org_payheads = Payhead.objects.filter(
                organization=self.organization,
                payhead_type='deduction',
                is_active=True
            ).order_by('display_order')
            
            for payhead in org_payheads:
                amount = self._calculate_payhead_amount(
                    payhead, None, basic_salary, attendance_data
                )
                deductions.append({
                    'payhead_id': payhead.id,
                    'payhead_code': payhead.code,
                    'payhead_name': payhead.name,
                    'calculation_type': payhead.calculation_type,
                    'amount': amount
                })
        else:
            for emp_payhead in employee_payheads:
                amount = emp_payhead.get_effective_amount(
                    base_amount=basic_salary,
                    attendance_hours=attendance_data.get('total_working_hours', 0),
                    overtime_hours=attendance_data.get('total_overtime_hours', 0),
                    production_units=0
                )
                deductions.append({
                    'payhead_id': emp_payhead.payhead.id,
                    'payhead_code': emp_payhead.payhead.code,
                    'payhead_name': emp_payhead.payhead.name,
                    'calculation_type': emp_payhead.payhead.calculation_type,
                    'amount': amount
                })
        
        return deductions
    
    def _calculate_payhead_amount(self, payhead, employee_payhead, basic_salary, attendance_data):
        """Calculate amount for a payhead"""
        amount = Decimal('0.00')
        
        if payhead.calculation_type == 'fixed':
            amount = payhead.amount
        
        elif payhead.calculation_type == 'percentage':
            if payhead.percentage_base == 'basic':
                amount = (basic_salary * payhead.percentage) / Decimal('100')
            else:
                amount = (basic_salary * payhead.percentage) / Decimal('100')
        
        elif payhead.calculation_type == 'attendance':
            hours = attendance_data.get('total_working_hours', 0)
            amount = payhead.attendance_rate_per_hour * Decimal(str(hours))
        
        elif payhead.calculation_type == 'overtime':
            hours = attendance_data.get('total_overtime_hours', 0)
            amount = payhead.overtime_rate_per_hour * Decimal(str(hours))
        
        # Apply limits
        if payhead.min_amount > 0:
            amount = max(amount, payhead.min_amount)
        if payhead.max_amount > 0:
            amount = min(amount, payhead.max_amount)
        
        return round(amount, 2)
    
    def _calculate_attendance_data(self, employee, period):
        """Calculate attendance summary"""
        attendance_records = AttendanceRecord.objects.filter(
            employee=employee,
            date__range=[period.start_date, period.end_date]
        )
        
        present_records = attendance_records.filter(
            status__in=['present', 'late', 'half_day']
        )
        
        total_working_hours = sum([
            record.working_hours or Decimal('0.00') 
            for record in present_records
        ])
        
        total_overtime_hours = sum([
            record.overtime_hours or Decimal('0.00') 
            for record in present_records
        ])
        
        return {
            'total_working_days': present_records.count(),
            'total_working_hours': total_working_hours,
            'total_overtime_hours': total_overtime_hours,
            'late_days': attendance_records.filter(is_late=True).count(),
            'absent_days': attendance_records.filter(status='absent').count(),
        }
    
    def _get_or_create_salary_structure(self, employee, period, basic_salary):
        """Get or create salary structure"""
        salary_structure = SalaryStructure.objects.filter(
            employee=employee,
            effective_date__lte=period.end_date,
            is_active=True
        ).order_by('-effective_date').first()
        
        if not salary_structure:
            salary_structure = SalaryStructure.objects.create(
                organization=self.organization,
                employee=employee,
                basic_salary=basic_salary,
                effective_date=period.start_date,
                is_active=True
            )
        
        return salary_structure
    
    def _save_payslip_components(self, payslip):
        """Save detailed components"""
        # Delete old components
        PayslipComponent.objects.filter(payslip=payslip).delete()
        
        # Save earnings
        if hasattr(payslip, '_earnings_breakdown'):
            for idx, earning in enumerate(payslip._earnings_breakdown):
                PayslipComponent.objects.create(
                    organization=self.organization,
                    payslip=payslip,
                    payhead_id=earning['payhead_id'],
                    component_type='earning',
                    component_name=earning['payhead_name'],
                    component_code=earning['payhead_code'],
                    calculation_type=earning['calculation_type'],
                    amount=earning['amount'],
                    display_order=idx
                )
        
        # Save deductions
        if hasattr(payslip, '_deduction_breakdown'):
            for idx, deduction in enumerate(payslip._deduction_breakdown):
                PayslipComponent.objects.create(
                    organization=self.organization,
                    payslip=payslip,
                    payhead_id=deduction['payhead_id'],
                    component_type='deduction',
                    component_name=deduction['payhead_name'],
                    component_code=deduction['payhead_code'],
                    calculation_type=deduction['calculation_type'],
                    amount=deduction['amount'],
                    display_order=idx
                )
    
    @transaction.atomic
    def run_payroll(self, period_id):
        """Run payroll for all active employees"""
        try:
            period = PayrollPeriod.objects.get(id=period_id, organization=self.organization)
            
            if period.status != 'draft':
                return False, "Payroll period is not in draft status"
            
            # Get active employees
            active_employees = Employee.objects.filter(
                organization=self.organization,
                employment_status='active',
                is_active=True
            )
            
            if not active_employees.exists():
                return False, "No active employees found"
            
            payslips_created = 0
            errors = []
            
            period.status = 'processing'
            period.save()
            
            for employee in active_employees:
                payslip, error = self.calculate_employee_salary(employee, period)
                if payslip:
                    payslip.save()
                    # IMPORTANT: Save components after payslip is saved
                    self._save_payslip_components(payslip)
                    payslips_created += 1
                else:
                    errors.append(error)
            
            if errors and payslips_created == 0:
                period.status = 'draft'
                period.save()
                return False, f"Payroll failed: {', '.join(errors)}"
            else:
                period.status = 'completed'
                period.save()
                return True, {
                    'payslips_created': payslips_created,
                    'errors': errors,
                    'total_employees': active_employees.count(),
                    'status': 'completed'
                }
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return False, f"Error running payroll: {str(e)}"
    
    def get_payroll_summary(self, period_id):
        """Get payroll summary"""
        try:
            period = PayrollPeriod.objects.get(id=period_id, organization=self.organization)
            payslips = Payslip.objects.filter(payroll_period=period, organization=self.organization)
            
            summary = payslips.aggregate(
                total_basic_salary=Sum('basic_salary'),
                total_allowances=Sum('allowances'),
                total_overtime=Sum('overtime_pay'),
                total_gross_salary=Sum('gross_salary'),
                total_deductions=Sum('total_deductions'),
                total_net_salary=Sum('net_salary'),
                employee_count=Count('id')
            )
            
            return True, summary
            
        except PayrollPeriod.DoesNotExist:
            return False, "Payroll period not found"
        except Exception as e:
            return False, f"Error: {str(e)}"