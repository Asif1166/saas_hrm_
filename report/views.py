# reports/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from functools import wraps
from django.http import JsonResponse
from hrm.models import Employee, Department, Designation, Branch
from organization.decorators import organization_member_required
from report.attendance_reports import *
from report.earnings_deductions_reports import *
from report.hr_analytics_reports import *
from report.payment_disbursement_reports import *
from report.payroll_analytics_reports import *
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



# Payment & Disbursement Reports
@login_required
@organization_member_required
def bank_transfer_report(request):
    """Bank Transfer Report"""
    organization = request.organization
    
    filters = {
        'department': request.GET.get('department'),
        'designation': request.GET.get('designation'),
        'employee_id': request.GET.get('employee_id'),
        'payroll_period': request.GET.get('payroll_period'),
        'start_date': request.GET.get('start_date'),
        'end_date': request.GET.get('end_date'),
    }
    
    report_generator = BankTransferReport()
    report_data = report_generator.generate_bank_transfer_report(organization, filters)
    
    # Get filter options
    from hrm.models import Department, Designation
    from payroll.models import PayrollPeriod
    filter_options = {
        'departments': Department.objects.filter(organization=organization, is_active=True),
        'designations': Designation.objects.filter(organization=organization, is_active=True),
        'payroll_periods': PayrollPeriod.objects.filter(organization=organization).order_by('-start_date')
    }
    
    context = {
        'report_type': 'bank-transfer',
        'report_data': report_data,
        'filters': filters,
        'filter_options': filter_options,
        'page_title': 'Bank Transfer Report'
    }
    
    return render(request, 'reports/payment_disbursement_reports.html', context)

@login_required
@organization_member_required
def cash_payment_report(request):
    """Cash Payment Report"""
    organization = request.organization
    
    filters = {
        'department': request.GET.get('department'),
        'employee_id': request.GET.get('employee_id'),
        'payroll_period': request.GET.get('payroll_period'),
        'start_date': request.GET.get('start_date'),
        'end_date': request.GET.get('end_date'),
    }
    
    report_generator = CashPaymentReport()
    report_data = report_generator.generate_cash_payment_report(organization, filters)
    
    # Get filter options
    from hrm.models import Department
    from payroll.models import PayrollPeriod
    filter_options = {
        'departments': Department.objects.filter(organization=organization, is_active=True),
        'payroll_periods': PayrollPeriod.objects.filter(organization=organization).order_by('-start_date')
    }
    
    context = {
        'report_type': 'cash-payment',
        'report_data': report_data,
        'filters': filters,
        'filter_options': filter_options,
        'page_title': 'Cash Payment Report'
    }
    
    return render(request, 'reports/payment_disbursement_reports.html', context)

@login_required
@organization_member_required
def payment_status_report(request):
    """Payment Status Report"""
    organization = request.organization
    
    filters = {
        'department': request.GET.get('department'),
        'employee_id': request.GET.get('employee_id'),
        'payroll_period': request.GET.get('payroll_period'),
        'status': request.GET.get('status'),
        'start_date': request.GET.get('start_date'),
        'end_date': request.GET.get('end_date'),
    }
    
    report_generator = PaymentStatusReport()
    report_data = report_generator.generate_payment_status_report(organization, filters)
    
    # Get filter options
    from hrm.models import Department
    from payroll.models import PayrollPeriod
    filter_options = {
        'departments': Department.objects.filter(organization=organization, is_active=True),
        'payroll_periods': PayrollPeriod.objects.filter(organization=organization).order_by('-start_date')
    }
    
    context = {
        'report_type': 'payment-status',
        'report_data': report_data,
        'filters': filters,
        'filter_options': filter_options,
        'page_title': 'Payment Status Report'
    }
    
    return render(request, 'reports/payment_disbursement_reports.html', context)

@login_required
@organization_member_required
def payment_reconciliation_report(request):
    """Payment Reconciliation Report"""
    organization = request.organization
    
    filters = {
        'payroll_period': request.GET.get('payroll_period'),
        'start_date': request.GET.get('start_date'),
        'end_date': request.GET.get('end_date'),
    }
    
    report_generator = PaymentReconciliationReport()
    report_data = report_generator.generate_payment_reconciliation_report(organization, filters)
    
    # Get filter options
    from payroll.models import PayrollPeriod
    filter_options = {
        'payroll_periods': PayrollPeriod.objects.filter(organization=organization).order_by('-start_date')
    }
    
    context = {
        'report_type': 'payment-reconciliation',
        'report_data': report_data,
        'filters': filters,
        'filter_options': filter_options,
        'page_title': 'Payment Reconciliation Report'
    }
    
    return render(request, 'reports/payment_disbursement_reports.html', context)





