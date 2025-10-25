from decimal import Decimal
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

User = get_user_model()


class BaseOrganizationModel(models.Model):
    """
    Abstract base model for organization-specific data
    All HRM and Payroll models should inherit from this
    """
    organization = models.ForeignKey('organization.Organization', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        abstract = True


class Branch(BaseOrganizationModel):
    """
    Branch model for organization-specific branches/offices
    """
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=10, help_text="Branch code (e.g., BR001)")
    description = models.TextField(blank=True, null=True)
    
    # Address
    address_line1 = models.CharField(max_length=255, blank=True, null=True)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    
    # Contact Information
    phone = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    
    # Manager
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_branches')
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['organization', 'code']
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.organization.name})"


class Department(BaseOrganizationModel):
    """
    Department model for organization-specific departments
    """
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=10, help_text="Department code (e.g., DEP001)")
    description = models.TextField(blank=True, null=True)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='departments', null=True, blank=True)
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_departments')
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['organization', 'code']
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.organization.name})"


class Designation(BaseOrganizationModel):
    """
    Designation/Job Title model for organization-specific designations
    """
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=10, help_text="Designation code (e.g., DES001)")
    description = models.TextField(blank=True, null=True)
    level = models.PositiveIntegerField(default=1, help_text="Hierarchy level (1=lowest)")
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='designations', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['organization', 'code']
        ordering = ['level', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.organization.name})"


class EmployeeRole(BaseOrganizationModel):
    """
    Employee role model for organization-specific roles
    """
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=10, help_text="Role code (e.g., ROL001)")
    description = models.TextField(blank=True, null=True)
    permissions = models.JSONField(default=dict, blank=True, help_text="Role-specific permissions")
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['organization', 'code']
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.organization.name})"


class Employee(BaseOrganizationModel):
    """
    Employee model for organization-specific employees
    """
    EMPLOYMENT_STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('terminated', 'Terminated'),
        ('on_leave', 'On Leave'),
    ]
    
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
        ('prefer_not_to_say', 'Prefer not to say'),
    ]
    
    MARITAL_STATUS_CHOICES = [
        ('single', 'Single'),
        ('married', 'Married'),
        ('divorced', 'Divorced'),
        ('widowed', 'Widowed'),
    ]
    
    BLOOD_GROUP_CHOICES = [
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
    ]
    
    # User Account
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee_profile')
    employee_id = models.CharField(max_length=50, unique=True)
    
    # Organizational Structure
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True, related_name='employees')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='employees')
    designation = models.ForeignKey(Designation, on_delete=models.SET_NULL, null=True, blank=True, related_name='employees')
    employee_role = models.ForeignKey(EmployeeRole, on_delete=models.SET_NULL, null=True, blank=True, related_name='employees')
    
    # Personal Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='employee_profiles/', blank=True, null=True)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES, blank=True, null=True)
    marital_status = models.CharField(max_length=20, choices=MARITAL_STATUS_CHOICES, blank=True, null=True)
    nationality = models.CharField(max_length=100, default='Bangladeshi')
    
    # Contact Information
    personal_email = models.EmailField(blank=True, null=True)
    personal_phone = models.CharField(max_length=15, blank=True, null=True)
    work_phone = models.CharField(max_length=15, blank=True, null=True)
    
    # Address Information
    current_address = models.TextField(blank=True, null=True)
    permanent_address = models.TextField(blank=True, null=True)
    
    # Employment Information
    employment_status = models.CharField(max_length=20, choices=EMPLOYMENT_STATUS_CHOICES, default='active')
    hire_date = models.DateField()
    confirmation_date = models.DateField(blank=True, null=True)
    termination_date = models.DateField(blank=True, null=True)
    probation_period_months = models.PositiveIntegerField(default=3)
    
    # Salary Information
    basic_salary = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    gross_salary = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    net_salary = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    
    # Reporting Structure
    reporting_manager = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subordinates')
    
    # Emergency Contact
    emergency_contact_name = models.CharField(max_length=200, blank=True, null=True)
    emergency_contact_phone = models.CharField(max_length=15, blank=True, null=True)
    emergency_contact_relationship = models.CharField(max_length=100, blank=True, null=True)
    emergency_contact_address = models.TextField(blank=True, null=True)
    
    # Bank Information
    bank_name = models.CharField(max_length=200, blank=True, null=True)
    bank_account_number = models.CharField(max_length=50, blank=True, null=True)
    bank_routing_number = models.CharField(max_length=50, blank=True, null=True)
    
    # Additional Information
    skills = models.TextField(blank=True, null=True, help_text="Comma-separated skills")
    notes = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    

    device_user_id = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        help_text='UID from attendance device'
    )
    device_enrollment_id = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text='Enrollment ID from attendance device'
    )

    class Meta:
        unique_together = ['organization', 'employee_id']
        ordering = ['last_name', 'first_name']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.employee_id})"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def age(self):
        if self.date_of_birth:
            from datetime import date
            today = date.today()
            return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        return None
    
    @property
    def experience_years(self):
        if self.hire_date:
            from datetime import date
            today = date.today()
            end_date = self.termination_date if self.termination_date else today
            return end_date.year - self.hire_date.year - ((end_date.month, end_date.day) < (self.hire_date.month, self.hire_date.day))
        return 0


