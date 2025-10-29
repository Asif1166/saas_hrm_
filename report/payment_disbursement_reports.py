from django.db.models import Q, Count, Sum, Avg, Min, Max
from django.utils import timezone
from datetime import datetime, date, timedelta
from payroll.models import Payslip, PayrollPeriod
from hrm.models import Employee, Department, Designation
from django.db.models import F

class BankTransferReport:
    def generate_bank_transfer_report(self, organization, filters=None):
        """
        Generate bank transfer report for salary processing
        """
        filters = filters or {}
        
        # Get generated payslips
        payslips = Payslip.objects.filter(
            organization=organization,
            is_generated=True
        ).select_related(
            'employee', 
            'employee__department', 
            'employee__designation',
            'payroll_period'
        )
        
        # Apply filters
        if filters.get('department'):
            payslips = payslips.filter(employee__department_id=filters['department'])
        
        if filters.get('designation'):
            payslips = payslips.filter(employee__designation_id=filters['designation'])
        
        if filters.get('employee_id'):
            payslips = payslips.filter(employee__employee_id__icontains=filters['employee_id'])
        
        if filters.get('payroll_period'):
            payslips = payslips.filter(payroll_period_id=filters['payroll_period'])
        
        if filters.get('start_date') and filters.get('end_date'):
            payslips = payslips.filter(
                payroll_period__start_date__gte=filters['start_date'],
                payroll_period__end_date__lte=filters['end_date']
            )
        
        bank_data = []
        total_transfer_amount = 0
        
        for payslip in payslips:
            employee = payslip.employee
            net_salary = float(payslip.net_salary)
            
            bank_data.append({
                'employee_id': employee.employee_id,
                'full_name': employee.full_name,
                'department': employee.department.name if employee.department else 'N/A',
                'designation': employee.designation.name if employee.designation else 'N/A',
                'bank_name': employee.bank_name or 'Not Provided',
                'bank_account_number': employee.bank_account_number or 'Not Provided',
                'bank_routing_number': employee.bank_routing_number or 'N/A',
                'payroll_period': payslip.payroll_period.name,
                'pay_date': payslip.payroll_period.pay_date,
                'net_salary': net_salary,
                'ifsc_code': getattr(employee, 'ifsc_code', 'N/A'),  # Add IFSC field to Employee model
                'account_type': getattr(employee, 'account_type', 'Savings'),  # Add account_type field
                'payment_status': 'Processed',  # You can add payment status field to Payslip
                'transfer_reference': f"SAL_{payslip.payroll_period.name}_{employee.employee_id}"
            })
            
            total_transfer_amount += net_salary
        
        # Bank-wise summary
        bank_summary = {}
        for data in bank_data:
            bank_name = data['bank_name']
            if bank_name not in bank_summary:
                bank_summary[bank_name] = {
                    'employee_count': 0,
                    'total_amount': 0,
                    'accounts': set()
                }
            
            bank_summary[bank_name]['employee_count'] += 1
            bank_summary[bank_name]['total_amount'] += data['net_salary']
            bank_summary[bank_name]['accounts'].add(data['bank_account_number'])
        
        # Convert sets to counts
        for bank_name, data in bank_summary.items():
            data['account_count'] = len(data['accounts'])
            data['avg_per_account'] = round(data['total_amount'] / data['employee_count'], 2) if data['employee_count'] > 0 else 0
        
        return {
            'report_name': 'Bank Transfer Report',
            'generated_on': timezone.now().strftime('%d-%m-%Y %H:%M:%S'),
            'filters': filters,
            'summary': {
                'total_employees': len(bank_data),
                'total_payslips': payslips.count(),
                'total_transfer_amount': round(total_transfer_amount, 2),
                'unique_banks': len(bank_summary),
                'avg_salary_transfer': round(total_transfer_amount / len(bank_data), 2) if bank_data else 0
            },
            'bank_summary': bank_summary,
            'bank_data': bank_data
        }

