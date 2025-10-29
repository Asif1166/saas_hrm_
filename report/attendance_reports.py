# reports/attendance_reports.py
from django.db.models import Q, Count, Sum, Avg, Max
from django.utils import timezone
from datetime import datetime, date, timedelta
from django.db.models.functions import TruncDate, TruncMonth
from hrm.models import Employee, Department, AttendanceRecord, LeaveRequest

class DailyAttendanceReport:
    def generate_daily_report(self, organization, filters=None):
        """
        Generate daily attendance report
        """
        filters = filters or {}
        target_date = filters.get('date') or timezone.now().date()
        
        # Get all employees for the organization
        employees = Employee.objects.filter(
            organization=organization,
            is_active=True
        ).select_related('department', 'designation')
        
        # Apply department filter
        if filters.get('department'):
            employees = employees.filter(department_id=filters['department'])
        
        daily_attendance = []
        present_count = 0
        absent_count = 0
        late_count = 0
        half_day_count = 0
        
        for employee in employees:
            # Get attendance record for the day
            attendance = AttendanceRecord.objects.filter(
                employee=employee,
                date=target_date
            ).first()
            
            if attendance:
                status = attendance.status
                check_in = attendance.check_in_time.strftime('%H:%M') if attendance.check_in_time else 'N/A'
                check_out = attendance.check_out_time.strftime('%H:%M') if attendance.check_out_time else 'N/A'
                working_hours = attendance.working_hours
                late_minutes = attendance.late_minutes
            else:
                status = 'absent'
                check_in = 'N/A'
                check_out = 'N/A'
                working_hours = 0
                late_minutes = 0
            
            # Count statuses
            if status == 'present':
                present_count += 1
            elif status == 'absent':
                absent_count += 1
            elif status == 'late':
                late_count += 1
            elif status == 'half_day':
                half_day_count += 1
            
            daily_attendance.append({
                'employee_id': employee.employee_id,
                'full_name': employee.full_name,
                'department': employee.department.name if employee.department else 'N/A',
                'designation': employee.designation.name if employee.designation else 'N/A',
                'status': status,
                'check_in': check_in,
                'check_out': check_out,
                'working_hours': working_hours,
                'late_minutes': late_minutes,
                'is_late': attendance.is_late if attendance else False,
                'is_early_departure': attendance.is_early_departure if attendance else False
            })
        
        return {
            'report_name': 'Daily Attendance Report',
            'generated_on': timezone.now().strftime('%d-%m-%Y %H:%M:%S'),
            'target_date': target_date.strftime('%d-%m-%Y'),
            'filters': filters,
            'summary': {
                'total_employees': len(daily_attendance),
                'present_count': present_count,
                'absent_count': absent_count,
                'late_count': late_count,
                'half_day_count': half_day_count,
                'present_percentage': round((present_count / len(daily_attendance) * 100), 2) if daily_attendance else 0
            },
            'attendance_data': daily_attendance
        }

