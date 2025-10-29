# reports/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from functools import wraps

from hrm.models import Employee, Department, Designation, Branch
from organization.decorators import organization_member_required
from report.attendance_reports import *
from report.earnings_deductions_reports import *
from report.payroll_reports import *
from report.salary_reports import *
from report.statutory_compliance_reports import *
from .employee_reports import (
    EmployeeDirectoryReport,
    EmployeeProfileSummaryReport,
    EmployeeStatusReport,
    EmployeeJoiningReport,
    EmployeeExitReport
)


@login_required
@organization_member_required
def employee_directory_report(request):
    """Employee Directory Report"""
    organization = request.organization
    
    filters = {
        'department': request.GET.get('department'),
        'designation': request.GET.get('designation'),
        'branch': request.GET.get('branch'),
        'employment_status': request.GET.get('employment_status'),
        'search': request.GET.get('search'),
    }
    
    # Pagination parameters
    page_number = request.GET.get('page', 1)
    page_size = request.GET.get('page_size', 20)
    show_all = request.GET.get('show_all') == 'true'
    
    report_generator = EmployeeDirectoryReport()
    report_data = report_generator.generate_employee_directory(
        organization, 
        filters, 
        page_number=page_number,
        page_size=page_size,
        show_all=show_all
    )
    
    # Get filter options
    from hrm.models import Department, Designation, Branch, Employee
    filter_options = {
        'departments': Department.objects.filter(organization=organization, is_active=True),
        'designations': Designation.objects.filter(organization=organization, is_active=True),
        'branches': Branch.objects.filter(organization=organization, is_active=True),
        'employment_statuses': Employee.EMPLOYMENT_STATUS_CHOICES,
    }
    
    context = {
        'report_type': 'directory',
        'report_data': report_data,
        'filters': filters,
        'filter_options': filter_options,
        'page_title': 'Employee Directory Report'
    }
    
    return render(request, 'reports/employee_reports.html', context)


@login_required
@organization_member_required
def employee_profile_summary_report(request):
    """Employee Profile Summary Report"""
    organization = request.organization
    
    filters = {
        'employee_id': request.GET.get('employee_id'),
        'search': request.GET.get('search'),
    }
    
    report_generator = EmployeeProfileSummaryReport()
    report_data = report_generator.generate_profile_summary(organization, filters)
    
    # Get filter options
    filter_options = {
        'departments': Department.objects.filter(organization=organization, is_active=True),
        'designations': Designation.objects.filter(organization=organization, is_active=True),
        'branches': Branch.objects.filter(organization=organization, is_active=True),
    }
    
    context = {
        'report_type': 'profile-summary',
        'report_data': report_data,
        'filters': filters,
        'filter_options': filter_options,
        'page_title': 'Employee Profile Summary Report'
    }
    
    return render(request, 'reports/employee_reports.html', context)

@login_required
@organization_member_required
def employee_status_report(request):
    """Employee Status Report"""
    organization = request.organization
    
    filters = {
        'department': request.GET.get('department'),
        'designation': request.GET.get('designation'),
        'status': request.GET.get('status'),
        'search': request.GET.get('search'),
    }
    
    report_generator = EmployeeStatusReport()
    report_data = report_generator.generate_employee_status(organization, filters)
    
    # Get filter options
    filter_options = {
        'departments': Department.objects.filter(organization=organization, is_active=True),
        'designations': Designation.objects.filter(organization=organization, is_active=True),
        'employment_statuses': Employee.EMPLOYMENT_STATUS_CHOICES,
    }
    
    context = {
        'report_type': 'status',
        'report_data': report_data,
        'filters': filters,
        'filter_options': filter_options,
        'page_title': 'Employee Status Report'
    }
    
    return render(request, 'reports/employee_reports.html', context)

@login_required
@organization_member_required
def employee_joining_report(request):
    """Employee Joining Report"""
    organization = request.organization
    
    filters = {
        'department': request.GET.get('department'),
        'start_date': request.GET.get('start_date'),
        'end_date': request.GET.get('end_date'),
        'search': request.GET.get('search'),
    }
    
    report_generator = EmployeeJoiningReport()
    report_data = report_generator.generate_joining_report(organization, filters)
    
    # Get filter options
    filter_options = {
        'departments': Department.objects.filter(organization=organization, is_active=True),
    }
    
    context = {
        'report_type': 'joining',
        'report_data': report_data,
        'filters': filters,
        'filter_options': filter_options,
        'page_title': 'Employee Joining Report'
    }
    
    return render(request, 'reports/employee_reports.html', context)

