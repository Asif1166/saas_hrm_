from django.urls import path
from . import views

app_name = 'hrm'

urlpatterns = [
    # Dashboard
    path('', views.hrm_dashboard, name='dashboard'),
    path('employee-dashboard/', views.employee_dashboard, name='employee_dashboard'),
    
    # Branch Management
    path('branches/', views.branch_list, name='branch_list'),
    path('branches/create/', views.create_branch, name='create_branch'),
    path('branches/<int:branch_id>/update/', views.update_branch, name='update_branch'),
    
    # Department Management
    path('departments/', views.department_list, name='department_list'),
    path('departments/create/', views.create_department, name='create_department'),
    path('departments/<int:department_id>/update/', views.update_department, name='update_department'),
    
    # Designation Management
    path('designations/', views.designation_list, name='designation_list'),
    path('designations/create/', views.create_designation, name='create_designation'),
    path('designations/<int:designation_id>/update/', views.update_designation, name='update_designation'),
    
    # Employee Role Management
    path('roles/', views.employee_role_list, name='employee_role_list'),
    path('roles/create/', views.create_employee_role, name='create_employee_role'),
    path('roles/<int:role_id>/update/', views.update_employee_role, name='update_employee_role'),
    
    # Employee Management
    path('employees/', views.employee_list, name='employee_list'),
    path('employees/create/', views.create_employee, name='create_employee'),
    path('employees/<int:employee_id>/', views.employee_detail, name='employee_detail'),
    path('employees/<int:employee_id>/update', views.update_employee, name='update_employee'),
    
    # Shift Management URLs
    path('shifts/', views.shift_list, name='shift_list'),
    path('shifts/create/', views.create_shift, name='create_shift'),
    path('shifts/<int:shift_id>/update/', views.update_shift, name='update_shift'),
    
    # Timetable Management URLs
    path('timetables/', views.timetable_list, name='timetable_list'),
    path('timetables/create/', views.create_timetable, name='create_timetable'),
    path('timetables/<int:timetable_id>/update/', views.update_timetable, name='update_timetable'),
    
    # Attendance Device Management URLs
    path('devices/', views.attendance_device_list, name='attendance_device_list'),
    path('devices/create/', views.create_attendance_device, name='create_attendance_device'),
    path('devices/<int:device_id>/update/', views.update_attendance_device, name='update_attendance_device'),
    path('devices/<int:device_id>/test/', views.test_device_connection_view, name='test_device_connection'),
    path('devices/<int:device_id>/diagnose/', views.diagnose_device_view, name='diagnose_device'),
    path('devices/<int:device_id>/sync/', views.sync_device_data, name='sync_device_data'),
    
    # Attendance Records URLs
    path('attendance-records/', views.attendance_record_list, name='attendance_record_list'),
    
    # Payhead Management URLs
    path('payheads/', views.payhead_list, name='payhead_list'),
    path('payheads/create/', views.create_payhead, name='create_payhead'),
    path('payheads/<int:payhead_id>/update/', views.update_payhead, name='update_payhead'),
    path('payheads/<int:pk>/delete/', views.payhead_delete, name='payhead_delete'),

    # Holiday Management URLs
    path('holidays/', views.holiday_list, name='holiday_list'),
    path('holidays/create/', views.create_holiday, name='create_holiday'),
    path('holidays/<int:holiday_id>/update/', views.update_holiday, name='update_holiday'),
    path('holidays/<int:holiday_id>/delete/', views.delete_holiday, name='delete_holiday'),

    # Attendance Management (Legacy)
    path('attendance/', views.attendance_list, name='attendance_list'),
    
    # Leave Management
    path('leaves/', views.leave_list, name='leave_list'),
    path('leaves/<int:pk>/', views.leave_detail, name='leave_detail'),
    path('leaves/<int:pk>/approve/', views.leave_approve, name='leave_approve'),
    path('leaves/<int:pk>/reject/', views.leave_reject, name='leave_reject'),
]