class CashPaymentReport:
    def generate_cash_payment_report(self, organization, filters=None):
        """
        Generate cash payment report for employees paid in cash
        """
        filters = filters or {}
        
        # Get payroll periods
        payroll_periods = PayrollPeriod.objects.filter(
            organization=organization,
            status='completed'
        )
        
        # Apply date filters
        if filters.get('start_date') and filters.get('end_date'):
            payroll_periods = payroll_periods.filter(
                start_date__gte=filters['start_date'],
                end_date__lte=filters['end_date']
            )
        
        if filters.get('payroll_period'):
            payroll_periods = payroll_periods.filter(id=filters['payroll_period'])
        
        cash_data = []
        total_cash_amount = 0
        
        # In a real scenario, you might have a payment method field in Payslip
        # For this example, we'll assume some employees are paid in cash based on certain criteria
        for period in payroll_periods:
            # Get payslips for this period
            payslips = Payslip.objects.filter(
                payroll_period=period,
                is_generated=True
            ).select_related('employee', 'employee__department', 'employee__designation')
            
            # Apply additional filters
            if filters.get('department'):
                payslips = payslips.filter(employee__department_id=filters['department'])
            
            if filters.get('employee_id'):
                payslips = payslips.filter(employee__employee_id__icontains=filters['employee_id'])
            
            # Identify cash payments (example: employees without bank account or specific designation)
            for payslip in payslips:
                employee = payslip.employee
                
                # Example criteria for cash payment: no bank account or specific roles
                is_cash_payment = (
                    not employee.bank_account_number or 
                    employee.designation and employee.designation.name.lower() in ['helper', 'peon', 'security']
                )
                
                if is_cash_payment:
                    net_salary = float(payslip.net_salary)
                    
                    cash_data.append({
                        'employee_id': employee.employee_id,
                        'full_name': employee.full_name,
                        'department': employee.department.name if employee.department else 'N/A',
                        'designation': employee.designation.name if employee.designation else 'N/A',
                        'payroll_period': period.name,
                        'pay_date': period.pay_date,
                        'net_salary': net_salary,
                        'payment_method': 'Cash',
                        'payment_status': 'Paid',  # You can track actual payment status
                        'paid_by': 'Cashier',  # Add paid_by field
                        'payment_date': period.pay_date,
                        'receipt_number': f"CASH_{period.name}_{employee.employee_id}",
                        'reason_for_cash': 'No Bank Account' if not employee.bank_account_number else 'Designation Policy'
                    })
                    
                    total_cash_amount += net_salary
        
        # Department-wise cash payment summary
        dept_summary = {}
        for data in cash_data:
            dept = data['department']
            if dept not in dept_summary:
                dept_summary[dept] = {
                    'employee_count': 0,
                    'total_amount': 0
                }
            
            dept_summary[dept]['employee_count'] += 1
            dept_summary[dept]['total_amount'] += data['net_salary']
        
        # Calculate averages
        for dept, data in dept_summary.items():
            data['avg_per_employee'] = round(data['total_amount'] / data['employee_count'], 2)
        
        return {
            'report_name': 'Cash Payment Report',
            'generated_on': timezone.now().strftime('%d-%m-%Y %H:%M:%S'),
            'filters': filters,
            'summary': {
                'total_cash_employees': len(cash_data),
                'total_cash_amount': round(total_cash_amount, 2),
                'payroll_periods': len(set(data['payroll_period'] for data in cash_data)),
                'departments_with_cash': len(dept_summary),
                'avg_cash_payment': round(total_cash_amount / len(cash_data), 2) if cash_data else 0
            },
            'department_summary': dept_summary,
            'cash_data': cash_data
        }

