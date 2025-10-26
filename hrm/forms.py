from django import forms
from django.contrib.auth import get_user_model
from .models import Branch, Department, Designation, EmployeeRole, Employee, AttendanceRecord, LeaveRequest, Shift, Timetable, AttendanceDevice, Payhead, EmployeePayhead, AttendanceHoliday

User = get_user_model()


class BranchForm(forms.ModelForm):
    class Meta:
        model = Branch
        fields = ['name', 'code', 'description', 'address_line1', 'address_line2', 'city', 'state', 'postal_code', 'country', 'phone', 'email', 'manager']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'code': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control form-control-sm'}),
            'address_line1': forms.TextInput(attrs={'placeholder': 'Street address', 'class': 'form-control form-control-sm'}),
            'address_line2': forms.TextInput(attrs={'placeholder': 'Apartment, suite, etc.', 'class': 'form-control form-control-sm'}),
            'city': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'state': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'country': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'phone': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'email': forms.EmailInput(attrs={'class': 'form-control form-control-sm'}),
            'manager': forms.Select(attrs={'class': 'form-control form-control-sm', 'data-placeholder': 'Select Manager'}),
        }
    
    def __init__(self, *args, **kwargs):
        organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        self.fields['name'].required = True
        self.fields['code'].required = True
        self.fields['manager'].empty_label = "Select Manager"
        
        # Filter managers by organization
        if organization:
            self.fields['manager'].queryset = User.objects.filter(
                organizationmembership__organization=organization,
                organizationmembership__is_active=True
            )


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'code', 'description', 'branch', 'manager']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'code': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control form-control-sm'}),
            'branch': forms.Select(attrs={'class': 'form-control form-control-sm', 'data-placeholder': 'Select Branch'}),
            'manager': forms.Select(attrs={'class': 'form-control form-control-sm', 'data-placeholder': 'Select Manager'}),
        }
    
    def __init__(self, *args, **kwargs):
        organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        self.fields['name'].required = True
        self.fields['code'].required = True
        self.fields['branch'].empty_label = "Select Branch"
        self.fields['manager'].empty_label = "Select Manager"
        
        # Filter branches and managers by organization
        if organization:
            self.fields['branch'].queryset = Branch.objects.filter(organization=organization, is_active=True)
            self.fields['manager'].queryset = User.objects.filter(
                organizationmembership__organization=organization,
                organizationmembership__is_active=True
            )


class DesignationForm(forms.ModelForm):
    class Meta:
        model = Designation
        fields = ['name', 'code', 'description', 'level', 'department']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'code': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control form-control-sm'}),
            'level': forms.NumberInput(attrs={'min': 1, 'max': 10, 'class': 'form-control form-control-sm'}),
            'department': forms.Select(attrs={'class': 'form-control form-control-sm', 'data-placeholder': 'Select Department'}),
        }
    
    def __init__(self, *args, **kwargs):
        organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        self.fields['name'].required = True
        self.fields['code'].required = True
        self.fields['level'].required = True
        self.fields['department'].empty_label = "Select Department"
        
        # Filter departments by organization
        if organization:
            self.fields['department'].queryset = Department.objects.filter(organization=organization, is_active=True)


class EmployeeRoleForm(forms.ModelForm):
    class Meta:
        model = EmployeeRole
        fields = ['name', 'code', 'description', 'permissions']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'code': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control form-control-sm'}),
            'permissions': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter permissions as JSON or comma-separated values', 'class': 'form-control form-control-sm'}),
        }

    def __init__(self, *args, **kwargs):
        self.organization = kwargs.pop('organization', None)  # <-- remove 'organization' from kwargs
        super().__init__(*args, **kwargs)
        self.fields['name'].required = True
        self.fields['code'].required = True


