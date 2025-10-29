from django.db.models import Q, Count, Sum, Avg, Min, Max
from django.utils import timezone
from datetime import datetime, date, timedelta
from payroll.models import Payslip, PayslipComponent, SalaryStructure
from hrm.models import Employee, Department, Designation, Payhead, EmployeePayhead
from django.db.models import F

class ProvidentFundReport:
    def generate_provident_fund_report(self, organization, filters=None):
        """
        Generate PF contributions report (employee + employer)
        """
        filters = filters or {}
        
        # Get payslips with PF deductions
        payslips = Payslip.objects.filter(
            organization=organization,
            is_generated=True,
            provident_fund__gt=0
        ).select_related('employee', 'employee__department', 'employee__designation', 'payroll_period')
        
        # Apply filters
        if filters.get('department'):
            payslips = payslips.filter(employee__department_id=filters['department'])
        
        if filters.get('employee_id'):
            payslips = payslips.filter(employee__employee_id__icontains=filters['employee_id'])
        
        if filters.get('start_date') and filters.get('end_date'):
            payslips = payslips.filter(
                payroll_period__start_date__gte=filters['start_date'],
                payroll_period__end_date__lte=filters['end_date']
            )
        
        pf_data = []
        total_employee_contribution = 0
        total_employer_contribution = 0
        
        for payslip in payslips:
            # Assuming employer contribution is 12% of basic (standard in many countries)
            # Adjust this calculation based on your organization's policy
            employee_contribution = float(payslip.provident_fund)
            employer_contribution = float(payslip.basic_salary) * 0.12  # 12% employer contribution
            
            total_contribution = employee_contribution + employer_contribution
            
            pf_data.append({
                'employee_id': payslip.employee.employee_id,
                'full_name': payslip.employee.full_name,
                'department': payslip.employee.department.name if payslip.employee.department else 'N/A',
                'designation': payslip.employee.designation.name if payslip.employee.designation else 'N/A',
                'payroll_period': payslip.payroll_period.name,
                'pay_date': payslip.payroll_period.pay_date,
                'basic_salary': float(payslip.basic_salary),
                'employee_contribution': employee_contribution,
                'employer_contribution': round(employer_contribution, 2),
                'total_contribution': round(total_contribution, 2),
                'pf_number': getattr(payslip.employee, 'pf_number', 'N/A')  # Add PF number field to Employee model if needed
            })
            
            total_employee_contribution += employee_contribution
            total_employer_contribution += employer_contribution
        
        total_contribution = total_employee_contribution + total_employer_contribution
        
        return {
            'report_name': 'Provident Fund Report',
            'generated_on': timezone.now().strftime('%d-%m-%Y %H:%M:%S'),
            'filters': filters,
            'summary': {
                'total_employees': len(pf_data),
                'total_payslips': payslips.count(),
                'total_employee_contribution': round(total_employee_contribution, 2),
                'total_employer_contribution': round(total_employer_contribution, 2),
                'total_contribution': round(total_contribution, 2),
                'avg_employee_contribution': round(total_employee_contribution / len(pf_data), 2) if pf_data else 0
            },
            'pf_data': pf_data
        }

