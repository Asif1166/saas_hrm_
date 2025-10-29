# reports/salary_reports.py
from django.db.models import Q, Count, Sum, Avg, Min, Max
from django.utils import timezone
from datetime import datetime, date, timedelta
from payroll.models import SalaryStructure, Payslip
from hrm.models import Employee, Department, Designation
from django.db.models import F

class SalaryStructureReport:
    def generate_salary_structure_report(self, organization, filters=None):
        """
        Generate employee-wise salary breakdown
        """
        filters = filters or {}
        
        # Get salary structures
        salary_structures = SalaryStructure.objects.filter(
            employee__organization=organization,
            is_active=True
        ).select_related('employee', 'employee__department', 'employee__designation')
        
        # Apply filters
        if filters.get('department'):
            salary_structures = salary_structures.filter(employee__department_id=filters['department'])
        
        if filters.get('designation'):
            salary_structures = salary_structures.filter(employee__designation_id=filters['designation'])
        
        if filters.get('employee_id'):
            salary_structures = salary_structures.filter(employee__employee_id__icontains=filters['employee_id'])
        
        salary_data = []
        
        for structure in salary_structures:
            # Calculate total allowances
            total_allowances = (
                structure.house_rent_allowance +
                structure.transport_allowance +
                structure.medical_allowance +
                structure.other_allowances
            )
            
            # Calculate total deductions
            total_deductions = (
                structure.provident_fund +
                structure.tax_deduction +
                structure.other_deductions
            )
            
            salary_data.append({
                'employee_id': structure.employee.employee_id,
                'full_name': structure.employee.full_name,
                'department': structure.employee.department.name if structure.employee.department else 'N/A',
                'designation': structure.employee.designation.name if structure.employee.designation else 'N/A',
                'effective_date': structure.effective_date.strftime('%d-%m-%Y'),
                'basic_salary': float(structure.basic_salary),
                'house_rent_allowance': float(structure.house_rent_allowance),
                'transport_allowance': float(structure.transport_allowance),
                'medical_allowance': float(structure.medical_allowance),
                'other_allowances': float(structure.other_allowances),
                'total_allowances': float(total_allowances),
                'provident_fund': float(structure.provident_fund),
                'tax_deduction': float(structure.tax_deduction),
                'other_deductions': float(structure.other_deductions),
                'total_deductions': float(total_deductions),
                'gross_salary': float(structure.basic_salary + total_allowances),
                'net_salary': float(structure.basic_salary + total_allowances - total_deductions),
                'is_active': structure.is_active
            })
        
        # Calculate summary statistics
        if salary_data:
            total_employees = len(salary_data)
            avg_basic = sum(item['basic_salary'] for item in salary_data) / total_employees
            avg_gross = sum(item['gross_salary'] for item in salary_data) / total_employees
            avg_net = sum(item['net_salary'] for item in salary_data) / total_employees
            total_payroll = sum(item['net_salary'] for item in salary_data)
        else:
            total_employees = 0
            avg_basic = avg_gross = avg_net = total_payroll = 0
        
        return {
            'report_name': 'Salary Structure Report',
            'generated_on': timezone.now().strftime('%d-%m-%Y %H:%M:%S'),
            'filters': filters,
            'summary': {
                'total_employees': total_employees,
                'avg_basic_salary': round(avg_basic, 2),
                'avg_gross_salary': round(avg_gross, 2),
                'avg_net_salary': round(avg_net, 2),
                'total_monthly_payroll': round(total_payroll, 2)
            },
            'salary_data': salary_data
        }

