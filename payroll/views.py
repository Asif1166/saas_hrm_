# payroll/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Sum, Count, Q
from organization.decorators import organization_member_required
from payroll.forms import PayrollPeriodForm, PayslipForm
from .models import PayrollPeriod, Payslip, SalaryStructure, Allowance, Deduction
from hrm.models import Employee
from .services import PayrollProcessor
import json
from django.utils import timezone
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.template.loader import get_template
from django.http import HttpResponse
from xhtml2pdf import pisa

@login_required
@organization_member_required
def payroll_dashboard(request):
    """Payroll Dashboard for organization members"""
    organization = request.organization
    
    # Dashboard statistics
    total_employees = Employee.objects.filter(
        organization=organization, 
        employment_status='active'
    ).count()
    
    recent_periods = PayrollPeriod.objects.filter(
        organization=organization
    ).order_by('-start_date')[:5]
    
    pending_payslips = Payslip.objects.filter(
        organization=organization,
        is_generated=False
    ).count()
    
    # Latest payroll summary
    latest_period = PayrollPeriod.objects.filter(
        organization=organization,
        status='completed'
    ).order_by('-end_date').first()
    
    if latest_period:
        latest_payroll = Payslip.objects.filter(
            payroll_period=latest_period
        ).aggregate(
            total_salary=Sum('net_salary'),
            employee_count=Count('id')
        )
    else:
        latest_payroll = None

    context = {
        'organization': organization,
        'total_employees': total_employees,
        'recent_periods': recent_periods,
        'pending_payslips': pending_payslips,
        'latest_payroll': latest_payroll,
        'latest_period': latest_period,
    }
    return render(request, 'payroll/dashboard.html', context)


@login_required
@organization_member_required
def payroll_periods(request):
    """Manage payroll periods for the organization"""
    organization = request.organization
    
    periods = PayrollPeriod.objects.filter(
        organization=organization
    ).order_by('-start_date')
    
    if request.method == 'POST':
        # Handle period creation
        name = request.POST.get('name')
        period_type = request.POST.get('period_type')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        pay_date = request.POST.get('pay_date')
        
        try:
            period = PayrollPeriod.objects.create(
                organization=organization,
                name=name,
                period_type=period_type,
                start_date=start_date,
                end_date=end_date,
                pay_date=pay_date,
                created_by=request.user
            )
            messages.success(request, f'Payroll period "{name}" created successfully!')
            return redirect('payroll_periods')
        except Exception as e:
            messages.error(request, f'Error creating payroll period: {str(e)}')
    
    context = {
        'organization': organization,
        'periods': periods,
    }
    return render(request, 'payroll/periods.html', context)


@login_required
@organization_member_required
def create_payroll_period(request):
    """Create a new payroll period"""
    organization = request.organization
    form = PayrollPeriodForm(request.POST or None)
    
    if request.method == 'POST':
        if form.is_valid():
            period = form.save(commit=False)
            period.organization = organization
            period.created_by = request.user
            period.save()
            messages.success(request, f'Payroll period "{period.name}" created successfully!')
            return redirect('payroll_periods')
        else:
            messages.error(request, 'Please correct the errors below.')

    context = {
        'form': form,
        'is_update': False,
    }
    return render(request, 'payroll/period_form.html', context)


@login_required
@organization_member_required
def update_payroll_period(request, pk):
    """Update an existing payroll period"""
    organization = request.organization
    period = get_object_or_404(PayrollPeriod, pk=pk, organization=organization)
    form = PayrollPeriodForm(request.POST or None, instance=period)

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, f'Payroll period "{period.name}" updated successfully!')
            return redirect('payroll_periods')
        else:
            messages.error(request, 'Please correct the errors below.')

    context = {
        'form': form,
        'is_update': True,
        'period': period,
    }
    return render(request, 'payroll/period_form.html', context)

@login_required
@organization_member_required
def run_payroll(request, period_id):
    """Run payroll for a specific period"""
    organization = request.organization
    period = get_object_or_404(PayrollPeriod, id=period_id, organization=organization)
    
    if request.method == 'POST':
        processor = PayrollProcessor(organization)
        success, result = processor.run_payroll(period_id)
        
        if success:
            if result.get('status') == 'completed':
                messages.success(request, 
                    f'Payroll run completed successfully! Created {result["payslips_created"]} payslips for {result["total_employees"]} employees.'
                )
            else:  # partial success
                messages.warning(request, 
                    f'Payroll run completed with some issues. Created {result["payslips_created"]} out of {result["total_employees"]} payslips.'
                )
                if result['errors']:
                    for error in result['errors'][:5]:  # Show first 5 errors
                        messages.error(request, error)
                    if len(result['errors']) > 5:
                        messages.info(request, f'... and {len(result["errors"]) - 5} more errors')
        else:
            messages.error(request, result)
        
        return redirect('payroll:payroll_periods')
    
    # Get employee count and existing payslips for confirmation
    employee_count = Employee.objects.filter(
        organization=organization,
        employment_status='active',
        is_active=True
    ).count()
    
    existing_payslips = Payslip.objects.filter(
        payroll_period=period,
        organization=organization
    ).count()
    
    context = {
        'organization': organization,
        'period': period,
        'employee_count': employee_count,
        'existing_payslips': existing_payslips,
    }
    return render(request, 'payroll/run_payroll.html', context)

