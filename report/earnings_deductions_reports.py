from django.db.models import Q, Count, Sum, Avg, Min, Max
from django.utils import timezone
from datetime import datetime, date, timedelta
from payroll.models import Payslip, PayslipComponent, SalaryStructure
from hrm.models import Employee, Department, Designation, Payhead, EmployeePayhead
from django.db.models import F

class EarningsBreakdownReport:
    def generate_earnings_breakdown_report(self, organization, filters=None):
        """
        Generate detailed earnings breakdown (allowances, overtime, bonuses)
        """
        filters = filters or {}
        
        # Get payslips for the organization
        payslips = Payslip.objects.filter(
            organization=organization,
            is_generated=True
        ).select_related('employee', 'employee__department', 'employee__designation')
        
        # Apply filters
        if filters.get('department'):
            payslips = payslips.filter(employee__department_id=filters['department'])
        
        if filters.get('designation'):
            payslips = payslips.filter(employee__designation_id=filters['designation'])
        
        if filters.get('employee_id'):
            payslips = payslips.filter(employee__employee_id__icontains=filters['employee_id'])
        
        if filters.get('start_date') and filters.get('end_date'):
            payslips = payslips.filter(
                payroll_period__start_date__gte=filters['start_date'],
                payroll_period__end_date__lte=filters['end_date']
            )
        
        # Get payslip components for detailed breakdown
        components = PayslipComponent.objects.filter(
            payslip__in=payslips,
            component_type='earning'
        ).select_related('payslip', 'payslip__employee', 'payhead')
        
        # Group earnings by type
        earnings_data = []
        earnings_summary = {}
        
        for component in components:
            employee = component.payslip.employee
            component_name = component.component_name
            
            if component_name not in earnings_summary:
                earnings_summary[component_name] = {
                    'total_amount': 0,
                    'employee_count': set(),
                    'payhead_code': component.payhead.code if component.payhead else '',
                    'calculation_type': component.calculation_type
                }
            
            earnings_summary[component_name]['total_amount'] += float(component.amount)
            earnings_summary[component_name]['employee_count'].add(employee.id)
            
            # Individual employee earnings
            earnings_data.append({
                'employee_id': employee.employee_id,
                'full_name': employee.full_name,
                'department': employee.department.name if employee.department else 'N/A',
                'designation': employee.designation.name if employee.designation else 'N/A',
                'payroll_period': component.payslip.payroll_period.name,
                'component_name': component_name,
                'payhead_code': component.payhead.code if component.payhead else '',
                'calculation_type': component.calculation_type,
                'amount': float(component.amount),
                'pay_date': component.payslip.payroll_period.pay_date
            })
        
        # Calculate summary statistics
        total_earnings = sum(item['total_amount'] for item in earnings_summary.values())
        
        # Convert sets to counts
        for component_name, data in earnings_summary.items():
            data['employee_count'] = len(data['employee_count'])
            data['avg_per_employee'] = round(data['total_amount'] / data['employee_count'], 2) if data['employee_count'] > 0 else 0
        
        return {
            'report_name': 'Earnings Breakdown Report',
            'generated_on': timezone.now().strftime('%d-%m-%Y %H:%M:%S'),
            'filters': filters,
            'summary': {
                'total_employees': len(set(comp.payslip.employee.id for comp in components)),
                'total_payslips': payslips.count(),
                'total_earnings': round(total_earnings, 2),
                'earning_components': len(earnings_summary)
            },
            'earnings_summary': earnings_summary,
            'earnings_data': earnings_data
        }

class DeductionsSummaryReport:
    def generate_deductions_summary_report(self, organization, filters=None):
        """
        Generate detailed deductions summary (PF, tax, other deductions)
        """
        filters = filters or {}
        
        # Get payslips for the organization
        payslips = Payslip.objects.filter(
            organization=organization,
            is_generated=True
        ).select_related('employee', 'employee__department', 'employee__designation')
        
        # Apply filters
        if filters.get('department'):
            payslips = payslips.filter(employee__department_id=filters['department'])
        
        if filters.get('designation'):
            payslips = payslips.filter(employee__designation_id=filters['designation'])
        
        if filters.get('employee_id'):
            payslips = payslips.filter(employee__employee_id__icontains=filters['employee_id'])
        
        if filters.get('start_date') and filters.get('end_date'):
            payslips = payslips.filter(
                payroll_period__start_date__gte=filters['start_date'],
                payroll_period__end_date__lte=filters['end_date']
            )
        
        # Get payslip components for detailed breakdown
        components = PayslipComponent.objects.filter(
            payslip__in=payslips,
            component_type='deduction'
        ).select_related('payslip', 'payslip__employee', 'payhead')
        
        # Group deductions by type
        deductions_data = []
        deductions_summary = {}
        
        for component in components:
            employee = component.payslip.employee
            component_name = component.component_name
            
            if component_name not in deductions_summary:
                deductions_summary[component_name] = {
                    'total_amount': 0,
                    'employee_count': set(),
                    'payhead_code': component.payhead.code if component.payhead else '',
                    'calculation_type': component.calculation_type,
                    'is_statutory': component_name.lower() in ['pf', 'tax', 'tds', 'esi']
                }
            
            deductions_summary[component_name]['total_amount'] += float(component.amount)
            deductions_summary[component_name]['employee_count'].add(employee.id)
            
            # Individual employee deductions
            deductions_data.append({
                'employee_id': employee.employee_id,
                'full_name': employee.full_name,
                'department': employee.department.name if employee.department else 'N/A',
                'designation': employee.designation.name if employee.designation else 'N/A',
                'payroll_period': component.payslip.payroll_period.name,
                'component_name': component_name,
                'payhead_code': component.payhead.code if component.payhead else '',
                'calculation_type': component.calculation_type,
                'amount': float(component.amount),
                'pay_date': component.payslip.payroll_period.pay_date,
                'is_statutory': component_name.lower() in ['pf', 'tax', 'tds', 'esi']
            })
        
        # Calculate summary statistics
        total_deductions = sum(item['total_amount'] for item in deductions_summary.values())
        statutory_deductions = sum(item['total_amount'] for item in deductions_summary.values() 
                                 if item['is_statutory'])
        
        # Convert sets to counts
        for component_name, data in deductions_summary.items():
            data['employee_count'] = len(data['employee_count'])
            data['avg_per_employee'] = round(data['total_amount'] / data['employee_count'], 2) if data['employee_count'] > 0 else 0
        
        return {
            'report_name': 'Deductions Summary Report',
            'generated_on': timezone.now().strftime('%d-%m-%Y %H:%M:%S'),
            'filters': filters,
            'summary': {
                'total_employees': len(set(comp.payslip.employee.id for comp in components)),
                'total_payslips': payslips.count(),
                'total_deductions': round(total_deductions, 2),
                'statutory_deductions': round(statutory_deductions, 2),
                'non_statutory_deductions': round(total_deductions - statutory_deductions, 2),
                'deduction_components': len(deductions_summary)
            },
            'deductions_summary': deductions_summary,
            'deductions_data': deductions_data
        }