class SalaryRevisionReport:
    def generate_salary_revision_report(self, organization, filters=None):
        """
        Generate salary change history report
        """
        filters = filters or {}
        
        # Get all salary structures (including inactive ones for history)
        salary_structures = SalaryStructure.objects.filter(
            employee__organization=organization
        ).select_related('employee', 'employee__department', 'employee__designation').order_by('employee', '-effective_date')
        
        # Apply filters
        if filters.get('department'):
            salary_structures = salary_structures.filter(employee__department_id=filters['department'])
        
        if filters.get('employee_id'):
            salary_structures = salary_structures.filter(employee__employee_id__icontains=filters['employee_id'])
        
        if filters.get('start_date'):
            salary_structures = salary_structures.filter(effective_date__gte=filters['start_date'])
        
        if filters.get('end_date'):
            salary_structures = salary_structures.filter(effective_date__lte=filters['end_date'])
        
        # Group by employee to track revisions
        employee_revisions = {}
        
        for structure in salary_structures:
            employee_id = structure.employee.employee_id
            
            if employee_id not in employee_revisions:
                employee_revisions[employee_id] = {
                    'employee_id': employee_id,
                    'full_name': structure.employee.full_name,
                    'department': structure.employee.department.name if structure.employee.department else 'N/A',
                    'designation': structure.employee.designation.name if structure.employee.designation else 'N/A',
                    'revisions': []
                }
            
            # Calculate totals for this structure
            total_allowances = (
                structure.house_rent_allowance +
                structure.transport_allowance +
                structure.medical_allowance +
                structure.other_allowances
            )
            
            total_deductions = (
                structure.provident_fund +
                structure.tax_deduction +
                structure.other_deductions
            )
            
            gross_salary = structure.basic_salary + total_allowances
            net_salary = gross_salary - total_deductions
            
            employee_revisions[employee_id]['revisions'].append({
                'effective_date': structure.effective_date.strftime('%d-%m-%Y'),
                'basic_salary': float(structure.basic_salary),
                'total_allowances': float(total_allowances),
                'total_deductions': float(total_deductions),
                'gross_salary': float(gross_salary),
                'net_salary': float(net_salary),
                'is_active': structure.is_active,
                'change_type': 'Current' if structure.is_active else 'Historical'
            })
        
        # Calculate revision statistics for each employee
        revision_data = []
        total_revisions = 0
        employees_with_revisions = 0
        
        for employee_id, data in employee_revisions.items():
            revisions = data['revisions']
            total_revisions += len(revisions)
            
            if len(revisions) > 1:
                employees_with_revisions += 1
                
                # Calculate salary growth
                first_revision = revisions[-1]  # Oldest revision
                current_revision = revisions[0]  # Latest revision
                
                basic_growth = ((current_revision['basic_salary'] - first_revision['basic_salary']) / first_revision['basic_salary']) * 100
                net_growth = ((current_revision['net_salary'] - first_revision['net_salary']) / first_revision['net_salary']) * 100
                
                data['revision_count'] = len(revisions)
                data['basic_growth_percentage'] = round(basic_growth, 2)
                data['net_growth_percentage'] = round(net_growth, 2)
                data['first_salary'] = first_revision['net_salary']
                data['current_salary'] = current_revision['net_salary']
                data['total_increase'] = current_revision['net_salary'] - first_revision['net_salary']
            
            revision_data.append(data)
        
        # Sort by number of revisions (most revisions first)
        revision_data.sort(key=lambda x: len(x['revisions']), reverse=True)
        
        return {
            'report_name': 'Salary Revision Report',
            'generated_on': timezone.now().strftime('%d-%m-%Y %H:%M:%S'),
            'filters': filters,
            'summary': {
                'total_employees': len(revision_data),
                'total_revisions': total_revisions,
                'employees_with_revisions': employees_with_revisions,
                'avg_revisions_per_employee': round(total_revisions / len(revision_data), 1) if revision_data else 0
            },
            'revision_data': revision_data
        }