class TaxDeductionReport:
    def generate_tax_deduction_report(self, organization, filters=None):
        """
        Generate TDS calculations and summaries
        """
        filters = filters or {}
        
        # Get payslips with tax deductions
        payslips = Payslip.objects.filter(
            organization=organization,
            is_generated=True,
            tax_deduction__gt=0
        ).select_related('employee', 'employee__department', 'employee__designation', 'payroll_period')
        
        # Apply filters
        if filters.get('department'):
            payslips = payslips.filter(employee__department_id=filters['department'])
        
        if filters.get('employee_id'):
            payslips = payslips.filter(employee__employee_id__icontains=filters['employee_id'])
        
        if filters.get('start_date') and filters.get('end_date'):
            payslips = payslips.filter(
                payroll_period__start_date__gte=filters['start_date'],
                payroll_period__end_date__lte=filters['end_date']
            )
        
        tax_data = []
        total_tax_deduction = 0
        
        for payslip in payslips:
            tax_amount = float(payslip.tax_deduction)
            annual_estimated_tax = tax_amount * 12  # Simple estimation
            
            tax_data.append({
                'employee_id': payslip.employee.employee_id,
                'full_name': payslip.employee.full_name,
                'department': payslip.employee.department.name if payslip.employee.department else 'N/A',
                'designation': payslip.employee.designation.name if payslip.employee.designation else 'N/A',
                'pan_number': getattr(payslip.employee, 'pan_number', 'N/A'),  # Add PAN field to Employee model
                'payroll_period': payslip.payroll_period.name,
                'pay_date': payslip.payroll_period.pay_date,
                'gross_salary': float(payslip.gross_salary),
                'taxable_income': float(payslip.gross_salary),  # Adjust based on your tax calculation
                'tax_deducted': tax_amount,
                'annual_estimated_tax': round(annual_estimated_tax, 2),
                'tax_slab': self._get_tax_slab(float(payslip.gross_salary) * 12),  # Annual income
                'financial_year': self._get_financial_year(payslip.payroll_period.start_date)
            })
            
            total_tax_deduction += tax_amount
        
        # Tax slab summary
        tax_slabs = {}
        for data in tax_data:
            slab = data['tax_slab']
            if slab not in tax_slabs:
                tax_slabs[slab] = {'employee_count': 0, 'total_tax': 0}
            tax_slabs[slab]['employee_count'] += 1
            tax_slabs[slab]['total_tax'] += data['tax_deducted']
        
        return {
            'report_name': 'Tax Deduction Report',
            'generated_on': timezone.now().strftime('%d-%m-%Y %H:%M:%S'),
            'filters': filters,
            'summary': {
                'total_employees': len(tax_data),
                'total_payslips': payslips.count(),
                'total_tax_deduction': round(total_tax_deduction, 2),
                'avg_tax_per_employee': round(total_tax_deduction / len(tax_data), 2) if tax_data else 0,
                'financial_year': tax_data[0]['financial_year'] if tax_data else 'N/A'
            },
            'tax_slabs': tax_slabs,
            'tax_data': tax_data
        }
    
    def _get_tax_slab(self, annual_income):
        """Determine tax slab based on annual income (Indian tax slabs as example)"""
        if annual_income <= 250000:
            return "No Tax"
        elif annual_income <= 500000:
            return "5% Slab"
        elif annual_income <= 1000000:
            return "20% Slab"
        else:
            return "30% Slab"
    
    def _get_financial_year(self, date_obj):
        """Get financial year from date"""
        year = date_obj.year
        if date_obj.month >= 4:  # April to March financial year
            return f"{year}-{year + 1}"
        else:
            return f"{year - 1}-{year}"

class ESIReport:
    def generate_esi_report(self, organization, filters=None):
        """
        Generate ESI contributions report (if applicable)
        """
        filters = filters or {}
        
        # Get employees eligible for ESI (based on salary threshold)
        # ESI typically applies to employees with gross salary up to a certain limit
        esi_salary_limit = 21000  # Example limit, adjust based on your country's rules
        
        payslips = Payslip.objects.filter(
            organization=organization,
            is_generated=True,
            gross_salary__lte=esi_salary_limit
        ).select_related('employee', 'employee__department', 'employee__designation', 'payroll_period')
        
        # Apply filters
        if filters.get('department'):
            payslips = payslips.filter(employee__department_id=filters['department'])
        
        if filters.get('employee_id'):
            payslips = payslips.filter(employee__employee_id__icontains=filters['employee_id'])
        
        if filters.get('start_date') and filters.get('end_date'):
            payslips = payslips.filter(
                payroll_period__start_date__gte=filters['start_date'],
                payroll_period__end_date__lte=filters['end_date']
            )
        
        esi_data = []
        total_employee_contribution = 0
        total_employer_contribution = 0
        
        for payslip in payslips:
            gross_salary = float(payslip.gross_salary)
            
            # ESI calculation (example rates: 0.75% employee, 3.25% employer)
            employee_contribution = gross_salary * 0.0075  # 0.75%
            employer_contribution = gross_salary * 0.0325  # 3.25%
            total_contribution = employee_contribution + employer_contribution
            
            esi_data.append({
                'employee_id': payslip.employee.employee_id,
                'full_name': payslip.employee.full_name,
                'department': payslip.employee.department.name if payslip.employee.department else 'N/A',
                'designation': payslip.employee.designation.name if payslip.employee.designation else 'N/A',
                'esi_number': getattr(payslip.employee, 'esi_number', 'N/A'),  # Add ESI number field
                'payroll_period': payslip.payroll_period.name,
                'pay_date': payslip.payroll_period.pay_date,
                'gross_salary': gross_salary,
                'employee_contribution': round(employee_contribution, 2),
                'employer_contribution': round(employer_contribution, 2),
                'total_contribution': round(total_contribution, 2),
                'is_eligible': gross_salary <= esi_salary_limit
            })
            
            total_employee_contribution += employee_contribution
            total_employer_contribution += employer_contribution
        
        total_contribution = total_employee_contribution + total_employer_contribution
        
        return {
            'report_name': 'ESI Report',
            'generated_on': timezone.now().strftime('%d-%m-%Y %H:%M:%S'),
            'filters': filters,
            'summary': {
                'total_employees': len(esi_data),
                'total_payslips': payslips.count(),
                'total_employee_contribution': round(total_employee_contribution, 2),
                'total_employer_contribution': round(total_employer_contribution, 2),
                'total_contribution': round(total_contribution, 2),
                'salary_limit': esi_salary_limit,
                'eligible_employees': len([d for d in esi_data if d['is_eligible']])
            },
            'esi_data': esi_data
        }

