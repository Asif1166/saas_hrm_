# reports/payroll_reports.py
from django.db.models import Q, Count, Sum, Avg, F
from django.utils import timezone
from datetime import datetime, date, timedelta
from django.db.models.functions import TruncMonth
from payroll.models import Payslip, PayrollPeriod, SalaryStructure
from hrm.models import Employee, Department

class PayrollRegisterReport:
    def generate_payroll_register(self, organization, filters=None):
        """
        Generate complete payroll register for a period
        """
        filters = filters or {}
        
        # Get payroll period
        payroll_period_id = filters.get('payroll_period')
        if payroll_period_id:
            payroll_period = PayrollPeriod.objects.get(id=payroll_period_id, organization=organization)
        else:
            # Get latest payroll period
            payroll_period = PayrollPeriod.objects.filter(
                organization=organization,
                status='completed'
            ).order_by('-start_date').first()
        
        if not payroll_period:
            return {
                'report_name': 'Payroll Register',
                'generated_on': timezone.now().strftime('%d-%m-%Y %H:%M:%S'),
                'error': 'No completed payroll periods found'
            }
        
        # Get payslips for the period
        payslips = Payslip.objects.filter(
            payroll_period=payroll_period,
            organization=organization
        ).select_related('employee', 'employee__department', 'salary_structure')
        
        # Apply department filter
        if filters.get('department'):
            payslips = payslips.filter(employee__department_id=filters['department'])
        
        payroll_data = []
        total_basic = 0
        total_allowances = 0
        total_overtime = 0
        total_bonus = 0
        total_earnings = 0
        total_pf = 0
        total_tax = 0
        total_deductions = 0
        total_net = 0
        
        for payslip in payslips:
            payroll_data.append({
                'employee_id': payslip.employee.employee_id,
                'full_name': payslip.employee.full_name,
                'department': payslip.employee.department.name if payslip.employee.department else 'N/A',
                'designation': payslip.employee.designation.name if payslip.employee.designation else 'N/A',
                'bank_account': payslip.employee.bank_account_number or 'N/A',
                'bank_name': payslip.employee.bank_name or 'N/A',
                'basic_salary': float(payslip.basic_salary),
                'allowances': float(payslip.allowances),
                'overtime_pay': float(payslip.overtime_pay),
                'bonus': float(payslip.bonus),
                'other_earnings': float(payslip.other_earnings),
                'gross_salary': float(payslip.gross_salary),
                'provident_fund': float(payslip.provident_fund),
                'tax_deduction': float(payslip.tax_deduction),
                'late_deduction': float(payslip.late_attendance_deduction),
                'other_deductions': float(payslip.other_deductions),
                'total_deductions': float(payslip.total_deductions),
                'net_salary': float(payslip.net_salary),
                'pay_date': payroll_period.pay_date.strftime('%d-%m-%Y')
            })
            
            # Update totals
            total_basic += payslip.basic_salary
            total_allowances += payslip.allowances
            total_overtime += payslip.overtime_pay
            total_bonus += payslip.bonus
            total_earnings += payslip.gross_salary
            total_pf += payslip.provident_fund
            total_tax += payslip.tax_deduction
            total_deductions += payslip.total_deductions
            total_net += payslip.net_salary
        
        return {
            'report_name': 'Payroll Register',
            'generated_on': timezone.now().strftime('%d-%m-%Y %H:%M:%S'),
            'payroll_period': payroll_period.name,
            'period': f"{payroll_period.start_date.strftime('%d-%m-%Y')} to {payroll_period.end_date.strftime('%d-%m-%Y')}",
            'pay_date': payroll_period.pay_date.strftime('%d-%m-%Y'),
            'filters': filters,
            'summary': {
                'total_employees': len(payroll_data),
                'total_basic': round(total_basic, 2),
                'total_allowances': round(total_allowances, 2),
                'total_overtime': round(total_overtime, 2),
                'total_bonus': round(total_bonus, 2),
                'total_earnings': round(total_earnings, 2),
                'total_pf': round(total_pf, 2),
                'total_tax': round(total_tax, 2),
                'total_deductions': round(total_deductions, 2),
                'total_net': round(total_net, 2)
            },
            'payroll_data': payroll_data
        }

