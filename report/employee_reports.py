# reports/employee_reports.py
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, date
from hrm.models import Employee, Department, Designation, Branch

class EmployeeDirectoryReport:
    def generate_employee_directory(self, organization, filters=None):
        """
        Generate comprehensive employee directory
        """
        filters = filters or {}
        
        # Base queryset
        employees = Employee.objects.filter(
            organization=organization,
            is_active=True
        ).select_related(
            'department', 'designation', 'branch', 'user'
        )
        
        # Apply filters
        if filters.get('department'):
            employees = employees.filter(department_id=filters['department'])
        
        if filters.get('designation'):
            employees = employees.filter(designation_id=filters['designation'])
        
        if filters.get('branch'):
            employees = employees.filter(branch_id=filters['branch'])
        
        if filters.get('employment_status'):
            employees = employees.filter(employment_status=filters['employment_status'])
        
        if filters.get('search'):
            search_term = filters['search']
            employees = employees.filter(
                Q(first_name__icontains=search_term) |
                Q(last_name__icontains=search_term) |
                Q(employee_id__icontains=search_term) |
                Q(personal_email__icontains=search_term)
            )
        
        # Prepare report data
        report_data = []
        for emp in employees:
            report_data.append({
                'employee_id': emp.employee_id,
                'full_name': emp.full_name,
                'department': emp.department.name if emp.department else 'N/A',
                'designation': emp.designation.name if emp.designation else 'N/A',
                'branch': emp.branch.name if emp.branch else 'N/A',
                'work_phone': emp.work_phone or 'N/A',
                'personal_phone': emp.personal_phone or 'N/A',
                'personal_email': emp.personal_email or 'N/A',
                'employment_status': emp.get_employment_status_display(),
                'hire_date': emp.hire_date.strftime('%d-%m-%Y') if emp.hire_date else 'N/A',
                'reporting_manager': emp.reporting_manager.full_name if emp.reporting_manager else 'N/A',
                'is_active': 'Yes' if emp.is_active else 'No'
            })
        
        return {
            'report_name': 'Employee Directory',
            'generated_on': timezone.now().strftime('%d-%m-%Y %H:%M:%S'),
            'filters': filters,
            'total_employees': len(report_data),
            'data': report_data
        }
    


class EmployeeProfileSummaryReport:
    def generate_profile_summary(self, organization, filters=None):
        """
        Generate detailed employee profile summary
        """
        filters = filters or {}
        
        employees = Employee.objects.filter(
            organization=organization,
            is_active=True
        ).select_related(
            'department', 'designation', 'branch', 'user'
        )
        
        # Apply filters
        if filters.get('employee_id'):
            employees = employees.filter(employee_id=filters['employee_id'])
        
        report_data = []
        for emp in employees:
            report_data.append({
                'personal_info': {
                    'employee_id': emp.employee_id,
                    'full_name': emp.full_name,
                    'date_of_birth': emp.date_of_birth.strftime('%d-%m-%Y') if emp.date_of_birth else 'N/A',
                    'age': emp.age or 'N/A',
                    'gender': emp.get_gender_display() if emp.gender else 'N/A',
                    'blood_group': emp.get_blood_group_display() if emp.blood_group else 'N/A',
                    'marital_status': emp.get_marital_status_display() if emp.marital_status else 'N/A',
                    'nationality': emp.nationality
                },
                'contact_info': {
                    'work_phone': emp.work_phone or 'N/A',
                    'personal_phone': emp.personal_phone or 'N/A',
                    'personal_email': emp.personal_email or 'N/A',
                    'current_address': emp.current_address or 'N/A',
                    'permanent_address': emp.permanent_address or 'N/A'
                },
                'employment_info': {
                    'department': emp.department.name if emp.department else 'N/A',
                    'designation': emp.designation.name if emp.designation else 'N/A',
                    'branch': emp.branch.name if emp.branch else 'N/A',
                    'employee_role': emp.employee_role.name if emp.employee_role else 'N/A',
                    'hire_date': emp.hire_date.strftime('%d-%m-%Y') if emp.hire_date else 'N/A',
                    'confirmation_date': emp.confirmation_date.strftime('%d-%m-%Y') if emp.confirmation_date else 'N/A',
                    'employment_status': emp.get_employment_status_display(),
                    'experience_years': emp.experience_years,
                    'reporting_manager': emp.reporting_manager.full_name if emp.reporting_manager else 'N/A'
                },
                'emergency_contact': {
                    'name': emp.emergency_contact_name or 'N/A',
                    'phone': emp.emergency_contact_phone or 'N/A',
                    'relationship': emp.emergency_contact_relationship or 'N/A'
                },
                'bank_info': {
                    'bank_name': emp.bank_name or 'N/A',
                    'account_number': emp.bank_account_number or 'N/A',
                    'routing_number': emp.bank_routing_number or 'N/A'
                }
            })
        
        return {
            'report_name': 'Employee Profile Summary',
            'generated_on': timezone.now().strftime('%d-%m-%Y %H:%M:%S'),
            'filters': filters,
            'total_employees': len(report_data),
            'data': report_data
        }
    


