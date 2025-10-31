from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from hrm.utils import handle_bulk_delete, restore_objects_view, trash_list_view
from organization.decorators import organization_member_required, organization_admin_required
from organization.utils import DynamicTableManager
from payroll.models import Payslip, SalaryStructure
from .models import Branch, Department, Designation, EmployeeRole, Employee, AttendanceRecord, HolidayCalendar, LeaveRequest, Shift, Timetable, AttendanceDevice, Payhead, EmployeePayhead, AttendanceHoliday
from .forms import EmployeeForm, BranchForm, DepartmentForm, DesignationForm, EmployeeRoleForm, EmployeeUpdateForm, ShiftForm, TimetableForm, AttendanceDeviceForm, PayheadForm, EmployeePayheadForm, AttendanceHolidayForm, AttendanceFilterForm
from .zkteco_utils import *
from datetime import date, datetime
from django.utils import timezone
from django.urls import reverse
from datetime import timedelta
from django.utils.dateparse import parse_date
import json
from django.views.decorators.http import require_http_methods

User = get_user_model()


@login_required
@organization_member_required
def hrm_dashboard(request):
    """HRM Dashboard for organization members"""
    organization = request.organization
    
    # Statistics
    total_employees = Employee.objects.filter(organization=organization, is_active=True).count()
    total_departments = Department.objects.filter(organization=organization, is_active=True).count()
    total_branches = Branch.objects.filter(organization=organization, is_active=True).count()
    
    # Recent employees
    recent_employees = Employee.objects.filter(organization=organization).order_by('-created_at')[:5]
    
    # Today's attendance
    # today_attendance = Attendance.objects.filter(
    #     organization=organization,
    #     date=date.today()
    # ).count()
    
    context = {
        'organization': organization,
        'total_employees': total_employees,
        'total_departments': total_departments,
        'total_branches': total_branches,
        'recent_employees': recent_employees,
        # 'today_attendance': today_attendance,
    }
    return render(request, 'hrm/dashboard.html', context)


# Branch Management Views
@login_required
@organization_admin_required
def branch_list(request):
    """List branches for the organization"""
    organization = request.organization
    
    # Get filter parameters
    search_query = request.GET.get('search')
    status_filter = request.GET.get('status')
    
    branches = Branch.objects.filter(organization=organization).order_by('name')
    
    # Apply filters
    if search_query:
        branches = branches.filter(
            Q(name__icontains=search_query) |
            Q(code__icontains=search_query) |
            Q(city__icontains=search_query)
        )
    
    if status_filter:
        if status_filter == 'active':
            branches = branches.filter(is_active=True)
        elif status_filter == 'inactive':
            branches = branches.filter(is_active=False)
    
    paginator = Paginator(branches, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'organization': organization,
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
    }
    return render(request, 'hrm/branch_list.html', context)


@login_required
@organization_admin_required
def create_branch(request):
    """Create new branch"""
    if request.method == 'POST':
        form = BranchForm(request.POST, request.FILES, organization=request.organization)
        if form.is_valid():
            branch = form.save(commit=False)
            branch.organization = request.organization
            branch.created_by = request.user
            branch.save()
            messages.success(request, f'Branch "{branch.name}" created successfully!')
            return redirect('hrm:branch_list')
    else:
        form = BranchForm(organization=request.organization)
    
    context = {
        'organization': request.organization,
        'form': form,
    }
    return render(request, 'hrm/branch_form.html', context)


@login_required
@organization_admin_required
def update_branch(request, branch_id):
    """Update existing branch"""
    try:
        branch = get_object_or_404(Branch, id=branch_id, organization=request.organization)
    except Branch.DoesNotExist:
        messages.error(request, 'Branch not found.')
        return redirect('hrm:branch_list')

    if request.method == 'POST':
        form = BranchForm(request.POST, request.FILES, instance=branch, organization=request.organization)
        if form.is_valid():
            branch = form.save(commit=False)
            branch.updated_by = request.user
            branch.save()
            messages.success(request, f'Branch "{branch.name}" updated successfully!')
            return redirect('hrm:branch_list')
    else:
        form = BranchForm(instance=branch, organization=request.organization)

    context = {
        'organization': request.organization,
        'form': form,
        'branch': branch,
        'is_update': True,
    }
    return render(request, 'hrm/branch_form.html', context)