class MonthlyAttendanceSummary:
    def generate_monthly_summary(self, organization, filters=None):
        """
        Generate monthly attendance summary
        """
        filters = filters or {}
        year = int(filters.get('year') or timezone.now().year)
        month = int(filters.get('month') or timezone.now().month)
        
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
        
        # Get attendance records for the month
        attendance_records = AttendanceRecord.objects.filter(
            employee__organization=organization,
            date__range=[start_date, end_date]
        ).select_related('employee', 'employee__department')
        
        # Apply department filter
        if filters.get('department'):
            attendance_records = attendance_records.filter(employee__department_id=filters['department'])
        
        # Monthly statistics
        total_working_days = (end_date - start_date).days + 1
        weekdays = sum(1 for i in range(total_working_days) 
                      if (start_date + timedelta(days=i)).weekday() < 5)
        
        # Employee-wise summary
        employee_summary = []
        employees = Employee.objects.filter(organization=organization, is_active=True)
        
        if filters.get('department'):
            employees = employees.filter(department_id=filters['department'])
        
        for employee in employees:
            emp_records = attendance_records.filter(employee=employee)
            
            present_days = emp_records.filter(status__in=['present', 'late']).count()
            absent_days = emp_records.filter(status='absent').count()
            late_days = emp_records.filter(status='late').count()
            half_days = emp_records.filter(status='half_day').count()
            
            total_working_hours = emp_records.aggregate(total=Sum('working_hours'))['total'] or 0
            total_overtime = emp_records.aggregate(total=Sum('overtime_hours'))['total'] or 0
            avg_working_hours = emp_records.aggregate(avg=Avg('working_hours'))['avg'] or 0
            
            attendance_percentage = round((present_days / weekdays * 100), 2) if weekdays > 0 else 0
            
            employee_summary.append({
                'employee_id': employee.employee_id,
                'full_name': employee.full_name,
                'department': employee.department.name if employee.department else 'N/A',
                'present_days': present_days,
                'absent_days': absent_days,
                'late_days': late_days,
                'half_days': half_days,
                'total_working_hours': round(total_working_hours, 2),
                'total_overtime': round(total_overtime, 2),
                'avg_working_hours': round(avg_working_hours, 2),
                'attendance_percentage': attendance_percentage
            })
        
        # Department-wise summary
        department_summary = []
        departments = Department.objects.filter(organization=organization, is_active=True)
        
        for dept in departments:
            dept_employees = employees.filter(department=dept)
            dept_records = attendance_records.filter(employee__department=dept)
            
            if dept_employees.exists():
                dept_present = dept_records.filter(status__in=['present', 'late']).count()
                dept_absent = dept_records.filter(status='absent').count()
                dept_attendance_percentage = round((dept_present / (dept_present + dept_absent) * 100), 2) if (dept_present + dept_absent) > 0 else 0
                
                department_summary.append({
                    'department': dept.name,
                    'employee_count': dept_employees.count(),
                    'present_days': dept_present,
                    'absent_days': dept_absent,
                    'attendance_percentage': dept_attendance_percentage
                })
        
        return {
            'report_name': 'Monthly Attendance Summary',
            'generated_on': timezone.now().strftime('%d-%m-%Y %H:%M:%S'),
            'period': f"{start_date.strftime('%B %Y')}",
            'filters': filters,
            'summary': {
                'total_employees': employees.count(),
                'total_working_days': weekdays,
                'period': f"{start_date.strftime('%d %b %Y')} to {end_date.strftime('%d %b %Y')}"
            },
            'employee_summary': employee_summary,
            'department_summary': department_summary
        }

class LateComingReport:
    def generate_late_report(self, organization, filters=None):
        """
        Generate late coming report
        """
        filters = filters or {}
        start_date = filters.get('start_date') or (timezone.now() - timedelta(days=30)).date()
        end_date = filters.get('end_date') or timezone.now().date()
        
        # Get late attendance records
        late_records = AttendanceRecord.objects.filter(
            employee__organization=organization,
            date__range=[start_date, end_date],
            is_late=True
        ).select_related('employee', 'employee__department')
        
        # Apply department filter
        if filters.get('department'):
            late_records = late_records.filter(employee__department_id=filters['department'])
        
        # Employee-wise late summary
        employee_late_summary = late_records.values(
            'employee__id',
            'employee__employee_id',
            'employee__first_name',
            'employee__last_name',
            'employee__department__name'
        ).annotate(
            total_late=Count('id'),
            avg_late_minutes=Avg('late_minutes'),
            max_late_minutes=Max('late_minutes')
        ).order_by('-total_late')
        
        late_employees = []
        for emp in employee_late_summary:
            late_employees.append({
                'employee_id': emp['employee__employee_id'],
                'full_name': f"{emp['employee__first_name']} {emp['employee__last_name']}",
                'department': emp['employee__department__name'],
                'total_late_days': emp['total_late'],
                'avg_late_minutes': round(emp['avg_late_minutes'] or 0, 1),
                'max_late_minutes': emp['max_late_minutes'] or 0
            })
        
        # Daily late trend
        daily_late_trend = late_records.values('date').annotate(
            late_count=Count('id'),
            avg_late=Avg('late_minutes')
        ).order_by('date')
        
        return {
            'report_name': 'Late Coming Report',
            'generated_on': timezone.now().strftime('%d-%m-%Y %H:%M:%S'),
            'filters': filters,
            'period': f"{start_date} to {end_date}",
            'summary': {
                'total_late_occurrences': late_records.count(),
                'total_late_employees': len(late_employees),
                'period': f"{start_date} to {end_date}"
            },
            'late_employees': late_employees,
            'daily_trend': list(daily_late_trend)
        }