class EmployeeForm(forms.ModelForm):
    # User account fields
    username = forms.CharField(
        max_length=150, 
        help_text="Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.",
        widget=forms.TextInput(attrs={'class': 'form-control form-control-sm'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control form-control-sm'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control form-control-sm'}), 
        min_length=8
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control form-control-sm'})
    )
    
    class Meta:
        model = Employee
        fields = [
            'username', 'email', 'password', 'confirm_password',
            'employee_id', 'first_name', 'last_name', 'middle_name', 'profile_picture',
            'branch', 'department', 'designation', 'employee_role',
            'gender', 'date_of_birth', 'blood_group', 'marital_status', 'nationality',
            'personal_email', 'personal_phone', 'work_phone',
            'current_address', 'permanent_address',
            'employment_status', 'hire_date', 'confirmation_date', 'probation_period_months',
            'basic_salary', 'gross_salary', 'net_salary',
            'reporting_manager',
            'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship', 'emergency_contact_address',
            'bank_name', 'bank_account_number', 'bank_routing_number',
            'skills', 'notes'
        ]
        widgets = {
            'employee_id': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'middle_name': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control form-control-sm'}),
            'branch': forms.Select(attrs={'class': 'form-control form-control-sm', 'data-placeholder': 'Select Branch'}),
            'department': forms.Select(attrs={'class': 'form-control form-control-sm', 'data-placeholder': 'Select Department'}),
            'designation': forms.Select(attrs={'class': 'form-control form-control-sm', 'data-placeholder': 'Select Designation'}),
            'employee_role': forms.Select(attrs={'class': 'form-control form-control-sm', 'data-placeholder': 'Select Role'}),
            'gender': forms.Select(attrs={'class': 'form-control form-control-sm', 'data-placeholder': 'Select Gender'}),
            'date_of_birth': forms.DateInput(attrs={
                'type': 'date', 
                'class': 'form-control form-control-sm date-picker',
                'placeholder': 'dd mmm, yy'
            }),
            'blood_group': forms.Select(attrs={'class': 'form-control form-control-sm', 'data-placeholder': 'Select Blood Group'}),
            'marital_status': forms.Select(attrs={'class': 'form-control form-control-sm', 'data-placeholder': 'Select Marital Status'}),
            'nationality': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'personal_email': forms.EmailInput(attrs={'class': 'form-control form-control-sm'}),
            'personal_phone': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'work_phone': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'current_address': forms.Textarea(attrs={
                'rows': 3, 
                'class': 'form-control form-control-sm'
            }),
            'permanent_address': forms.Textarea(attrs={
                'rows': 3, 
                'class': 'form-control form-control-sm'
            }),
            'employment_status': forms.Select(attrs={'class': 'form-control form-control-sm', 'data-placeholder': 'Select Employment Status'}),
            'hire_date': forms.DateInput(attrs={
                'type': 'date', 
                'class': 'form-control form-control-sm date-picker',
                'placeholder': 'dd mmm, yy'
            }),
            'confirmation_date': forms.DateInput(attrs={
                'type': 'date', 
                'class': 'form-control form-control-sm date-picker',
                'placeholder': 'dd mmm, yy'
            }),
            'probation_period_months': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'basic_salary': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'gross_salary': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'net_salary': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'reporting_manager': forms.Select(attrs={'class': 'form-control form-control-sm', 'data-placeholder': 'Select Reporting Manager'}),
            'emergency_contact_name': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Name'}),
            'emergency_contact_phone': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Phone'}),
            'emergency_contact_relationship': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Relation'}),
            'emergency_contact_address': forms.Textarea(attrs={
                'rows': 3, 
                'class': 'form-control form-control-sm'
            }),
            'bank_name': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'bank_account_number': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'bank_routing_number': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'skills': forms.Textarea(attrs={
                'rows': 3, 
                'class': 'form-control form-control-sm',
                'placeholder': 'Enter skills separated by commas'
            }),
            'notes': forms.Textarea(attrs={
                'rows': 3, 
                'class': 'form-control form-control-sm'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make some fields required
        self.fields['employee_id'].required = True
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['hire_date'].required = True
        
        # Add placeholders for select fields
        self.fields['branch'].empty_label = "Select Branch"
        self.fields['department'].empty_label = "Select Department"
        self.fields['designation'].empty_label = "Select Designation"
        self.fields['employee_role'].empty_label = "Select Role"
        self.fields['gender'].empty_label = "Select Gender"
        self.fields['blood_group'].empty_label = "Select Blood Group"
        self.fields['marital_status'].empty_label = "Select Marital Status"
        self.fields['employment_status'].empty_label = "Select Employment Status"
        self.fields['reporting_manager'].empty_label = "Select Reporting Manager"
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and confirm_password:
            if password != confirm_password:
                raise forms.ValidationError("Passwords don't match.")
        
        return cleaned_data
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("A user with this username already exists.")
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email



class EmployeeUpdateForm(forms.ModelForm):
    """Form for updating existing employees (without password fields)"""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control form-control-sm'})
    )
    
    class Meta:
        model = Employee
        fields = [
            'email',
            'employee_id', 'first_name', 'last_name', 'middle_name', 'profile_picture',
            'branch', 'department', 'designation', 'employee_role',
            'gender', 'date_of_birth', 'blood_group', 'marital_status', 'nationality',
            'personal_email', 'personal_phone', 'work_phone',
            'current_address', 'permanent_address',
            'employment_status', 'hire_date', 'confirmation_date', 'probation_period_months',
            'basic_salary', 'gross_salary', 'net_salary',
            'reporting_manager',
            'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship', 'emergency_contact_address',
            'bank_name', 'bank_account_number', 'bank_routing_number',
            'skills', 'notes'
        ]
        widgets = {
            'employee_id': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'readonly': 'readonly'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'middle_name': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control form-control-sm'}),
            'branch': forms.Select(attrs={'class': 'form-control form-control-sm', 'data-placeholder': 'Select Branch'}),
            'department': forms.Select(attrs={'class': 'form-control form-control-sm', 'data-placeholder': 'Select Department'}),
            'designation': forms.Select(attrs={'class': 'form-control form-control-sm', 'data-placeholder': 'Select Designation'}),
            'employee_role': forms.Select(attrs={'class': 'form-control form-control-sm', 'data-placeholder': 'Select Role'}),
            'gender': forms.Select(attrs={'class': 'form-control form-control-sm', 'data-placeholder': 'Select Gender'}),
            'date_of_birth': forms.DateInput(attrs={
                'type': 'date', 
                'class': 'form-control form-control-sm date-picker',
                'placeholder': 'dd mmm, yy'
            }),
            'blood_group': forms.Select(attrs={'class': 'form-control form-control-sm', 'data-placeholder': 'Select Blood Group'}),
            'marital_status': forms.Select(attrs={'class': 'form-control form-control-sm', 'data-placeholder': 'Select Marital Status'}),
            'nationality': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'personal_email': forms.EmailInput(attrs={'class': 'form-control form-control-sm'}),
            'personal_phone': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'work_phone': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'current_address': forms.Textarea(attrs={
                'rows': 3, 
                'class': 'form-control form-control-sm'
            }),
            'permanent_address': forms.Textarea(attrs={
                'rows': 3, 
                'class': 'form-control form-control-sm'
            }),
            'employment_status': forms.Select(attrs={'class': 'form-control form-control-sm', 'data-placeholder': 'Select Employment Status'}),
            'hire_date': forms.DateInput(attrs={
                'type': 'date', 
                'class': 'form-control form-control-sm date-picker',
                'placeholder': 'dd mmm, yy'
            }),
            'confirmation_date': forms.DateInput(attrs={
                'type': 'date', 
                'class': 'form-control form-control-sm date-picker',
                'placeholder': 'dd mmm, yy'
            }),
            'probation_period_months': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'basic_salary': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'gross_salary': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'net_salary': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'reporting_manager': forms.Select(attrs={'class': 'form-control form-control-sm', 'data-placeholder': 'Select Reporting Manager'}),
            'emergency_contact_name': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Name'}),
            'emergency_contact_phone': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Phone'}),
            'emergency_contact_relationship': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Relation'}),
            'emergency_contact_address': forms.Textarea(attrs={
                'rows': 3, 
                'class': 'form-control form-control-sm'
            }),
            'bank_name': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'bank_account_number': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'bank_routing_number': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'skills': forms.Textarea(attrs={
                'rows': 3, 
                'class': 'form-control form-control-sm',
                'placeholder': 'Enter skills separated by commas'
            }),
            'notes': forms.Textarea(attrs={
                'rows': 3, 
                'class': 'form-control form-control-sm'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make some fields required
        self.fields['employee_id'].required = True
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['hire_date'].required = True
        
        # Add placeholders for select fields
        self.fields['branch'].empty_label = "Select Branch"
        self.fields['department'].empty_label = "Select Department"
        self.fields['designation'].empty_label = "Select Designation"
        self.fields['employee_role'].empty_label = "Select Role"
        self.fields['gender'].empty_label = "Select Gender"
        self.fields['blood_group'].empty_label = "Select Blood Group"
        self.fields['marital_status'].empty_label = "Select Marital Status"
        self.fields['employment_status'].empty_label = "Select Employment Status"
        self.fields['reporting_manager'].empty_label = "Select Reporting Manager"
        
        # Make employee_id read-only for updates
        if self.instance and self.instance.pk:
            self.fields['employee_id'].widget.attrs['readonly'] = True
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if self.instance and self.instance.user:
            if User.objects.filter(email=email).exclude(pk=self.instance.user.pk).exists():
                raise forms.ValidationError("A user with this email already exists.")
        return email


class ShiftForm(forms.ModelForm):
    class Meta:
        model = Shift
        fields = ['name', 'code', 'description', 'start_time', 'end_time', 'break_start_time', 'break_end_time', 'working_hours', 'break_hours', 'grace_period_minutes', 'overtime_start_after_hours']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'code': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control form-control-sm'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control form-control-sm'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control form-control-sm'}),
            'break_start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control form-control-sm'}),
            'break_end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control form-control-sm'}),
            'working_hours': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01'}),
            'break_hours': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01'}),
            'grace_period_minutes': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'overtime_start_after_hours': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01'}),
        }
    
    def __init__(self, *args, **kwargs):
        organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        self.fields['name'].required = True
        self.fields['code'].required = True
        self.fields['start_time'].required = True
        self.fields['end_time'].required = True
        self.fields['working_hours'].required = True