@login_required
@organization_member_required
def employee_exit_report(request):
    """Employee Exit Report"""
    organization = request.organization
    
    filters = {
        'department': request.GET.get('department'),
        'start_date': request.GET.get('start_date'),
        'end_date': request.GET.get('end_date'),
        'search': request.GET.get('search'),
    }
    
    report_generator = EmployeeExitReport()
    report_data = report_generator.generate_exit_report(organization, filters)
    
    # Get filter options
    filter_options = {
        'departments': Department.objects.filter(organization=organization, is_active=True),
    }
    
    context = {
        'report_type': 'exit',
        'report_data': report_data,
        'filters': filters,
        'filter_options': filter_options,
        'page_title': 'Employee Exit Report'
    }
    
    return render(request, 'reports/employee_reports.html', context)




# Attendance Report

@login_required
@organization_member_required
def daily_attendance_report(request):
    """Daily Attendance Report"""
    organization = request.organization
    
    filters = {
        'date': request.GET.get('date'),
        'department': request.GET.get('department'),
    }
    
    report_generator = DailyAttendanceReport()
    report_data = report_generator.generate_daily_report(organization, filters)
    
    # Get filter options
    from hrm.models import Department
    filter_options = {
        'departments': Department.objects.filter(organization=organization, is_active=True),
    }
    
    context = {
        'report_type': 'daily-attendance',
        'report_data': report_data,
        'filters': filters,
        'filter_options': filter_options,
        'page_title': 'Daily Attendance Report'
    }
    
    return render(request, 'reports/attendance_reports.html', context)