# HR Analytics Reports
@login_required
@organization_member_required
def headcount_analysis_report(request):
    """Headcount Analysis Report"""
    organization = request.organization
    
    filters = {
        'department': request.GET.get('department'),
        'designation': request.GET.get('designation'),
        'start_date': request.GET.get('start_date'),
        'end_date': request.GET.get('end_date'),
    }
    
    report_generator = HeadcountAnalysisReport()
    report_data = report_generator.generate_headcount_analysis_report(organization, filters)
    
    # Get filter options
    from hrm.models import Department, Designation
    filter_options = {
        'departments': Department.objects.filter(organization=organization, is_active=True),
        'designations': Designation.objects.filter(organization=organization, is_active=True),
    }
    
    context = {
        'report_type': 'headcount-analysis',
        'report_data': report_data,
        'filters': filters,
        'filter_options': filter_options,
        'page_title': 'Headcount Analysis Report'
    }
    
    return render(request, 'reports/hr_analytics_reports.html', context)

@login_required
@organization_member_required
def attrition_report(request):
    """Attrition Report"""
    organization = request.organization
    
    filters = {
        'department': request.GET.get('department'),
        'designation': request.GET.get('designation'),
        'start_date': request.GET.get('start_date'),
        'end_date': request.GET.get('end_date'),
    }
    
    report_generator = AttritionReport()
    report_data = report_generator.generate_attrition_report(organization, filters)
    
    # Get filter options
    from hrm.models import Department, Designation
    filter_options = {
        'departments': Department.objects.filter(organization=organization, is_active=True),
        'designations': Designation.objects.filter(organization=organization, is_active=True),
    }
    
    context = {
        'report_type': 'attrition',
        'report_data': report_data,
        'filters': filters,
        'filter_options': filter_options,
        'page_title': 'Attrition Report'
    }
    
    return render(request, 'reports/hr_analytics_reports.html', context)

@login_required
@organization_member_required
def department_cost_analysis_report(request):
    """Department Cost Analysis Report"""
    organization = request.organization
    
    filters = {
        'start_date': request.GET.get('start_date'),
        'end_date': request.GET.get('end_date'),
    }
    
    report_generator = DepartmentCostAnalysisReport()
    report_data = report_generator.generate_department_cost_analysis(organization, filters)
    
    context = {
        'report_type': 'department-cost-analysis',
        'report_data': report_data,
        'filters': filters,
        'page_title': 'Department Cost Analysis Report'
    }
    
    return render(request, 'reports/hr_analytics_reports.html', context)

@login_required
@organization_member_required
def employee_cost_to_company_report(request):
    """Employee Cost-to-Company Report"""
    organization = request.organization
    
    filters = {
        'department': request.GET.get('department'),
        'designation': request.GET.get('designation'),
        'employee_id': request.GET.get('employee_id'),
    }
    
    report_generator = EmployeeCostToCompanyReport()
    report_data = report_generator.generate_employee_cost_to_company_report(organization, filters)
    
    # Get filter options
    from hrm.models import Department, Designation
    filter_options = {
        'departments': Department.objects.filter(organization=organization, is_active=True),
        'designations': Designation.objects.filter(organization=organization, is_active=True),
    }
    
    context = {
        'report_type': 'employee-ctc',
        'report_data': report_data,
        'filters': filters,
        'filter_options': filter_options,
        'page_title': 'Employee Cost-to-Company Report'
    }
    
    return render(request, 'reports/hr_analytics_reports.html', context)







@login_required
def payroll_analytics_dashboard(request):
    """Main payroll analytics dashboard"""
    try:
        organization = request.organization
        
        # Get filter parameters
        filters = _get_filters_from_request(request)
        
        # Generate dashboard data
        dashboard = PayrollAnalyticsDashboard(organization)
        dashboard_data = dashboard.generate_comprehensive_dashboard(filters)
        
        # Get filter options
        departments = Department.objects.filter(organization=organization, is_active=True)
        designations = Designation.objects.filter(organization=organization, is_active=True)
        
        context = {
            'dashboard_data': dashboard_data,
            'departments': departments,
            'designations': designations,
            'current_filters': filters,
            'page_title': 'Payroll Analytics Dashboard'
        }
        
        return render(request, 'report/analytics_dashboard.html', context)
    
    except ZeroDivisionError as e:
        # Handle division by zero errors gracefully
        return render(request, 'reports/analytics_error.html', {
            'error_message': 'Unable to generate analytics: No payroll data available for the selected period.',
            'page_title': 'Analytics Error'
        })
    
    except Exception as e:
        # Handle other errors
        import traceback
        print(f"Error in payroll analytics: {e}")
        print(traceback.format_exc())
        return render(request, 'reports/analytics_error.html', {
            'error_message': f'Error generating analytics: {str(e)}',
            'page_title': 'Analytics Error'
        })