# forms.py
class TimetableForm(forms.ModelForm):
    designation = forms.ModelChoiceField(
        queryset=Designation.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control form-control-sm'})
    )

    class Meta:
        model = Timetable
        fields = [
            'designation', 'employees', 'shift', 'start_date', 'end_date',
            'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'
        ]
        widgets = {
            'employees': forms.SelectMultiple(attrs={'class': 'form-control form-control-sm'}),
            'shift': forms.Select(attrs={'class': 'form-control form-control-sm'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control form-control-sm'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control form-control-sm'}),
        }

    def __init__(self, *args, **kwargs):
        organization = kwargs.pop('organization', None)
        designation_id = kwargs.pop('designation_id', None)
        super().__init__(*args, **kwargs)

        if organization:
            self.fields['designation'].queryset = Designation.objects.filter(
                organization=organization, is_active=True
            )
            self.fields['shift'].queryset = Shift.objects.filter(
                organization=organization, is_active=True
            )

            employee_qs = Employee.objects.filter(organization=organization, is_active=True)
            if designation_id:
                employee_qs = employee_qs.filter(designation_id=designation_id)
            self.fields['employees'].queryset = employee_qs



class AttendanceDeviceForm(forms.ModelForm):
    class Meta:
        model = AttendanceDevice
        fields = ['name', 'device_type', 'ip_address', 'port', 'device_id', 'serial_number', 'model', 'firmware_version', 'location', 'description', 'auto_sync_enabled', 'sync_interval_minutes']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'device_type': forms.Select(attrs={'class': 'form-control form-control-sm'}),
            'ip_address': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'placeholder': '192.168.1.100'}),
            'port': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'device_id': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'serial_number': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'model': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'firmware_version': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'location': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control form-control-sm'}),
            'auto_sync_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'sync_interval_minutes': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
        }
    
    def __init__(self, *args, **kwargs):
        organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        self.fields['name'].required = True
        self.fields['ip_address'].required = True


