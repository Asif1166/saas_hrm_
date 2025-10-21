from django.contrib import admin
from .models import *


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'organization', 'manager', 'is_active')
    list_filter = ('organization', 'is_active')
    search_fields = ('name', 'code', 'organization__name')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'organization', 'branch', 'manager', 'is_active')
    list_filter = ('organization', 'branch', 'is_active')
    search_fields = ('name', 'code', 'organization__name')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Designation)
class DesignationAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'organization', 'department', 'level', 'is_active')
    list_filter = ('organization', 'department', 'level', 'is_active')
    search_fields = ('name', 'code', 'organization__name')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(EmployeeRole)
class EmployeeRoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'organization', 'is_active')
    list_filter = ('organization', 'is_active')
    search_fields = ('name', 'code', 'organization__name')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'full_name', 'organization', 'department', 'designation', 'employment_status', 'hire_date')
    list_filter = ('organization', 'department', 'designation', 'employment_status', 'gender', 'marital_status')
    search_fields = ('employee_id', 'first_name', 'last_name', 'user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at', 'age', 'experience_years')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'employee_id', 'first_name', 'last_name', 'middle_name', 'profile_picture')
        }),
        ('Organizational Structure', {
            'fields': ('branch', 'department', 'designation', 'employee_role', 'reporting_manager')
        }),
        ('Personal Information', {
            'fields': ('gender', 'date_of_birth', 'blood_group', 'marital_status', 'nationality')
        }),
        ('Contact Information', {
            'fields': ('personal_email', 'personal_phone', 'work_phone', 'current_address', 'permanent_address')
        }),
        ('Employment Information', {
            'fields': ('employment_status', 'hire_date', 'confirmation_date', 'termination_date', 'probation_period_months')
        }),
        ('Salary Information', {
            'fields': ('basic_salary', 'gross_salary', 'net_salary')
        }),
        ('Emergency Contact', {
            'fields': ('emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship', 'emergency_contact_address')
        }),
        ('Bank Information', {
            'fields': ('bank_name', 'bank_account_number', 'bank_routing_number')
        }),
        ('Additional Information', {
            'fields': ('skills', 'notes', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'age', 'experience_years'),
            'classes': ('collapse',)
        }),
    )


# @admin.register(Attendance)
# class AttendanceAdmin(admin.ModelAdmin):
#     list_display = ('employee', 'date', 'check_in_time', 'check_out_time', 'total_hours', 'status')
#     list_filter = ('organization', 'employee__department', 'status', 'date')
#     search_fields = ('employee__first_name', 'employee__last_name', 'employee__employee_id')
#     readonly_fields = ('created_at', 'updated_at')


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ('employee', 'leave_type', 'start_date', 'end_date', 'days_requested', 'status')
    list_filter = ('organization', 'leave_type', 'status', 'start_date')
    search_fields = ('employee__first_name', 'employee__last_name', 'employee__employee_id')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ('employee', 'date', 'status', 'check_in_time', 'check_out_time', 'total_hours')
    list_filter = ('employee__organization', 'status', 'date')
    search_fields = ('employee__first_name', 'employee__last_name', 'employee__employee_id')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(HolidayCalendar)
class HolidayCalendarAdmin(admin.ModelAdmin):
	list_display = [field.name for field in HolidayCalendar._meta.fields]