class EmployeeStatusReport:
    def generate_employee_status(self, organization, filters=None):
        """
        Generate employee status and statistics report
        """
        filters = filters or {}
        
        employees = Employee.objects.filter(organization=organization)
        
        if filters.get('status'):
            employees = employees.filter(employment_status=filters['status'])
        
        # Calculate statistics
        total_employees = employees.count()
        active_employees = employees.filter(employment_status='active').count()
        inactive_employees = employees.filter(employment_status='inactive').count()
        terminated_employees = employees.filter(employment_status='terminated').count()
        on_leave_employees = employees.filter(employment_status='on_leave').count()
        
        # Department-wise breakdown
        department_stats = []
        departments = Department.objects.filter(organization=organization, is_active=True)
        for dept in departments:
            dept_count = employees.filter(department=dept).count()
            if dept_count > 0:
                department_stats.append({
                    'department': dept.name,
                    'employee_count': dept_count,
                    'active_count': employees.filter(department=dept, employment_status='active').count(),
                    'inactive_count': employees.filter(department=dept, employment_status='inactive').count()
                })
        
        # Employment status breakdown
        status_breakdown = []
        for status_code, status_name in Employee.EMPLOYMENT_STATUS_CHOICES:
            count = employees.filter(employment_status=status_code).count()
            percentage = (count / total_employees * 100) if total_employees > 0 else 0
            status_breakdown.append({
                'status': status_name,
                'count': count,
                'percentage': round(percentage, 2)
            })
        
        # Detailed employee list
        employee_details = []
        for emp in employees.select_related('department', 'designation', 'branch'):
            employee_details.append({
                'employee_id': emp.employee_id,
                'full_name': emp.full_name,
                'department': emp.department.name if emp.department else 'N/A',
                'designation': emp.designation.name if emp.designation else 'N/A',
                'employment_status': emp.get_employment_status_display(),
                'hire_date': emp.hire_date.strftime('%d-%m-%Y') if emp.hire_date else 'N/A',
                'is_active': 'Yes' if emp.is_active else 'No',
                'last_updated': emp.updated_at.strftime('%d-%m-%Y')
            })
        
        return {
            'report_name': 'Employee Status Report',
            'generated_on': timezone.now().strftime('%d-%m-%Y %H:%M:%S'),
            'summary': {
                'total_employees': total_employees,
                'active_employees': active_employees,
                'inactive_employees': inactive_employees,
                'terminated_employees': terminated_employees,
                'on_leave_employees': on_leave_employees
            },
            'department_stats': department_stats,
            'status_breakdown': status_breakdown,
            'employee_details': employee_details,
            'filters': filters
        }
    


class EmployeeJoiningReport:
    def generate_joining_report(self, organization, filters=None):
        """
        Generate employee joining/onboarding report
        """
        filters = filters or {}
        
        employees = Employee.objects.filter(
            organization=organization
        ).select_related('department', 'designation', 'branch')
        
        # Date range filter
        start_date = filters.get('start_date')
        end_date = filters.get('end_date')
        
        if start_date and end_date:
            employees = employees.filter(hire_date__range=[start_date, end_date])
        elif start_date:
            employees = employees.filter(hire_date__gte=start_date)
        elif end_date:
            employees = employees.filter(hire_date__lte=end_date)
        
        if filters.get('department'):
            employees = employees.filter(department_id=filters['department'])
        
        # Monthly joining trend
        from django.db.models import Count
        from django.db.models.functions import TruncMonth
        
        monthly_trend = employees.annotate(
            month=TruncMonth('hire_date')
        ).values('month').annotate(
            count=Count('id')
        ).order_by('month')
        
        # Department-wise joining
        department_joining = employees.values(
            'department__name'
        ).annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Prepare detailed joining list
        joining_list = []
        for emp in employees:
            # Calculate probation status
            probation_status = "Completed"
            if emp.confirmation_date:
                if emp.confirmation_date > timezone.now().date():
                    probation_status = "Under Probation"
            else:
                # Calculate based on hire date + probation period
                probation_end_date = emp.hire_date + timezone.timedelta(days=emp.probation_period_months * 30)
                if probation_end_date > timezone.now().date():
                    probation_status = "Under Probation"
            
            joining_list.append({
                'employee_id': emp.employee_id,
                'full_name': emp.full_name,
                'department': emp.department.name if emp.department else 'N/A',
                'designation': emp.designation.name if emp.designation else 'N/A',
                'branch': emp.branch.name if emp.branch else 'N/A',
                'hire_date': emp.hire_date.strftime('%d-%m-%Y'),
                'confirmation_date': emp.confirmation_date.strftime('%d-%m-%Y') if emp.confirmation_date else 'N/A',
                'probation_period': f"{emp.probation_period_months} months",
                'probation_status': probation_status,
                'employment_status': emp.get_employment_status_display(),
                'reporting_manager': emp.reporting_manager.full_name if emp.reporting_manager else 'N/A',
                'work_email': emp.user.email if emp.user else 'N/A'
            })
        
        return {
            'report_name': 'Employee Joining Report',
            'generated_on': timezone.now().strftime('%d-%m-%Y %H:%M:%S'),
            'filters': filters,
            'summary': {
                'total_joinees': len(joining_list),
                'period': f"{start_date} to {end_date}" if start_date and end_date else "All Time"
            },
            'monthly_trend': list(monthly_trend),
            'department_wise_joining': list(department_joining),
            'joining_list': joining_list
        }
    