class Shift(BaseOrganizationModel):
    """
    Shift model for organization-specific work shifts
    """
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, help_text="Shift code (e.g., SH001)")
    description = models.TextField(blank=True, null=True)
    
    # Shift timings
    start_time = models.TimeField()
    end_time = models.TimeField()
    break_start_time = models.TimeField(blank=True, null=True)
    break_end_time = models.TimeField(blank=True, null=True)
    
    # Working hours
    working_hours = models.DecimalField(max_digits=5, decimal_places=2, help_text="Total working hours per day")
    break_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Break hours")
    
    # Grace period
    grace_period_minutes = models.PositiveIntegerField(default=15, help_text="Grace period for late arrival in minutes")
    
    # Overtime settings
    overtime_start_after_hours = models.DecimalField(max_digits=5, decimal_places=2, default=8.00, help_text="Overtime starts after these hours")
    
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['organization', 'code']
        ordering = ['start_time']
    
    def __str__(self):
        return f"{self.name} ({self.start_time} - {self.end_time})"


class Timetable(BaseOrganizationModel):
    """
    Timetable model for employee work schedules
    (shared by multiple employees)
    """
    employees = models.ManyToManyField('Employee', related_name='timetables')

    shift = models.ForeignKey('Shift', on_delete=models.CASCADE, related_name='timetables')
    
    # Schedule period
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True, help_text="Leave blank for indefinite schedule")
    
    # Working days
    monday = models.BooleanField(default=True)
    tuesday = models.BooleanField(default=True)
    wednesday = models.BooleanField(default=True)
    thursday = models.BooleanField(default=True)
    friday = models.BooleanField(default=True)
    saturday = models.BooleanField(default=False)
    sunday = models.BooleanField(default=False)
    
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['start_date']
    
    def __str__(self):
        employee_names = ", ".join(e.full_name for e in self.employees.all()[:3])
        more = "..." if self.employees.count() > 3 else ""
        return f"{employee_names}{more} - {self.shift.name} ({self.start_date})"
    
    @property
    def working_days(self):
        """Return list of working days"""
        days = []
        if self.monday: days.append('Monday')
        if self.tuesday: days.append('Tuesday')
        if self.wednesday: days.append('Wednesday')
        if self.thursday: days.append('Thursday')
        if self.friday: days.append('Friday')
        if self.saturday: days.append('Saturday')
        if self.sunday: days.append('Sunday')
        return days