class EarlyDepartureReport:
    def generate_early_departure_report(self, organization, filters=None):
        """
        Generate early departure report
        """
        filters = filters or {}
        start_date = filters.get('start_date') or (timezone.now() - timedelta(days=30)).date()
        end_date = filters.get('end_date') or timezone.now().date()
        
        # Get early departure records
        early_records = AttendanceRecord.objects.filter(
            employee__organization=organization,
            date__range=[start_date, end_date],
            is_early_departure=True
        ).select_related('employee', 'employee__department')
        
        # Apply department filter
        if filters.get('department'):
            early_records = early_records.filter(employee__department_id=filters['department'])
        
        # Employee-wise early departure summary
        employee_early_summary = early_records.values(
            'employee__id',
            'employee__employee_id',
            'employee__first_name',
            'employee__last_name',
            'employee__department__name'
        ).annotate(
            total_early=Count('id'),
            avg_early_minutes=Avg('early_departure_minutes'),
            max_early_minutes=Max('early_departure_minutes')
        ).order_by('-total_early')
        
        early_employees = []
        for emp in employee_early_summary:
            early_employees.append({
                'employee_id': emp['employee__employee_id'],
                'full_name': f"{emp['employee__first_name']} {emp['employee__last_name']}",
                'department': emp['employee__department__name'],
                'total_early_days': emp['total_early'],
                'avg_early_minutes': round(emp['avg_early_minutes'] or 0, 1),
                'max_early_minutes': emp['max_early_minutes'] or 0
            })
        
        return {
            'report_name': 'Early Departure Report',
            'generated_on': timezone.now().strftime('%d-%m-%Y %H:%M:%S'),
            'filters': filters,
            'period': f"{start_date} to {end_date}",
            'summary': {
                'total_early_occurrences': early_records.count(),
                'total_early_employees': len(early_employees),
                'period': f"{start_date} to {end_date}"
            },
            'early_employees': early_employees
        }

class OvertimeReport:
    def generate_overtime_report(self, organization, filters=None):
        """
        Generate overtime report
        """
        filters = filters or {}
        start_date = filters.get('start_date') or (timezone.now() - timedelta(days=30)).date()
        end_date = filters.get('end_date') or timezone.now().date()
        
        # Get overtime records
        overtime_records = AttendanceRecord.objects.filter(
            employee__organization=organization,
            date__range=[start_date, end_date],
            overtime_hours__gt=0
        ).select_related('employee', 'employee__department')
        
        # Apply department filter
        if filters.get('department'):
            overtime_records = overtime_records.filter(employee__department_id=filters['department'])
        
        # Employee-wise overtime summary
        employee_overtime_summary = overtime_records.values(
            'employee__id',
            'employee__employee_id',
            'employee__first_name',
            'employee__last_name',
            'employee__department__name'
        ).annotate(
            total_overtime_days=Count('id'),
            total_overtime_hours=Sum('overtime_hours'),
            avg_overtime_hours=Avg('overtime_hours')
        ).order_by('-total_overtime_hours')
        
        overtime_employees = []
        for emp in employee_overtime_summary:
            overtime_employees.append({
                'employee_id': emp['employee__employee_id'],
                'full_name': f"{emp['employee__first_name']} {emp['employee__last_name']}",
                'department': emp['employee__department__name'],
                'total_overtime_days': emp['total_overtime_days'],
                'total_overtime_hours': round(emp['total_overtime_hours'] or 0, 2),
                'avg_overtime_hours': round(emp['avg_overtime_hours'] or 0, 2)
            })
        
        # Department-wise overtime summary
        department_overtime = overtime_records.values('employee__department__name').annotate(
            total_hours=Sum('overtime_hours'),
            employee_count=Count('employee', distinct=True)
        ).order_by('-total_hours')
        
        # Monthly overtime trend
        monthly_trend = overtime_records.annotate(
            month=TruncMonth('date')
        ).values('month').annotate(
            total_hours=Sum('overtime_hours'),
            record_count=Count('id')
        ).order_by('month')
        
        return {
            'report_name': 'Overtime Report',
            'generated_on': timezone.now().strftime('%d-%m-%Y %H:%M:%S'),
            'filters': filters,
            'period': f"{start_date} to {end_date}",
            'summary': {
                'total_overtime_hours': round(overtime_records.aggregate(total=Sum('overtime_hours'))['total'] or 0, 2),
                'total_overtime_days': overtime_records.count(),
                'employees_with_overtime': len(overtime_employees),
                'period': f"{start_date} to {end_date}"
            },
            'employee_overtime': overtime_employees,
            'department_overtime': list(department_overtime),
            'monthly_trend': list(monthly_trend)
        }

