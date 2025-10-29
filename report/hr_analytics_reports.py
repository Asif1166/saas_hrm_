from django.db.models import Q, Count, Sum, Avg, Min, Max
from django.utils import timezone
from datetime import datetime, date, timedelta
from payroll.models import Payslip, SalaryStructure, PayrollPeriod
from hrm.models import Employee, Department, Designation, AttendanceRecord
from django.db.models import F
from decimal import Decimal
import math

class HeadcountAnalysisReport:
    def generate_headcount_analysis_report(self, organization, filters=None):
        """
        Generate employee headcount analysis and growth trends
        """
        filters = filters or {}
        
        # Get all employees (including inactive for historical analysis)
        employees = Employee.objects.filter(organization=organization)
        
        # Apply filters
        if filters.get('department'):
            employees = employees.filter(department_id=filters['department'])
        
        if filters.get('designation'):
            employees = employees.filter(designation_id=filters['designation'])
        
        # Date range for trend analysis
        end_date = timezone.now().date()
        if filters.get('end_date'):
            end_date = datetime.strptime(filters['end_date'], '%Y-%m-%d').date()
        
        start_date = end_date - timedelta(days=365)  # Default 1 year analysis
        if filters.get('start_date'):
            start_date = datetime.strptime(filters['start_date'], '%Y-%m-%d').date()
        
        # Monthly headcount trend
        monthly_trend = self._calculate_monthly_headcount(organization, start_date, end_date, filters)
        
        # Department-wise headcount
        dept_headcount = employees.filter(is_active=True).values(
            'department__name'
        ).annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Calculate average salary manually for each department
        for dept in dept_headcount:
            dept_emps = employees.filter(
                department__name=dept['department__name'],
                is_active=True
            )
            salaries = [emp.basic_salary for emp in dept_emps if emp.basic_salary]
            dept['avg_salary'] = sum(salaries) / len(salaries) if salaries else 0
            dept['avg_experience'] = self._calculate_avg_experience(dept_emps)
        
        # Designation-wise headcount
        desg_headcount = employees.filter(is_active=True).values(
            'designation__name',
            'designation__level'
        ).annotate(
            count=Count('id')
        ).order_by('designation__level', '-count')
        
        # Calculate average salary manually for each designation
        for desg in desg_headcount:
            desg_emps = employees.filter(
                designation__name=desg['designation__name'],
                is_active=True
            )
            salaries = [emp.basic_salary for emp in desg_emps if emp.basic_salary]
            desg['avg_salary'] = sum(salaries) / len(salaries) if salaries else 0
        
        # Employment status breakdown
        status_breakdown = employees.values('employment_status').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Hiring trends (last 12 months)
        hiring_trend = self._calculate_hiring_trend(organization, start_date, end_date)
        
        # Headcount summary
        total_employees = employees.filter(is_active=True).count()
        active_employees = employees.filter(employment_status='active').count()
        new_hires = employees.filter(hire_date__gte=start_date).count()
        terminated = employees.filter(termination_date__gte=start_date, employment_status='terminated').count()
        
        # Growth rate calculation
        previous_period_count = Employee.objects.filter(
            organization=organization,
            hire_date__lt=start_date,
            is_active=True
        ).count()
        
        growth_rate = ((total_employees - previous_period_count) / previous_period_count * 100) if previous_period_count > 0 else 0
        
        # Attrition rate calculation with zero division protection
        attrition_rate = (terminated / total_employees * 100) if total_employees > 0 else 0
        
        return {
            'report_name': 'Headcount Analysis Report',
            'generated_on': timezone.now().strftime('%d-%m-%Y %H:%M:%S'),
            'filters': filters,
            'summary': {
                'total_employees': total_employees,
                'active_employees': active_employees,
                'new_hires': new_hires,
                'terminated': terminated,
                'growth_rate': round(growth_rate, 2),
                'analysis_period': f"{start_date.strftime('%b %Y')} to {end_date.strftime('%b %Y')}",
                'attrition_rate': round(attrition_rate, 2)
            },
            'monthly_trend': monthly_trend,
            'department_headcount': dept_headcount,
            'designation_headcount': desg_headcount,
            'status_breakdown': status_breakdown,
            'hiring_trend': hiring_trend
        }
    
    def _calculate_avg_experience(self, employees):
        """Calculate average experience manually"""
        total_experience = 0
        count = 0
        
        for emp in employees:
            if emp.hire_date:
                experience = (timezone.now().date() - emp.hire_date).days / 365.25
                total_experience += experience
                count += 1
        
        return round(total_experience / count, 1) if count > 0 else 0
    
    def _calculate_monthly_headcount(self, organization, start_date, end_date, filters):
        """Calculate monthly headcount trend"""
        monthly_data = []
        current_date = start_date.replace(day=1)
        
        while current_date <= end_date:
            month_start = current_date
            month_end = (current_date.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
            
            # Count employees hired before or on month_end and not terminated or terminated after month_end
            employees_count = Employee.objects.filter(
                organization=organization,
                hire_date__lte=month_end,
                is_active=True
            ).filter(
                Q(termination_date__isnull=True) | Q(termination_date__gt=month_end)
            )
            
            # Apply filters
            if filters.get('department'):
                employees_count = employees_count.filter(department_id=filters['department'])
            
            if filters.get('designation'):
                employees_count = employees_count.filter(designation_id=filters['designation'])
            
            count = employees_count.count()
            
            # Calculate month-over-month growth
            prev_month = current_date - timedelta(days=1)
            prev_month_start = prev_month.replace(day=1)
            prev_month_end = (prev_month.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
            
            prev_count = Employee.objects.filter(
                organization=organization,
                hire_date__lte=prev_month_end,
                is_active=True
            ).filter(
                Q(termination_date__isnull=True) | Q(termination_date__gt=prev_month_end)
            )
            
            if filters.get('department'):
                prev_count = prev_count.filter(department_id=filters['department'])
            
            if filters.get('designation'):
                prev_count = prev_count.filter(designation_id=filters['designation'])
            
            prev_count = prev_count.count()
            
            mom_growth = ((count - prev_count) / prev_count * 100) if prev_count > 0 else 0
            
            monthly_data.append({
                'month': current_date.strftime('%b %Y'),
                'headcount': count,
                'mom_growth': round(mom_growth, 2),
                'new_hires': Employee.objects.filter(
                    organization=organization,
                    hire_date__gte=month_start,
                    hire_date__lte=month_end
                ).count(),
                'terminations': Employee.objects.filter(
                    organization=organization,
                    termination_date__gte=month_start,
                    termination_date__lte=month_end
                ).count()
            })
            
            # Move to next month
            current_date = (current_date.replace(day=28) + timedelta(days=4)).replace(day=1)
        
        return monthly_data
    
    def _calculate_hiring_trend(self, organization, start_date, end_date):
        """Calculate hiring trends by month"""
        hiring_data = []
        current_date = start_date.replace(day=1)
        
        while current_date <= end_date:
            month_start = current_date
            month_end = (current_date.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
            
            hires = Employee.objects.filter(
                organization=organization,
                hire_date__gte=month_start,
                hire_date__lte=month_end
            )
            
            hire_count = hires.count()
            
            # Calculate average salary manually
            salaries = [emp.basic_salary for emp in hires if emp.basic_salary]
            avg_salary = sum(salaries) / len(salaries) if salaries else 0
            
            hiring_data.append({
                'month': current_date.strftime('%b %Y'),
                'hires': hire_count,
                'avg_salary': avg_salary,
                'departments': hires.values('department__name').annotate(count=Count('id')).count()
            })
            
            # Move to next month
            current_date = (current_date.replace(day=28) + timedelta(days=4)).replace(day=1)
        
        return hiring_data

class AttritionReport:
    def generate_attrition_report(self, organization, filters=None):
        """
        Generate employee turnover and attrition analysis
        """
        filters = filters or {}
        
        # Date range for analysis
        end_date = timezone.now().date()
        if filters.get('end_date'):
            end_date = datetime.strptime(filters['end_date'], '%Y-%m-%d').date()
        
        start_date = end_date - timedelta(days=365)  # Default 1 year analysis
        if filters.get('start_date'):
            start_date = datetime.strptime(filters['start_date'], '%Y-%m-%d').date()
        
        # Get terminated employees in the period
        terminated_employees = Employee.objects.filter(
            organization=organization,
            termination_date__gte=start_date,
            termination_date__lte=end_date,
            employment_status='terminated'
        ).select_related('department', 'designation')
        
        # Apply filters
        if filters.get('department'):
            terminated_employees = terminated_employees.filter(department_id=filters['department'])
        
        if filters.get('designation'):
            terminated_employees = terminated_employees.filter(designation_id=filters['designation'])
        
        # Calculate attrition metrics
        total_employees = Employee.objects.filter(organization=organization, is_active=True).count()
        terminated_count = terminated_employees.count()
        
        # Monthly attrition trend
        monthly_attrition = self._calculate_monthly_attrition(organization, start_date, end_date, filters)
        
        # Department-wise attrition
        dept_attrition = terminated_employees.values('department__name').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Calculate average tenure manually for each department
        for dept in dept_attrition:
            dept_emps = terminated_employees.filter(department__name=dept['department__name'])
            total_tenure_days = 0
            count = 0
            for emp in dept_emps:
                if emp.hire_date and emp.termination_date:
                    tenure_days = (emp.termination_date - emp.hire_date).days
                    total_tenure_days += tenure_days
                    count += 1
            dept['avg_tenure_days'] = total_tenure_days // count if count > 0 else 0
        
        # Designation-wise attrition
        desg_attrition = terminated_employees.values('designation__name').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Calculate average tenure manually for each designation
        for desg in desg_attrition:
            desg_emps = terminated_employees.filter(designation__name=desg['designation__name'])
            total_tenure_days = 0
            count = 0
            for emp in desg_emps:
                if emp.hire_date and emp.termination_date:
                    tenure_days = (emp.termination_date - emp.hire_date).days
                    total_tenure_days += tenure_days
                    count += 1
            desg['avg_tenure_days'] = total_tenure_days // count if count > 0 else 0
        
        # Tenure analysis
        tenure_analysis = self._analyze_tenure(terminated_employees)
        
        # Calculate overall average tenure
        total_tenure_days = 0
        count_with_dates = 0
        for emp in terminated_employees:
            if emp.hire_date and emp.termination_date:
                tenure_days = (emp.termination_date - emp.hire_date).days
                total_tenure_days += tenure_days
                count_with_dates += 1
        
        avg_tenure_days = total_tenure_days // count_with_dates if count_with_dates > 0 else 0
        
        # Calculate attrition rate with zero division protection
        avg_headcount = total_employees  # Simplified calculation
        attrition_rate = (terminated_count / avg_headcount * 100) if avg_headcount > 0 else 0
        
        # Voluntary vs Involuntary (simplified - you would need termination_type field)
        voluntary_count = terminated_count  # Default all as voluntary for now
        involuntary_count = 0
        
        return {
            'report_name': 'Attrition Report',
            'generated_on': timezone.now().strftime('%d-%m-%Y %H:%M:%S'),
            'filters': filters,
            'summary': {
                'analysis_period': f"{start_date.strftime('%d %b %Y')} to {end_date.strftime('%d %b %Y')}",
                'total_employees': total_employees,
                'employees_terminated': terminated_count,
                'attrition_rate': round(attrition_rate, 2),
                'voluntary_attrition': voluntary_count,
                'involuntary_attrition': involuntary_count,
                'avg_tenure_days': avg_tenure_days
            },
            'monthly_attrition': monthly_attrition,
            'department_attrition': dept_attrition,
            'designation_attrition': desg_attrition,
            'tenure_analysis': tenure_analysis,
            'terminated_employees': list(terminated_employees.values(
                'employee_id', 'department__name', 'designation__name',
                'hire_date', 'termination_date'
            )[:50])  # Limit to 50 records for performance
        }
    
    def _calculate_monthly_attrition(self, organization, start_date, end_date, filters):
        """Calculate monthly attrition rates"""
        monthly_data = []
        current_date = start_date.replace(day=1)
        
        while current_date <= end_date:
            month_start = current_date
            month_end = (current_date.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
            
            # Terminations in month
            terminations = Employee.objects.filter(
                organization=organization,
                termination_date__gte=month_start,
                termination_date__lte=month_end,
                employment_status='terminated'
            )
            
            if filters.get('department'):
                terminations = terminations.filter(department_id=filters['department'])
            
            if filters.get('designation'):
                terminations = terminations.filter(designation_id=filters['designation'])
            
            termination_count = terminations.count()
            
            # Average headcount for the month
            avg_headcount = Employee.objects.filter(
                organization=organization,
                hire_date__lte=month_end,
                is_active=True
            ).filter(
                Q(termination_date__isnull=True) | Q(termination_date__gt=month_end)
            ).count()
            
            # Monthly attrition rate with zero division protection
            monthly_attrition_rate = (termination_count / avg_headcount * 100) if avg_headcount > 0 else 0
            
            monthly_data.append({
                'month': current_date.strftime('%b %Y'),
                'terminations': termination_count,
                'attrition_rate': round(monthly_attrition_rate, 2),
                'avg_headcount': avg_headcount
            })
            
            # Move to next month
            current_date = (current_date.replace(day=28) + timedelta(days=4)).replace(day=1)
        
        return monthly_data
    
    def _analyze_tenure(self, terminated_employees):
        """Analyze tenure of terminated employees"""
        tenure_brackets = [
            ('< 6 months', 0, 180),
            ('6-12 months', 180, 365),
            ('1-2 years', 365, 730),
            ('2-5 years', 730, 1825),
            ('5+ years', 1825, 99999)
        ]
        
        analysis = []
        total_count = terminated_employees.count()
        
        for bracket_name, min_days, max_days in tenure_brackets:
            count = 0
            for emp in terminated_employees:
                if emp.hire_date and emp.termination_date:
                    tenure_days = (emp.termination_date - emp.hire_date).days
                    if min_days <= tenure_days < max_days:
                        count += 1
            
            percentage = (count / total_count * 100) if total_count > 0 else 0
            
            analysis.append({
                'tenure_bracket': bracket_name,
                'count': count,
                'percentage': round(percentage, 2)
            })
        
        return analysis

class DepartmentCostAnalysisReport:
    def generate_department_cost_analysis(self, organization, filters=None):
        """
        Generate department-wise cost analysis
        """
        filters = filters or {}
        
        # Get payroll data for analysis period
        payroll_periods = PayrollPeriod.objects.filter(
            organization=organization,
            status='completed'
        ).order_by('-start_date')
        
        # Apply date filters
        if filters.get('start_date') and filters.get('end_date'):
            payroll_periods = payroll_periods.filter(
                start_date__gte=filters['start_date'],
                end_date__lte=filters['end_date']
            )
        else:
            # Default to last 3 months
            three_months_ago = timezone.now().date() - timedelta(days=90)
            payroll_periods = payroll_periods.filter(start_date__gte=three_months_ago)
        
        # Department-wise cost analysis
        dept_cost_analysis = []
        total_organization_cost = 0
        
        departments = Department.objects.filter(organization=organization, is_active=True)
        
        for department in departments:
            # Get employees in department
            dept_employees = Employee.objects.filter(
                organization=organization,
                department=department,
                is_active=True
            )
            
            # Get payslips for these employees in the analysis period
            dept_payslips = Payslip.objects.filter(
                organization=organization,
                employee__in=dept_employees,
                payroll_period__in=payroll_periods,
                is_generated=True
            )
            
            # Calculate costs manually
            total_salary_cost = 0
            total_pf_employer = 0
            payslip_count = dept_payslips.count()
            
            for payslip in dept_payslips:
                total_salary_cost += float(payslip.net_salary)
                total_pf_employer += float(payslip.provident_fund)
            
            # Calculate averages with zero division protection
            avg_salary = total_salary_cost / payslip_count if payslip_count > 0 else 0
            
            # Assuming employer PF contribution is 12% of basic
            # For simplicity, we'll use the actual PF deduction from payslip
            employer_pf_contribution = total_pf_employer * Decimal('1.0')  # Adjust based on your calculation
            
            # Total cost to company (simplified)
            total_cost = total_salary_cost + float(employer_pf_contribution)
            
            employee_count = dept_employees.count()
            
            # Calculate cost per employee with zero division protection
            cost_per_employee = total_cost / employee_count if employee_count > 0 else 0
            
            # Calculate salary to total ratio with zero division protection
            salary_to_total_ratio = (total_salary_cost / total_cost * 100) if total_cost > 0 else 0
            
            dept_cost_analysis.append({
                'department_name': department.name,
                'employee_count': employee_count,
                'total_salary_cost': total_salary_cost,
                'employer_pf_contribution': float(employer_pf_contribution),
                'total_cost': total_cost,
                'avg_salary_per_employee': avg_salary,
                'cost_per_employee': cost_per_employee,
                'salary_to_total_ratio': salary_to_total_ratio
            })
            
            total_organization_cost += total_cost
        
        # Calculate percentages with zero division protection
        for dept in dept_cost_analysis:
            dept['cost_percentage'] = round((dept['total_cost'] / total_organization_cost * 100), 2) if total_organization_cost > 0 else 0
        
        # Cost trends by month
        cost_trends = self._calculate_cost_trends(organization, payroll_periods)
        
        # Cost efficiency metrics
        efficiency_metrics = self._calculate_efficiency_metrics(dept_cost_analysis)
        
        # Calculate summary metrics with zero division protection
        total_employees_all = sum(dept['employee_count'] for dept in dept_cost_analysis)
        avg_cost_per_employee = total_organization_cost / total_employees_all if total_employees_all > 0 else 0
        
        # Find most and least expensive departments
        most_expensive_dept = 'N/A'
        least_expensive_dept = 'N/A'
        if dept_cost_analysis:
            most_expensive_dept = max(dept_cost_analysis, key=lambda x: x['total_cost'])['department_name']
            least_expensive_dept = min(dept_cost_analysis, key=lambda x: x['total_cost'])['department_name']
        
        return {
            'report_name': 'Department Cost Analysis Report',
            'generated_on': timezone.now().strftime('%d-%m-%Y %H:%M:%S'),
            'filters': filters,
            'summary': {
                'total_departments': len(dept_cost_analysis),
                'total_organization_cost': round(total_organization_cost, 2),
                'analysis_periods': payroll_periods.count(),
                'avg_cost_per_employee': round(avg_cost_per_employee, 2),
                'most_expensive_dept': most_expensive_dept,
                'least_expensive_dept': least_expensive_dept
            },
            'department_cost_analysis': dept_cost_analysis,
            'cost_trends': cost_trends,
            'efficiency_metrics': efficiency_metrics
        }
    
    def _calculate_cost_trends(self, organization, payroll_periods):
        """Calculate cost trends by month"""
        monthly_costs = []
        
        for period in payroll_periods:
            period_payslips = Payslip.objects.filter(
                organization=organization,
                payroll_period=period,
                is_generated=True
            )
            
            total_cost = 0
            payslip_count = period_payslips.count()
            for payslip in period_payslips:
                total_cost += float(payslip.net_salary)
            
            # Calculate average cost per employee with zero division protection
            avg_cost_per_employee = total_cost / payslip_count if payslip_count > 0 else 0
            
            monthly_costs.append({
                'period': period.name,
                'month': period.start_date.strftime('%b %Y'),
                'total_cost': total_cost,
                'employee_count': payslip_count,
                'avg_cost_per_employee': avg_cost_per_employee
            })
        
        return monthly_costs
    
    def _calculate_efficiency_metrics(self, dept_cost_analysis):
        """Calculate cost efficiency metrics with zero division protection"""
        if not dept_cost_analysis:
            return {}
        
        total_cost = sum(dept['total_cost'] for dept in dept_cost_analysis)
        total_employees = sum(dept['employee_count'] for dept in dept_cost_analysis)
        
        # Calculate overall metrics with zero division protection
        overall_cost_per_employee = total_cost / total_employees if total_employees > 0 else 0
        salary_cost_ratio = (sum(dept['total_salary_cost'] for dept in dept_cost_analysis) / total_cost * 100) if total_cost > 0 else 0
        
        return {
            'overall_cost_per_employee': overall_cost_per_employee,
            'salary_cost_ratio': salary_cost_ratio,
            'cost_variance': self._calculate_cost_variance(dept_cost_analysis),
            'efficient_departments': [dept for dept in dept_cost_analysis if dept['cost_per_employee'] < overall_cost_per_employee]
        }
    
    def _calculate_cost_variance(self, dept_cost_analysis):
        """Calculate cost variance between departments"""
        if len(dept_cost_analysis) < 2:
            return 0
        
        costs = [dept['cost_per_employee'] for dept in dept_cost_analysis]
        mean_cost = sum(costs) / len(costs)
        variance = sum((cost - mean_cost) ** 2 for cost in costs) / len(costs)
        return variance

class EmployeeCostToCompanyReport:
    def generate_employee_cost_to_company_report(self, organization, filters=None):
        """
        Generate Employee Cost-to-Company (CTC) analysis
        """
        filters = filters or {}
        
        # Get active employees
        employees = Employee.objects.filter(
            organization=organization,
            is_active=True
        ).select_related('department', 'designation')
        
        # Apply filters
        if filters.get('department'):
            employees = employees.filter(department_id=filters['department'])
        
        if filters.get('designation'):
            employees = employees.filter(designation_id=filters['designation'])
        
        if filters.get('employee_id'):
            employees = employees.filter(employee_id__icontains=filters['employee_id'])
        
        ctc_data = []
        total_organization_ctc = 0
        
        for employee in employees:
            # Get current salary structure
            current_structure = SalaryStructure.objects.filter(
                organization=organization,
                employee=employee,
                is_active=True
            ).order_by('-effective_date').first()
            
            if not current_structure:
                continue
            
            # Calculate monthly CTC components
            basic_salary = float(current_structure.basic_salary)
            allowances = float(current_structure.house_rent_allowance + 
                             current_structure.transport_allowance + 
                             current_structure.medical_allowance + 
                             current_structure.other_allowances)
            
            # Employer contributions (simplified calculations)
            employer_pf = basic_salary * 0.12  # 12% employer PF
            employer_esi = basic_salary * 0.0325 if basic_salary <= 21000 else 0.00  # ESI if applicable
            gratuity = (basic_salary * 15 / 26) / 12  # Monthly gratuity accrual
            
            # Other statutory costs (simplified)
            other_statutory = employer_pf + employer_esi + gratuity
            
            # Monthly CTC
            monthly_ctc = basic_salary + allowances + other_statutory
            
            # Annual CTC
            annual_ctc = monthly_ctc * 12
            
            # Cost breakdown percentages with zero division protection
            basic_percentage = (basic_salary / monthly_ctc * 100) if monthly_ctc > 0 else 0
            allowances_percentage = (allowances / monthly_ctc * 100) if monthly_ctc > 0 else 0
            statutory_percentage = (other_statutory / monthly_ctc * 100) if monthly_ctc > 0 else 0
            
            ctc_data.append({
                'employee_id': employee.employee_id,
                'full_name': employee.full_name,
                'department': employee.department.name if employee.department else 'N/A',
                'designation': employee.designation.name if employee.designation else 'N/A',
                'experience_years': employee.experience_years,
                'basic_salary': basic_salary,
                'allowances': allowances,
                'employer_pf': employer_pf,
                'employer_esi': employer_esi,
                'gratuity': gratuity,
                'monthly_ctc': monthly_ctc,
                'annual_ctc': annual_ctc,
                'cost_breakdown': {
                    'basic_percentage': round(basic_percentage, 2),
                    'allowances_percentage': round(allowances_percentage, 2),
                    'statutory_percentage': round(statutory_percentage, 2)
                }
            })
            
            total_organization_ctc += annual_ctc
        
        # CTC statistics
        ctc_statistics = self._calculate_ctc_statistics(ctc_data)
        
        # Department-wise CTC summary
        dept_ctc_summary = self._calculate_department_ctc_summary(ctc_data)
        
        # Designation-wise CTC summary
        desg_ctc_summary = self._calculate_designation_ctc_summary(ctc_data)
        
        # Calculate averages with zero division protection
        avg_annual_ctc = total_organization_ctc / len(ctc_data) if ctc_data else 0
        avg_monthly_ctc = sum(item['monthly_ctc'] for item in ctc_data) / len(ctc_data) if ctc_data else 0
        
        return {
            'report_name': 'Employee Cost-to-Company Report',
            'generated_on': timezone.now().strftime('%d-%m-%Y %H:%M:%S'),
            'filters': filters,
            'summary': {
                'total_employees': len(ctc_data),
                'total_annual_ctc': round(total_organization_ctc, 2),
                'avg_annual_ctc': round(avg_annual_ctc, 2),
                'avg_monthly_ctc': round(avg_monthly_ctc, 2)
            },
            'ctc_statistics': ctc_statistics,
            'department_ctc_summary': dept_ctc_summary,
            'designation_ctc_summary': desg_ctc_summary,
            'ctc_data': ctc_data
        }
    
    def _calculate_ctc_statistics(self, ctc_data):
        """Calculate CTC statistics with zero division protection"""
        if not ctc_data:
            return {}
        
        monthly_ctc_values = [item['monthly_ctc'] for item in ctc_data]
        annual_ctc_values = [item['annual_ctc'] for item in ctc_data]
        
        avg_monthly_ctc = sum(monthly_ctc_values) / len(monthly_ctc_values) if monthly_ctc_values else 0
        avg_annual_ctc = sum(annual_ctc_values) / len(annual_ctc_values) if annual_ctc_values else 0
        
        return {
            'min_monthly_ctc': min(monthly_ctc_values) if monthly_ctc_values else 0,
            'max_monthly_ctc': max(monthly_ctc_values) if monthly_ctc_values else 0,
            'avg_monthly_ctc': avg_monthly_ctc,
            'median_monthly_ctc': sorted(monthly_ctc_values)[len(monthly_ctc_values) // 2] if monthly_ctc_values else 0,
            'min_annual_ctc': min(annual_ctc_values) if annual_ctc_values else 0,
            'max_annual_ctc': max(annual_ctc_values) if annual_ctc_values else 0,
            'avg_annual_ctc': avg_annual_ctc
        }
    
    def _calculate_department_ctc_summary(self, ctc_data):
        """Calculate department-wise CTC summary with zero division protection"""
        dept_summary = {}
        
        for item in ctc_data:
            dept = item['department']
            if dept not in dept_summary:
                dept_summary[dept] = {
                    'employee_count': 0,
                    'total_annual_ctc': 0,
                    'total_monthly_ctc': 0,
                    'employees': []
                }
            
            dept_summary[dept]['employee_count'] += 1
            dept_summary[dept]['total_annual_ctc'] += item['annual_ctc']
            dept_summary[dept]['total_monthly_ctc'] += item['monthly_ctc']
            dept_summary[dept]['employees'].append({
                'employee_id': item['employee_id'],
                'name': item['full_name'],
                'annual_ctc': item['annual_ctc']
            })
        
        # Calculate averages with zero division protection
        for dept, data in dept_summary.items():
            data['avg_annual_ctc'] = data['total_annual_ctc'] / data['employee_count'] if data['employee_count'] > 0 else 0
            data['avg_monthly_ctc'] = data['total_monthly_ctc'] / data['employee_count'] if data['employee_count'] > 0 else 0
        
        return dept_summary
    
    def _calculate_designation_ctc_summary(self, ctc_data):
        """Calculate designation-wise CTC summary with zero division protection"""
        desg_summary = {}
        
        for item in ctc_data:
            desg = item['designation']
            if desg not in desg_summary:
                desg_summary[desg] = {
                    'employee_count': 0,
                    'total_annual_ctc': 0,
                    'total_monthly_ctc': 0,
                    'min_ctc': float('inf'),
                    'max_ctc': 0
                }
            
            desg_summary[desg]['employee_count'] += 1
            desg_summary[desg]['total_annual_ctc'] += item['annual_ctc']
            desg_summary[desg]['total_monthly_ctc'] += item['monthly_ctc']
            desg_summary[desg]['min_ctc'] = min(desg_summary[desg]['min_ctc'], item['annual_ctc'])
            desg_summary[desg]['max_ctc'] = max(desg_summary[desg]['max_ctc'], item['annual_ctc'])
        
        # Calculate averages and ranges with zero division protection
        for desg, data in desg_summary.items():
            data['avg_annual_ctc'] = data['total_annual_ctc'] / data['employee_count'] if data['employee_count'] > 0 else 0
            data['avg_monthly_ctc'] = data['total_monthly_ctc'] / data['employee_count'] if data['employee_count'] > 0 else 0
            data['ctc_range'] = data['max_ctc'] - data['min_ctc'] if data['min_ctc'] != float('inf') else 0
        
        return desg_summary