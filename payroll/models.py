from django.db import models
from django.contrib.auth import get_user_model
from decimal import Decimal
from django.utils import timezone
from hrm.models import Payhead
from django.db.models import UniqueConstraint

User = get_user_model()


class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)
    
    def all_with_deleted(self):
        """Return all records including deleted ones"""
        return super().get_queryset()
    
    def only_deleted(self):
        """Return only deleted records"""
        return super().get_queryset().filter(deleted_at__isnull=False)
    
    def restore(self, *args, **kwargs):
        """Restore soft deleted records"""
        queryset = self.only_deleted()
        if args or kwargs:
            queryset = queryset.filter(*args, **kwargs)
        return queryset.update(deleted_at=None)
    

class BaseOrganizationModel(models.Model):
    """
    Abstract base model for organization-specific data
    All Payroll models inherit from this for data isolation
    """
    organization = models.ForeignKey('organization.Organization', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True, editable=False)  # Add this field

    
    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        """Soft delete implementation"""
        self.deleted_at = timezone.now()
        self.save()
    
    def hard_delete(self):
        """Permanently delete the record"""
        super().delete()
    
    @property
    def is_deleted(self):
        """Check if record is soft deleted"""
        return self.deleted_at is not None


class PayrollPeriod(BaseOrganizationModel):
    """
    Payroll periods for each organization
    """
    PERIOD_TYPE_CHOICES = [
        ('monthly', 'Monthly'),
        ('biweekly', 'Bi-weekly'),
        ('weekly', 'Weekly'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    name = models.CharField(max_length=200)
    period_type = models.CharField(max_length=20, choices=PERIOD_TYPE_CHOICES, default='monthly')
    start_date = models.DateField()
    end_date = models.DateField()
    pay_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    class Meta:
        unique_together = ['organization', 'start_date', 'end_date']
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.name} ({self.start_date} to {self.end_date})"


class SalaryStructure(BaseOrganizationModel):
    """
    Salary structures for employees within organization
    """
    employee = models.ForeignKey('hrm.Employee', on_delete=models.CASCADE, related_name='salary_structures')
    basic_salary = models.DecimalField(max_digits=12, decimal_places=2)
    house_rent_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    transport_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    medical_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    other_allowances = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    # Deductions
    provident_fund = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    tax_deduction = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    other_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    effective_date = models.DateField()
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-effective_date']
    
    def __str__(self):
        return f"{self.employee.full_name} - {self.effective_date}"
    
    @property
    def gross_salary(self):
        return (self.basic_salary + self.house_rent_allowance + 
                self.transport_allowance + self.medical_allowance + 
                self.other_allowances)
    
    @property
    def total_deductions(self):
        return (self.provident_fund + self.tax_deduction + 
                self.other_deductions)
    
    @property
    def net_salary(self):
        return self.gross_salary - self.total_deductions


class Payslip(BaseOrganizationModel):
    """
    Individual payslips for employees
    """
    employee = models.ForeignKey('hrm.Employee', on_delete=models.CASCADE, related_name='payslips')
    payroll_period = models.ForeignKey(PayrollPeriod, on_delete=models.CASCADE, related_name='payslips')
    salary_structure = models.ForeignKey(SalaryStructure, on_delete=models.CASCADE)
    
    # Earnings
    basic_salary = models.DecimalField(max_digits=12, decimal_places=2)
    allowances = models.DecimalField(max_digits=12, decimal_places=2)
    overtime_pay = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    bonus = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    other_earnings = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    # Deductions
    provident_fund = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    tax_deduction = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    late_attendance_deduction = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    other_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    # Calculations
    gross_salary = models.DecimalField(max_digits=12, decimal_places=2)
    total_deductions = models.DecimalField(max_digits=12, decimal_places=2)
    net_salary = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Status
    is_generated = models.BooleanField(default=False)
    generated_at = models.DateTimeField(blank=True, null=True)
    objects = SoftDeleteManager()
    
    class Meta:
        unique_together = ['organization', 'employee', 'payroll_period']
        constraints = [
            UniqueConstraint(
                fields=['organization', 'employee', 'payroll_period'],
                condition=models.Q(deleted_at__isnull=True),
                name='unique_org_code_when_not_deleted'
            )
        ]
        ordering = ['-payroll_period__start_date']
    
    def __str__(self):
        return f"{self.employee.full_name} - {self.payroll_period.name}"
    
    def calculate_totals(self):
        """Calculate gross, deductions, and net salary"""
        # Earnings
        total_earnings = (self.basic_salary + self.allowances + 
                         self.overtime_pay + self.bonus + self.other_earnings)
        
        # Deductions
        total_deductions = (self.provident_fund + self.tax_deduction + 
                           self.late_attendance_deduction + self.other_deductions)
        
        self.gross_salary = total_earnings
        self.total_deductions = total_deductions
        self.net_salary = total_earnings - total_deductions


class PayslipComponent(BaseOrganizationModel):
    """Detailed breakdown of payslip earnings and deductions"""
    payslip = models.ForeignKey(Payslip, on_delete=models.CASCADE, related_name='components')
    payhead = models.ForeignKey(Payhead, on_delete=models.CASCADE, null=True, blank=True)
    
    component_type = models.CharField(max_length=20, choices=[
        ('earning', 'Earning'),
        ('deduction', 'Deduction')
    ])
    component_name = models.CharField(max_length=200)
    component_code = models.CharField(max_length=20)
    calculation_type = models.CharField(max_length=20, default='fixed')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    display_order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['component_type', 'display_order', 'component_name']
    
    def __str__(self):
        return f"{self.component_name}: ₹{self.amount}"



class Allowance(BaseOrganizationModel):
    """
    Allowance types for organization
    """
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    is_taxable = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['organization', 'name']
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.organization.name})"


class Deduction(BaseOrganizationModel):
    """
    Deduction types for organization
    """
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    is_taxable = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['organization', 'name']
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.organization.name})"