class GratuityReport:
    def generate_gratuity_report(self, organization, filters=None):
        """
        Generate gratuity calculations and summaries
        """
        filters = filters or {}
        
        # Get employees eligible for gratuity (typically after 5 years of service)
        employees = Employee.objects.filter(
            organization=organization,
            is_active=True
        ).select_related('department', 'designation')
        
        # Apply filters
        if filters.get('department'):
            employees = employees.filter(department_id=filters['department'])
        
        if filters.get('employee_id'):
            employees = employees.filter(employee_id__icontains=filters['employee_id'])
        
        gratuity_data = []
        total_gratuity_liability = 0
        
        for employee in employees:
            # Calculate years of service
            today = timezone.now().date()
            years_of_service = (today - employee.hire_date).days / 365.25
            
            if years_of_service >= 5:  # Eligible for gratuity
                # Gratuity calculation: (Last drawn salary * 15/26) * Number of years of service
                last_basic_salary = float(employee.basic_salary or 0)
                gratuity_amount = (last_basic_salary * 15 / 26) * years_of_service
                
                gratuity_data.append({
                    'employee_id': employee.employee_id,
                    'full_name': employee.full_name,
                    'department': employee.department.name if employee.department else 'N/A',
                    'designation': employee.designation.name if employee.designation else 'N/A',
                    'hire_date': employee.hire_date,
                    'years_of_service': round(years_of_service, 2),
                    'last_basic_salary': last_basic_salary,
                    'gratuity_amount': round(gratuity_amount, 2),
                    'eligibility_status': 'Eligible',
                    'completion_date': employee.hire_date + timedelta(days=5*365)  # 5 years completion date
                })
                
                total_gratuity_liability += gratuity_amount
            else:
                years_remaining = 5 - years_of_service
                gratuity_data.append({
                    'employee_id': employee.employee_id,
                    'full_name': employee.full_name,
                    'department': employee.department.name if employee.department else 'N/A',
                    'designation': employee.designation.name if employee.designation else 'N/A',
                    'hire_date': employee.hire_date,
                    'years_of_service': round(years_of_service, 2),
                    'last_basic_salary': float(employee.basic_salary or 0),
                    'gratuity_amount': 0,
                    'eligibility_status': 'Not Eligible',
                    'years_remaining': round(years_remaining, 2) if years_remaining > 0 else 0
                })
        
        # Sort by gratuity amount (highest first)
        gratuity_data.sort(key=lambda x: x['gratuity_amount'], reverse=True)
        
        eligible_employees = [emp for emp in gratuity_data if emp['eligibility_status'] == 'Eligible']
        
        return {
            'report_name': 'Gratuity Report',
            'generated_on': timezone.now().strftime('%d-%m-%Y %H:%M:%S'),
            'filters': filters,
            'summary': {
                'total_employees': len(gratuity_data),
                'eligible_employees': len(eligible_employees),
                'total_gratuity_liability': round(total_gratuity_liability, 2),
                'avg_gratuity_per_employee': round(total_gratuity_liability / len(eligible_employees), 2) if eligible_employees else 0,
                'avg_years_of_service': round(sum(emp['years_of_service'] for emp in gratuity_data) / len(gratuity_data), 2) if gratuity_data else 0
            },
            'gratuity_data': gratuity_data
        }