from django.urls import path
from . import views

app_name = 'payroll'

urlpatterns = [
    path('', views.payroll_dashboard, name='payroll_dashboard'),
    path('periods/', views.payroll_periods, name='payroll_periods'),
    path('periods/create/', views.create_payroll_period, name='create_payroll_period'),
    path('periods/<int:pk>/update/', views.update_payroll_period, name='update_payroll_period'),
    path('run-payroll/<int:period_id>/', views.run_payroll, name='run_payroll'),
    path('payslips/', views.payslips, name='payslips'),
    path('payslip/create/', views.payslip_create, name='payslip_create'),
    path('payslip/<int:pk>/update/', views.payslip_update, name='payslip_update'),
    path('payslips/<int:payslip_id>/', views.payslip_detail, name='payslip_detail'),
    path('payslips/<int:payslip_id>/pdf/', views.generate_payslip_pdf, name='generate_payslip_pdf'),
    path('payslips/delete-multiple/', views.delete_multiple_payslips, name='delete_multiple_payslips'),
    path('salary-structures/', views.salary_structures, name='salary_structures'),
    path('allowances/', views.allowances, name='allowances'),
    path('deductions/', views.deductions, name='deductions'),
    path('reports/', views.payroll_reports, name='payroll_reports'),
]
