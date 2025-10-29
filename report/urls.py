from django.urls import path
from . import views

app_name = 'report'

urlpatterns = [
    path('employee-directory/', views.employee_directory_report, name='employee_directory_report'),
    path('employee-profile-summary/', views.employee_profile_summary_report, name='employee_profile_summary_report'),
    path('employee-status/', views.employee_status_report, name='employee_status_report'),
    path('employee-joining/', views.employee_joining_report, name='employee_joining_report'),
    path('employee-exit/', views.employee_exit_report, name='employee_exit_report'),



    path('daily-attendance/', views.daily_attendance_report, name='daily_attendance_report'),
    path('monthly-attendance-summary/', views.monthly_attendance_summary, name='monthly_attendance_summary'),
    path('late-coming/', views.late_coming_report, name='late_coming_report'),
    path('early-departure/', views.early_departure_report, name='early_departure_report'),
    path('overtime/', views.overtime_report, name='overtime_report'),
    path('leave-balance/', views.leave_balance_report, name='leave_balance_report'),
    path('leave-utilization/', views.leave_utilization_report, name='leave_utilization_report'),


    # Payroll Reports
    path('payroll-register/', views.payroll_register_report, name='payroll_register_report'),
    path('payroll-summary/', views.payroll_summary_report, name='payroll_summary_report'),
    path('payroll-variance/', views.payroll_variance_report, name='payroll_variance_report'),


    # Salary Reports
    path('salary-structure/', views.salary_structure_report, name='salary_structure_report'),
    path('salary-revision/', views.salary_revision_report, name='salary_revision_report'),
    path('comparative-salary/', views.comparative_salary_report, name='comparative_salary_report'),
    
    ]