class PayrollSummaryReport:
    def generate_payroll_summary(self, organization, filters=None):
        """
        Generate department/company-wide payroll summary
        """
        filters = filters or {}
        
        # Get payroll period
        payroll_period_id = filters.get('payroll_period')
        if payroll_period_id:
            payroll_period = PayrollPeriod.objects.get(id=payroll_period_id, organization=organization)
        else:
            # Get latest payroll period
            payroll_period = PayrollPeriod.objects.filter(
                organization=organization,
                status='completed'
            ).order_by('-start_date').first()
        
        if not payroll_period:
            return {
                'report_name': 'Payroll Summary',
                'generated_on': timezone.now().strftime('%d-%m-%Y %H:%M:%S'),
                'error': 'No completed payroll periods found'
            }
        
        # Get payslips for the period
        payslips = Payslip.objects.filter(
            payroll_period=payroll_period,
            organization=organization
        ).select_related('employee', 'employee__department')
        
        # Company-wide totals
        company_totals = payslips.aggregate(
            total_employees=Count('id'),
            total_basic=Sum('basic_salary'),
            total_allowances=Sum('allowances'),
            total_overtime=Sum('overtime_pay'),
            total_bonus=Sum('bonus'),
            total_gross=Sum('gross_salary'),
            total_pf=Sum('provident_fund'),
            total_tax=Sum('tax_deduction'),
            total_deductions=Sum('total_deductions'),
            total_net=Sum('net_salary'),
            avg_salary=Avg('net_salary')
        )
        
        # Department-wise summary
        department_summary = payslips.values(
            'employee__department__name'
        ).annotate(
            employee_count=Count('id'),
            total_basic=Sum('basic_salary'),
            total_allowances=Sum('allowances'),
            total_gross=Sum('gross_salary'),
            total_deductions=Sum('total_deductions'),
            total_net=Sum('net_salary'),
            avg_salary=Avg('net_salary')
        ).order_by('-total_net')
        
        dept_summary_data = []
        for dept in department_summary:
            dept_summary_data.append({
                'department': dept['employee__department__name'] or 'Not Assigned',
                'employee_count': dept['employee_count'],
                'total_basic': dept['total_basic'] or 0,
                'total_allowances': dept['total_allowances'] or 0,
                'total_gross': dept['total_gross'] or 0,
                'total_deductions': dept['total_deductions'] or 0,
                'total_net': dept['total_net'] or 0,
                'avg_salary': dept['avg_salary'] or 0
            })
        
        # Salary range distribution
        salary_ranges = [
            ('< 20000', 0, 20000),
            ('20000 - 40000', 20000, 40000),
            ('40000 - 60000', 40000, 60000),
            ('60000 - 80000', 60000, 80000),
            ('80000 - 100000', 80000, 100000),
            ('> 100000', 100000, 999999999)
        ]
        
        salary_distribution = []
        for range_name, min_sal, max_sal in salary_ranges:
            count = payslips.filter(net_salary__gte=min_sal, net_salary__lt=max_sal).count()
            percentage = (count / company_totals['total_employees'] * 100) if company_totals['total_employees'] > 0 else 0
            salary_distribution.append({
                'range': range_name,
                'count': count,
                'percentage': round(percentage, 1)
            })
        
        return {
            'report_name': 'Payroll Summary',
            'generated_on': timezone.now().strftime('%d-%m-%Y %H:%M:%S'),
            'payroll_period': payroll_period.name,
            'period': f"{payroll_period.start_date.strftime('%d-%m-%Y')} to {payroll_period.end_date.strftime('%d-%m-%Y')}",
            'pay_date': payroll_period.pay_date.strftime('%d-%m-%Y'),
            'filters': filters,
            'company_summary': {
                'total_employees': company_totals['total_employees'] or 0,
                'total_basic': round(company_totals['total_basic'] or 0, 2),
                'total_allowances': round(company_totals['total_allowances'] or 0, 2),
                'total_overtime': round(company_totals['total_overtime'] or 0, 2),
                'total_bonus': round(company_totals['total_bonus'] or 0, 2),
                'total_gross': round(company_totals['total_gross'] or 0, 2),
                'total_pf': round(company_totals['total_pf'] or 0, 2),
                'total_tax': round(company_totals['total_tax'] or 0, 2),
                'total_deductions': round(company_totals['total_deductions'] or 0, 2),
                'total_net': round(company_totals['total_net'] or 0, 2),
                'avg_salary': round(company_totals['avg_salary'] or 0, 2)
            },
            'department_summary': dept_summary_data,
            'salary_distribution': salary_distribution
        }

