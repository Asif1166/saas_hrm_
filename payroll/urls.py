from django.urls import path
from . import views

app_name = 'payroll'

urlpatterns = [
    path('', views.payroll_dashboard, name='dashboard'),
    path('periods/', views.payroll_periods, name='periods'),
    path('payslips/', views.payslips, name='payslips'),
    path('salary-structures/', views.salary_structures, name='salary_structures'),
    path('allowances/', views.allowances, name='allowances'),
    path('deductions/', views.deductions, name='deductions'),
]
