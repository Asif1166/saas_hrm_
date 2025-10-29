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


    # Earnings & Deductions Reports
    path('earnings-breakdown/', views.earnings_breakdown_report, name='earnings_breakdown_report'),
    path('deductions-summary/', views.deductions_summary_report, name='deductions_summary_report'),
    path('payhead-analysis/', views.payhead_analysis_report, name='payhead_analysis_report'),
    
    # Statutory & Compliance Reports
    path('provident-fund/', views.provident_fund_report, name='provident_fund_report'),
    path('tax-deduction/', views.tax_deduction_report, name='tax_deduction_report'),
    path('esi-report/', views.esi_report, name='esi_report'),
    path('gratuity-report/', views.gratuity_report, name='gratuity_report'),
    

    path('bank-transfer/', views.bank_transfer_report, name='bank_transfer_report'),
    path('cash-payment/', views.cash_payment_report, name='cash_payment_report'),
    path('payment-status/', views.payment_status_report, name='payment_status_report'),
    path('payment-reconciliation/', views.payment_reconciliation_report, name='payment_reconciliation_report'),


    # HR Analytics Reports
    path('headcount-analysis/', views.headcount_analysis_report, name='headcount_analysis_report'),
    path('attrition-report/', views.attrition_report, name='attrition_report'),
    path('department-cost-analysis/', views.department_cost_analysis_report, name='department_cost_analysis_report'),
    path('employee-ctc-report/', views.employee_cost_to_company_report, name='employee_cost_to_company_report'),
    
    
    # Payroll Analytics Reports
    path('payroll_analytics_dashboard/', views.payroll_analytics_dashboard, name='analytics_dashboard'),
    path('cost-trends/', views.payroll_cost_trends_report, name='cost_trends_report'),
    path('overtime-analysis/', views.overtime_cost_analysis_report, name='overtime_analysis'),
    path('bonus-analysis/', views.bonus_incentive_analysis_report, name='bonus_analysis'),
    path('tax-projections/', views.tax_liability_projection_report, name='tax_projections'),
    path('api/analytics/', views.payroll_analytics_api, name='analytics_api'),
    
    ]