class PaymentStatusReport:
    def generate_payment_status_report(self, organization, filters=None):
        """
        Generate payment status report (paid/pending payments)
        """
        filters = filters or {}
        
        # Get payroll periods
        payroll_periods = PayrollPeriod.objects.filter(
            organization=organization
        ).order_by('-start_date')
        
        # Apply filters
        if filters.get('start_date') and filters.get('end_date'):
            payroll_periods = payroll_periods.filter(
                start_date__gte=filters['start_date'],
                end_date__lte=filters['end_date']
            )
        
        if filters.get('payroll_period'):
            payroll_periods = payroll_periods.filter(id=filters['payroll_period'])
        
        if filters.get('status'):
            payroll_periods = payroll_periods.filter(status=filters['status'])
        
        payment_data = []
        period_summary = {}
        
        for period in payroll_periods:
            # Get all payslips for this period
            payslips = Payslip.objects.filter(
                payroll_period=period
            ).select_related('employee', 'employee__department', 'employee__designation')
            
            # Apply additional filters
            if filters.get('department'):
                payslips = payslips.filter(employee__department_id=filters['department'])
            
            if filters.get('employee_id'):
                payslips = payslips.filter(employee__employee_id__icontains=filters['employee_id'])
            
            # Calculate payment statistics for this period
            total_employees = payslips.count()
            generated_payslips = payslips.filter(is_generated=True)
            paid_count = generated_payslips.count()  # In real scenario, you might have a separate paid status
            pending_count = total_employees - paid_count
            
            total_amount = sum(float(p.net_salary) for p in generated_payslips)
            paid_amount = total_amount  # Assuming generated payslips are paid
            
            period_summary[period.name] = {
                'period_name': period.name,
                'start_date': period.start_date,
                'end_date': period.end_date,
                'pay_date': period.pay_date,
                'status': period.status,
                'total_employees': total_employees,
                'paid_count': paid_count,
                'pending_count': pending_count,
                'paid_amount': round(paid_amount, 2),
                'completion_rate': round((paid_count / total_employees * 100), 2) if total_employees > 0 else 0
            }
            
            # Detailed data for each employee in this period
            for payslip in payslips:
                payment_status = 'Paid' if payslip.is_generated else 'Pending'
                payment_date = payslip.generated_at if payslip.is_generated else None
                
                payment_data.append({
                    'employee_id': payslip.employee.employee_id,
                    'full_name': payslip.employee.full_name,
                    'department': payslip.employee.department.name if payslip.employee.department else 'N/A',
                    'designation': payslip.employee.designation.name if payslip.employee.designation else 'N/A',
                    'payroll_period': period.name,
                    'pay_date': period.pay_date,
                    'net_salary': float(payslip.net_salary) if payslip.is_generated else float(payslip.salary_structure.net_salary),
                    'payment_status': payment_status,
                    'payment_date': payment_date,
                    'payslip_generated': payslip.is_generated,
                    'generated_at': payslip.generated_at,
                    'payment_method': self._get_payment_method(payslip.employee),
                    'delay_days': self._calculate_delay_days(period.pay_date, payment_date) if payment_date else None
                })
        
        # Overall summary
        total_periods = len(period_summary)
        total_employees_all = sum(data['total_employees'] for data in period_summary.values())
        total_paid_all = sum(data['paid_count'] for data in period_summary.values())
        total_pending_all = sum(data['pending_count'] for data in period_summary.values())
        total_paid_amount = sum(data['paid_amount'] for data in period_summary.values())
        
        return {
            'report_name': 'Payment Status Report',
            'generated_on': timezone.now().strftime('%d-%m-%Y %H:%M:%S'),
            'filters': filters,
            'summary': {
                'total_periods': total_periods,
                'total_employees': total_employees_all,
                'paid_employees': total_paid_all,
                'pending_employees': total_pending_all,
                'total_paid_amount': round(total_paid_amount, 2),
                'overall_completion_rate': round((total_paid_all / total_employees_all * 100), 2) if total_employees_all > 0 else 0,
                'avg_payment_per_employee': round(total_paid_amount / total_paid_all, 2) if total_paid_all > 0 else 0
            },
            'period_summary': period_summary,
            'payment_data': payment_data
        }
    
    def _get_payment_method(self, employee):
        """Determine payment method based on employee data"""
        if employee.bank_account_number:
            return 'Bank Transfer'
        else:
            return 'Cash'
    
    def _calculate_delay_days(self, due_date, payment_date):
        """Calculate delay in payment"""
        if due_date and payment_date:
            payment_datetime = payment_date.date() if hasattr(payment_date, 'date') else payment_date
            due_datetime = due_date if isinstance(due_date, date) else due_date
            delay = (payment_datetime - due_datetime).days
            return max(0, delay)  # Return 0 if paid early
        return None

