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
    path('branches/trash/', views.branch_trash, name='branch_trash'),
    path('branches/restore/', views.restore_branch, name='restore_branch'),
    path('branches/delete-multiple/', views.delete_multiple_branches, name='delete_multiple_branches'),

    # Department Management
    path('departments/', views.department_list, name='department_list'),
    path('departments/create/', views.create_department, name='create_department'),
    path('departments/<int:department_id>/update/', views.update_department, name='update_department'),
    path('departments/trash/', views.department_trash, name='department_trash'),
    path('departments/restore/', views.restore_department, name='restore_department'),
    path('departments/delete-multiple/', views.delete_multiple_departments, name='delete_multiple_departments'),

    # Designation Management
    path('designations/', views.designation_list, name='designation_list'),
    path('designations/create/', views.create_designation, name='create_designation'),
    path('designations/<int:designation_id>/update/', views.update_designation, name='update_designation'),
    path('designations/trash/', views.designation_trash, name='designation_trash'),
    path('designations/restore/', views.restore_designation, name='restore_designation'),
    path('designations/delete-multiple/', views.delete_multiple_designations, name='delete_multiple_designations'),

    # Employee Role Management
    path('roles/', views.employee_role_list, name='employee_role_list'),
    path('roles/create/', views.create_employee_role, name='create_employee_role'),
    path('roles/<int:role_id>/update/', views.update_employee_role, name='update_employee_role'),
    path('roles/trash/', views.employee_role_trash, name='employee_role_trash'),
    path('roles/restore/', views.restore_employee_role, name='restore_employee_role'),
    path('roles/delete-multiple/', views.delete_multiple_roles, name='delete_multiple_roles'),

    # Employee Management
    path('employees/', views.employee_list, name='employee_list'),
    path('employees/create/', views.create_employee, name='create_employee'),
    path('employees/<int:employee_id>/', views.employee_detail, name='employee_detail'),
    path('employees/<int:employee_id>/update', views.update_employee, name='update_employee'),
    path('employees/trash/', views.employee_trash, name='employee_trash'),
    path('employees/restore/', views.restore_employee, name='restore_employee'),
    path('employees/delete-multiple/', views.delete_multiple_employees, name='delete_multiple_employees'),

    # Shift Management URLs
    path('shifts/', views.shift_list, name='shift_list'),
    path('shifts/create/', views.create_shift, name='create_shift'),
    path('shifts/<int:shift_id>/update/', views.update_shift, name='update_shift'),
    path('shifts/trash/', views.shift_trash, name='shift_trash'),
    path('shifts/restore/', views.restore_shift, name='restore_shift'),
    path('shifts/delete-multiple/', views.delete_multiple_shifts, name='delete_multiple_shifts'),
    # Timetable Management URLs
    path('timetables/', views.timetable_list, name='timetable_list'),
    path('timetables/create/', views.create_timetable, name='create_timetable'),
    path('timetables/<int:timetable_id>/update/', views.update_timetable, name='update_timetable'),
    path('timetables/trash/', views.timetable_trash, name='timetable_trash'),
    path('timetables/restore/', views.restore_timetable, name='restore_timetable'),
    path('timetables/delete-multiple/', views.delete_multiple_timetables, name='delete_multiple_timetables'),

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
    path('payheads/trash/', views.payhead_trash, name='payhead_trash'),
    path('payheads/restore/', views.restore_payhead, name='restore_payhead'),
    path('payheads/delete-multiple/', views.delete_multiple_payheads, name='delete_multiple_payheads'),

    # Holiday Management URLs
    path('holidays/', views.holiday_list, name='holiday_list'),
    path('holidays/create/', views.create_holiday, name='create_holiday'),
    path('holidays/<int:holiday_id>/update/', views.update_holiday, name='update_holiday'),
    path('holidays/<int:holiday_id>/delete/', views.delete_holiday, name='delete_holiday'),
    path('holidays/trash/', views.holiday_trash, name='holiday_trash'),
    path('holidays/restore/', views.restore_holiday, name='restore_holiday'),
    path('holidays/delete-multiple/', views.delete_multiple_holidays, name='delete_multiple_holidays'),

    # Attendance Management (Legacy)
    path('attendance/', views.attendance_list, name='attendance_list'),
    path('attendance-records/trash/', views.attendance_record_trash, name='attendance_record_trash'),
    path('attendance-records/restore/', views.restore_attendance_record, name='restore_attendance_record'),
    path('attendance-records/delete-multiple/', views.delete_multiple_attendance_records, name='delete_multiple_attendance_records'),


    path('calculate/', views.calculate_attendance_records, name='calculate_attendance'),

    # Leave Management
    path('leaves/', views.leave_list, name='leave_list'),
    path('leaves/create/', views.leave_create, name='leave_create'),
    path('leaves/<int:pk>/update/', views.leave_edit, name='leave_edit'),

    path('leaves/<int:pk>/', views.leave_detail, name='leave_detail'),
    path('leaves/<int:pk>/approve/', views.leave_approve, name='leave_approve'),
    path('leaves/<int:pk>/reject/', views.leave_reject, name='leave_reject'),
    path('leave-requests/trash/', views.leave_request_trash, name='leave_request_trash'),
    path('leave-requests/restore/', views.restore_leave_request, name='restore_leave_request'),
    path('leave-requests/delete-multiple/', views.delete_multiple_leave_requests, name='delete_multiple_leave_requests'),


    path('employee-payheads/', views.employee_payhead_list, name='employee_payhead_list'),
    path('employee-payheads/create/', views.employee_create_payhead, name='employee_create_payhead'),
    path('employee-payheads/<int:employee_payhead_id>/update/', views.employee_update_payhead, name='employee_update_payhead'),
    path('employee-payheads/trash/', views.employee_payhead_trash, name='employee_payhead_trash'),
    path('employee-payheads/restore/', views.restore_employee_payhead, name='restore_employee_payhead'),
    path('employee-payheads/delete-multiple/', views.delete_multiple_employee_payheads, name='delete_multiple_employee_payheads'),

]