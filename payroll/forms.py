from django import forms

from hrm.models import Employee
from .models import PayrollPeriod, Payslip

class PayrollPeriodForm(forms.ModelForm):
    class Meta:
        model = PayrollPeriod
        fields = ['name', 'period_type', 'start_date', 'end_date', 'pay_date', 'status']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'pay_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'period_type': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Period Name'}),
        }


class PayslipForm(forms.ModelForm):
    class Meta:
        model = Payslip
        fields = [
            'employee', 'payroll_period', 'salary_structure',
            'basic_salary', 'allowances', 'overtime_pay', 'bonus', 'other_earnings',
            'provident_fund', 'tax_deduction', 'late_attendance_deduction', 'other_deductions'
        ]
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-control'}),
            'payroll_period': forms.Select(attrs={'class': 'form-control'}),
            'salary_structure': forms.Select(attrs={'class': 'form-control'}),
            'basic_salary': forms.NumberInput(attrs={'class': 'form-control'}),
            'allowances': forms.NumberInput(attrs={'class': 'form-control'}),
            'overtime_pay': forms.NumberInput(attrs={'class': 'form-control'}),
            'bonus': forms.NumberInput(attrs={'class': 'form-control'}),
            'other_earnings': forms.NumberInput(attrs={'class': 'form-control'}),
            'provident_fund': forms.NumberInput(attrs={'class': 'form-control'}),
            'tax_deduction': forms.NumberInput(attrs={'class': 'form-control'}),
            'late_attendance_deduction': forms.NumberInput(attrs={'class': 'form-control'}),
            'other_deductions': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)

        # Filter employee list by organization
        if organization:
            self.fields['employee'].queryset = Employee.objects.filter(
                organization=organization, is_active=True
            ).order_by('id')