class EmployeeExitReport:
    def generate_exit_report(self, organization, filters=None):
        """
        Generate employee exit/termination report
        """
        filters = filters or {}
        
        employees = Employee.objects.filter(
            organization=organization,
            employment_status='terminated'
        ).select_related('department', 'designation', 'branch')
        
        # Date range filter for termination
        start_date = filters.get('start_date')
        end_date = filters.get('end_date')
        
        if start_date and end_date:
            employees = employees.filter(termination_date__range=[start_date, end_date])
        elif start_date:
            employees = employees.filter(termination_date__gte=start_date)
        elif end_date:
            employees = employees.filter(termination_date__lte=end_date)
        
        if filters.get('department'):
            employees = employees.filter(department_id=filters['department'])
        
        # Calculate attrition rate
        total_current_employees = Employee.objects.filter(
            organization=organization,
            employment_status='active'
        ).count()
        
        exited_count = employees.count()
        attrition_rate = (exited_count / (total_current_employees + exited_count)) * 100 if (total_current_employees + exited_count) > 0 else 0
        
        # Monthly exit trend
        from django.db.models import Count
        from django.db.models.functions import TruncMonth
        
        monthly_exit_trend = employees.annotate(
            month=TruncMonth('termination_date')
        ).values('month').annotate(
            count=Count('id')
        ).order_by('month')
        
        # Department-wise exit analysis
        department_exit = employees.values(
            'department__name'
        ).annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Experience analysis of exited employees
        experience_analysis = []
        experience_ranges = [
            ('0-1', (0, 1)),
            ('1-3', (1, 3)),
            ('3-5', (3, 5)),
            ('5-10', (5, 10)),
            ('10+', (10, 100))
        ]
        
        for range_name, (min_exp, max_exp) in experience_ranges:
            count = employees.filter(experience_years__gte=min_exp, experience_years__lt=max_exp).count()
            experience_analysis.append({
                'experience_range': range_name,
                'count': count
            })
        
        # Prepare detailed exit list
        exit_list = []
        for emp in employees:
            # Calculate employment duration
            employment_duration = "N/A"
            if emp.hire_date and emp.termination_date:
                duration_days = (emp.termination_date - emp.hire_date).days
                years = duration_days // 365
                months = (duration_days % 365) // 30
                employment_duration = f"{years} years, {months} months"
            
            exit_list.append({
                'employee_id': emp.employee_id,
                'full_name': emp.full_name,
                'department': emp.department.name if emp.department else 'N/A',
                'designation': emp.designation.name if emp.designation else 'N/A',
                'branch': emp.branch.name if emp.branch else 'N/A',
                'hire_date': emp.hire_date.strftime('%d-%m-%Y') if emp.hire_date else 'N/A',
                'termination_date': emp.termination_date.strftime('%d-%m-%Y') if emp.termination_date else 'N/A',
                'employment_duration': employment_duration,
                'experience_at_exit': f"{emp.experience_years} years",
                'last_designation': emp.designation.name if emp.designation else 'N/A',
                'reporting_manager': emp.reporting_manager.full_name if emp.reporting_manager else 'N/A',
                'exit_reason': 'Terminated'  # You can add reason field in Employee model
            })
        
        return {
            'report_name': 'Employee Exit Report',
            'generated_on': timezone.now().strftime('%d-%m-%Y %H:%M:%S'),
            'filters': filters,
            'summary': {
                'total_exits': exited_count,
                'attrition_rate': round(attrition_rate, 2),
                'current_employee_count': total_current_employees,
                'period': f"{start_date} to {end_date}" if start_date and end_date else "All Time"
            },
            'monthly_exit_trend': list(monthly_exit_trend),
            'department_wise_exit': list(department_exit),
            'experience_analysis': experience_analysis,
            'exit_list': exit_list
        }