class PayheadAnalysisReport:
    def generate_payhead_analysis_report(self, organization, filters=None):
        """
        Generate payhead-wise totals and analysis
        """
        filters = filters or {}
        
        # Get all payheads for the organization
        payheads = Payhead.objects.filter(
            organization=organization,
            is_active=True
        )
        
        # Get payslip components
        components = PayslipComponent.objects.filter(
            payslip__organization=organization,
            payslip__is_generated=True
        ).select_related('payslip', 'payslip__employee', 'payhead')
        
        # Apply filters
        if filters.get('start_date') and filters.get('end_date'):
            components = components.filter(
                payslip__payroll_period__start_date__gte=filters['start_date'],
                payslip__payroll_period__end_date__lte=filters['end_date']
            )
        
        if filters.get('payhead_type'):
            components = components.filter(payhead__payhead_type=filters['payhead_type'])
        
        # Group by payhead
        payhead_analysis = {}
        
        for component in components:
            payhead = component.payhead
            if payhead and payhead.code not in payhead_analysis:
                payhead_analysis[payhead.code] = {
                    'name': payhead.name,
                    'code': payhead.code,
                    'type': payhead.payhead_type,
                    'calculation_type': payhead.calculation_type,
                    'total_amount': 0,
                    'employee_count': set(),
                    'payslip_count': set(),
                    'min_amount': float('inf'),
                    'max_amount': 0,
                    'is_statutory': payhead.statutory_code is not None
                }
            
            if payhead and payhead.code in payhead_analysis:
                data = payhead_analysis[payhead.code]
                amount = float(component.amount)
                
                data['total_amount'] += amount
                data['employee_count'].add(component.payslip.employee.id)
                data['payslip_count'].add(component.payslip.id)
                data['min_amount'] = min(data['min_amount'], amount)
                data['max_amount'] = max(data['max_amount'], amount)
        
        # Calculate averages and clean up data
        for payhead_code, data in payhead_analysis.items():
            data['employee_count'] = len(data['employee_count'])
            data['payslip_count'] = len(data['payslip_count'])
            data['avg_per_employee'] = round(data['total_amount'] / data['employee_count'], 2) if data['employee_count'] > 0 else 0
            data['avg_per_payslip'] = round(data['total_amount'] / data['payslip_count'], 2) if data['payslip_count'] > 0 else 0
            data['min_amount'] = round(data['min_amount'], 2) if data['min_amount'] != float('inf') else 0
            data['max_amount'] = round(data['max_amount'], 2)
        
        # Separate earnings and deductions
        earnings_payheads = {k: v for k, v in payhead_analysis.items() if v['type'] == 'earning'}
        deductions_payheads = {k: v for k, v in payhead_analysis.items() if v['type'] == 'deduction'}
        
        # Summary statistics
        total_earnings = sum(item['total_amount'] for item in earnings_payheads.values())
        total_deductions = sum(item['total_amount'] for item in deductions_payheads.values())
        
        return {
            'report_name': 'Payhead Analysis Report',
            'generated_on': timezone.now().strftime('%d-%m-%Y %H:%M:%S'),
            'filters': filters,
            'summary': {
                'total_payheads': len(payhead_analysis),
                'earning_payheads': len(earnings_payheads),
                'deduction_payheads': len(deductions_payheads),
                'total_earnings': round(total_earnings, 2),
                'total_deductions': round(total_deductions, 2),
                'net_amount': round(total_earnings - total_deductions, 2)
            },
            'earnings_payheads': earnings_payheads,
            'deductions_payheads': deductions_payheads,
            'all_payheads': payhead_analysis
        }