class LeaveBalanceReport:
    def generate_leave_balance_report(self, organization, filters=None):
        """
        Generate leave balance report
        """
        # This is a simplified version - you'll need to integrate with your actual leave management system
        filters = filters or {}
        
        employees = Employee.objects.filter(
            organization=organization,
            is_active=True
        ).select_related('department')
        
        # Apply department filter
        if filters.get('department'):
            employees = employees.filter(department_id=filters['department'])
        
        leave_balances = []
        
        for employee in employees:
            # Get approved leave requests (you'll need to adjust this based on your leave system)
            approved_leaves = LeaveRequest.objects.filter(
                employee=employee,
                status='approved'
            )
            
            # Calculate leave usage (simplified)
            sick_leave_taken = approved_leaves.filter(leave_type='sick').count()
            vacation_leave_taken = approved_leaves.filter(leave_type='vacation').count()
            personal_leave_taken = approved_leaves.filter(leave_type='personal').count()
            
            # Default leave entitlements (adjust based on your policy)
            sick_leave_entitlement = 14  # days per year
            vacation_leave_entitlement = 21  # days per year
            personal_leave_entitlement = 7   # days per year
            
            leave_balances.append({
                'employee_id': employee.employee_id,
                'full_name': employee.full_name,
                'department': employee.department.name if employee.department else 'N/A',
                'sick_leave_balance': sick_leave_entitlement - sick_leave_taken,
                'vacation_leave_balance': vacation_leave_entitlement - vacation_leave_taken,
                'personal_leave_balance': personal_leave_entitlement - personal_leave_taken,
                'total_balance': (sick_leave_entitlement + vacation_leave_entitlement + personal_leave_entitlement) - 
                               (sick_leave_taken + vacation_leave_taken + personal_leave_taken)
            })
        
        return {
            'report_name': 'Leave Balance Report',
            'generated_on': timezone.now().strftime('%d-%m-%Y %H:%M:%S'),
            'filters': filters,
            'summary': {
                'total_employees': len(leave_balances),
                'employees_with_leave': len([lb for lb in leave_balances if lb['total_balance'] > 0])
            },
            'leave_balances': leave_balances
        }

class LeaveUtilizationReport:
    def generate_leave_utilization_report(self, organization, filters=None):
        """
        Generate leave utilization report
        """
        filters = filters or {}
        year = int(filters.get('year') or timezone.now().year)
        
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)
        
        # Get leave requests for the year
        leave_requests = LeaveRequest.objects.filter(
            employee__organization=organization,
            start_date__year=year,
            status='approved'
        ).select_related('employee', 'employee__department')
        
        # Apply department filter
        if filters.get('department'):
            leave_requests = leave_requests.filter(employee__department_id=filters['department'])
        
        # Leave type summary
        leave_type_summary = leave_requests.values('leave_type').annotate(
            total_days=Sum('days_requested'),
            total_requests=Count('id'),
            avg_days=Avg('days_requested')
        ).order_by('-total_days')
        
        # Monthly leave trend
        monthly_trend = leave_requests.annotate(
            month=TruncMonth('start_date')
        ).values('month').annotate(
            total_days=Sum('days_requested'),
            total_requests=Count('id')
        ).order_by('month')
        
        # Department-wise leave utilization
        department_leave = leave_requests.values('employee__department__name').annotate(
            total_days=Sum('days_requested'),
            employee_count=Count('employee', distinct=True),
            avg_days_per_employee=Avg('days_requested')
        ).order_by('-total_days')
        
        return {
            'report_name': 'Leave Utilization Report',
            'generated_on': timezone.now().strftime('%d-%m-%Y %H:%M:%S'),
            'filters': filters,
            'year': year,
            'summary': {
                'total_leave_days': leave_requests.aggregate(total=Sum('days_requested'))['total'] or 0,
                'total_leave_requests': leave_requests.count(),
                'employees_on_leave': leave_requests.values('employee').distinct().count()
            },
            'leave_type_summary': list(leave_type_summary),
            'monthly_trend': list(monthly_trend),
            'department_leave': list(department_leave)
        }