# Add this new view for payroll summary
@login_required
@organization_member_required
def payroll_summary(request, period_id):
    """Get payroll summary for a period"""
    organization = request.organization
    period = get_object_or_404(PayrollPeriod, id=period_id, organization=organization)
    
    processor = PayrollProcessor(organization)
    success, result = processor.get_payroll_summary(period_id)
    
    if success:
        return JsonResponse({
            'success': True,
            'summary': result
        })
    else:
        return JsonResponse({
            'success': False,
            'message': result
        }, status=400)




@login_required
@organization_member_required
def payslips(request):
    """Manage payslips for the organization"""
    organization = request.organization

    # Filter parameters
    period_id = request.GET.get('period')
    employee_id = request.GET.get('employee')
    status = request.GET.get('status')

    payslips = Payslip.objects.filter(organization=organization)

    # Apply filters
    if period_id:
        payslips = payslips.filter(payroll_period_id=period_id)
    if employee_id:
        payslips = payslips.filter(employee_id=employee_id)
    if status:
        payslips = payslips.filter(is_generated=(status == 'generated'))

    payslips = payslips.select_related('employee', 'payroll_period').order_by('-payroll_period__start_date')

    # Pagination setup
    paginator = Paginator(payslips, 10)  # show 10 payslips per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Available filters
    periods = PayrollPeriod.objects.filter(organization=organization)
    employees = Employee.objects.filter(organization=organization, employment_status='active')

    context = {
        'organization': organization,
        'page_obj': page_obj,  # pagination object
        'periods': periods,
        'employees': employees,
        'period_filter': period_id,
        'employee_filter': employee_id,
        'status_filter': status,
    }
    return render(request, 'payroll/payslips.html', context)

def payslip_create(request):
    if request.method == "POST":
        form = PayslipForm(request.POST, organization=request.organization)
        if form.is_valid():
            payslip = form.save(commit=False)
            payslip.organization = request.organization
            payslip.calculate_totals()
            payslip.save()
            messages.success(request, "Payslip created successfully!")
            return redirect('payroll:payslips')
    else:
        form = PayslipForm(organization=request.organization)

    return render(request, 'payroll/payslip_form.html', {'form': form, 'is_update': False})


def payslip_update(request, pk):
    payslip = get_object_or_404(Payslip, pk=pk, organization=request.organization)

    if request.method == "POST":
        form = PayslipForm(request.POST, instance=payslip, organization=request.organization)
        if form.is_valid():
            payslip = form.save(commit=False)
            payslip.calculate_totals()
            payslip.save()
            messages.success(request, "Payslip updated successfully!")
            return redirect('payroll:payslips')
    else:
        form = PayslipForm(instance=payslip, organization=request.organization)

    return render(request, 'payroll/payslip_form.html', {'form': form, 'is_update': True})

@login_required
@organization_member_required
def payslip_detail(request, payslip_id):
    """View individual payslip details"""
    organization = request.organization
    payslip = get_object_or_404(
        Payslip, 
        id=payslip_id, 
        organization=organization
    )
    
    context = {
        'organization': organization,
        'payslip': payslip,
    }
    return render(request, 'payroll/payslip_detail.html', context)


@login_required
@organization_member_required
def generate_payslip_pdf(request, payslip_id):
    """Generate PDF for individual payslip"""
    organization = request.organization
    payslip = get_object_or_404(Payslip, id=payslip_id, organization=organization)

    # Mark as generated
    if not payslip.is_generated:
        payslip.is_generated = True
        payslip.generated_at = timezone.now()
        payslip.save()

    # Load template
    template_path = 'payroll/payslip_pdf.html'
    context = {'payslip': payslip, 'organization': organization}
    template = get_template(template_path)
    html = template.render(context)

    # Create PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'filename="Payslip_{payslip.employee.full_name}.pdf"'

    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        messages.error(request, "Error generating PDF.")
        return redirect('payroll:payslip_detail', payslip_id=payslip_id)

    return response