class PaymentReconciliationReport:
    def generate_payment_reconciliation_report(self, organization, filters=None):
        """
        Generate payment reconciliation report
        """
        filters = filters or {}
        
        # Get payroll periods
        payroll_periods = PayrollPeriod.objects.filter(
            organization=organization,
            status='completed'
        ).order_by('-start_date')
        
        # Apply filters
        if filters.get('start_date') and filters.get('end_date'):
            payroll_periods = payroll_periods.filter(
                start_date__gte=filters['start_date'],
                end_date__lte=filters['end_date']
            )
        
        if filters.get('payroll_period'):
            payroll_periods = payroll_periods.filter(id=filters['payroll_period'])
        
        reconciliation_data = []
        
        for period in payroll_periods:
            # Get payslips for this period
            payslips = Payslip.objects.filter(
                payroll_period=period,
                is_generated=True
            ).select_related('employee')
            
            # Calculate totals
            total_net_salary = sum(float(p.net_salary) for p in payslips)
            total_bank_transfers = sum(float(p.net_salary) for p in payslips if p.employee.bank_account_number)
            total_cash_payments = total_net_salary - total_bank_transfers
            
            # Count employees by payment method
            bank_employees = payslips.filter(employee__bank_account_number__isnull=False).count()
            cash_employees = payslips.filter(employee__bank_account_number__isnull=True).count()
            
            reconciliation_data.append({
                'payroll_period': period.name,
                'start_date': period.start_date,
                'end_date': period.end_date,
                'pay_date': period.pay_date,
                'total_employees': payslips.count(),
                'total_net_salary': round(total_net_salary, 2),
                'bank_transfers': {
                    'employee_count': bank_employees,
                    'total_amount': round(total_bank_transfers, 2),
                    'percentage': round((total_bank_transfers / total_net_salary * 100), 2) if total_net_salary > 0 else 0
                },
                'cash_payments': {
                    'employee_count': cash_employees,
                    'total_amount': round(total_cash_payments, 2),
                    'percentage': round((total_cash_payments / total_net_salary * 100), 2) if total_net_salary > 0 else 0
                },
                'reconciliation_status': 'Balanced' if abs(total_net_salary - (total_bank_transfers + total_cash_payments)) < 0.01 else 'Unbalanced',
                'variance': round(total_net_salary - (total_bank_transfers + total_cash_payments), 2)
            })
        
        # Overall reconciliation summary
        total_periods = len(reconciliation_data)
        total_net_all = sum(item['total_net_salary'] for item in reconciliation_data)
        total_bank_all = sum(item['bank_transfers']['total_amount'] for item in reconciliation_data)
        total_cash_all = sum(item['cash_payments']['total_amount'] for item in reconciliation_data)
        balanced_periods = len([item for item in reconciliation_data if item['reconciliation_status'] == 'Balanced'])
        
        return {
            'report_name': 'Payment Reconciliation Report',
            'generated_on': timezone.now().strftime('%d-%m-%Y %H:%M:%S'),
            'filters': filters,
            'summary': {
                'total_periods': total_periods,
                'balanced_periods': balanced_periods,
                'unbalanced_periods': total_periods - balanced_periods,
                'total_net_salary': round(total_net_all, 2),
                'total_bank_transfers': round(total_bank_all, 2),
                'total_cash_payments': round(total_cash_all, 2),
                'overall_variance': round(total_net_all - (total_bank_all + total_cash_all), 2),
                'balance_percentage': round((balanced_periods / total_periods * 100), 2) if total_periods > 0 else 0
            },
            'reconciliation_data': reconciliation_data
        }