class AttendanceDevice(BaseOrganizationModel):
    """
    Attendance device model for ZKTeco integration
    """
    DEVICE_TYPES = [
        ('zkteco', 'ZKTeco'),
        ('manual', 'Manual Entry'),
        ('mobile', 'Mobile App'),
    ]
    
    name = models.CharField(max_length=200)
    device_type = models.CharField(max_length=20, choices=DEVICE_TYPES, default='zkteco')
    
    # Device connection details
    ip_address = models.GenericIPAddressField()
    port = models.PositiveIntegerField(default=4370)
    timeout = models.IntegerField(default=10, help_text='Connection timeout in seconds')
    password = models.IntegerField(default=0, help_text='Device password (usually 0)')
    mac_address = models.CharField(max_length=17, blank=True)
    platform = models.CharField(max_length=50, blank=True)
    device_id = models.PositiveIntegerField(default=1)
    
    # Device information
    serial_number = models.CharField(max_length=100, blank=True, null=True)
    model = models.CharField(max_length=100, blank=True, null=True)
    firmware_version = models.CharField(max_length=50, blank=True, null=True)
    
    # Location
    location = models.CharField(max_length=200, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_online = models.BooleanField(default=False)
    last_sync = models.DateTimeField(blank=True, null=True)
    
    # Sync settings
    auto_sync_enabled = models.BooleanField(default=True)
    sync_interval_minutes = models.PositiveIntegerField(default=30)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.ip_address})"


class AttendanceRecord(BaseOrganizationModel):
    """
    Detailed attendance record model
    """
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendance_records')
    device = models.ForeignKey(AttendanceDevice, on_delete=models.SET_NULL, null=True, blank=True, related_name='attendance_records')
    
    # Date and time
    date = models.DateField()
    check_in_time = models.TimeField(blank=True, null=True)
    check_out_time = models.TimeField(blank=True, null=True)
    
    # Break times
    break_start_time = models.TimeField(blank=True, null=True)
    break_end_time = models.TimeField(blank=True, null=True)
    
    # Calculated times
    total_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    working_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    break_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    overtime_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    # Status
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('half_day', 'Half Day'),
        ('on_leave', 'On Leave'),
        ('holiday', 'Holiday'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='present')
    
    # Late arrival
    is_late = models.BooleanField(default=False)
    late_minutes = models.PositiveIntegerField(default=0)
    
    # Early departure
    is_early_departure = models.BooleanField(default=False)
    early_departure_minutes = models.PositiveIntegerField(default=0)
    
    # Notes
    notes = models.TextField(blank=True, null=True)
    
    # Device sync info
    device_user_id = models.CharField(max_length=50, blank=True, null=True, help_text="User ID from device")
    sync_timestamp = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        unique_together = ['organization', 'employee', 'date']
        ordering = ['-date', 'employee']
    
    def __str__(self):
        return f"{self.employee.full_name} - {self.date} ({self.status})"
    
    def calculate_hours(self):
        """Calculate working hours, late/early flags, overtime, and status from shift + timetable"""
        from datetime import datetime, timedelta

        # Step 1: Find applicable timetable
        timetable = (
            Timetable.objects.filter(
                employees=self.employee,
                start_date__lte=self.date,
                is_active=True
            )
            .filter(models.Q(end_date__gte=self.date) | models.Q(end_date__isnull=True))
            .order_by('-start_date')
            .first()
        )

        if not timetable:
            self.status = 'absent'
            self.save()
            return

        shift = timetable.shift

        # Step 2: Skip if it's off day
        weekday = self.date.strftime("%A").lower()
        if not getattr(timetable, weekday):
            self.status = 'holiday'
            self.save()
            return

        # Step 3: Ensure check-in/out times exist
        if not self.check_in_time or not self.check_out_time:
            self.status = 'absent'
            self.save()
            return

        check_in_dt = datetime.combine(self.date, self.check_in_time)
        check_out_dt = datetime.combine(self.date, self.check_out_time)
        shift_start_dt = datetime.combine(self.date, shift.start_time)
        shift_end_dt = datetime.combine(self.date, shift.end_time)

        # Handle overnight shifts (e.g., ends next day)
        if shift_end_dt <= shift_start_dt:
            shift_end_dt += timedelta(days=1)
        if check_out_dt <= check_in_dt:
            check_out_dt += timedelta(days=1)

        # Step 4: Calculate base hours
        total_seconds = (check_out_dt - check_in_dt).total_seconds()
        self.total_hours = round(total_seconds / 3600, 2)

        # Step 5: Calculate break hours (either from record or shift)
        break_hours = 0.00
        if self.break_start_time and self.break_end_time:
            break_start_dt = datetime.combine(self.date, self.break_start_time)
            break_end_dt = datetime.combine(self.date, self.break_end_time)
            if break_end_dt <= break_start_dt:
                break_end_dt += timedelta(days=1)
            break_hours = round((break_end_dt - break_start_dt).total_seconds() / 3600, 2)
        elif shift.break_start_time and shift.break_end_time:
            break_start_dt = datetime.combine(self.date, shift.break_start_time)
            break_end_dt = datetime.combine(self.date, shift.break_end_time)
            if break_end_dt <= break_start_dt:
                break_end_dt += timedelta(days=1)
            break_hours = round((break_end_dt - break_start_dt).total_seconds() / 3600, 2)

        self.break_hours = break_hours
        self.working_hours = round(self.total_hours - self.break_hours, 2)

        # Step 6: Late & early calculations
        grace_minutes = shift.grace_period_minutes
        late_diff = (check_in_dt - shift_start_dt).total_seconds() / 60
        early_diff = (shift_end_dt - check_out_dt).total_seconds() / 60

        self.is_late = late_diff > grace_minutes
        self.late_minutes = int(late_diff) if self.is_late else 0

        self.is_early_departure = early_diff > grace_minutes
        self.early_departure_minutes = int(early_diff) if self.is_early_departure else 0

        # Step 7: Overtime calculation
        if self.working_hours > float(shift.overtime_start_after_hours):
            self.overtime_hours = round(self.working_hours - float(shift.overtime_start_after_hours), 2)
        else:
            self.overtime_hours = 0.00

        # Step 8: Determine attendance status
        if self.total_hours < (float(shift.working_hours) / 2):
            self.status = 'half_day'
        elif self.is_late:
            self.status = 'late'
        else:
            self.status = 'present'

        self.save()



