from django.contrib import admin
from .models import *


# -------------------- BRANCH --------------------
@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'organization', 'manager', 'is_active', 'deleted_at')
    list_filter = ('organization', 'is_active', 'deleted_at')
    search_fields = ('name', 'code', 'organization__name')
    readonly_fields = ('created_at', 'updated_at')

    def get_queryset(self, request):
        return Branch.objects.all_with_deleted()

    actions = ['restore_branches']

    @admin.action(description="Restore selected soft-deleted branches")
    def restore_branches(self, request, queryset):
        restored_count = queryset.filter(deleted_at__isnull=False).update(deleted_at=None)
        self.message_user(request, f"{restored_count} branch(es) restored successfully.")

# -------------------- DEPARTMENT --------------------
@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'organization', 'branch', 'manager', 'is_active', 'deleted_at')
    list_filter = ('organization', 'branch', 'is_active', 'deleted_at')
    search_fields = ('name', 'code', 'organization__name')
    readonly_fields = ('created_at', 'updated_at')

    def get_queryset(self, request):
        return Department.objects.all_with_deleted()

    actions = ['restore_departments']

    @admin.action(description="Restore selected soft-deleted departments")
    def restore_departments(self, request, queryset):
        restored_count = queryset.filter(deleted_at__isnull=False).update(deleted_at=None)
        self.message_user(request, f"{restored_count} department(s) restored successfully.")

# -------------------- DESIGNATION --------------------
@admin.register(Designation)
class DesignationAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'organization', 'department', 'level', 'is_active', 'deleted_at')
    list_filter = ('organization', 'department', 'level', 'is_active', 'deleted_at')
    search_fields = ('name', 'code', 'organization__name')
    readonly_fields = ('created_at', 'updated_at')

    def get_queryset(self, request):
        return Designation.objects.all_with_deleted()

    actions = ['restore_designations']

    @admin.action(description="Restore selected soft-deleted designations")
    def restore_designations(self, request, queryset):
        restored_count = queryset.filter(deleted_at__isnull=False).update(deleted_at=None)
        self.message_user(request, f"{restored_count} designation(s) restored successfully.")

# -------------------- EMPLOYEE ROLE --------------------
@admin.register(EmployeeRole)
class EmployeeRoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'organization', 'is_active', 'deleted_at')
    list_filter = ('organization', 'is_active', 'deleted_at')
    search_fields = ('name', 'code', 'organization__name')
    readonly_fields = ('created_at', 'updated_at')

    def get_queryset(self, request):
        return EmployeeRole.objects.all_with_deleted()

    actions = ['restore_roles']

    @admin.action(description="Restore selected soft-deleted roles")
    def restore_roles(self, request, queryset):
        restored_count = queryset.filter(deleted_at__isnull=False).update(deleted_at=None)
        self.message_user(request, f"{restored_count} role(s) restored successfully.")