@login_required
@organization_member_required
def delete_multiple_payslips(request):
    """Delete multiple payslips"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            ids = data.get('ids', [])
            if not ids:
                return JsonResponse({'success': False, 'message': 'No payslips selected.'})

            Payslip.objects.filter(id__in=ids, organization=request.organization).delete()
            return JsonResponse({'success': True, 'message': f'{len(ids)} payslip(s) deleted successfully.'})

        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

    return JsonResponse({'success': False, 'message': 'Invalid request method.'})
    
@login_required
@organization_member_required
def salary_structures(request):
    """Manage salary structures for the organization"""
    organization = request.organization
    
    salary_structures = SalaryStructure.objects.filter(
        organization=organization,
        is_active=True
    ).select_related('employee').order_by('-effective_date')
    
    employees = Employee.objects.filter(
        organization=organization,
        employment_status='active'
    )
    
    if request.method == 'POST':
        employee_id = request.POST.get('employee')
        basic_salary = request.POST.get('basic_salary')
        effective_date = request.POST.get('effective_date')
        
        try:
            employee = Employee.objects.get(id=employee_id, organization=organization)
            
            # Deactivate previous structure
            SalaryStructure.objects.filter(
                employee=employee,
                is_active=True
            ).update(is_active=False)
            
            # Create new structure
            SalaryStructure.objects.create(
                organization=organization,
                employee=employee,
                basic_salary=basic_salary,
                effective_date=effective_date,
                created_by=request.user
            )
            
            messages.success(request, f'Salary structure updated for {employee.full_name}')
            return redirect('salary_structures')
            
        except Exception as e:
            messages.error(request, f'Error creating salary structure: {str(e)}')
    
    context = {
        'organization': organization,
        'salary_structures': salary_structures,
        'employees': employees,
    }
    return render(request, 'payroll/salary_structures.html', context)


@login_required
@organization_member_required
def allowances(request):
    """Manage allowances for the organization"""
    organization = request.organization
    
    allowances_list = Allowance.objects.filter(organization=organization)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        is_taxable = request.POST.get('is_taxable') == 'on'
        
        try:
            Allowance.objects.create(
                organization=organization,
                name=name,
                description=description,
                is_taxable=is_taxable,
                created_by=request.user
            )
            messages.success(request, f'Allowance "{name}" created successfully!')
            return redirect('allowances')
        except Exception as e:
            messages.error(request, f'Error creating allowance: {str(e)}')
    
    context = {
        'organization': organization,
        'allowances': allowances_list,
    }
    return render(request, 'payroll/allowances.html', context)


@login_required
@organization_member_required
def deductions(request):
    """Manage deductions for the organization"""
    organization = request.organization
    
    deductions_list = Deduction.objects.filter(organization=organization)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        is_taxable = request.POST.get('is_taxable') == 'on'
        
        try:
            Deduction.objects.create(
                organization=organization,
                name=name,
                description=description,
                is_taxable=is_taxable,
                created_by=request.user
            )
            messages.success(request, f'Deduction "{name}" created successfully!')
            return redirect('deductions')
        except Exception as e:
            messages.error(request, f'Error creating deduction: {str(e)}')
    
    context = {
        'organization': organization,
        'deductions': deductions_list,
    }
    return render(request, 'payroll/deductions.html', context)


@login_required
@organization_member_required
def payroll_reports(request):
    """Payroll reports and analytics"""
    organization = request.organization
    
    # Report parameters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    report_type = request.GET.get('report_type', 'summary')
    
    # Base queryset
    payslips = Payslip.objects.filter(
        organization=organization,
        is_generated=True
    )
    
    if start_date and end_date:
        payslips = payslips.filter(
            payroll_period__start_date__gte=start_date,
            payroll_period__end_date__lte=end_date
        )
    
    # Generate report data based on type
    if report_type == 'summary':
        report_data = payslips.aggregate(
            total_net_salary=Sum('net_salary'),
            total_gross_salary=Sum('gross_salary'),
            total_deductions=Sum('total_deductions'),
            total_payslips=Count('id')
        )
    elif report_type == 'employee_wise':
        report_data = payslips.values(
            'employee__first_name', 
            'employee__last_name',
            'employee__employee_id'
        ).annotate(
            total_salary=Sum('net_salary'),
            payslip_count=Count('id')
        ).order_by('-total_salary')
    
    periods = PayrollPeriod.objects.filter(organization=organization)
    
    context = {
        'organization': organization,
        'report_data': report_data,
        'report_type': report_type,
        'periods': periods,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'payroll/reports.html', context)