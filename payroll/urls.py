from django.urls import path
from . import views

app_name = 'payroll'

urlpatterns = [
    path('', views.payroll_dashboard, name='payroll_dashboard'),
    path('periods/', views.payroll_periods, name='payroll_periods'),
    path('run-payroll/<int:period_id>/', views.run_payroll, name='run_payroll'),
    path('payslips/', views.payslips, name='payslips'),
    path('payslips/<int:payslip_id>/', views.payslip_detail, name='payslip_detail'),
    path('payslips/<int:payslip_id>/pdf/', views.generate_payslip_pdf, name='generate_payslip_pdf'),
    path('salary-structures/', views.salary_structures, name='salary_structures'),
    path('allowances/', views.allowances, name='allowances'),
    path('deductions/', views.deductions, name='deductions'),
    path('reports/', views.payroll_reports, name='payroll_reports'),
]