class PayrollVarianceReport:
    def generate_payroll_variance(self, organization, filters=None):
        """
        Generate payroll variance report comparing with previous period
        """
        filters = filters or {}
        
        # Get current payroll period
        current_period_id = filters.get('current_period')
        if current_period_id:
            current_period = PayrollPeriod.objects.get(id=current_period_id, organization=organization)
        else:
            # Get latest payroll period
            current_period = PayrollPeriod.objects.filter(
                organization=organization,
                status='completed'
            ).order_by('-start_date').first()
        
        if not current_period:
            return {
                'report_name': 'Payroll Variance Report',
                'generated_on': timezone.now().strftime('%d-%m-%Y %H:%M:%S'),
                'error': 'No completed payroll periods found'
            }
        
        # Get previous payroll period
        previous_period = PayrollPeriod.objects.filter(
            organization=organization,
            status='completed',
            start_date__lt=current_period.start_date
        ).order_by('-start_date').first()
        
        if not previous_period:
            return {
                'report_name': 'Payroll Variance Report',
                'generated_on': timezone.now().strftime('%d-%m-%Y %H:%M:%S'),
                'error': 'No previous payroll period found for comparison'
            }
        
        # Get payslips for both periods
        current_payslips = Payslip.objects.filter(
            payroll_period=current_period,
            organization=organization
        )
        
        previous_payslips = Payslip.objects.filter(
            payroll_period=previous_period,
            organization=organization
        )
        
        # Current period totals
        current_totals = current_payslips.aggregate(
            total_employees=Count('id'),
            total_basic=Sum('basic_salary'),
            total_allowances=Sum('allowances'),
            total_gross=Sum('gross_salary'),
            total_deductions=Sum('total_deductions'),
            total_net=Sum('net_salary')
        )
        
        # Previous period totals
        previous_totals = previous_payslips.aggregate(
            total_employees=Count('id'),
            total_basic=Sum('basic_salary'),
            total_allowances=Sum('allowances'),
            total_gross=Sum('gross_salary'),
            total_deductions=Sum('total_deductions'),
            total_net=Sum('net_salary')
        )
        
        # Calculate variances
        def calculate_variance(current, previous):
            if previous == 0:
                return 0, 0
            variance_amount = current - previous
            variance_percentage = (variance_amount / previous) * 100
            return round(variance_amount, 2), round(variance_percentage, 2)
        
        employee_variance_amt, employee_variance_pct = calculate_variance(
            current_totals['total_employees'] or 0,
            previous_totals['total_employees'] or 0
        )
        
        basic_variance_amt, basic_variance_pct = calculate_variance(
            current_totals['total_basic'] or 0,
            previous_totals['total_basic'] or 0
        )
        
        allowances_variance_amt, allowances_variance_pct = calculate_variance(
            current_totals['total_allowances'] or 0,
            previous_totals['total_allowances'] or 0
        )
        
        gross_variance_amt, gross_variance_pct = calculate_variance(
            current_totals['total_gross'] or 0,
            previous_totals['total_gross'] or 0
        )
        
        deductions_variance_amt, deductions_variance_pct = calculate_variance(
            current_totals['total_deductions'] or 0,
            previous_totals['total_deductions'] or 0
        )
        
        net_variance_amt, net_variance_pct = calculate_variance(
            current_totals['total_net'] or 0,
            previous_totals['total_net'] or 0
        )
        
        # Department-wise variance
        current_dept = current_payslips.values('employee__department__name').annotate(
            total_net=Sum('net_salary')
        )
        
        previous_dept = previous_payslips.values('employee__department__name').annotate(
            total_net=Sum('net_salary')
        )
        
        department_variance = []
        for current in current_dept:
            dept_name = current['employee__department__name'] or 'Not Assigned'
            current_net = current['total_net'] or 0
            
            # Find matching department in previous period
            previous_net = 0
            for prev in previous_dept:
                if prev['employee__department__name'] == dept_name:
                    previous_net = prev['total_net'] or 0
                    break
            
            variance_amt, variance_pct = calculate_variance(current_net, previous_net)
            
            department_variance.append({
                'department': dept_name,
                'current_amount': current_net,
                'previous_amount': previous_net,
                'variance_amount': variance_amt,
                'variance_percentage': variance_pct
            })
        
        return {
            'report_name': 'Payroll Variance Report',
            'generated_on': timezone.now().strftime('%d-%m-%Y %H:%M:%S'),
            'current_period': current_period.name,
            'previous_period': previous_period.name,
            'current_period_dates': f"{current_period.start_date.strftime('%d-%m-%Y')} to {current_period.end_date.strftime('%d-%m-%Y')}",
            'previous_period_dates': f"{previous_period.start_date.strftime('%d-%m-%Y')} to {previous_period.end_date.strftime('%d-%m-%Y')}",
            'filters': filters,
            'summary_variance': {
                'employees': {
                    'current': current_totals['total_employees'] or 0,
                    'previous': previous_totals['total_employees'] or 0,
                    'variance_amount': employee_variance_amt,
                    'variance_percentage': employee_variance_pct
                },
                'basic_salary': {
                    'current': round(current_totals['total_basic'] or 0, 2),
                    'previous': round(previous_totals['total_basic'] or 0, 2),
                    'variance_amount': basic_variance_amt,
                    'variance_percentage': basic_variance_pct
                },
                'allowances': {
                    'current': round(current_totals['total_allowances'] or 0, 2),
                    'previous': round(previous_totals['total_allowances'] or 0, 2),
                    'variance_amount': allowances_variance_amt,
                    'variance_percentage': allowances_variance_pct
                },
                'gross_salary': {
                    'current': round(current_totals['total_gross'] or 0, 2),
                    'previous': round(previous_totals['total_gross'] or 0, 2),
                    'variance_amount': gross_variance_amt,
                    'variance_percentage': gross_variance_pct
                },
                'deductions': {
                    'current': round(current_totals['total_deductions'] or 0, 2),
                    'previous': round(previous_totals['total_deductions'] or 0, 2),
                    'variance_amount': deductions_variance_amt,
                    'variance_percentage': deductions_variance_pct
                },
                'net_salary': {
                    'current': round(current_totals['total_net'] or 0, 2),
                    'previous': round(previous_totals['total_net'] or 0, 2),
                    'variance_amount': net_variance_amt,
                    'variance_percentage': net_variance_pct
                }
            },
            'department_variance': department_variance
        }