# -------------------- EMPLOYEE --------------------
@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'full_name', 'organization', 'department', 'designation', 'employment_status', 'deleted_at')
    list_filter = ('organization', 'department', 'designation', 'employment_status', 'gender', 'marital_status', 'deleted_at')
    search_fields = ('employee_id', 'first_name', 'last_name', 'user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at', 'age', 'experience_years')

    fieldsets = (
        ('Basic Information', {'fields': ('user', 'employee_id', 'first_name', 'last_name', 'middle_name', 'profile_picture')}),
        ('Organizational Structure', {'fields': ('branch', 'department', 'designation', 'employee_role', 'reporting_manager')}),
        ('Personal Information', {'fields': ('gender', 'date_of_birth', 'blood_group', 'marital_status', 'nationality')}),
        ('Contact Information', {'fields': ('personal_email', 'personal_phone', 'work_phone', 'current_address', 'permanent_address')}),
        ('Employment Information', {'fields': ('employment_status', 'hire_date', 'confirmation_date', 'termination_date', 'probation_period_months')}),
        ('Salary Information', {'fields': ('basic_salary', 'gross_salary', 'net_salary')}),
        ('Emergency Contact', {'fields': ('emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship', 'emergency_contact_address')}),
        ('Bank Information', {'fields': ('bank_name', 'bank_account_number', 'bank_routing_number')}),
        ('Additional Information', {'fields': ('skills', 'notes', 'is_active')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at', 'age', 'experience_years'), 'classes': ('collapse',)})
    )

    def get_queryset(self, request):
        return Employee.objects.all_with_deleted()

    actions = ['restore_employees']

    @admin.action(description="Restore selected soft-deleted employees")
    def restore_employees(self, request, queryset):
        restored_count = queryset.filter(deleted_at__isnull=False).update(deleted_at=None)
        self.message_user(request, f"{restored_count} employee(s) restored successfully.")

# -------------------- LEAVE REQUEST --------------------
@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ('employee', 'leave_type', 'start_date', 'end_date', 'days_requested', 'status', 'deleted_at')
    list_filter = ('organization', 'leave_type', 'status', 'start_date', 'deleted_at')
    search_fields = ('employee__first_name', 'employee__last_name', 'employee__employee_id')
    readonly_fields = ('created_at', 'updated_at')

    def get_queryset(self, request):
        return LeaveRequest.objects.all_with_deleted()

    actions = ['restore_leave_requests']

    @admin.action(description="Restore selected soft-deleted leave requests")
    def restore_leave_requests(self, request, queryset):
        restored_count = queryset.filter(deleted_at__isnull=False).update(deleted_at=None)
        self.message_user(request, f"{restored_count} leave request(s) restored successfully.")

# -------------------- ATTENDANCE RECORD --------------------
@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ('employee', 'date', 'status', 'check_in_time', 'check_out_time', 'total_hours', 'deleted_at')
    list_filter = ('employee__organization', 'status', 'date', 'deleted_at')
    search_fields = ('employee__first_name', 'employee__last_name', 'employee__employee_id')
    readonly_fields = ('created_at', 'updated_at')

    def get_queryset(self, request):
        return AttendanceRecord.objects.all_with_deleted()

    actions = ['restore_attendance']

    @admin.action(description="Restore selected soft-deleted attendance records")
    def restore_attendance(self, request, queryset):
        restored_count = queryset.filter(deleted_at__isnull=False).update(deleted_at=None)
        self.message_user(request, f"{restored_count} attendance record(s) restored successfully.")

# -------------------- HOLIDAY CALENDAR --------------------
@admin.register(HolidayCalendar)
class HolidayCalendarAdmin(admin.ModelAdmin):
    list_display = [field.name for field in HolidayCalendar._meta.fields]
    
    def get_queryset(self, request):
        return HolidayCalendar.objects.all_with_deleted()

    actions = ['restore_holidays']

    @admin.action(description="Restore selected soft-deleted holidays")
    def restore_holidays(self, request, queryset):
        restored_count = queryset.filter(deleted_at__isnull=False).update(deleted_at=None)
        self.message_user(request, f"{restored_count} holiday(s) restored successfully.")

# -------------------- PAYHEAD, TIMETABLE, EMPLOYEE PAYHEAD --------------------
@admin.register(Payhead)
class PayheadAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'organization', 'deleted_at')
    list_filter = ('organization', 'deleted_at')
    search_fields = ('name', 'code')
    actions = ['restore_payheads']

    def get_queryset(self, request):
        return Payhead.objects.all_with_deleted()

    @admin.action(description="Restore selected soft-deleted payheads")
    def restore_payheads(self, request, queryset):
        restored_count = queryset.filter(deleted_at__isnull=False).update(deleted_at=None)
        self.message_user(request, f"{restored_count} payhead(s) restored successfully.")

@admin.register(Timetable)
class TimetableAdmin(admin.ModelAdmin):
    list_display = ('organization', 'deleted_at')
    list_filter = ('organization', 'deleted_at')
 
    actions = ['restore_timetables']

    def get_queryset(self, request):
        return Timetable.objects.all_with_deleted()

    @admin.action(description="Restore selected soft-deleted timetables")
    def restore_timetables(self, request, queryset):
        restored_count = queryset.filter(deleted_at__isnull=False).update(deleted_at=None)
        self.message_user(request, f"{restored_count} timetable(s) restored successfully.")

@admin.register(EmployeePayhead)
class EmployeePayheadAdmin(admin.ModelAdmin):
    list_display = ('employee', 'payhead', 'organization', 'deleted_at')
    list_filter = ('organization', 'deleted_at')
    search_fields = ('employee__first_name', 'employee__last_name', 'payhead__name')
    actions = ['restore_employee_payheads']

    def get_queryset(self, request):
        return EmployeePayhead.objects.all_with_deleted()

    @admin.action(description="Restore selected soft-deleted employee payheads")
    def restore_employee_payheads(self, request, queryset):
        restored_count = queryset.filter(deleted_at__isnull=False).update(deleted_at=None)
        self.message_user(request, f"{restored_count} employee payhead(s) restored successfully.")


@admin.register(AttendanceHoliday)
class AttendanceHolidayAdmin(admin.ModelAdmin):
    list_display = ('name', 'date', 'organization', 'deleted_at')
    list_filter = ('organization', 'deleted_at')
    actions = ['restore_attendance_holidays']

    def get_queryset(self, request):
        return AttendanceHoliday.objects.all_with_deleted()

    @admin.action(description="Restore selected soft-deleted attendance holidays")
    def restore_employee_payheads(self, request, queryset):
        restored_count = queryset.filter(deleted_at__isnull=False).update(deleted_at=None)
        self.message_user(request, f"{restored_count} attendance holiday restored successfully.")

