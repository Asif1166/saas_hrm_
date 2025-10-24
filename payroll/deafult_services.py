# payroll/services.py
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from django.db import transaction
from hrm.models import Employee, AttendanceRecord
from .models import PayrollPeriod, Payslip, SalaryStructure
from django.db.models import Sum, Count 

class PayrollProcessor:
    def __init__(self, organization):
        self.organization = organization
    
    def calculate_employee_salary(self, employee, period):
        """Calculate salary for a single employee"""
        try:
            # Get current salary structure
            salary_structure = SalaryStructure.objects.filter(
                employee=employee,
                effective_date__lte=period.end_date,
                is_active=True
            ).order_by('-effective_date').first()
            
            if not salary_structure:
                return None, f"No active salary structure found for {employee.full_name}"
            
            # Calculate attendance-based components
            attendance_data = self._calculate_attendance_data(employee, period)
            overtime_pay = self._calculate_overtime_pay(employee, period, salary_structure)
            deductions = self._calculate_deductions(employee, period, salary_structure, attendance_data)
            allowances = self._calculate_allowances(salary_structure)
            
            # Create payslip
            payslip = Payslip(
                organization=self.organization,
                employee=employee,
                payroll_period=period,
                salary_structure=salary_structure,
                basic_salary=salary_structure.basic_salary,
                allowances=allowances,
                overtime_pay=overtime_pay,
                bonus=Decimal('0.00'),  # Can be extended for bonus calculations
                other_earnings=Decimal('0.00'),
                provident_fund=salary_structure.provident_fund,
                tax_deduction=salary_structure.tax_deduction,
                late_attendance_deduction=deductions['late_deduction'],
                other_deductions=salary_structure.other_deductions,
                created_by=period.created_by
            )
            
            payslip.calculate_totals()
            return payslip, None
            
        except Exception as e:
            return None, f"Error calculating salary for {employee.full_name}: {str(e)}"
    
    def _calculate_attendance_data(self, employee, period):
        """Calculate attendance summary for the period"""
        attendance_records = AttendanceRecord.objects.filter(
            employee=employee,
            date__range=[period.start_date, period.end_date],
            status__in=['present', 'late', 'half_day']
        )
        
        total_working_days = attendance_records.count()
        late_days = attendance_records.filter(is_late=True).count()
        total_overtime_hours = sum([record.overtime_hours or Decimal('0.00') for record in attendance_records])
        
        return {
            'total_working_days': total_working_days,
            'late_days': late_days,
            'total_overtime_hours': total_overtime_hours
        }
    
    def _calculate_overtime_pay(self, employee, period, salary_structure):
        """Calculate overtime pay"""
        try:
            attendance_data = self._calculate_attendance_data(employee, period)
            overtime_hours = attendance_data['total_overtime_hours']
            
            if overtime_hours <= 0:
                return Decimal('0.00')
            
            # Calculate hourly rate (assuming 8 hours per day, 22 days per month)
            monthly_hours = Decimal('176')  # 8 hours * 22 days
            hourly_rate = salary_structure.basic_salary / monthly_hours
            
            # Overtime rate (1.5x for regular overtime)
            overtime_rate = hourly_rate * Decimal('1.5')
            
            return overtime_hours * overtime_rate
            
        except Exception as e:
            print(f"Error calculating overtime for {employee.full_name}: {str(e)}")
            return Decimal('0.00')
    
    def _calculate_allowances(self, salary_structure):
        """Calculate total allowances"""
        return (salary_structure.house_rent_allowance + 
                salary_structure.transport_allowance + 
                salary_structure.medical_allowance + 
                salary_structure.other_allowances)
    
    def _calculate_deductions(self, employee, period, salary_structure, attendance_data):
        """Calculate various deductions"""
        late_deduction = Decimal('0.00')
        
        # Late attendance deduction (example: 1% of basic per late day after 3 lates)
        if attendance_data['late_days'] > 3:
            late_days_to_deduct = attendance_data['late_days'] - 3
            late_deduction = (salary_structure.basic_salary * Decimal('0.01') * 
                            Decimal(str(late_days_to_deduct)))
        
        return {
            'late_deduction': late_deduction
        }
    
    def _get_working_days_in_period(self, period):
        """Calculate total working days in the period (excluding weekends)"""
        from datetime import timedelta
        
        total_days = (period.end_date - period.start_date).days + 1
        working_days = 0
        
        for day in range(total_days):
            current_date = period.start_date + timedelta(days=day)
            # Monday=0, Sunday=6 - consider Saturday(5) and Sunday(6) as weekends
            if current_date.weekday() < 5:
                working_days += 1
        
        return working_days
    
    @transaction.atomic
    def run_payroll(self, period_id):
        """Run payroll for all active employees in the period"""
        try:
            period = PayrollPeriod.objects.get(id=period_id, organization=self.organization)
            
            if period.status != 'draft':
                return False, "Payroll period is not in draft status"
            
            # Check if payroll already run for this period
            existing_payslips = Payslip.objects.filter(
                payroll_period=period,
                organization=self.organization
            ).count()
            
            if existing_payslips > 0:
                return False, "Payroll has already been run for this period"
            
            # Get all active employees
            active_employees = Employee.objects.filter(
                organization=self.organization,
                employment_status='active',
                is_active=True
            )
            
            if not active_employees.exists():
                return False, "No active employees found for payroll processing"
            
            payslips_created = 0
            errors = []
            
            # Update period status to processing
            period.status = 'processing'
            period.save()
            
            for employee in active_employees:
                payslip, error = self.calculate_employee_salary(employee, period)
                if payslip:
                    payslip.save()
                    payslips_created += 1
                else:
                    errors.append(error)
            
            # Update period status based on results
            if errors and payslips_created == 0:
                period.status = 'draft'  # Revert to draft if all failed
                period.save()
                return False, f"Payroll processing failed: {', '.join(errors)}"
            elif errors:
                period.status = 'processing'  # Partial success
                period.save()
                return True, {
                    'payslips_created': payslips_created,
                    'errors': errors,
                    'total_employees': active_employees.count(),
                    'status': 'partial'
                }
            else:
                period.status = 'completed'
                period.save()
                return True, {
                    'payslips_created': payslips_created,
                    'errors': errors,
                    'total_employees': active_employees.count(),
                    'status': 'completed'
                }
            
        except PayrollPeriod.DoesNotExist:
            return False, "Payroll period not found"
        except Exception as e:
            # Rollback any changes if error occurs
            try:
                period.status = 'draft'
                period.save()
            except:
                pass
            return False, f"Error running payroll: {str(e)}"
    
    def recalculate_payslip(self, payslip_id):
        """Recalculate a specific payslip"""
        try:
            payslip = Payslip.objects.get(id=payslip_id, organization=self.organization)
            employee = payslip.employee
            period = payslip.payroll_period
            
            new_payslip, error = self.calculate_employee_salary(employee, period)
            
            if new_payslip:
                # Update existing payslip with new values
                payslip.basic_salary = new_payslip.basic_salary
                payslip.allowances = new_payslip.allowances
                payslip.overtime_pay = new_payslip.overtime_pay
                payslip.provident_fund = new_payslip.provident_fund
                payslip.tax_deduction = new_payslip.tax_deduction
                payslip.late_attendance_deduction = new_payslip.late_attendance_deduction
                payslip.other_deductions = new_payslip.other_deductions
                payslip.calculate_totals()
                payslip.save()
                
                return True, "Payslip recalculated successfully"
            else:
                return False, error
                
        except Payslip.DoesNotExist:
            return False, "Payslip not found"
        except Exception as e:
            return False, f"Error recalculating payslip: {str(e)}"
    
    def get_payroll_summary(self, period_id):
        """Get summary of payroll for a period"""
        try:
            period = PayrollPeriod.objects.get(id=period_id, organization=self.organization)
            payslips = Payslip.objects.filter(payroll_period=period, organization=self.organization)
            
            summary = payslips.aggregate(
                total_basic_salary=Sum('basic_salary'),
                total_allowances=Sum('allowances'),
                total_overtime=Sum('overtime_pay'),
                total_deductions=Sum('total_deductions'),
                total_net_salary=Sum('net_salary'),
                employee_count=Count('id')
            )
            
            return True, summary
            
        except PayrollPeriod.DoesNotExist:
            return False, "Payroll period not found"
        except Exception as e:
            return False, f"Error getting payroll summary: {str(e)}"