@login_required
def payroll_cost_trends_report(request):
    """Payroll cost trends report view"""
    organization = request.organization
    
    filters = _get_filters_from_request(request)
    
    report_generator = PayrollCostTrendsReport()
    report_data = report_generator.generate_payroll_cost_trends_report(organization, filters)
    
    departments = Department.objects.filter(organization=organization, is_active=True)
    
    context = {
        'report_data': report_data,
        'departments': departments,
        'current_filters': filters,
        'page_title': 'Payroll Cost Trends Report'
    }
    
    return render(request, 'reports/partials/cost_trends_report.html', context)


@login_required
def overtime_cost_analysis_report(request):
    """Overtime cost analysis report view"""
    organization = request.organization
    
    filters = _get_filters_from_request(request)
    
    report_generator = OvertimeCostAnalysisReport()
    report_data = report_generator.generate_overtime_cost_analysis(organization, filters)
    
    departments = Department.objects.filter(organization=organization, is_active=True)
    
    context = {
        'report_data': report_data,
        'departments': departments,
        'current_filters': filters,
        'page_title': 'Overtime Cost Analysis Report'
    }
    
    return render(request, 'reports/partials/overtime_analysis.html', context)


@login_required
def bonus_incentive_analysis_report(request):
    """Bonus and incentive analysis report view"""
    organization = request.organization
    
    filters = _get_filters_from_request(request)
    
    report_generator = BonusIncentiveAnalysisReport()
    report_data = report_generator.generate_bonus_incentive_analysis(organization, filters)
    
    departments = Department.objects.filter(organization=organization, is_active=True)
    designations = Designation.objects.filter(organization=organization, is_active=True)
    
    context = {
        'report_data': report_data,
        'departments': departments,
        'designations': designations,
        'current_filters': filters,
        'page_title': 'Bonus & Incentive Analysis Report'
    }
    
    return render(request, 'reports/partials/bonus_analysis.html', context)


@login_required
def tax_liability_projection_report(request):
    """Tax liability projection report view"""
    organization = request.organization
    
    filters = _get_filters_from_request(request)
    
    report_generator = TaxLiabilityProjectionReport()
    report_data = report_generator.generate_tax_liability_projection(organization, filters)
    
    departments = Department.objects.filter(organization=organization, is_active=True)
    
    context = {
        'report_data': report_data,
        'departments': departments,
        'current_filters': filters,
        'page_title': 'Tax Liability Projection Report'
    }
    
    return render(request, 'reports/partials/tax_projections.html', context)


@login_required
def payroll_analytics_api(request):
    """API endpoint for AJAX analytics data"""
    organization = request.organization
    report_type = request.GET.get('report_type', 'dashboard')
    filters = _get_filters_from_request(request)
    
    try:
        if report_type == 'cost_trends':
            report_generator = PayrollCostTrendsReport()
            data = report_generator.generate_payroll_cost_trends_report(organization, filters)
        elif report_type == 'overtime':
            report_generator = OvertimeCostAnalysisReport()
            data = report_generator.generate_overtime_cost_analysis(organization, filters)
        elif report_type == 'bonus':
            report_generator = BonusIncentiveAnalysisReport()
            data = report_generator.generate_bonus_incentive_analysis(organization, filters)
        elif report_type == 'tax':
            report_generator = TaxLiabilityProjectionReport()
            data = report_generator.generate_tax_liability_projection(organization, filters)
        else:
            dashboard = PayrollAnalyticsDashboard(organization)
            data = dashboard.generate_comprehensive_dashboard(filters)
        
        return JsonResponse({'success': True, 'data': data})
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def _get_filters_from_request(request):
    """Extract filters from request parameters"""
    filters = {}
    
    # Date filters
    if request.GET.get('start_date'):
        filters['start_date'] = request.GET.get('start_date')
    if request.GET.get('end_date'):
        filters['end_date'] = request.GET.get('end_date')
    
    # Department filter
    if request.GET.get('department'):
        filters['department'] = request.GET.get('department')
    
    # Designation filter
    if request.GET.get('designation'):
        filters['designation'] = request.GET.get('designation')
    
    # Employee filter
    if request.GET.get('employee_id'):
        filters['employee_id'] = request.GET.get('employee_id')
    
    return filters