class PayheadForm(forms.ModelForm):
    class Meta:
        model = Payhead
        fields = ['name', 'code', 'description', 'payhead_type', 'calculation_type', 'amount', 'percentage', 'attendance_rate_per_hour', 'overtime_rate_per_hour', 'is_taxable', 'is_pf_applicable', 'is_esi_applicable', 'display_order']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'code': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control form-control-sm'}),
            'payhead_type': forms.Select(attrs={'class': 'form-control form-control-sm'}),
            'calculation_type': forms.Select(attrs={'class': 'form-control form-control-sm'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01'}),
            'percentage': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01'}),
            'attendance_rate_per_hour': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01'}),
            'overtime_rate_per_hour': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01'}),
            'is_taxable': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_pf_applicable': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_esi_applicable': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'display_order': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
        }
    
    def __init__(self, *args, **kwargs):
        organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        self.fields['name'].required = True
        self.fields['code'].required = True
        self.fields['payhead_type'].required = True


class EmployeePayheadForm(forms.ModelForm):
    class Meta:
        model = EmployeePayhead
        fields = ['employee', 'payhead', 'amount', 'percentage', 'effective_from', 'effective_to']
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-control form-control-sm'}),
            'payhead': forms.Select(attrs={'class': 'form-control form-control-sm'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01'}),
            'percentage': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01'}),
            'effective_from': forms.DateInput(attrs={'type': 'date', 'class': 'form-control form-control-sm'}),
            'effective_to': forms.DateInput(attrs={'type': 'date', 'class': 'form-control form-control-sm'}),
        }
    
    def __init__(self, *args, **kwargs):
        organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        self.fields['employee'].required = True
        self.fields['payhead'].required = True
        self.fields['effective_from'].required = True
        
        if organization:
            self.fields['employee'].queryset = Employee.objects.filter(organization=organization, is_active=True)
            self.fields['payhead'].queryset = Payhead.objects.filter(organization=organization, is_active=True)


class AttendanceHolidayForm(forms.ModelForm):
    class Meta:
        model = AttendanceHoliday
        fields = ['name', 'date', 'is_recurring', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control form-control-sm'}),
            'is_recurring': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control form-control-sm'}),
        }
    
    def __init__(self, *args, **kwargs):
        organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        self.fields['name'].required = True
        self.fields['date'].required = True


class AttendanceFilterForm(forms.Form):
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    employee = forms.ModelChoiceField(
        queryset=Employee.objects.none(),
        required=False,
        empty_label="All Employees",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    department = forms.ModelChoiceField(
        queryset=Department.objects.none(),
        required=False,
        empty_label="All Departments",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    status = forms.ChoiceField(
        choices=[('', 'All Status')] + list(AttendanceRecord.STATUS_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        if organization:
            self.fields['employee'].queryset = Employee.objects.filter(organization=organization, is_active=True)
            self.fields['department'].queryset = Department.objects.filter(organization=organization, is_active=True)
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError("Start date must be before end date.")
        
        return cleaned_data


class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ['employee', 'leave_type', 'start_date', 'end_date', 'reason']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'reason': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        if organization:
            self.fields['employee'].queryset = Employee.objects.filter(organization=organization)
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date:
            if start_date > end_date:
                raise forms.ValidationError("End date must be after start date.")
            
            # Calculate days requested
            days_requested = (end_date - start_date).days + 1
            cleaned_data['days_requested'] = days_requested
        
        return cleaned_data


class EmployeeSearchForm(forms.Form):
    search = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Search by name, employee ID, or email...',
            'class': 'form-control'
        })
    )
    department = forms.ModelChoiceField(
        queryset=Department.objects.none(),
        required=False,
        empty_label="All Departments",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    status = forms.ChoiceField(
        choices=[('', 'All Status')] + list(Employee.EMPLOYMENT_STATUS_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def __init__(self, *args, **kwargs):
        organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        if organization:
            self.fields['department'].queryset = Department.objects.filter(organization=organization, is_active=True)


class AttendanceFilterForm(forms.Form):
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError("Start date must be before end date.")
        
        return cleaned_data


class LeaveFilterForm(forms.Form):
    status = forms.ChoiceField(
        choices=[('', 'All Status')] + list(LeaveRequest.STATUS_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    leave_type = forms.ChoiceField(
        choices=[('', 'All Types')] + list(LeaveRequest.LEAVE_TYPE_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