@login_required
@organization_member_required
def monthly_attendance_summary(request):
    """Monthly Attendance Summary"""
    organization = request.organization
    
    filters = {
        'year': request.GET.get('year'),
        'month': request.GET.get('month'),
        'department': request.GET.get('department'),
    }
    
    report_generator = MonthlyAttendanceSummary()
    report_data = report_generator.generate_monthly_summary(organization, filters)
    
    # Get filter options
    from hrm.models import Department
    filter_options = {
        'departments': Department.objects.filter(organization=organization, is_active=True),
        'months': [
            (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
            (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
            (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')
        ],
        'years': range(2020, timezone.now().year + 1)
    }
    
    context = {
        'report_type': 'monthly-summary',
        'report_data': report_data,
        'filters': filters,
        'filter_options': filter_options,
        'page_title': 'Monthly Attendance Summary'
    }
    
    return render(request, 'reports/attendance_reports.html', context)

@login_required
@organization_member_required
def late_coming_report(request):
    """Late Coming Report"""
    organization = request.organization
    
    filters = {
        'start_date': request.GET.get('start_date'),
        'end_date': request.GET.get('end_date'),
        'department': request.GET.get('department'),
    }
    
    report_generator = LateComingReport()
    report_data = report_generator.generate_late_report(organization, filters)
    
    # Get filter options
    from hrm.models import Department
    filter_options = {
        'departments': Department.objects.filter(organization=organization, is_active=True),
    }
    
    context = {
        'report_type': 'late-coming',
        'report_data': report_data,
        'filters': filters,
        'filter_options': filter_options,
        'page_title': 'Late Coming Report'
    }
    
    return render(request, 'reports/attendance_reports.html', context)

@login_required
@organization_member_required
def early_departure_report(request):
    """Early Departure Report"""
    organization = request.organization
    
    filters = {
        'start_date': request.GET.get('start_date'),
        'end_date': request.GET.get('end_date'),
        'department': request.GET.get('department'),
    }
    
    report_generator = EarlyDepartureReport()
    report_data = report_generator.generate_early_departure_report(organization, filters)
    
    # Get filter options
    from hrm.models import Department
    filter_options = {
        'departments': Department.objects.filter(organization=organization, is_active=True),
    }
    
    context = {
        'report_type': 'early-departure',
        'report_data': report_data,
        'filters': filters,
        'filter_options': filter_options,
        'page_title': 'Early Departure Report'
    }
    
    return render(request, 'reports/attendance_reports.html', context)

@login_required
@organization_member_required
def overtime_report(request):
    """Overtime Report"""
    organization = request.organization
    
    filters = {
        'start_date': request.GET.get('start_date'),
        'end_date': request.GET.get('end_date'),
        'department': request.GET.get('department'),
    }
    
    report_generator = OvertimeReport()
    report_data = report_generator.generate_overtime_report(organization, filters)
    
    # Get filter options
    from hrm.models import Department
    filter_options = {
        'departments': Department.objects.filter(organization=organization, is_active=True),
    }
    
    context = {
        'report_type': 'overtime',
        'report_data': report_data,
        'filters': filters,
        'filter_options': filter_options,
        'page_title': 'Overtime Report'
    }
    
    return render(request, 'reports/attendance_reports.html', context)

@login_required
@organization_member_required
def leave_balance_report(request):
    """Leave Balance Report"""
    organization = request.organization
    
    filters = {
        'department': request.GET.get('department'),
    }
    
    report_generator = LeaveBalanceReport()
    report_data = report_generator.generate_leave_balance_report(organization, filters)
    
    # Get filter options
    from hrm.models import Department
    filter_options = {
        'departments': Department.objects.filter(organization=organization, is_active=True),
    }
    
    context = {
        'report_type': 'leave-balance',
        'report_data': report_data,
        'filters': filters,
        'filter_options': filter_options,
        'page_title': 'Leave Balance Report'
    }
    
    return render(request, 'reports/attendance_reports.html', context)

@login_required
@organization_member_required
def leave_utilization_report(request):
    """Leave Utilization Report"""
    organization = request.organization
    
    filters = {
        'year': request.GET.get('year'),
        'department': request.GET.get('department'),
    }
    
    report_generator = LeaveUtilizationReport()
    report_data = report_generator.generate_leave_utilization_report(organization, filters)
    
    # Get filter options
    from hrm.models import Department
    filter_options = {
        'departments': Department.objects.filter(organization=organization, is_active=True),
        'years': range(2020, timezone.now().year + 1)
    }
    
    context = {
        'report_type': 'leave-utilization',
        'report_data': report_data,
        'filters': filters,
        'filter_options': filter_options,
        'page_title': 'Leave Utilization Report'
    }
    
    return render(request, 'reports/attendance_reports.html', context)





# Payroll Reports

@login_required
@organization_member_required
def payroll_register_report(request):
    """Payroll Register Report"""
    organization = request.organization
    
    filters = {
        'payroll_period': request.GET.get('payroll_period'),
        'department': request.GET.get('department'),
    }
    
    report_generator = PayrollRegisterReport()
    report_data = report_generator.generate_payroll_register(organization, filters)
    
    # Get filter options
    from payroll.models import PayrollPeriod
    from hrm.models import Department
    filter_options = {
        'payroll_periods': PayrollPeriod.objects.filter(organization=organization, status='completed').order_by('-start_date'),
        'departments': Department.objects.filter(organization=organization, is_active=True),
    }
    
    context = {
        'report_type': 'payroll-register',
        'report_data': report_data,
        'filters': filters,
        'filter_options': filter_options,
        'page_title': 'Payroll Register Report'
    }
    
    return render(request, 'reports/payroll_reports.html', context)

@login_required
@organization_member_required
def payroll_summary_report(request):
    """Payroll Summary Report"""
    organization = request.organization
    
    filters = {
        'payroll_period': request.GET.get('payroll_period'),
    }
    
    report_generator = PayrollSummaryReport()
    report_data = report_generator.generate_payroll_summary(organization, filters)
    
    # Get filter options
    from payroll.models import PayrollPeriod
    filter_options = {
        'payroll_periods': PayrollPeriod.objects.filter(organization=organization, status='completed').order_by('-start_date'),
    }
    
    context = {
        'report_type': 'payroll-summary',
        'report_data': report_data,
        'filters': filters,
        'filter_options': filter_options,
        'page_title': 'Payroll Summary Report'
    }
    
    return render(request, 'reports/payroll_reports.html', context)

@login_required
@organization_member_required
def payroll_variance_report(request):
    """Payroll Variance Report"""
    organization = request.organization
    
    filters = {
        'current_period': request.GET.get('current_period'),
    }
    
    report_generator = PayrollVarianceReport()
    report_data = report_generator.generate_payroll_variance(organization, filters)
    
    # Get filter options
    from payroll.models import PayrollPeriod
    filter_options = {
        'payroll_periods': PayrollPeriod.objects.filter(organization=organization, status='completed').order_by('-start_date'),
    }
    
    context = {
        'report_type': 'payroll-variance',
        'report_data': report_data,
        'filters': filters,
        'filter_options': filter_options,
        'page_title': 'Payroll Variance Report'
    }
    
    return render(request, 'reports/payroll_reports.html', context)



# Salary Reports

@login_required
@organization_member_required
def salary_structure_report(request):
    """Salary Structure Report"""
    organization = request.organization
    
    filters = {
        'department': request.GET.get('department'),
        'designation': request.GET.get('designation'),
        'employee_id': request.GET.get('employee_id'),
    }
    
    report_generator = SalaryStructureReport()
    report_data = report_generator.generate_salary_structure_report(organization, filters)
    
    # Get filter options
    from hrm.models import Department, Designation
    filter_options = {
        'departments': Department.objects.filter(organization=organization, is_active=True),
        'designations': Designation.objects.filter(organization=organization, is_active=True),
    }
    
    context = {
        'report_type': 'salary-structure',
        'report_data': report_data,
        'filters': filters,
        'filter_options': filter_options,
        'page_title': 'Salary Structure Report'
    }
    
    return render(request, 'reports/salary_reports.html', context)

@login_required
@organization_member_required
def salary_revision_report(request):
    """Salary Revision Report"""
    organization = request.organization
    
    filters = {
        'department': request.GET.get('department'),
        'employee_id': request.GET.get('employee_id'),
        'start_date': request.GET.get('start_date'),
        'end_date': request.GET.get('end_date'),
    }
    
    report_generator = SalaryRevisionReport()
    report_data = report_generator.generate_salary_revision_report(organization, filters)
    
    # Get filter options
    from hrm.models import Department
    filter_options = {
        'departments': Department.objects.filter(organization=organization, is_active=True),
    }
    
    context = {
        'report_type': 'salary-revision',
        'report_data': report_data,
        'filters': filters,
        'filter_options': filter_options,
        'page_title': 'Salary Revision Report'
    }
    
    return render(request, 'reports/salary_reports.html', context)

@login_required
@organization_member_required
def comparative_salary_report(request):
    """Comparative Salary Report"""
    organization = request.organization
    
    filters = {
        'department': request.GET.get('department'),
    }
    
    report_generator = ComparativeSalaryReport()
    report_data = report_generator.generate_comparative_salary_report(organization, filters)
    
    # Get filter options
    from hrm.models import Department
    filter_options = {
        'departments': Department.objects.filter(organization=organization, is_active=True),
    }
    
    context = {
        'report_type': 'comparative-salary',
        'report_data': report_data,
        'filters': filters,
        'filter_options': filter_options,
        'page_title': 'Comparative Salary Report'
    }
    
    return render(request, 'reports/salary_reports.html', context)




# Earnings & Deductions Reports
@login_required
@organization_member_required
def earnings_breakdown_report(request):
    """Earnings Breakdown Report"""
    organization = request.organization
    
    filters = {
        'department': request.GET.get('department'),
        'designation': request.GET.get('designation'),
        'employee_id': request.GET.get('employee_id'),
        'start_date': request.GET.get('start_date'),
        'end_date': request.GET.get('end_date'),
    }
    
    report_generator = EarningsBreakdownReport()
    report_data = report_generator.generate_earnings_breakdown_report(organization, filters)
    
    # Get filter options
    from hrm.models import Department, Designation
    filter_options = {
        'departments': Department.objects.filter(organization=organization, is_active=True),
        'designations': Designation.objects.filter(organization=organization, is_active=True),
    }
    
    context = {
        'report_type': 'earnings-breakdown',
        'report_data': report_data,
        'filters': filters,
        'filter_options': filter_options,
        'page_title': 'Earnings Breakdown Report'
    }
    
    return render(request, 'reports/earnings_deductions_reports.html', context)

@login_required
@organization_member_required
def deductions_summary_report(request):
    """Deductions Summary Report"""
    organization = request.organization
    
    filters = {
        'department': request.GET.get('department'),
        'designation': request.GET.get('designation'),
        'employee_id': request.GET.get('employee_id'),
        'start_date': request.GET.get('start_date'),
        'end_date': request.GET.get('end_date'),
    }
    
    report_generator = DeductionsSummaryReport()
    report_data = report_generator.generate_deductions_summary_report(organization, filters)
    
    # Get filter options
    from hrm.models import Department, Designation
    filter_options = {
        'departments': Department.objects.filter(organization=organization, is_active=True),
        'designations': Designation.objects.filter(organization=organization, is_active=True),
    }
    
    context = {
        'report_type': 'deductions-summary',
        'report_data': report_data,
        'filters': filters,
        'filter_options': filter_options,
        'page_title': 'Deductions Summary Report'
    }
    
    return render(request, 'reports/earnings_deductions_reports.html', context)

@login_required
@organization_member_required
def payhead_analysis_report(request):
    """Payhead Analysis Report"""
    organization = request.organization
    
    filters = {
        'start_date': request.GET.get('start_date'),
        'end_date': request.GET.get('end_date'),
        'payhead_type': request.GET.get('payhead_type'),
    }
    
    report_generator = PayheadAnalysisReport()
    report_data = report_generator.generate_payhead_analysis_report(organization, filters)
    
    context = {
        'report_type': 'payhead-analysis',
        'report_data': report_data,
        'filters': filters,
        'page_title': 'Payhead Analysis Report'
    }
    
    return render(request, 'reports/earnings_deductions_reports.html', context)

# Statutory & Compliance Reports
@login_required
@organization_member_required
def provident_fund_report(request):
    """Provident Fund Report"""
    organization = request.organization
    
    filters = {
        'department': request.GET.get('department'),
        'employee_id': request.GET.get('employee_id'),
        'start_date': request.GET.get('start_date'),
        'end_date': request.GET.get('end_date'),
    }
    
    report_generator = ProvidentFundReport()
    report_data = report_generator.generate_provident_fund_report(organization, filters)
    
    # Get filter options
    from hrm.models import Department
    filter_options = {
        'departments': Department.objects.filter(organization=organization, is_active=True),
    }
    
    context = {
        'report_type': 'provident-fund',
        'report_data': report_data,
        'filters': filters,
        'filter_options': filter_options,
        'page_title': 'Provident Fund Report'
    }
    
    return render(request, 'reports/statutory_compliance_reports.html', context)

@login_required
@organization_member_required
def tax_deduction_report(request):
    """Tax Deduction Report"""
    organization = request.organization
    
    filters = {
        'department': request.GET.get('department'),
        'employee_id': request.GET.get('employee_id'),
        'start_date': request.GET.get('start_date'),
        'end_date': request.GET.get('end_date'),
    }
    
    report_generator = TaxDeductionReport()
    report_data = report_generator.generate_tax_deduction_report(organization, filters)
    
    # Get filter options
    from hrm.models import Department
    filter_options = {
        'departments': Department.objects.filter(organization=organization, is_active=True),
    }
    
    context = {
        'report_type': 'tax-deduction',
        'report_data': report_data,
        'filters': filters,
        'filter_options': filter_options,
        'page_title': 'Tax Deduction Report'
    }
    
    return render(request, 'reports/statutory_compliance_reports.html', context)

@login_required
@organization_member_required
def esi_report(request):
    """ESI Report"""
    organization = request.organization
    
    filters = {
        'department': request.GET.get('department'),
        'employee_id': request.GET.get('employee_id'),
        'start_date': request.GET.get('start_date'),
        'end_date': request.GET.get('end_date'),
    }
    
    report_generator = ESIReport()
    report_data = report_generator.generate_esi_report(organization, filters)
    
    # Get filter options
    from hrm.models import Department
    filter_options = {
        'departments': Department.objects.filter(organization=organization, is_active=True),
    }
    
    context = {
        'report_type': 'esi',
        'report_data': report_data,
        'filters': filters,
        'filter_options': filter_options,
        'page_title': 'ESI Report'
    }
    
    return render(request, 'reports/statutory_compliance_reports.html', context)

@login_required
@organization_member_required
def gratuity_report(request):
    """Gratuity Report"""
    organization = request.organization
    
    filters = {
        'department': request.GET.get('department'),
        'employee_id': request.GET.get('employee_id'),
    }
    
    report_generator = GratuityReport()
    report_data = report_generator.generate_gratuity_report(organization, filters)
    
    # Get filter options
    from hrm.models import Department
    filter_options = {
        'departments': Department.objects.filter(organization=organization, is_active=True),
    }
    
    context = {
        'report_type': 'gratuity',
        'report_data': report_data,
        'filters': filters,
        'filter_options': filter_options,
        'page_title': 'Gratuity Report'
    }
    
    return render(request, 'reports/statutory_compliance_reports.html', context)