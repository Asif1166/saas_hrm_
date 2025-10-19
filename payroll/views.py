from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from organization.decorators import organization_member_required


@login_required
@organization_member_required
def payroll_dashboard(request):
    """Payroll Dashboard for organization members"""
    context = {
        'organization': request.organization,
    }
    return render(request, 'payroll/dashboard.html', context)


@login_required
@organization_member_required
def payroll_periods(request):
    """Manage payroll periods for the organization"""
    context = {
        'organization': request.organization,
    }
    return render(request, 'payroll/periods.html', context)


@login_required
@organization_member_required
def payslips(request):
    """Manage payslips for the organization"""
    context = {
        'organization': request.organization,
    }
    return render(request, 'payroll/payslips.html', context)


@login_required
@organization_member_required
def salary_structures(request):
    """Manage salary structures for the organization"""
    context = {
        'organization': request.organization,
    }
    return render(request, 'payroll/salary_structures.html', context)


@login_required
@organization_member_required
def allowances(request):
    """Manage allowances for the organization"""
    context = {
        'organization': request.organization,
    }
    return render(request, 'payroll/allowances.html', context)


@login_required
@organization_member_required
def deductions(request):
    """Manage deductions for the organization"""
    context = {
        'organization': request.organization,
    }
    return render(request, 'payroll/deductions.html', context)