class Payhead(BaseOrganizationModel):
    """
    Payhead model for salary components
    """
    PAYHEAD_TYPES = [
        ('earning', 'Earning'),
        ('deduction', 'Deduction'),
    ]
    
    CALCULATION_TYPES = [
        ('fixed', 'Fixed Amount'),
        ('percentage', 'Percentage of Basic'),
        ('attendance', 'Based on Attendance'),
        ('overtime', 'Based on Overtime'),
        ('production', 'Based on Production/Performance'),
        ('custom', 'Custom Calculation'),
    ]
    
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, help_text="Payhead code (e.g., BASIC, HRA, PF)")
    short_name = models.CharField(max_length=50, blank=True, null=True, help_text="Short name for display")
    description = models.TextField(blank=True, null=True)
    
    # Type and calculation
    payhead_type = models.CharField(max_length=20, choices=PAYHEAD_TYPES)
    calculation_type = models.CharField(max_length=20, choices=CALCULATION_TYPES, default='fixed')
    
    # Amount settings
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, 
                                   help_text="Percentage for percentage-based calculation")
    percentage_base = models.CharField(max_length=50, default='basic', 
                                     help_text="Base for percentage calculation (basic, gross, etc.)")
    
    # Rate-based settings
    attendance_rate_per_hour = models.DecimalField(max_digits=8, decimal_places=2, default=0.00, 
                                                 help_text="Rate per hour for attendance-based calculation")
    overtime_rate_per_hour = models.DecimalField(max_digits=8, decimal_places=2, default=0.00, 
                                               help_text="Rate per hour for overtime-based calculation")
    production_rate_per_unit = models.DecimalField(max_digits=8, decimal_places=2, default=0.00,
                                                 help_text="Rate per unit for production-based calculation")
    
    # Limits and constraints
    min_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, 
                                   help_text="Minimum amount limit")
    max_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, 
                                   help_text="Maximum amount limit")
    max_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00,
                                       help_text="Maximum percentage limit")
    
    # Tax and statutory settings
    is_taxable = models.BooleanField(default=True)
    is_pf_applicable = models.BooleanField(default=False)
    is_esi_applicable = models.BooleanField(default=False)
    is_gratuity_applicable = models.BooleanField(default=False)
    statutory_code = models.CharField(max_length=20, blank=True, null=True, 
                                    help_text="Statutory code for compliance reporting")
    
    # Display and ordering
    display_order = models.PositiveIntegerField(default=0)
    show_in_payslip = models.BooleanField(default=True)
    is_auto_calculated = models.BooleanField(default=True, 
                                           help_text="Whether this payhead is automatically calculated")
    
    # Activation settings
    is_active = models.BooleanField(default=True)
    effective_from = models.DateField(default=timezone.now, help_text="Date from which this payhead is effective")
    effective_to = models.DateField(blank=True, null=True, help_text="Date until which this payhead is effective")
    
    class Meta:
        unique_together = ['organization', 'code']
        ordering = ['display_order', 'name']
        indexes = [
            models.Index(fields=['organization', 'is_active', 'payhead_type']),
            models.Index(fields=['organization', 'calculation_type', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_payhead_type_display()})"
    
    @property
    def is_effective(self):
        """Check if payhead is currently effective"""
        today = timezone.now().date()
        if self.effective_from and self.effective_from > today:
            return False
        if self.effective_to and self.effective_to < today:
            return False
        return self.is_active
    
    def clean(self):
        """Validate payhead configuration"""
        from django.core.exceptions import ValidationError
        
        if self.calculation_type == 'percentage' and self.percentage <= 0:
            raise ValidationError({
                'percentage': 'Percentage must be greater than 0 for percentage-based calculation.'
            })
        
        if self.calculation_type == 'fixed' and self.amount <= 0:
            raise ValidationError({
                'amount': 'Amount must be greater than 0 for fixed amount calculation.'
            })
        
        if self.max_amount > 0 and self.min_amount > self.max_amount:
            raise ValidationError({
                'min_amount': 'Minimum amount cannot be greater than maximum amount.'
            })


class EmployeePayhead(BaseOrganizationModel):
    """
    Employee-specific payhead assignments and overrides
    """
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='employee_payheads')
    payhead = models.ForeignKey(Payhead, on_delete=models.CASCADE, related_name='employee_payheads')
    
    # Amount settings (override organization defaults)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    # Employee-specific rates
    attendance_rate_per_hour = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    overtime_rate_per_hour = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    production_rate_per_unit = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    
    # Employee-specific limits
    min_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    max_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    max_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    # Effective dates
    effective_from = models.DateField()
    effective_to = models.DateField(blank=True, null=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Audit fields
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                 related_name='created_employee_payheads')
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='modified_employee_payheads')
    
    class Meta:
        unique_together = ['organization', 'employee', 'payhead', 'effective_from']
        ordering = ['employee', 'payhead__display_order', '-effective_from']
        indexes = [
            models.Index(fields=['employee', 'is_active', 'effective_from']),
            models.Index(fields=['payhead', 'is_active']),
        ]
        verbose_name = "Employee Payhead"
        verbose_name_plural = "Employee Payheads"
    
    def __str__(self):
        return f"{self.employee.full_name} - {self.payhead.name} ({self.effective_from})"
    
    @property
    def is_effective(self):
        """Check if employee payhead is currently effective"""
        today = timezone.now().date()
        if self.effective_from > today:
            return False
        if self.effective_to and self.effective_to < today:
            return False
        return self.is_active and self.payhead.is_effective
    
    def get_effective_amount(self, base_amount=0, attendance_hours=0, overtime_hours=0, production_units=0):
        """Calculate effective amount based on payhead configuration"""
        if not self.is_effective:
            return Decimal('0.00')
        
        # Use employee-specific values if set, otherwise use payhead defaults
        calculation_type = self.payhead.calculation_type
        amount = self.amount if self.amount > 0 else self.payhead.amount
        percentage = self.percentage if self.percentage > 0 else self.payhead.percentage
        
        if calculation_type == 'fixed':
            result = amount
        
        elif calculation_type == 'percentage':
            result = (base_amount * percentage) / Decimal('100')
        
        elif calculation_type == 'attendance':
            rate = (self.attendance_rate_per_hour if self.attendance_rate_per_hour > 0 
                   else self.payhead.attendance_rate_per_hour)
            result = rate * Decimal(str(attendance_hours))
        
        elif calculation_type == 'overtime':
            rate = (self.overtime_rate_per_hour if self.overtime_rate_per_hour > 0 
                   else self.payhead.overtime_rate_per_hour)
            result = rate * Decimal(str(overtime_hours))
        
        elif calculation_type == 'production':
            rate = (self.production_rate_per_unit if self.production_rate_per_unit > 0 
                   else self.payhead.production_rate_per_unit)
            result = rate * Decimal(str(production_units))
        
        else:
            result = Decimal('0.00')
        
        # Apply limits
        min_amt = self.min_amount if self.min_amount > 0 else self.payhead.min_amount
        max_amt = self.max_amount if self.max_amount > 0 else self.payhead.max_amount
        
        if min_amt > 0:
            result = max(result, min_amt)
        if max_amt > 0:
            result = min(result, max_amt)
        
        return result
    
    def clean(self):
        """Validate employee payhead configuration"""
        from django.core.exceptions import ValidationError
        
        if self.effective_to and self.effective_to < self.effective_from:
            raise ValidationError({
                'effective_to': 'Effective to date cannot be before effective from date.'
            })
        
        # Check for overlapping effective periods
        overlapping = EmployeePayhead.objects.filter(
            organization=self.organization,
            employee=self.employee,
            payhead=self.payhead,
            is_active=True
        ).exclude(pk=self.pk).filter(
            models.Q(effective_to__isnull=True) | models.Q(effective_to__gte=self.effective_from)
        ).exists()
        
        if overlapping:
            raise ValidationError(
                "An active payhead assignment already exists for this employee with overlapping effective period."
            )


