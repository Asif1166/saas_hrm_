# reports/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from functools import wraps

from hrm.models import Employee, Department, Designation, Branch
from organization.decorators import organization_member_required
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
    
    report_generator = EmployeeDirectoryReport()
    # Fix: Use the correct method name
    report_data = report_generator.generate_employee_directory(organization, filters)
    
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
    report_data = report_generator.generate_report(organization, filters)
    
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
    report_data = report_generator.generate_report(organization, filters)
    
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
    report_data = report_generator.generate_report(organization, filters)
    
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
    report_data = report_generator.generate_report(organization, filters)
    
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