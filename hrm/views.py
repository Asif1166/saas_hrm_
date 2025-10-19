from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from organization.decorators import organization_member_required, organization_admin_required
from organization.utils import DynamicTableManager
from .models import Branch, Department, Designation, EmployeeRole, Employee, AttendanceRecord, LeaveRequest, Shift, Timetable, AttendanceDevice, Payhead, EmployeePayhead, AttendanceHoliday
from .forms import EmployeeForm, BranchForm, DepartmentForm, DesignationForm, EmployeeRoleForm, EmployeeUpdateForm, ShiftForm, TimetableForm, AttendanceDeviceForm, PayheadForm, EmployeePayheadForm, AttendanceHolidayForm, AttendanceFilterForm
from .zkteco_utils import *
from datetime import date, datetime
from django.utils import timezone

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
    """Employee dashboard for logged-in employees"""
    try:
        employee = Employee.objects.get(user=request.user, organization=request.organization)
    except Employee.DoesNotExist:
        messages.error(request, 'Employee profile not found.')
        return redirect('authentication:login')
    
    # Get recent attendance
    # recent_attendance = Attendance.objects.filter(employee=employee).order_by('-date')[:10]
    
    # Get recent leave requests
    recent_leaves = LeaveRequest.objects.filter(employee=employee).order_by('-created_at')[:5]
    
    # Today's attendance
    # today_attendance = Attendance.objects.filter(employee=employee, date=date.today()).first()
    
    context = {
        'organization': request.organization,
        'employee': employee,
        # 'recent_attendance': recent_attendance,
        'recent_leaves': recent_leaves,
        # 'today_attendance': today_attendance,
    }
    return render(request, 'hrm/employee_dashboard.html', context)


@login_required
@organization_member_required
def attendance_list(request):
    """List attendance for the organization"""
    organization = request.organization
    
    # If user is employee, show only their attendance
    if request.user.is_employee:
        try:
            employee = Employee.objects.get(user=request.user, organization=organization)
            # attendances = Attendance.objects.filter(employee=employee).order_by('-date')
        except Employee.DoesNotExist:
            messages.error(request, 'Employee profile not found.')
            return redirect('authentication:login')
    else:
        # Admin can see all attendance
        # attendances = Attendance.objects.filter(organization=organization).order_by('-date')
        pass
    
    # Filter by date range
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if start_date:
        attendances = attendances.filter(date__gte=start_date)
    if end_date:
        attendances = attendances.filter(date__lte=end_date)
    
    paginator = Paginator(attendances, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'organization': organization,
        'page_obj': page_obj,
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
    """List timetables for the organization"""
    organization = request.organization
    
    timetables = Timetable.objects.filter(organization=organization).order_by('employee', 'start_date')
    
    paginator = Paginator(timetables, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'organization': organization,
        'page_obj': page_obj,
    }
    return render(request, 'hrm/timetable_list.html', context)


@login_required
@organization_admin_required
def create_timetable(request):
    """Create new timetable"""
    if request.method == 'POST':
        form = TimetableForm(request.POST, organization=request.organization)
        if form.is_valid():
            timetable = form.save(commit=False)
            timetable.organization = request.organization
            timetable.created_by = request.user
            timetable.save()
            messages.success(request, f'Timetable for "{timetable.employee.full_name}" created successfully!')
            return redirect('hrm:timetable_list')
    else:
        form = TimetableForm(organization=request.organization)
    
    context = {
        'organization': request.organization,
        'form': form,
    }
    return render(request, 'hrm/timetable_form.html', context)


@login_required
@organization_admin_required
def update_timetable(request, timetable_id):
    """Update existing timetable"""
    try:
        timetable = get_object_or_404(Timetable, id=timetable_id, organization=request.organization)
    except Timetable.DoesNotExist:
        messages.error(request, 'Timetable not found.')
        return redirect('hrm:timetable_list')

    if request.method == 'POST':
        form = TimetableForm(request.POST, instance=timetable, organization=request.organization)
        if form.is_valid():
            timetable = form.save(commit=False)
            timetable.updated_by = request.user
            timetable.save()
            messages.success(request, f'Timetable for "{timetable.employee.full_name}" updated successfully!')
            return redirect('hrm:timetable_list')
    else:
        form = TimetableForm(instance=timetable, organization=request.organization)

    context = {
        'organization': request.organization,
        'form': form,
        'timetable': timetable,
        'is_update': True,
    }
    return render(request, 'hrm/timetable_form.html', context)


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
            messages.success(request, f'✓ Device info updated')
        
        # Sync users
        users_synced = sync_manager.sync_users()
        
        # Sync attendance (last 30 days)
        from datetime import date, timedelta
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        attendance_synced = sync_manager.sync_attendance(start_date, end_date)
        
        messages.success(request, f'✓ Sync completed: {users_synced} users, {attendance_synced} attendance records')
        
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