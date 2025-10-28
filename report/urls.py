from django.urls import path
from . import views

app_name = 'report'

urlpatterns = [
    path('employee-directory/', views.employee_directory_report, name='employee_directory_report'),
    path('employee-profile-summary/', views.employee_profile_summary_report, name='employee_profile_summary_report'),
    path('employee-status/', views.employee_status_report, name='employee_status_report'),
    path('employee-joining/', views.employee_joining_report, name='employee_joining_report'),
    path('employee-exit/', views.employee_exit_report, name='employee_exit_report'),
    
    ]