class ComparativeSalaryReport:
    def generate_comparative_salary_report(self, organization, filters=None):
        """
        Generate department/designation wise comparative salary report
        """
        filters = filters or {}
        
        # Get current salary structures
        salary_structures = SalaryStructure.objects.filter(
            employee__organization=organization,
            is_active=True
        ).select_related('employee', 'employee__department', 'employee__designation')
        
        # Apply filters
        if filters.get('department'):
            salary_structures = salary_structures.filter(employee__department_id=filters['department'])
        
        # Department-wise analysis
        department_stats = salary_structures.values(
            'employee__department__name'
        ).annotate(
            employee_count=Count('id'),
            avg_basic=Avg('basic_salary'),
            avg_gross=Avg(
                F('basic_salary') + 
                F('house_rent_allowance') + 
                F('transport_allowance') + 
                F('medical_allowance') + 
                F('other_allowances')
            ),
            min_salary=Min('basic_salary'),
            max_salary=Max('basic_salary'),
            total_payroll=Sum(
                F('basic_salary') + 
                F('house_rent_allowance') + 
                F('transport_allowance') + 
                F('medical_allowance') + 
                F('other_allowances') -
                F('provident_fund') -
                F('tax_deduction') -
                F('other_deductions')
            )
        ).order_by('-avg_gross')
        
        department_comparison = []
        for dept in department_stats:
            department_comparison.append({
                'department': dept['employee__department__name'] or 'Not Assigned',
                'employee_count': dept['employee_count'],
                'avg_basic_salary': round(dept['avg_basic'] or 0, 2),
                'avg_gross_salary': round(dept['avg_gross'] or 0, 2),
                'min_salary': round(dept['min_salary'] or 0, 2),
                'max_salary': round(dept['max_salary'] or 0, 2),
                'salary_range': round((dept['max_salary'] or 0) - (dept['min_salary'] or 0), 2),
                'total_payroll': round(dept['total_payroll'] or 0, 2)
            })
        
        # Designation-wise analysis
        designation_stats = salary_structures.values(
            'employee__designation__name',
            'employee__designation__level'
        ).annotate(
            employee_count=Count('id'),
            avg_basic=Avg('basic_salary'),
            avg_gross=Avg(
                F('basic_salary') + 
                F('house_rent_allowance') + 
                F('transport_allowance') + 
                F('medical_allowance') + 
                F('other_allowances')
            ),
            min_salary=Min('basic_salary'),
            max_salary=Max('basic_salary')
        ).order_by('employee__designation__level', '-avg_gross')
        
        designation_comparison = []
        for desg in designation_stats:
            if desg['employee__designation__name']:  # Only include records with designation
                designation_comparison.append({
                    'designation': desg['employee__designation__name'],
                    'level': desg['employee__designation__level'] or 0,
                    'employee_count': desg['employee_count'],
                    'avg_basic_salary': round(desg['avg_basic'] or 0, 2),
                    'avg_gross_salary': round(desg['avg_gross'] or 0, 2),
                    'min_salary': round(desg['min_salary'] or 0, 2),
                    'max_salary': round(desg['max_salary'] or 0, 2),
                    'salary_range': round((desg['max_salary'] or 0) - (desg['min_salary'] or 0), 2)
                })
        
        # Salary distribution by ranges
        salary_ranges = [
            ('< 20,000', 0, 20000),
            ('20,000 - 40,000', 20000, 40000),
            ('40,000 - 60,000', 40000, 60000),
            ('60,000 - 80,000', 60000, 80000),
            ('80,000 - 1,00,000', 80000, 100000),
            ('1,00,000 - 1,50,000', 100000, 150000),
            ('1,50,000 - 2,00,000', 150000, 200000),
            ('> 2,00,000', 200000, 999999999)
        ]
        
        salary_distribution = []
        total_employees = salary_structures.count()
        
        for range_name, min_sal, max_sal in salary_ranges:
            count = salary_structures.filter(
                basic_salary__gte=min_sal, 
                basic_salary__lt=max_sal
            ).count()
            
            percentage = (count / total_employees * 100) if total_employees > 0 else 0
            
            salary_distribution.append({
                'range': range_name,
                'count': count,
                'percentage': round(percentage, 1)
            })
        
        # Allowance breakdown
        allowance_breakdown = {
            'house_rent': round(salary_structures.aggregate(total=Sum('house_rent_allowance'))['total'] or 0, 2),
            'transport': round(salary_structures.aggregate(total=Sum('transport_allowance'))['total'] or 0, 2),
            'medical': round(salary_structures.aggregate(total=Sum('medical_allowance'))['total'] or 0, 2),
            'other': round(salary_structures.aggregate(total=Sum('other_allowances'))['total'] or 0, 2)
        }
        
        total_allowances = sum(allowance_breakdown.values())
        
        return {
            'report_name': 'Comparative Salary Report',
            'generated_on': timezone.now().strftime('%d-%m-%Y %H:%M:%S'),
            'filters': filters,
            'summary': {
                'total_employees': total_employees,
                'total_departments': len(department_comparison),
                'total_designations': len(designation_comparison),
                'avg_basic_salary': round(salary_structures.aggregate(avg=Avg('basic_salary'))['avg'] or 0, 2),
                'total_monthly_payroll': round(salary_structures.aggregate(
                    total=Sum(
                        F('basic_salary') + 
                        F('house_rent_allowance') + 
                        F('transport_allowance') + 
                        F('medical_allowance') + 
                        F('other_allowances') -
                        F('provident_fund') -
                        F('tax_deduction') -
                        F('other_deductions')
                    )
                )['total'] or 0, 2)
            },
            'department_comparison': department_comparison,
            'designation_comparison': designation_comparison,
            'salary_distribution': salary_distribution,
            'allowance_breakdown': allowance_breakdown,
            'total_allowances': total_allowances
        }