class HolidayCalendar(BaseOrganizationModel):
    class HolidayTypes(models.TextChoices):
        governmental = 'governmental'
        offical = 'official'
    name = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True)
    holiday_type = models.CharField(max_length=255, choices=HolidayTypes.choices, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        verbose_name_plural = 'Holiday Calendar'
        ordering = ['-id']

    def __str__(self):
        return f"{self.name}"


class AttendanceHoliday(BaseOrganizationModel):
    """
    Holiday model for attendance calculation
    """
    name = models.CharField(max_length=200)
    date = models.DateField()
    is_recurring = models.BooleanField(default=False, help_text="Recurring yearly")
    description = models.TextField(blank=True, null=True)
    
    class Meta:
        unique_together = ['organization', 'date']
        ordering = ['date']
    
    def __str__(self):
        return f"{self.name} ({self.date})"


class LeaveRequest(BaseOrganizationModel):
    """
    Leave requests for employees
    """
    LEAVE_TYPE_CHOICES = [
        ('sick', 'Sick Leave'),
        ('vacation', 'Vacation Leave'),
        ('personal', 'Personal Leave'),
        ('maternity', 'Maternity Leave'),
        ('paternity', 'Paternity Leave'),
        ('emergency', 'Emergency Leave'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPE_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    days_requested = models.PositiveIntegerField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_leave_requests')
    approved_at = models.DateTimeField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.employee.full_name} - {self.leave_type} ({self.start_date} to {self.end_date})"