# Department Management Views
@login_required
@organization_admin_required
def department_list(request):
    """List departments for the organization"""
    organization = request.organization
    
    # Get filter parameters
    search_query = request.GET.get('search')
    branch_filter = request.GET.get('branch')
    status_filter = request.GET.get('status')
    
    departments = Department.objects.filter(organization=organization).order_by('name')
    
    # Apply filters
    if search_query:
        departments = departments.filter(
            Q(name__icontains=search_query) |
            Q(code__icontains=search_query)
        )
    
    if branch_filter:
        departments = departments.filter(branch_id=branch_filter)
    
    if status_filter:
        if status_filter == 'active':
            departments = departments.filter(is_active=True)
        elif status_filter == 'inactive':
            departments = departments.filter(is_active=False)
    
    paginator = Paginator(departments, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    branches = Branch.objects.filter(organization=organization, is_active=True)
    
    context = {
        'organization': organization,
        'page_obj': page_obj,
        'search_query': search_query,
        'branch_filter': branch_filter,
        'status_filter': status_filter,
        'branches': branches,
    }
    return render(request, 'hrm/department_list.html', context)


@login_required
@organization_admin_required
def create_department(request):
    """Create new department"""
    if request.method == 'POST':
        form = DepartmentForm(request.POST, request.FILES, organization=request.organization)
        if form.is_valid():
            department = form.save(commit=False)
            department.organization = request.organization
            department.created_by = request.user
            department.save()
            messages.success(request, f'Department "{department.name}" created successfully!')
            return redirect('hrm:department_list')
    else:
        form = DepartmentForm(organization=request.organization)
    
    context = {
        'organization': request.organization,
        'form': form,
    }
    return render(request, 'hrm/department_form.html', context)


@login_required
@organization_admin_required
def update_department(request, department_id):
    """Update existing department"""
    try:
        department = get_object_or_404(Department, id=department_id, organization=request.organization)
    except Department.DoesNotExist:
        messages.error(request, 'Department not found.')
        return redirect('hrm:department_list')

    if request.method == 'POST':
        form = DepartmentForm(request.POST, request.FILES, instance=department, organization=request.organization)
        if form.is_valid():
            department = form.save(commit=False)
            department.updated_by = request.user
            department.save()
            messages.success(request, f'Department "{department.name}" updated successfully!')
            return redirect('hrm:department_list')
    else:
        form = DepartmentForm(instance=department, organization=request.organization)

    context = {
        'organization': request.organization,
        'form': form,
        'department': department,
        'is_update': True,
    }
    return render(request, 'hrm/department_form.html', context)


# Designation Management Views
@login_required
@organization_admin_required
def designation_list(request):
    """List designations for the organization"""
    organization = request.organization
    
    # Get filter parameters
    search_query = request.GET.get('search')
    department_filter = request.GET.get('department')
    level_filter = request.GET.get('level')
    status_filter = request.GET.get('status')
    
    designations = Designation.objects.filter(organization=organization).order_by('level', 'name')
    
    # Apply filters
    if search_query:
        designations = designations.filter(
            Q(name__icontains=search_query) |
            Q(code__icontains=search_query)
        )
    
    if department_filter:
        designations = designations.filter(department_id=department_filter)
    
    if level_filter:
        designations = designations.filter(level=level_filter)
    
    if status_filter:
        if status_filter == 'active':
            designations = designations.filter(is_active=True)
        elif status_filter == 'inactive':
            designations = designations.filter(is_active=False)
    
    paginator = Paginator(designations, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    departments = Department.objects.filter(organization=organization, is_active=True)
    
    context = {
        'organization': organization,
        'page_obj': page_obj,
        'search_query': search_query,
        'department_filter': department_filter,
        'level_filter': level_filter,
        'status_filter': status_filter,
        'departments': departments,
    }
    return render(request, 'hrm/designation_list.html', context)


@login_required
@organization_admin_required
def create_designation(request):
    """Create new designation"""
    if request.method == 'POST':
        form = DesignationForm(request.POST, request.FILES, organization=request.organization)
        if form.is_valid():
            designation = form.save(commit=False)
            designation.organization = request.organization
            designation.created_by = request.user
            designation.save()
            messages.success(request, f'Designation "{designation.name}" created successfully!')
            return redirect('hrm:designation_list')
    else:
        form = DesignationForm(organization=request.organization)
    
    context = {
        'organization': request.organization,
        'form': form,
    }
    return render(request, 'hrm/designation_form.html', context)


@login_required
@organization_admin_required
def update_designation(request, designation_id):
    """Update existing designation"""
    try:
        designation = get_object_or_404(Designation, id=designation_id, organization=request.organization)
    except Designation.DoesNotExist:
        messages.error(request, 'Designation not found.')
        return redirect('hrm:designation_list')

    if request.method == 'POST':
        form = DesignationForm(request.POST, request.FILES, instance=designation, organization=request.organization)
        if form.is_valid():
            designation = form.save(commit=False)
            designation.updated_by = request.user
            designation.save()
            messages.success(request, f'Designation "{designation.name}" updated successfully!')
            return redirect('hrm:designation_list')
    else:
        form = DesignationForm(instance=designation, organization=request.organization)

    context = {
        'organization': request.organization,
        'form': form,
        'designation': designation,
        'is_update': True,
    }
    return render(request, 'hrm/designation_form.html', context)


# Employee Role Management Views
@login_required
@organization_admin_required
def employee_role_list(request):
    """List employee roles for the organization"""
    organization = request.organization
    
    # Get filter parameters
    search_query = request.GET.get('search')
    status_filter = request.GET.get('status')
    
    roles = EmployeeRole.objects.filter(organization=organization).order_by('name')
    
    # Apply filters
    if search_query:
        roles = roles.filter(
            Q(name__icontains=search_query) |
            Q(code__icontains=search_query)
        )
    
    if status_filter:
        if status_filter == 'active':
            roles = roles.filter(is_active=True)
        elif status_filter == 'inactive':
            roles = roles.filter(is_active=False)
    
    paginator = Paginator(roles, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'organization': organization,
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
    }
    return render(request, 'hrm/employee_role_list.html', context)


@login_required
@organization_admin_required
def create_employee_role(request):
    """Create new employee role"""
    if request.method == 'POST':
        form = EmployeeRoleForm(request.POST, request.FILES, organization=request.organization)
        if form.is_valid():
            role = form.save(commit=False)
            role.organization = request.organization
            role.created_by = request.user
            role.save()
            messages.success(request, f'Employee Role "{role.name}" created successfully!')
            return redirect('hrm:employee_role_list')
    else:
        form = EmployeeRoleForm(organization=request.organization)
    
    context = {
        'organization': request.organization,
        'form': form,
    }
    return render(request, 'hrm/employee_role_form.html', context)


@login_required
@organization_admin_required
def update_employee_role(request, role_id):
    """Update existing employee role"""
    try:
        role = get_object_or_404(EmployeeRole, id=role_id, organization=request.organization)
    except EmployeeRole.DoesNotExist:
        messages.error(request, 'Employee role not found.')
        return redirect('hrm:employee_role_list')

    if request.method == 'POST':
        form = EmployeeRoleForm(request.POST, request.FILES, instance=role, organization=request.organization)
        if form.is_valid():
            role = form.save(commit=False)
            role.updated_by = request.user
            role.save()
            messages.success(request, f'Employee Role "{role.name}" updated successfully!')
            return redirect('hrm:employee_role_list')
    else:
        form = EmployeeRoleForm(instance=role, organization=request.organization)

    context = {
        'organization': request.organization,
        'form': form,
        'role': role,
        'is_update': True,
    }
    return render(request, 'hrm/employee_role_form.html', context)


# Employee Management Views
@login_required
@organization_member_required
def employee_list(request):
    """List employees for the organization with dynamic table support"""
    organization = request.organization
    
    # Check if user can access employee list table
    # Organization admins and super admins always have access
    if not (request.user.is_organization_admin or request.user.is_super_admin or 
            DynamicTableManager.can_user_access_table(request.user, organization, 'employee_list', 'view')):
        messages.error(request, 'You do not have permission to view the employee list.')
        return redirect('hrm:dashboard')
    
    employees = Employee.objects.filter(organization=organization).select_related(
        'user', 'department', 'designation', 'employee_role', 'branch', 'reporting_manager'
    ).order_by('last_name', 'first_name')
    
    # Get filter parameters
    search_query = request.GET.get('search')
    branch_filter = request.GET.get('branch')
    department_filter = request.GET.get('department')
    designation_filter = request.GET.get('designation')
    role_filter = request.GET.get('role')
    status_filter = request.GET.get('status')
    
    # Apply filters
    if search_query:
        employees = employees.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(employee_id__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(personal_email__icontains=search_query)
        )
    
    if branch_filter:
        employees = employees.filter(branch_id=branch_filter)
    
    if department_filter:
        employees = employees.filter(department_id=department_filter)
    
    if designation_filter:
        employees = employees.filter(designation_id=designation_filter)
    
    if role_filter:
        employees = employees.filter(employee_role_id=role_filter)
    
    if status_filter:
        employees = employees.filter(employment_status=status_filter)
    
    # Pagination
    paginator = Paginator(employees, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    branches = Branch.objects.filter(organization=organization, is_active=True)
    departments = Department.objects.filter(organization=organization, is_active=True)
    designations = Designation.objects.filter(organization=organization, is_active=True)
    roles = EmployeeRole.objects.filter(organization=organization, is_active=True)
    
    # Get dynamic table columns for this user
    table_columns = DynamicTableManager.get_user_table_columns(
        request.user, organization, 'employee_list'
    )
    
    # Get user preferences
    user_preferences = DynamicTableManager.get_user_table_preferences(
        request.user, organization, 'employee_list'
    )
    
    context = {
        'organization': organization,
        'page_obj': page_obj,
        'search_query': search_query,
        'branch_filter': branch_filter,
        'department_filter': department_filter,
        'designation_filter': designation_filter,
        'role_filter': role_filter,
        'status_filter': status_filter,
        'branches': branches,
        'departments': departments,
        'designations': designations,
        'roles': roles,
        'status_choices': Employee.EMPLOYMENT_STATUS_CHOICES,
        'table_columns': table_columns,
        'user_preferences': user_preferences,
        'can_edit': request.user.is_organization_admin or request.user.is_super_admin or DynamicTableManager.can_user_access_table(request.user, organization, 'employee_list', 'edit'),
        'can_delete': request.user.is_organization_admin or request.user.is_super_admin or DynamicTableManager.can_user_access_table(request.user, organization, 'employee_list', 'delete'),
    }
    return render(request, 'hrm/employee_list.html', context)


@login_required
@organization_admin_required
def create_employee(request):
    """Create new employee"""
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Create user account
                    user = User.objects.create_user(
                        username=form.cleaned_data['username'],
                        email=form.cleaned_data['email'],
                        password=form.cleaned_data['password'],
                        first_name=form.cleaned_data['first_name'],
                        last_name=form.cleaned_data['last_name'],
                        role='employee',
                        is_active=True
                    )
                    
                    # Create employee profile
                    employee = form.save(commit=False)
                    employee.user = user
                    employee.organization = request.organization
                    employee.created_by = request.user
                    employee.save()
                    
                    # Create organization membership
                    from organization.models import OrganizationMembership
                    OrganizationMembership.objects.create(
                        user=user,
                        organization=request.organization,
                        is_admin=False,
                        is_active=True
                    )
                    
                    messages.success(request, f'Employee "{employee.full_name}" created successfully!')
                    return redirect('hrm:employee_list')
            except Exception as e:
                messages.error(request, f'Error creating employee: {str(e)}')
    else:
        form = EmployeeForm()
        # Filter related objects for this organization
        form.fields['branch'].queryset = Branch.objects.filter(organization=request.organization)
        form.fields['department'].queryset = Department.objects.filter(organization=request.organization)
        form.fields['designation'].queryset = Designation.objects.filter(organization=request.organization)
        form.fields['employee_role'].queryset = EmployeeRole.objects.filter(organization=request.organization)
        form.fields['reporting_manager'].queryset = Employee.objects.filter(organization=request.organization)
    
    context = {
        'organization': request.organization,
        'form': form,
    }
    return render(request, 'hrm/employee_form.html', context)


@login_required
@organization_admin_required
def update_employee(request, employee_id):
    """Update existing employee"""
    try:
        employee = get_object_or_404(Employee, id=employee_id, organization=request.organization)
    except Employee.DoesNotExist:
        messages.error(request, 'Employee not found.')
        return redirect('hrm:employee_list')

    if request.method == 'POST':
        form = EmployeeUpdateForm(request.POST, request.FILES, instance=employee)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Update employee profile
                    employee = form.save(commit=False)
                    employee.updated_by = request.user
                    employee.save()
                    
                    # Update user account if needed
                    user = employee.user
                    if form.cleaned_data.get('first_name'):
                        user.first_name = form.cleaned_data['first_name']
                    if form.cleaned_data.get('last_name'):
                        user.last_name = form.cleaned_data['last_name']
                    if form.cleaned_data.get('email'):
                        user.email = form.cleaned_data['email']
                    user.save()
                    
                    messages.success(request, f'Employee "{employee.full_name}" updated successfully!')
                    return redirect('hrm:employee_list')
                    
            except Exception as e:
                messages.error(request, f'Error updating employee: {str(e)}')
    else:
        # Initialize form with current data
        initial_data = {
            'email': employee.user.email,
            'first_name': employee.user.first_name,
            'last_name': employee.user.last_name,
        }
        form = EmployeeUpdateForm(instance=employee, initial=initial_data)
        
        # Filter related objects for this organization
        form.fields['branch'].queryset = Branch.objects.filter(organization=request.organization)
        form.fields['department'].queryset = Department.objects.filter(organization=request.organization)
        form.fields['designation'].queryset = Designation.objects.filter(organization=request.organization)
        form.fields['employee_role'].queryset = EmployeeRole.objects.filter(organization=request.organization)
        form.fields['reporting_manager'].queryset = Employee.objects.filter(
            organization=request.organization
        ).exclude(id=employee_id)  # Exclude self from reporting manager choices

    context = {
        'organization': request.organization,
        'form': form,
        'employee': employee,
        'is_update': True,
    }
    return render(request, 'hrm/employee_form.html', context)



@login_required
@organization_admin_required
def employee_detail(request, employee_id):
    """View employee details"""
    employee = get_object_or_404(Employee, id=employee_id, organization=request.organization)
    
    # Get attendance records
    # attendance_records = Attendance.objects.filter(employee=employee).order_by('-date')[:10]
    
    # Get leave requests
    leave_requests = LeaveRequest.objects.filter(employee=employee).order_by('-created_at')[:10]
    
    context = {
        'organization': request.organization,
        'employee': employee,
        # 'attendance_records': attendance_records,
        'leave_requests': leave_requests,
    }
    return render(request, 'hrm/employee_detail.html', context)


@login_required
@organization_member_required
def employee_dashboard(request):
    """Enhanced Employee dashboard for logged-in employees"""
    try:
        employee = Employee.objects.get(user=request.user, organization=request.organization)
    except Employee.DoesNotExist:
        messages.error(request, 'Employee profile not found.')
        return redirect('authentication:login')
    
    # Get current date and time
    today = timezone.now().date()
    current_month = today.month
    current_year = today.year
    
    # Get recent attendance (last 7 days)
    recent_attendance = AttendanceRecord.objects.filter(
        employee=employee, 
        date__gte=today - timedelta(days=7)
    ).order_by('-date')[:10]
    
    # Get today's attendance
    today_attendance = AttendanceRecord.objects.filter(
        employee=employee, 
        date=today
    ).first()
    
    # Get recent leave requests
    recent_leaves = LeaveRequest.objects.filter(employee=employee).order_by('-created_at')[:5]
    
    # Get monthly attendance summary
    monthly_attendance = AttendanceRecord.objects.filter(
        employee=employee,
        date__year=current_year,
        date__month=current_month
    )
    
    # Calculate stats
    present_days = monthly_attendance.filter(status__in=['present', 'late']).count()
    absent_days = monthly_attendance.filter(status='absent').count()
    late_days = monthly_attendance.filter(status='late').count()
    total_working_days = present_days + absent_days
    
    # Get upcoming holidays
    upcoming_holidays = AttendanceHoliday.objects.filter(
        organization=request.organization,
        date__gte=today
    ).order_by('date')[:3]
    
    # Get current salary info
    current_salary = SalaryStructure.objects.filter(
        employee=employee,
        is_active=True
    ).order_by('-effective_date').first()
    
    # Get recent payslips
    recent_payslips = Payslip.objects.filter(
        employee=employee
    ).order_by('-payroll_period__start_date')[:3]
    
    # Calculate experience
    experience_years = 0
    if employee.hire_date:
        delta = today - employee.hire_date
        experience_years = delta.days // 365

    context = {
        'organization': request.organization,
        'employee': employee,
        'recent_attendance': recent_attendance,
        'recent_leaves': recent_leaves,
        'today_attendance': today_attendance,
        'upcoming_holidays': upcoming_holidays,
        'current_salary': current_salary,
        'recent_payslips': recent_payslips,
        'present_days': present_days,
        'absent_days': absent_days,
        'late_days': late_days,
        'total_working_days': total_working_days,
        'experience_years': experience_years,
        'today': today,
    }
    return render(request, 'hrm/employee_dashboard.html', context)


@login_required
@organization_member_required
def attendance_list(request):
    """List attendance records for the organization"""
    organization = request.organization

    # Base queryset
    attendances = AttendanceRecord.objects.filter(organization=organization).select_related(
        'employee', 'employee__branch', 'employee__department', 'employee__designation'
    ).order_by('-date')

    # --- Filters ---
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    branch_id = request.GET.get('branch')
    department_id = request.GET.get('department')
    designation_id = request.GET.get('designation')
    employee_id = request.GET.get('employee')
    search_query = request.GET.get('search', '').strip()

    # If user is an employee → restrict to their own records
    if request.user.is_employee:
        try:
            employee = Employee.objects.get(user=request.user, organization=organization)
            attendances = attendances.filter(employee=employee)
        except Employee.DoesNotExist:
            messages.error(request, 'Employee profile not found.')
            return redirect('authentication:login')

    # --- Date range filter ---
    if start_date and end_date:
        attendances = attendances.filter(date__range=[start_date, end_date])
    elif start_date:
        attendances = attendances.filter(date__gte=start_date)
    elif end_date:
        attendances = attendances.filter(date__lte=end_date)

    # --- Branch filter ---
    if branch_id:
        attendances = attendances.filter(employee__branch_id=branch_id)

    # --- Department filter ---
    if department_id:
        attendances = attendances.filter(employee__department_id=department_id)

    # --- Designation filter ---
    if designation_id:
        attendances = attendances.filter(employee__designation_id=designation_id)

    # --- Employee filter ---
    if employee_id:
        attendances = attendances.filter(employee_id=employee_id)

    # --- Search filter (by name, ID, or email) ---
    if search_query:
        attendances = attendances.filter(
            Q(employee__first_name__icontains=search_query) |
            Q(employee__employee_id__icontains=search_query) |
            Q(employee__user__email__icontains=search_query)
        )

    # --- Pagination ---
    paginator = Paginator(attendances, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'organization': organization,
        'page_obj': page_obj,

        # For dropdowns
        'branches': Branch.objects.filter(organization=organization),
        'departments': Department.objects.filter(organization=organization),
        'designations': Designation.objects.filter(organization=organization),
        'employees': Employee.objects.filter(organization=organization),

        # For keeping selected filters active
        'branch_filter': branch_id,
        'department_filter': department_id,
        'designation_filter': designation_id,
        'employee_filter': employee_id,
        'search_query': search_query,
        'start_date': start_date,
        'end_date': end_date,
    }

    return render(request, 'hrm/attendance_list.html', context)


@login_required
@organization_member_required
def leave_list(request):
    """List leave requests for the organization"""
    organization = request.organization
    
    # If user is employee, show only their leave requests
    if request.user.is_employee:
        try:
            employee = Employee.objects.get(user=request.user, organization=organization)
            leave_requests = LeaveRequest.objects.filter(employee=employee).order_by('-created_at')
        except Employee.DoesNotExist:
            messages.error(request, 'Employee profile not found.')
            return redirect('authentication:login')
    else:
        # Admin can see all leave requests
        leave_requests = LeaveRequest.objects.filter(organization=organization).order_by('-created_at')
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        leave_requests = leave_requests.filter(status=status_filter)
    
    paginator = Paginator(leave_requests, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'organization': organization,
        'page_obj': page_obj,
        'status_filter': status_filter,
        'status_choices': LeaveRequest.STATUS_CHOICES,
    }
    return render(request, 'hrm/leave_list.html', context)



@login_required
@organization_member_required
def leave_create(request):
    """Create a new leave request"""
    try:
        employee = Employee.objects.get(user=request.user, organization=request.organization)
    except Employee.DoesNotExist:
        messages.error(request, 'Employee profile not found.')
        return redirect('authentication:login')
    
    if request.method == 'POST':
        form_data = request.POST.copy()
        
        # Calculate days requested
        start_date = form_data.get('start_date')
        end_date = form_data.get('end_date')
        
        if start_date and end_date:
            start = date.fromisoformat(start_date)
            end = date.fromisoformat(end_date)
            days_requested = (end - start).days + 1
            form_data['days_requested'] = days_requested
        
        # Create leave request
        leave_request = LeaveRequest(
            organization=request.organization,
            employee=employee,
            leave_type=form_data.get('leave_type'),
            start_date=start_date,
            end_date=end_date,
            days_requested=days_requested,
            reason=form_data.get('reason'),
            status='pending',
            created_by=request.user
        )
        
        try:
            leave_request.save()
            messages.success(request, 'Leave request submitted successfully!')
            return redirect('hrm:leave_list')
        except Exception as e:
            messages.error(request, f'Error creating leave request: {str(e)}')
    
    # Get available leave balances (you can implement this based on your policy)
    leave_balances = {
        'sick': 10,  # Example values
        'vacation': 15,
        'personal': 5,
    }
    
    context = {
        'organization': request.organization,
        'employee': employee,
        'leave_type_choices': LeaveRequest.LEAVE_TYPE_CHOICES,
        'leave_balances': leave_balances,
        'min_date': date.today().isoformat(),
    }
    return render(request, 'hrm/leave_create.html', context)



@login_required
@organization_member_required
def leave_edit(request, pk):
    """Edit a leave request (only if pending)"""
    try:
        employee = Employee.objects.get(user=request.user, organization=request.organization)
    except Employee.DoesNotExist:
        messages.error(request, 'Employee profile not found.')
        return redirect('authentication:login')
    
    leave_request = get_object_or_404(
        LeaveRequest, 
        pk=pk, 
        employee=employee,
        organization=request.organization
    )
    
    # Check if editable
    if leave_request.status != 'pending':
        messages.error(request, 'Cannot edit leave request that has already been processed.')
        return redirect('hrm:leave_detail', pk=pk)
    
    if request.method == 'POST':
        form_data = request.POST.copy()
        
        # Calculate days requested
        start_date = form_data.get('start_date')
        end_date = form_data.get('end_date')
        
        if start_date and end_date:
            start = date.fromisoformat(start_date)
            end = date.fromisoformat(end_date)
            days_requested = (end - start).days + 1
            
            # Update leave request
            leave_request.leave_type = form_data.get('leave_type')
            leave_request.start_date = start_date
            leave_request.end_date = end_date
            leave_request.days_requested = days_requested
            leave_request.reason = form_data.get('reason')
            
            try:
                leave_request.save()
                messages.success(request, 'Leave request updated successfully!')
                return redirect('hrm:leave_detail', pk=pk)
            except Exception as e:
                messages.error(request, f'Error updating leave request: {str(e)}')
    
    context = {
        'organization': request.organization,
        'employee': employee,
        'leave_request': leave_request,
        'leave_type_choices': LeaveRequest.LEAVE_TYPE_CHOICES,
        'min_date': date.today().isoformat(),
    }
    return render(request, 'hrm/leave_edit.html', context)



@login_required
@organization_member_required
def leave_detail(request, pk):
    """View leave request details"""
    try:
        employee = Employee.objects.get(user=request.user, organization=request.organization)
    except Employee.DoesNotExist:
        messages.error(request, 'Employee profile not found.')
        return redirect('authentication:login')
    
    leave_request = get_object_or_404(
        LeaveRequest, 
        pk=pk, 
        employee=employee,
        organization=request.organization
    )
    
    # Check if editable (only pending requests can be edited)
    is_editable = leave_request.status == 'pending'
    is_deletable = leave_request.status == 'pending'
    
    context = {
        'organization': request.organization,
        'employee': employee,
        'leave_request': leave_request,
        'is_editable': is_editable,
        'is_deletable': is_deletable,
    }
    return render(request, 'hrm/leave_detail.html', context)


@login_required
@organization_member_required
def leave_approve(request, pk):
    leave = get_object_or_404(LeaveRequest, pk=pk, organization=request.organization)
    if not request.user.is_employee:
        leave.status = 'approved'
        leave.approved_by = request.user
        leave.approved_at = timezone.now()
        leave.save()
        messages.success(request, f"Leave request for {leave.employee.full_name} approved.")
    return redirect('hrm:leave_list')


@login_required
@organization_member_required
def leave_reject(request, pk):
    leave = get_object_or_404(LeaveRequest, pk=pk, organization=request.organization)
    if not request.user.is_employee:
        leave.status = 'rejected'
        leave.rejection_reason = request.GET.get('reason', 'Rejected by admin.')
        leave.approved_by = request.user
        leave.approved_at = timezone.now()
        leave.save()
        messages.warning(request, f"Leave request for {leave.employee.full_name} rejected.")
    return redirect('hrm:leave_list')



# Shift Management Views
@login_required
@organization_admin_required
def shift_list(request):
    """List shifts for the organization"""
    organization = request.organization
    
    shifts = Shift.objects.filter(organization=organization).order_by('start_time')
    
    paginator = Paginator(shifts, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'organization': organization,
        'page_obj': page_obj,
    }
    return render(request, 'hrm/shift_list.html', context)


@login_required
@organization_admin_required
def create_shift(request):
    """Create new shift"""
    if request.method == 'POST':
        form = ShiftForm(request.POST, organization=request.organization)
        if form.is_valid():
            shift = form.save(commit=False)
            shift.organization = request.organization
            shift.created_by = request.user
            shift.save()
            messages.success(request, f'Shift "{shift.name}" created successfully!')
            return redirect('hrm:shift_list')
    else:
        form = ShiftForm(organization=request.organization)
    
    context = {
        'organization': request.organization,
        'form': form,
    }
    return render(request, 'hrm/shift_form.html', context)


@login_required
@organization_admin_required
def update_shift(request, shift_id):
    """Update existing shift"""
    try:
        shift = get_object_or_404(Shift, id=shift_id, organization=request.organization)
    except Shift.DoesNotExist:
        messages.error(request, 'Shift not found.')
        return redirect('hrm:shift_list')

    if request.method == 'POST':
        form = ShiftForm(request.POST, instance=shift, organization=request.organization)
        if form.is_valid():
            shift = form.save(commit=False)
            shift.updated_by = request.user
            shift.save()
            messages.success(request, f'Shift "{shift.name}" updated successfully!')
            return redirect('hrm:shift_list')
    else:
        form = ShiftForm(instance=shift, organization=request.organization)

    context = {
        'organization': request.organization,
        'form': form,
        'shift': shift,
        'is_update': True,
    }
    return render(request, 'hrm/shift_form.html', context)


# Timetable Management Views
@login_required
@organization_admin_required
def timetable_list(request):
    """List timetables for the organization (supports multi-employee timetables)"""
    organization = request.organization

    timetables = Timetable.objects.filter(organization=organization).prefetch_related('employees', 'shift')

    # --- Filtering ---
    employee_filter = request.GET.get('employee')
    shift_filter = request.GET.get('shift')
    status_filter = request.GET.get('status')
    search_query = request.GET.get('search')

    if employee_filter:
        timetables = timetables.filter(employees__id=employee_filter)

    if shift_filter:
        timetables = timetables.filter(shift_id=shift_filter)

    if status_filter == 'active':
        timetables = timetables.filter(is_active=True)
    elif status_filter == 'inactive':
        timetables = timetables.filter(is_active=False)

    if search_query:
        timetables = timetables.filter(
            Q(employees__full_name__icontains=search_query) |
            Q(shift__name__icontains=search_query)
        ).distinct()

    timetables = timetables.order_by('start_date')

    # Pagination
    paginator = Paginator(timetables.distinct(), 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Dropdowns
    employees = Employee.objects.filter(organization=organization, is_active=True)
    shifts = Shift.objects.filter(organization=organization, is_active=True)

    context = {
        'organization': organization,
        'page_obj': page_obj,
        'employees': employees,
        'shifts': shifts,
        'employee_filter': employee_filter,
        'shift_filter': shift_filter,
        'status_filter': status_filter,
        'search_query': search_query,
    }
    return render(request, 'hrm/timetable_list.html', context)



# views.py
@login_required
@organization_admin_required
def create_timetable(request):
    """Create new timetable"""
    organization = request.organization

    # Handle AJAX request to filter employees
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        designation_id = request.GET.get('designation_id')
        employees = Employee.objects.filter(
            organization=organization, is_active=True, designation_id=designation_id
        ).values('id', 'full_name')
        return JsonResponse(list(employees), safe=False)

    if request.method == 'POST':
        form = TimetableForm(request.POST, organization=organization)
        if form.is_valid():
            timetable = form.save(commit=False)
            timetable.organization = organization
            timetable.created_by = request.user
            timetable.save()
            form.save_m2m()  # save employees many-to-many
            messages.success(request, "Timetable created successfully!")
            return redirect('hrm:timetable_list')
    else:
        form = TimetableForm(organization=organization)

    return render(request, 'hrm/timetable_form.html', {
        'organization': organization,
        'form': form,
    })


@login_required
@organization_admin_required
def update_timetable(request, timetable_id):
    """Update timetable"""
    organization = request.organization
    timetable = get_object_or_404(Timetable, id=timetable_id, organization=organization)

    if request.method == 'POST':
        form = TimetableForm(request.POST, instance=timetable, organization=organization)
        if form.is_valid():
            timetable = form.save(commit=False)
            timetable.updated_by = request.user
            timetable.save()
            form.save_m2m()
            messages.success(request, "Timetable updated successfully!")
            return redirect('hrm:timetable_list')
    else:
        form = TimetableForm(instance=timetable, organization=organization)

    return render(request, 'hrm/timetable_form.html', {
        'organization': organization,
        'form': form,
        'timetable': timetable,
        'is_update': True,
    })



# Attendance Device Management Views
@login_required
@organization_admin_required
def attendance_device_list(request):
    """List attendance devices for the organization"""
    organization = request.organization
    
    devices = AttendanceDevice.objects.filter(organization=organization).order_by('name')
    
    paginator = Paginator(devices, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'organization': organization,
        'page_obj': page_obj,
    }
    return render(request, 'hrm/attendance_device_list.html', context)


@login_required
@organization_admin_required
def create_attendance_device(request):
    """Create new attendance device"""
    if request.method == 'POST':
        form = AttendanceDeviceForm(request.POST, organization=request.organization)
        if form.is_valid():
            device = form.save(commit=False)
            device.organization = request.organization
            device.created_by = request.user
            device.save()
            messages.success(request, f'Attendance device "{device.name}" created successfully!')
            return redirect('hrm:attendance_device_list')
    else:
        form = AttendanceDeviceForm(organization=request.organization)
    
    context = {
        'organization': request.organization,
        'form': form,
    }
    return render(request, 'hrm/attendance_device_form.html', context)


@login_required
@organization_admin_required
def update_attendance_device(request, device_id):
    """Update existing attendance device"""
    try:
        device = get_object_or_404(AttendanceDevice, id=device_id, organization=request.organization)
    except AttendanceDevice.DoesNotExist:
        messages.error(request, 'Attendance device not found.')
        return redirect('hrm:attendance_device_list')

    if request.method == 'POST':
        form = AttendanceDeviceForm(request.POST, instance=device, organization=request.organization)
        if form.is_valid():
            device = form.save(commit=False)
            device.updated_by = request.user
            device.save()
            messages.success(request, f'Attendance device "{device.name}" updated successfully!')
            return redirect('hrm:attendance_device_list')
    else:
        form = AttendanceDeviceForm(instance=device, organization=request.organization)

    context = {
        'organization': request.organization,
        'form': form,
        'device': device,
        'is_update': True,
    }
    return render(request, 'hrm/attendance_device_form.html', context)


@login_required
@organization_admin_required
def test_device_connection_view(request, device_id):
    """Test connection to attendance device"""
    try:
        device = get_object_or_404(AttendanceDevice, id=device_id, organization=request.organization)
        
        # Test connection
        result = test_device_connection(device.ip_address, device.port)
        
        if result['connected']:
            # Update device info
            device_info = result['device_info']
            if device_info:
                device.serial_number = device_info.get('serial_number', '')
                device.model = device_info.get('model', '')
                device.firmware_version = device_info.get('firmware_version', '')
            device.is_online = True
            device.last_sync = timezone.now()
            device.save()
            
            messages.success(request, f'Successfully connected to device "{device.name}"')
        else:
            device.is_online = False
            device.save()
            error_msg = result.get("error", "Unknown error")
            messages.error(request, f'Failed to connect to device "{device.name}": {error_msg}')
            
    except Exception as e:
        messages.error(request, f'Error testing device connection: {str(e)}')
    
    return redirect('hrm:attendance_device_list')


@login_required
@organization_admin_required
def diagnose_device_view(request, device_id):
    """Diagnose device connection issues"""
    try:
        device = get_object_or_404(AttendanceDevice, id=device_id, organization=request.organization)
        
        # Run comprehensive diagnostics
        diagnostics = diagnose_device_issues(device.ip_address, device.port)
        
        context = {
            'organization': request.organization,
            'device': device,
            'diagnostics': diagnostics,
        }
        return render(request, 'hrm/device_diagnostics.html', context)
        
    except Exception as e:
        messages.error(request, f'Error running diagnostics: {str(e)}')
        return redirect('hrm:attendance_device_list')


@login_required
@organization_admin_required
def sync_device_data(request, device_id):
    """Sync data with attendance device"""
    try:
        device = get_object_or_404(AttendanceDevice, id=device_id, organization=request.organization)
        
        sync_manager = AttendanceSyncManager(device)
        
        # Sync device info
        if sync_manager.sync_device_info():
            messages.info(request, '✓ Device info updated')
        
        # Sync users (auto-create enabled by default)
        user_stats = sync_manager.sync_users(auto_create=True)
        
        # Build user sync message
        msg_parts = []
        if user_stats['synced'] > 0:
            msg_parts.append(f"{user_stats['synced']} matched")
        if user_stats['created'] > 0:
            msg_parts.append(f"{user_stats['created']} created")
        if user_stats['failed'] > 0:
            msg_parts.append(f"{user_stats['failed']} failed")
        
        if msg_parts:
            messages.success(request, f"✓ Users: {', '.join(msg_parts)}")
        
        # Sync attendance (last 30 days)
        from datetime import date, timedelta
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        attendance_synced = sync_manager.sync_attendance(start_date, end_date)
        
        messages.success(request, f'✓ Attendance: {attendance_synced} records synced')
        
    except Exception as e:
        messages.error(request, f'✗ Error syncing device: {str(e)}')
        logger.exception("Device sync error")
    
    return redirect('hrm:attendance_device_list')


# Attendance Records Views
@login_required
@organization_member_required
def attendance_record_list(request):
    """List attendance records for the organization"""
    organization = request.organization
    
    # Get filter parameters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    employee_filter = request.GET.get('employee')
    department_filter = request.GET.get('department')
    status_filter = request.GET.get('status')
    
    # If user is employee, show only their records
    if request.user.is_employee:
        try:
            employee = Employee.objects.get(user=request.user, organization=organization)
            records = AttendanceRecord.objects.filter(employee=employee).order_by('-date')
        except Employee.DoesNotExist:
            messages.error(request, 'Employee profile not found.')
            return redirect('authentication:login')
    else:
        # Admin can see all records
        records = AttendanceRecord.objects.filter(organization=organization).order_by('-date')
    
    # Apply filters
    if start_date:
        records = records.filter(date__gte=start_date)
    if end_date:
        records = records.filter(date__lte=end_date)
    if employee_filter:
        records = records.filter(employee_id=employee_filter)
    if department_filter:
        records = records.filter(employee__department_id=department_filter)
    if status_filter:
        records = records.filter(status=status_filter)
    
    paginator = Paginator(records, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    employees = Employee.objects.filter(organization=organization, is_active=True)
    departments = Department.objects.filter(organization=organization, is_active=True)
    
    context = {
        'organization': organization,
        'page_obj': page_obj,
        'start_date': start_date,
        'end_date': end_date,
        'employee_filter': employee_filter,
        'department_filter': department_filter,
        'status_filter': status_filter,
        'employees': employees,
        'departments': departments,
        'status_choices': AttendanceRecord.STATUS_CHOICES,
    }
    return render(request, 'hrm/attendance_record_list.html', context)


@login_required
def calculate_attendance_records(request):
    """Auto-calculate attendance for all employees from timetable & shift"""
    timetables = Timetable.objects.filter(is_active=True)
    print("timetables:", timetables)

    if not timetables.exists():
        messages.warning(request, "No active timetables found.")
        return redirect(request.META.get('HTTP_REFERER', '/'))

    count_created, count_updated = 0, 0

    for timetable in timetables:
        shift = timetable.shift
        employees = timetable.employees.all()

        start_date = timetable.start_date
        print("start_date:", start_date)
        end_date = timetable.end_date or date.today()  # if no end date, calculate up to today
        print("end_date:", end_date)

        current_date = start_date
        while current_date <= end_date:
            weekday = current_date.strftime("%A").lower()
            if getattr(timetable, weekday):  # Only process working days
                for emp in employees:
                    record, created = AttendanceRecord.objects.get_or_create(
                        organization=timetable.organization,
                        employee=emp,
                        date=current_date
                    )
                    record.calculate_hours()
                    if created:
                        count_created += 1
                    else:
                        count_updated += 1
            current_date += timedelta(days=1)

    messages.success(
        request,
        f"✅ Attendance calculated successfully — Created: {count_created}, Updated: {count_updated}"
    )
    return redirect(request.META.get('HTTP_REFERER', '/'))


# Payhead Management Views
@login_required
@organization_admin_required
def payhead_list(request):
    """List payheads for the organization"""
    organization = request.organization
    
    payheads = Payhead.objects.filter(organization=organization).order_by('display_order', 'name')
    
    paginator = Paginator(payheads, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'organization': organization,
        'page_obj': page_obj,
    }
    return render(request, 'hrm/payhead_list.html', context)


@login_required
@organization_admin_required
def create_payhead(request):
    """Create new payhead"""
    if request.method == 'POST':
        form = PayheadForm(request.POST, organization=request.organization)
        if form.is_valid():
            payhead = form.save(commit=False)
            payhead.organization = request.organization
            payhead.created_by = request.user
            payhead.save()
            messages.success(request, f'Payhead "{payhead.name}" created successfully!')
            return redirect('hrm:payhead_list')
    else:
        form = PayheadForm(organization=request.organization)
    
    context = {
        'organization': request.organization,
        'form': form,
    }
    return render(request, 'hrm/payhead_form.html', context)


@login_required
@organization_admin_required
def update_payhead(request, payhead_id):
    """Update existing payhead"""
    try:
        payhead = get_object_or_404(Payhead, id=payhead_id, organization=request.organization)
    except Payhead.DoesNotExist:
        messages.error(request, 'Payhead not found.')
        return redirect('hrm:payhead_list')

    if request.method == 'POST':
        form = PayheadForm(request.POST, instance=payhead, organization=request.organization)
        if form.is_valid():
            payhead = form.save(commit=False)
            payhead.updated_by = request.user
            payhead.save()
            messages.success(request, f'Payhead "{payhead.name}" updated successfully!')
            return redirect('hrm:payhead_list')
    else:
        form = PayheadForm(instance=payhead, organization=request.organization)

    context = {
        'organization': request.organization,
        'form': form,
        'payhead': payhead,
        'is_update': True,
    }
    return render(request, 'hrm/payhead_form.html', context)

@login_required
def payhead_delete(request, pk):
    if request.method == "POST":
        payhead = get_object_or_404(Payhead, pk=pk, organization=request.organization)
        payhead.delete()
        return JsonResponse({"success": True, "message": f"Payhead '{payhead.name}' deleted successfully."})
    return JsonResponse({"success": False, "message": "Invalid request."}, status=400)

# Holiday Management Views
@login_required
@organization_admin_required
def holiday_list(request):
    """List holidays for the organization"""
    organization = request.organization
    
    holidays = AttendanceHoliday.objects.filter(organization=organization).order_by('date')
    
    paginator = Paginator(holidays, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'organization': organization,
        'page_obj': page_obj,
    }
    return render(request, 'hrm/holiday_list.html', context)


@login_required
@organization_admin_required
def create_holiday(request):
    """Create new holiday"""
    if request.method == 'POST':
        form = AttendanceHolidayForm(request.POST, organization=request.organization)
        if form.is_valid():
            holiday = form.save(commit=False)
            holiday.organization = request.organization
            holiday.created_by = request.user
            holiday.save()
            messages.success(request, f'Holiday "{holiday.name}" created successfully!')
            return redirect('hrm:holiday_list')
    else:
        form = AttendanceHolidayForm(organization=request.organization)
    
    context = {
        'organization': request.organization,
        'form': form,
    }
    return render(request, 'hrm/holiday_form.html', context)


@login_required
@organization_admin_required
def update_holiday(request, holiday_id):
    """Update existing holiday"""
    try:
        holiday = get_object_or_404(AttendanceHoliday, id=holiday_id, organization=request.organization)
    except AttendanceHoliday.DoesNotExist:
        messages.error(request, 'Holiday not found.')
        return redirect('hrm:holiday_list')

    if request.method == 'POST':
        form = AttendanceHolidayForm(request.POST, instance=holiday, organization=request.organization)
        if form.is_valid():
            holiday = form.save(commit=False)
            holiday.updated_by = request.user
            holiday.save()
            messages.success(request, f'Holiday "{holiday.name}" updated successfully!')
            return redirect('hrm:holiday_list')
    else:
        form = AttendanceHolidayForm(instance=holiday, organization=request.organization)

    context = {
        'organization': request.organization,
        'form': form,
        'holiday': holiday,
        'is_update': True,
    }
    return render(request, 'hrm/holiday_form.html', context)


@login_required
@organization_admin_required
def delete_holiday(request, holiday_id):
    """Delete a holiday"""
    if request.method == "POST":
        holiday = get_object_or_404(AttendanceHoliday, id=holiday_id, organization=request.organization)
        name = holiday.name
        holiday.delete()
        return JsonResponse({"success": True, "message": f"Holiday '{name}' deleted successfully."})
    return JsonResponse({"success": False, "message": "Invalid request."}, status=400)





# Payhead Management Views
@login_required
@organization_admin_required
def employee_payhead_list(request):
    """List payheads for the organization"""
    organization = request.organization
    
    employee_payheads = EmployeePayhead.objects.filter(organization=organization).order_by('amount')
    
    paginator = Paginator(employee_payheads, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'organization': organization,
        'page_obj': page_obj,
    }
    return render(request, 'hrm/employee_payhead_list.html', context)


@login_required
@organization_admin_required
def employee_create_payhead(request):
    """Create new payhead"""
    organization=request.organization
    print("DEBUG ORGANIZATION:", request.organization)

    if not organization:
        messages.error(request, "You are not associated with any organization.")
        return redirect('organization_dashboard')

    if request.method == 'POST':
        form = EmployeePayheadForm(request.POST, organization=organization)
        if form.is_valid():
            employee_payhead = form.save(commit=False)
            employee_payhead.organization = organization
            employee_payhead.created_by = request.user
            employee_payhead.save()
            messages.success(request, f'Payhead for "{employee_payhead.employee}" created successfully!')
            return redirect('hrm:employee_payhead_list')
    else:
        form = EmployeePayheadForm(organization=organization)
    
    context = {
        'organization': organization,
        'form': form,
        'is_update': False,
    }
    return render(request, 'hrm/employee_payhead_form.html', context)



@login_required
@organization_admin_required
def employee_update_payhead(request, employee_payhead_id):
    """Update existing payhead"""
    try:
        emoloyee_payhead = get_object_or_404(EmployeePayhead, id=employee_payhead_id, organization=request.organization)
    except EmployeePayhead.DoesNotExist:
        messages.error(request, 'EmployeePayhead not found.')
        return redirect('hrm:emoloyee_payhead_list')

    if request.method == 'POST':
        form = EmployeePayheadForm(request.POST, instance=emoloyee_payhead, organization=request.organization)
        if form.is_valid():
            emoloyee_payhead = form.save(commit=False)
            emoloyee_payhead.updated_by = request.user
            emoloyee_payhead.save()
            messages.success(request, f'Payhead "{emoloyee_payhead}" updated successfully!')
            return redirect('hrm:employee_payhead_list')
    else:
        form = EmployeePayheadForm(instance=emoloyee_payhead, organization=request.organization)

    context = {
        'organization': request.organization,
        'form': form,
        'emoloyee_payhead': emoloyee_payhead,
        'is_update': True,
    }
    return render(request, 'hrm/employee_payhead_form.html', context)










def manual_attendance_entry(request):
    """Manual attendance entry view"""
    selected_date = request.GET.get('date') or timezone.now().date().isoformat()
    
    try:
        selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        selected_date = timezone.now().date()
    
    # Get all active employees for the organization
    employees = Employee.objects.filter(
        organization=request.organization,
        is_active=True,
        employment_status='active'
    ).select_related('department', 'designation').order_by('first_name', 'last_name')
    
    # Get existing attendance records for the selected date
    existing_records = AttendanceRecord.objects.filter(
        organization=request.organization,
        date=selected_date
    ).select_related('employee')
    
    # Create a dictionary for easy lookup
    attendance_dict = {record.employee_id: record for record in existing_records}
    
    # Prepare employee data with attendance info
    employee_data = []
    for employee in employees:
        record = attendance_dict.get(employee.id)
        employee_data.append({
            'employee': employee,
            'record': record,
            'has_record': record is not None
        })
    
    context = {
        'selected_date': selected_date,
        'employee_data': employee_data,
        'today': timezone.now().date(),
    }
    
    return render(request, 'hrm/manual_attendance.html', context)

@require_http_methods(["POST"])
@transaction.atomic
def save_manual_attendance(request):
    """Save manual attendance records"""
    try:
        data = request.POST
        selected_date = data.get('selected_date')
        employee_ids = data.getlist('employee_ids[]')
        
        if not selected_date or not employee_ids:
            return JsonResponse({
                'success': False,
                'message': 'Missing required data'
            })
        
        selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
        organization = request.organization
        
        saved_count = 0
        updated_count = 0
        
        for employee_id in employee_ids:
            employee = get_object_or_404(Employee, id=employee_id, organization=organization)
            
            # Get form data for this employee
            check_in = data.get(f'check_in_{employee_id}')
            check_out = data.get(f'check_out_{employee_id}')
            is_present = data.get(f'is_present_{employee_id}') == 'on'
            is_absent = data.get(f'is_absent_{employee_id}') == 'on'
            is_late = data.get(f'is_late_{employee_id}') == 'on'
            on_leave = data.get(f'on_leave_{employee_id}') == 'on'
            
            # Determine status based on checkboxes
            if on_leave:
                status = 'on_leave'
            elif is_absent:
                status = 'absent'
            elif is_late:
                status = 'late'
            elif is_present:
                status = 'present'
            else:
                # Default to present if check-in/out times exist
                status = 'present' if (check_in or check_out) else 'absent'
            
            # Get or create attendance record
            record, created = AttendanceRecord.objects.get_or_create(
                organization=organization,
                employee=employee,
                date=selected_date,
                defaults={
                    'check_in_time': check_in if check_in else None,
                    'check_out_time': check_out if check_out else None,
                    'status': status,
                    'is_late': is_late,
                    'created_by': request.user,
                }
            )
            
            if not created:
                # Update existing record
                record.check_in_time = check_in if check_in else None
                record.check_out_time = check_out if check_out else None
                record.status = status
                record.is_late = is_late
                record.updated_at = timezone.now()
                updated_count += 1
            else:
                saved_count += 1
            
            # Calculate hours if both check-in and check-out are provided
            if check_in and check_out:
                record.calculate_hours()
            else:
                record.save()
        
        message = f"Attendance saved successfully! {saved_count} new records, {updated_count} updated records."
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': message
            })
        else:
            messages.success(request, message)
            return redirect('hrm:manual_attendance_entry')
            
    except Exception as e:
        error_message = f"Error saving attendance: {str(e)}"
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': error_message
            })
        else:
            messages.error(request, error_message)
            return redirect('hrm:manual_attendance_entry')

def get_employee_attendance_data(request):
    """Get attendance data for a specific date - AJAX endpoint"""
    selected_date = request.GET.get('date')
    
    if not selected_date:
        return JsonResponse({'error': 'Date is required'}, status=400)
    
    try:
        selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Invalid date format'}, status=400)
    
    employees = Employee.objects.filter(
        organization=request.organization,
        is_active=True,
        employment_status='active'
    ).select_related('department', 'designation').order_by('first_name', 'last_name')
    
    existing_records = AttendanceRecord.objects.filter(
        organization=request.organization,
        date=selected_date
    ).select_related('employee')
    
    attendance_dict = {record.employee_id: record for record in existing_records}
    
    data = []
    for employee in employees:
        record = attendance_dict.get(employee.id)
        
        data.append({
            'id': employee.id,
            'name': employee.full_name,
            'employee_id': employee.employee_id,
            'department': employee.department.name if employee.department else '-',
            'designation': employee.designation.name if employee.designation else '-',
            'check_in': record.check_in_time.strftime('%H:%M') if record and record.check_in_time else '',
            'check_out': record.check_out_time.strftime('%H:%M') if record and record.check_out_time else '',
            'status': record.status if record else '',
            'is_late': record.is_late if record else False,
            'has_record': record is not None
        })
    
    return JsonResponse({'employees': data})




# --- DELETE MULTIPLE ---
@login_required
@organization_member_required
def delete_multiple_branches(request):
    return handle_bulk_delete(request, Branch, 'branch')

@login_required
@organization_member_required
def delete_multiple_departments(request):
    return handle_bulk_delete(request, Department, 'department')

@login_required
@organization_member_required
def delete_multiple_designations(request):
    return handle_bulk_delete(request, Designation, 'designation')

@login_required
@organization_member_required
def delete_multiple_roles(request):
    return handle_bulk_delete(request, EmployeeRole, 'employee role')

@login_required
@organization_member_required
def delete_multiple_employees(request):
    return handle_bulk_delete(request, Employee, 'employee')

@login_required
@organization_member_required
def delete_multiple_leave_requests(request):
    return handle_bulk_delete(request, LeaveRequest, 'leave request')

@login_required
@organization_member_required
def delete_multiple_attendance_records(request):
    return handle_bulk_delete(request, AttendanceRecord, 'attendance record')

@login_required
@organization_member_required
def delete_multiple_holidays(request):
    return handle_bulk_delete(request, AttendanceHoliday, 'holiday')

@login_required
@organization_member_required
def delete_multiple_payheads(request):
    return handle_bulk_delete(request, Payhead, 'payhead')

@login_required
@organization_member_required
def delete_multiple_timetables(request):
    return handle_bulk_delete(request, Timetable, 'timetable')

@login_required
@organization_member_required
def delete_multiple_employee_payheads(request):
    return handle_bulk_delete(request, EmployeePayhead, 'employee payhead')

@login_required
@organization_member_required
def delete_multiple_shifts(request):
    return handle_bulk_delete(request, Shift, 'shift')




# --- Trash ---

@login_required
@organization_member_required
def branch_trash(request):
    return trash_list_view(request, Branch, 'hrm/branch_trash.html', 'branches')

@login_required
@organization_member_required
def department_trash(request):
    return trash_list_view(request, Department, 'hrm/department_trash.html', 'departments')

@login_required
@organization_member_required
def designation_trash(request):
    return trash_list_view(request, Designation, 'hrm/designation_trash.html', 'designations')

@login_required
@organization_member_required
def employee_role_trash(request):
    return trash_list_view(request, EmployeeRole, 'hrm/role_trash.html', 'employee roles')

@login_required
@organization_member_required
def employee_trash(request):
    return trash_list_view(request, Employee, 'hrm/employee_trash.html', 'employees')

@login_required
@organization_member_required
def leave_request_trash(request):
    return trash_list_view(request, LeaveRequest, 'hrm/leave_request_trash.html', 'leave requests')

@login_required
@organization_member_required
def attendance_record_trash(request):
    return trash_list_view(request, AttendanceRecord, 'hrm/attendance_record_trash.html', 'attendance records')

@login_required
@organization_member_required
def holiday_trash(request):
    return trash_list_view(request, AttendanceHoliday, 'hrm/holiday_trash.html', 'holidays')

@login_required
@organization_member_required
def payhead_trash(request):
    return trash_list_view(request, Payhead, 'hrm/payhead_trash.html', 'payheads')

@login_required
@organization_member_required
def timetable_trash(request):
    return trash_list_view(request, Timetable, 'hrm/timetable_trash.html', 'timetables')

@login_required
@organization_member_required
def employee_payhead_trash(request):
    return trash_list_view(request, EmployeePayhead, 'hrm/employee_payhead_trash.html', 'employee payheads')

@login_required
@organization_member_required
def shift_trash(request):
    return trash_list_view(request, Shift, 'hrm/shift_trash.html', 'shifts')



# --- Restore ---
@login_required
@organization_member_required
def restore_branch(request):
    return restore_objects_view(request, Branch, 'branch')

@login_required
@organization_member_required
def restore_department(request):
    return restore_objects_view(request, Department, 'department')

@login_required
@organization_member_required
def restore_designation(request):
    return restore_objects_view(request, Designation, 'designation')

@login_required
@organization_member_required
def restore_employee_role(request):
    return restore_objects_view(request, EmployeeRole, 'employee role')

@login_required
@organization_member_required
def restore_employee(request):
    return restore_objects_view(request, Employee, 'employee')

@login_required
@organization_member_required
def restore_leave_request(request):
    return restore_objects_view(request, LeaveRequest, 'leave request')

@login_required
@organization_member_required
def restore_attendance_record(request):
    return restore_objects_view(request, AttendanceRecord, 'attendance record')

@login_required
@organization_member_required
def restore_holiday(request):
    return restore_objects_view(request, AttendanceHoliday, 'holiday')

@login_required
@organization_member_required
def restore_payhead(request):
    return restore_objects_view(request, Payhead, 'payhead')

@login_required
@organization_member_required
def restore_timetable(request):
    return restore_objects_view(request, Timetable, 'timetable')

@login_required
@organization_member_required
def restore_employee_payhead(request):
    return restore_objects_view(request, EmployeePayhead, 'employee payhead')

@login_required
@organization_member_required
def restore_shift(request):
    return restore_objects_view(request, Shift, 'shift')