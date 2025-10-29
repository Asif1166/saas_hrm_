from django.db.models import Q, Count, Sum, Avg, Min, Max
from django.utils import timezone
from datetime import datetime, date, timedelta
from payroll.models import Payslip, PayrollPeriod, SalaryStructure, PayslipComponent
from hrm.models import Employee, Department, Designation
from django.db.models import F
from decimal import Decimal
import math

class PayrollCostTrendsReport:
    def generate_payroll_cost_trends_report(self, organization, filters=None):
        """
        Generate payroll cost trends with monthly/quarterly comparisons
        """
        filters = filters or {}
        
        # Determine analysis period
        end_date = timezone.now().date()
        if filters.get('end_date'):
            end_date = datetime.strptime(filters['end_date'], '%Y-%m-%d').date()
        
        # Default to last 12 months
        start_date = end_date - timedelta(days=365)
        if filters.get('start_date'):
            start_date = datetime.strptime(filters['start_date'], '%Y-%m-%d').date()
        
        # Get payroll periods in the analysis range
        payroll_periods = PayrollPeriod.objects.filter(
            organization=organization,
            status='completed',
            start_date__gte=start_date,
            end_date__lte=end_date
        ).order_by('start_date')
        
        # Apply department filter if provided
        if filters.get('department'):
            payroll_periods = payroll_periods.filter(
                payslips__employee__department_id=filters['department']
            ).distinct()
        
        # Monthly trends
        monthly_trends = self._calculate_monthly_trends(organization, payroll_periods, filters)
        
        # Quarterly trends
        quarterly_trends = self._calculate_quarterly_trends(monthly_trends)
        
        # Year-over-year comparison
        yoy_comparison = self._calculate_yoy_comparison(organization, start_date, end_date, filters)
        
        # Cost breakdown by component
        cost_breakdown = self._calculate_cost_breakdown(organization, payroll_periods, filters)
        
        # Summary statistics
        summary = self._calculate_trends_summary(monthly_trends, quarterly_trends)
        
        return {
            'report_name': 'Payroll Cost Trends Report',
            'generated_on': timezone.now().strftime('%d-%m-%Y %H:%M:%S'),
            'filters': filters,
            'summary': summary,
            'monthly_trends': monthly_trends,
            'quarterly_trends': quarterly_trends,
            'yoy_comparison': yoy_comparison,
            'cost_breakdown': cost_breakdown,
            'analysis_period': {
                'start_date': start_date.strftime('%d %b %Y'),
                'end_date': end_date.strftime('%d %b %Y'),
                'months': len(monthly_trends)
            }
        }
    
    def _calculate_monthly_trends(self, organization, payroll_periods, filters):
        """Calculate monthly payroll cost trends"""
        monthly_data = []
        
        # Return empty if no periods
        if not payroll_periods.exists():
            return monthly_data
            
        # Group periods by month
        periods_by_month = {}
        for period in payroll_periods:
            month_key = period.start_date.strftime('%Y-%m')
            if month_key not in periods_by_month:
                periods_by_month[month_key] = []
            periods_by_month[month_key].append(period)
        
        # Calculate metrics for each month
        for month_key, periods in periods_by_month.items():
            total_gross = 0
            total_net = 0
            total_deductions = 0
            total_employees = 0
            total_payslips = 0
            
            for period in periods:
                payslips = Payslip.objects.filter(
                    organization=organization,
                    payroll_period=period,
                    is_generated=True
                )
                
                # Apply department filter
                if filters.get('department'):
                    payslips = payslips.filter(employee__department_id=filters['department'])
                
                payslip_count = payslips.count()
                total_payslips += payslip_count
                
                for payslip in payslips:
                    total_gross += float(payslip.gross_salary)
                    total_net += float(payslip.net_salary)
                    total_deductions += float(payslip.total_deductions)
                
                total_employees = max(total_employees, payslip_count)
            
            # Calculate averages with zero division protection
            avg_gross = total_gross / total_payslips if total_payslips > 0 else 0
            avg_net = total_net / total_payslips if total_payslips > 0 else 0
            deduction_rate = (total_deductions / total_gross * 100) if total_gross > 0 else 0
            
            monthly_data.append({
                'month': periods[0].start_date.strftime('%b %Y'),
                'month_key': month_key,
                'total_gross': total_gross,
                'total_net': total_net,
                'total_deductions': total_deductions,
                'employee_count': total_employees,
                'payslip_count': total_payslips,
                'avg_gross_salary': avg_gross,
                'avg_net_salary': avg_net,
                'deduction_rate': deduction_rate
            })
        
        # Calculate month-over-month growth with zero division protection
        for i in range(1, len(monthly_data)):
            prev_gross = monthly_data[i-1]['total_gross']
            curr_gross = monthly_data[i]['total_gross']
            mom_growth = ((curr_gross - prev_gross) / prev_gross * 100) if prev_gross > 0 else 0
            monthly_data[i]['mom_growth'] = mom_growth
        
        if monthly_data:
            monthly_data[0]['mom_growth'] = 0
        
        return monthly_data
    
    def _calculate_quarterly_trends(self, monthly_trends):
        """Calculate quarterly trends from monthly data"""
        quarterly_data = []
        quarterly_totals = {}
        
        # Group monthly data by quarter
        for month_data in monthly_trends:
            year = int(month_data['month_key'].split('-')[0])
            month = int(month_data['month_key'].split('-')[1])
            quarter = (month - 1) // 3 + 1
            quarter_key = f"Q{quarter} {year}"
            
            if quarter_key not in quarterly_totals:
                quarterly_totals[quarter_key] = {
                    'total_gross': 0,
                    'total_net': 0,
                    'total_deductions': 0,
                    'total_employees': 0,
                    'total_payslips': 0,
                    'months': 0
                }
            
            quarterly_totals[quarter_key]['total_gross'] += month_data['total_gross']
            quarterly_totals[quarter_key]['total_net'] += month_data['total_net']
            quarterly_totals[quarter_key]['total_deductions'] += month_data['total_deductions']
            quarterly_totals[quarter_key]['total_employees'] += month_data['employee_count']
            quarterly_totals[quarter_key]['total_payslips'] += month_data['payslip_count']
            quarterly_totals[quarter_key]['months'] += 1
        
        # Calculate quarterly averages and metrics
        for quarter_key, data in quarterly_totals.items():
            avg_gross = data['total_gross'] / data['months'] if data['months'] > 0 else 0
            avg_net = data['total_net'] / data['months'] if data['months'] > 0 else 0
            avg_employees = data['total_employees'] / data['months'] if data['months'] > 0 else 0
            
            quarterly_data.append({
                'quarter': quarter_key,
                'total_gross': data['total_gross'],
                'total_net': data['total_net'],
                'total_deductions': data['total_deductions'],
                'avg_gross_salary': avg_gross,
                'avg_net_salary': avg_net,
                'avg_employee_count': avg_employees,
                'deduction_rate': (data['total_deductions'] / data['total_gross'] * 100) if data['total_gross'] > 0 else 0
            })
        
        # Calculate quarter-over-quarter growth
        quarterly_data.sort(key=lambda x: x['quarter'])
        for i in range(1, len(quarterly_data)):
            prev_gross = quarterly_data[i-1]['total_gross']
            curr_gross = quarterly_data[i]['total_gross']
            qoq_growth = ((curr_gross - prev_gross) / prev_gross * 100) if prev_gross > 0 else 0
            quarterly_data[i]['qoq_growth'] = qoq_growth
        
        if quarterly_data:
            quarterly_data[0]['qoq_growth'] = 0
        
        return quarterly_data
    
    def _calculate_yoy_comparison(self, organization, start_date, end_date, filters):
        """Calculate year-over-year comparison"""
        current_year = end_date.year
        previous_year = current_year - 1
        
        # Current year data
        current_year_periods = PayrollPeriod.objects.filter(
            organization=organization,
            status='completed',
            start_date__year=current_year
        )
        
        if filters.get('department'):
            current_year_periods = current_year_periods.filter(
                payslips__employee__department_id=filters['department']
            ).distinct()
        
        current_year_gross = 0
        current_year_employees = 0
        
        for period in current_year_periods:
            payslips = Payslip.objects.filter(
                organization=organization,
                payroll_period=period,
                is_generated=True
            )
            
            if filters.get('department'):
                payslips = payslips.filter(employee__department_id=filters['department'])
            
            for payslip in payslips:
                current_year_gross += float(payslip.gross_salary)
            
            current_year_employees = max(current_year_employees, payslips.count())
        
        # Previous year data
        previous_year_periods = PayrollPeriod.objects.filter(
            organization=organization,
            status='completed',
            start_date__year=previous_year
        )
        
        if filters.get('department'):
            previous_year_periods = previous_year_periods.filter(
                payslips__employee__department_id=filters['department']
            ).distinct()
        
        previous_year_gross = 0
        previous_year_employees = 0
        
        for period in previous_year_periods:
            payslips = Payslip.objects.filter(
                organization=organization,
                payroll_period=period,
                is_generated=True
            )
            
            if filters.get('department'):
                payslips = payslips.filter(employee__department_id=filters['department'])
            
            for payslip in payslips:
                previous_year_gross += float(payslip.gross_salary)
            
            previous_year_employees = max(previous_year_employees, payslips.count())
        
        # Calculate growth rates with zero division protection
        gross_growth = ((current_year_gross - previous_year_gross) / previous_year_gross * 100) if previous_year_gross > 0 else 0
        employee_growth = ((current_year_employees - previous_year_employees) / previous_year_employees * 100) if previous_year_employees > 0 else 0
        
        return {
            'current_year': current_year,
            'previous_year': previous_year,
            'current_year_gross': current_year_gross,
            'previous_year_gross': previous_year_gross,
            'current_year_employees': current_year_employees,
            'previous_year_employees': previous_year_employees,
            'gross_growth_rate': gross_growth,
            'employee_growth_rate': employee_growth,
            'absolute_growth': current_year_gross - previous_year_gross
        }
        
    def _calculate_cost_breakdown(self, organization, payroll_periods, filters):
        """Calculate cost breakdown by component"""
        breakdown = {
            'basic_salary': 0,
            'allowances': 0,
            'overtime': 0,
            'bonus': 0,
            'other_earnings': 0,
            'pf_deductions': 0,
            'tax_deductions': 0,
            'other_deductions': 0
        }
        
        total_payslips = 0
        
        for period in payroll_periods:
            payslips = Payslip.objects.filter(
                organization=organization,
                payroll_period=period,
                is_generated=True
            )
            
            if filters.get('department'):
                payslips = payslips.filter(employee__department_id=filters['department'])
            
            for payslip in payslips:
                breakdown['basic_salary'] += float(payslip.basic_salary)
                breakdown['allowances'] += float(payslip.allowances)
                breakdown['overtime'] += float(payslip.overtime_pay)
                breakdown['bonus'] += float(payslip.bonus)
                breakdown['other_earnings'] += float(payslip.other_earnings)
                breakdown['pf_deductions'] += float(payslip.provident_fund)
                breakdown['tax_deductions'] += float(payslip.tax_deduction)
                breakdown['other_deductions'] += float(payslip.other_deductions)
                total_payslips += 1
        
        # Calculate totals with zero division protection
        total_earnings = sum([
            breakdown['basic_salary'],
            breakdown['allowances'],
            breakdown['overtime'],
            breakdown['bonus'],
            breakdown['other_earnings']
        ])
        
        total_deductions = sum([
            breakdown['pf_deductions'],
            breakdown['tax_deductions'],
            breakdown['other_deductions']
        ])
        
        # Create result dictionary with all data
        result = breakdown.copy()
        
        # Add percentages with zero division protection
        for key in breakdown:
            if key in ['basic_salary', 'allowances', 'overtime', 'bonus', 'other_earnings']:
                base = total_earnings
            else:
                base = total_deductions
            
            # Prevent division by zero
            result[f'{key}_percentage'] = (breakdown[key] / base * 100) if base > 0 else 0
        
        # Add summary fields
        result['total_earnings'] = total_earnings
        result['total_deductions'] = total_deductions
        result['total_payslips'] = total_payslips
        
        return result
    
    def _calculate_trends_summary(self, monthly_trends, quarterly_trends):
        """Calculate summary statistics for trends"""
        if not monthly_trends:
            return {
                'total_months': 0,
                'total_quarters': 0,
                'total_gross_payroll': 0,
                'total_net_payroll': 0,
                'avg_monthly_gross': 0,
                'overall_growth_rate': 0,
                'highest_month': 'N/A',
                'highest_amount': 0,
                'lowest_month': 'N/A',
                'lowest_amount': 0,
                'total_deductions': 0
            }
        
        total_gross = sum(month['total_gross'] for month in monthly_trends)
        total_net = sum(month['total_net'] for month in monthly_trends)
        avg_monthly_gross = total_gross / len(monthly_trends) if monthly_trends else 0
        
        # Calculate overall growth rate with zero division protection
        if len(monthly_trends) >= 2:
            first_month = monthly_trends[0]['total_gross']
            last_month = monthly_trends[-1]['total_gross']
            overall_growth = ((last_month - first_month) / first_month * 100) if first_month > 0 else 0
        else:
            overall_growth = 0
        
        # Find highest and lowest months
        if monthly_trends:
            highest_month = max(monthly_trends, key=lambda x: x['total_gross'])
            lowest_month = min(monthly_trends, key=lambda x: x['total_gross'])
            highest_month_data = highest_month.get('month', 'N/A')
            highest_amount = highest_month.get('total_gross', 0)
            lowest_month_data = lowest_month.get('month', 'N/A')
            lowest_amount = lowest_month.get('total_gross', 0)
        else:
            highest_month_data = 'N/A'
            highest_amount = 0
            lowest_month_data = 'N/A'
            lowest_amount = 0
        
        return {
            'total_months': len(monthly_trends),
            'total_quarters': len(quarterly_trends),
            'total_gross_payroll': total_gross,
            'total_net_payroll': total_net,
            'avg_monthly_gross': avg_monthly_gross,
            'overall_growth_rate': overall_growth,
            'highest_month': highest_month_data,
            'highest_amount': highest_amount,
            'lowest_month': lowest_month_data,
            'lowest_amount': lowest_amount,
            'total_deductions': sum(month['total_deductions'] for month in monthly_trends)
        }
class OvertimeCostAnalysisReport:
    def generate_overtime_cost_analysis(self, organization, filters=None):
        """
        Generate overtime cost analysis report
        """
        filters = filters or {}
        
        # Date range for analysis
        end_date = timezone.now().date()
        if filters.get('end_date'):
            end_date = datetime.strptime(filters['end_date'], '%Y-%m-%d').date()
        
        start_date = end_date - timedelta(days=90)  # Default 3 months
        if filters.get('start_date'):
            start_date = datetime.strptime(filters['start_date'], '%Y-%m-%d').date()
        
        # Get payroll periods in the analysis range
        payroll_periods = PayrollPeriod.objects.filter(
            organization=organization,
            status='completed',
            start_date__gte=start_date,
            end_date__lte=end_date
        ).order_by('start_date')
        
        # Overtime analysis data
        overtime_data = []
        total_overtime_cost = 0
        total_overtime_hours = 0
        
        for period in payroll_periods:
            payslips = Payslip.objects.filter(
                organization=organization,
                payroll_period=period,
                is_generated=True,
                overtime_pay__gt=0
            ).select_related('employee', 'employee__department', 'employee__designation')
            
            # Apply filters
            if filters.get('department'):
                payslips = payslips.filter(employee__department_id=filters['department'])
            
            if filters.get('employee_id'):
                payslips = payslips.filter(employee__employee_id__icontains=filters['employee_id'])
            
            period_overtime_cost = 0
            period_overtime_hours = 0
            period_employees = set()
            
            for payslip in payslips:
                overtime_cost = float(payslip.overtime_pay)
                period_overtime_cost += overtime_cost
                total_overtime_cost += overtime_cost
                period_employees.add(payslip.employee_id)
                
                # Estimate overtime hours (assuming average overtime rate)
                # In a real scenario, you would track actual overtime hours
                estimated_hours = overtime_cost / 100  # Assuming ৳100 per hour average
                period_overtime_hours += estimated_hours
                total_overtime_hours += estimated_hours
            
            if period_overtime_cost > 0:
                overtime_data.append({
                    'period_name': period.name,
                    'start_date': period.start_date,
                    'end_date': period.end_date,
                    'overtime_cost': period_overtime_cost,
                    'overtime_hours': period_overtime_hours,
                    'employee_count': len(period_employees),
                    'avg_cost_per_employee': period_overtime_cost / len(period_employees) if period_employees else 0,
                    'avg_hours_per_employee': period_overtime_hours / len(period_employees) if period_employees else 0
                })
        
        # Department-wise analysis
        dept_overtime = self._calculate_department_overtime(organization, payroll_periods, filters)
        
        # Employee-wise analysis (top overtime earners)
        top_overtime_earners = self._get_top_overtime_earners(organization, payroll_periods, filters, limit=10)
        
        # Overtime trends
        overtime_trends = self._calculate_overtime_trends(overtime_data)
        
        # Summary statistics
        summary = self._calculate_overtime_summary(overtime_data, total_overtime_cost, total_overtime_hours)
        
        return {
            'report_name': 'Overtime Cost Analysis Report',
            'generated_on': timezone.now().strftime('%d-%m-%Y %H:%M:%S'),
            'filters': filters,
            'summary': summary,
            'overtime_data': overtime_data,
            'department_overtime': dept_overtime,
            'top_overtime_earners': top_overtime_earners,
            'overtime_trends': overtime_trends,
            'analysis_period': {
                'start_date': start_date.strftime('%d %b %Y'),
                'end_date': end_date.strftime('%d %b %Y')
            }
        }
    
    def _calculate_department_overtime(self, organization, payroll_periods, filters):
        """Calculate department-wise overtime analysis"""
        dept_overtime = {}
        
        for period in payroll_periods:
            payslips = Payslip.objects.filter(
                organization=organization,
                payroll_period=period,
                is_generated=True,
                overtime_pay__gt=0
            ).select_related('employee__department')
            
            if filters.get('employee_id'):
                payslips = payslips.filter(employee__employee_id__icontains=filters['employee_id'])
            
            for payslip in payslips:
                dept_name = payslip.employee.department.name if payslip.employee.department else 'No Department'
                
                if dept_name not in dept_overtime:
                    dept_overtime[dept_name] = {
                        'total_cost': 0,
                        'total_hours': 0,
                        'employee_count': set(),
                        'period_count': set()
                    }
                
                overtime_cost = float(payslip.overtime_pay)
                dept_overtime[dept_name]['total_cost'] += overtime_cost
                dept_overtime[dept_name]['total_hours'] += overtime_cost / 100  # Estimated hours
                dept_overtime[dept_name]['employee_count'].add(payslip.employee_id)
                dept_overtime[dept_name]['period_count'].add(period.id)
        
        # Convert sets to counts and calculate averages
        result = []
        for dept_name, data in dept_overtime.items():
            employee_count = len(data['employee_count'])
            period_count = len(data['period_count'])
            
            result.append({
                'department': dept_name,
                'total_cost': data['total_cost'],
                'total_hours': data['total_hours'],
                'employee_count': employee_count,
                'period_count': period_count,
                'avg_cost_per_employee': data['total_cost'] / employee_count if employee_count > 0 else 0,
                'avg_hours_per_employee': data['total_hours'] / employee_count if employee_count > 0 else 0,
                'cost_per_period': data['total_cost'] / period_count if period_count > 0 else 0
            })
        
        return sorted(result, key=lambda x: x['total_cost'], reverse=True)
    
    def _get_top_overtime_earners(self, organization, payroll_periods, filters, limit=10):
        """Get top overtime earners"""
        employee_overtime = {}
        
        for period in payroll_periods:
            payslips = Payslip.objects.filter(
                organization=organization,
                payroll_period=period,
                is_generated=True,
                overtime_pay__gt=0
            ).select_related('employee', 'employee__department')
            
            if filters.get('department'):
                payslips = payslips.filter(employee__department_id=filters['department'])
            
            if filters.get('employee_id'):
                payslips = payslips.filter(employee__employee_id__icontains=filters['employee_id'])
            
            for payslip in payslips:
                employee = payslip.employee
                if employee.id not in employee_overtime:
                    employee_overtime[employee.id] = {
                        'employee_id': employee.employee_id,
                        'full_name': employee.full_name,
                        'department': employee.department.name if employee.department else 'N/A',
                        'designation': employee.designation.name if employee.designation else 'N/A',
                        'total_overtime': 0,
                        'period_count': 0
                    }
                
                employee_overtime[employee.id]['total_overtime'] += float(payslip.overtime_pay)
                employee_overtime[employee.id]['period_count'] += 1
        
        # Convert to list and sort by total overtime
        result = list(employee_overtime.values())
        result.sort(key=lambda x: x['total_overtime'], reverse=True)
        
        return result[:limit]
    
    def _calculate_overtime_trends(self, overtime_data):
        """Calculate overtime trends"""
        if len(overtime_data) < 2:
            return {}
        
        # Calculate month-over-month growth
        trends = []
        for i in range(1, len(overtime_data)):
            prev_cost = overtime_data[i-1]['overtime_cost']
            curr_cost = overtime_data[i]['overtime_cost']
            growth = ((curr_cost - prev_cost) / prev_cost * 100) if prev_cost > 0 else 0
            
            trends.append({
                'period': overtime_data[i]['period_name'],
                'cost': curr_cost,
                'growth_rate': growth,
                'trend': 'increasing' if growth > 0 else 'decreasing' if growth < 0 else 'stable'
            })
        
        return trends
    
    def _calculate_overtime_summary(self, overtime_data, total_cost, total_hours):
        """Calculate overtime summary statistics"""
        if not overtime_data:
            return {}
        
        avg_period_cost = total_cost / len(overtime_data) if overtime_data else 0
        avg_hourly_rate = total_cost / total_hours if total_hours > 0 else 0
        
        # Find highest and lowest overtime periods
        highest_period = max(overtime_data, key=lambda x: x['overtime_cost']) if overtime_data else {}
        lowest_period = min(overtime_data, key=lambda x: x['overtime_cost']) if overtime_data else {}
        
        return {
            'total_periods': len(overtime_data),
            'total_overtime_cost': total_cost,
            'total_overtime_hours': total_hours,
            'avg_period_cost': avg_period_cost,
            'avg_hourly_rate': avg_hourly_rate,
            'highest_period': highest_period.get('period_name', 'N/A'),
            'highest_cost': highest_period.get('overtime_cost', 0),
            'lowest_period': lowest_period.get('period_name', 'N/A'),
            'lowest_cost': lowest_period.get('overtime_cost', 0)
        }

class BonusIncentiveAnalysisReport:
    def generate_bonus_incentive_analysis(self, organization, filters=None):
        """
        Generate bonus and incentive analysis report
        """
        filters = filters or {}
        
        # Date range for analysis
        end_date = timezone.now().date()
        if filters.get('end_date'):
            end_date = datetime.strptime(filters['end_date'], '%Y-%m-%d').date()
        
        start_date = end_date - timedelta(days=365)  # Default 1 year
        if filters.get('start_date'):
            start_date = datetime.strptime(filters['start_date'], '%Y-%m-%d').date()
        
        # Get payroll periods in the analysis range
        payroll_periods = PayrollPeriod.objects.filter(
            organization=organization,
            status='completed',
            start_date__gte=start_date,
            end_date__lte=end_date
        ).order_by('start_date')
        
        # Bonus analysis data
        bonus_data = []
        total_bonus_cost = 0
        total_bonus_employees = set()
        
        for period in payroll_periods:
            payslips = Payslip.objects.filter(
                organization=organization,
                payroll_period=period,
                is_generated=True,
                bonus__gt=0
            )
            
            # Apply filters
            if filters.get('department'):
                payslips = payslips.filter(employee__department_id=filters['department'])
            
            if filters.get('designation'):
                payslips = payslips.filter(employee__designation_id=filters['designation'])
            
            period_bonus_cost = 0
            period_bonus_employees = set()
            
            for payslip in payslips:
                bonus_amount = float(payslip.bonus)
                period_bonus_cost += bonus_amount
                total_bonus_cost += bonus_amount
                period_bonus_employees.add(payslip.employee_id)
                total_bonus_employees.add(payslip.employee_id)
            
            if period_bonus_cost > 0:
                bonus_data.append({
                    'period_name': period.name,
                    'start_date': period.start_date,
                    'end_date': period.end_date,
                    'bonus_cost': period_bonus_cost,
                    'employee_count': len(period_bonus_employees),
                    'avg_bonus_per_employee': period_bonus_cost / len(period_bonus_employees) if period_bonus_employees else 0,
                    'bonus_percentage': (period_bonus_cost / self._get_period_payroll_cost(period, filters) * 100) if self._get_period_payroll_cost(period, filters) > 0 else 0
                })
        
        # Department-wise bonus analysis
        dept_bonus = self._calculate_department_bonus(organization, payroll_periods, filters)
        
        # Employee-wise bonus analysis
        employee_bonus = self._get_employee_bonus_analysis(organization, payroll_periods, filters)
        
        # Bonus type analysis (you would need to track bonus types in your model)
        bonus_type_analysis = self._analyze_bonus_types(organization, payroll_periods, filters)
        
        # Summary statistics
        summary = self._calculate_bonus_summary(bonus_data, total_bonus_cost, len(total_bonus_employees))
        
        return {
            'report_name': 'Bonus & Incentive Analysis Report',
            'generated_on': timezone.now().strftime('%d-%m-%Y %H:%M:%S'),
            'filters': filters,
            'summary': summary,
            'bonus_data': bonus_data,
            'department_bonus': dept_bonus,
            'employee_bonus': employee_bonus,
            'bonus_type_analysis': bonus_type_analysis,
            'analysis_period': {
                'start_date': start_date.strftime('%d %b %Y'),
                'end_date': end_date.strftime('%d %b %Y')
            }
        }
    
    def _get_period_payroll_cost(self, period, filters):
        """Get total payroll cost for a period"""
        payslips = Payslip.objects.filter(
            payroll_period=period,
            is_generated=True
        )
        
        if filters.get('department'):
            payslips = payslips.filter(employee__department_id=filters['department'])
        
        total_cost = 0
        for payslip in payslips:
            total_cost += float(payslip.gross_salary)
        
        return total_cost
    
    def _calculate_department_bonus(self, organization, payroll_periods, filters):
        """Calculate department-wise bonus analysis"""
        dept_bonus = {}
        
        for period in payroll_periods:
            payslips = Payslip.objects.filter(
                organization=organization,
                payroll_period=period,
                is_generated=True,
                bonus__gt=0
            ).select_related('employee__department')
            
            if filters.get('designation'):
                payslips = payslips.filter(employee__designation_id=filters['designation'])
            
            for payslip in payslips:
                dept_name = payslip.employee.department.name if payslip.employee.department else 'No Department'
                
                if dept_name not in dept_bonus:
                    dept_bonus[dept_name] = {
                        'total_bonus': 0,
                        'employee_count': set(),
                        'period_count': set()
                    }
                
                bonus_amount = float(payslip.bonus)
                dept_bonus[dept_name]['total_bonus'] += bonus_amount
                dept_bonus[dept_name]['employee_count'].add(payslip.employee_id)
                dept_bonus[dept_name]['period_count'].add(period.id)
        
        # Convert to list format
        result = []
        for dept_name, data in dept_bonus.items():
            employee_count = len(data['employee_count'])
            
            result.append({
                'department': dept_name,
                'total_bonus': data['total_bonus'],
                'employee_count': employee_count,
                'period_count': len(data['period_count']),
                'avg_bonus_per_employee': data['total_bonus'] / employee_count if employee_count > 0 else 0,
                'bonus_frequency': employee_count / len(data['period_count']) if data['period_count'] else 0
            })
        
        return sorted(result, key=lambda x: x['total_bonus'], reverse=True)
    
    def _get_employee_bonus_analysis(self, organization, payroll_periods, filters):
        """Get employee-wise bonus analysis"""
        employee_bonus = {}
        
        for period in payroll_periods:
            payslips = Payslip.objects.filter(
                organization=organization,
                payroll_period=period,
                is_generated=True,
                bonus__gt=0
            ).select_related('employee', 'employee__department', 'employee__designation')
            
            if filters.get('department'):
                payslips = payslips.filter(employee__department_id=filters['department'])
            
            if filters.get('designation'):
                payslips = payslips.filter(employee__designation_id=filters['designation'])
            
            for payslip in payslips:
                employee = payslip.employee
                if employee.id not in employee_bonus:
                    employee_bonus[employee.id] = {
                        'employee_id': employee.employee_id,
                        'full_name': employee.full_name,
                        'department': employee.department.name if employee.department else 'N/A',
                        'designation': employee.designation.name if employee.designation else 'N/A',
                        'total_bonus': 0,
                        'bonus_count': 0,
                        'avg_basic_salary': 0,
                        'salary_count': 0
                    }
                
                employee_bonus[employee.id]['total_bonus'] += float(payslip.bonus)
                employee_bonus[employee.id]['bonus_count'] += 1
                employee_bonus[employee.id]['avg_basic_salary'] += float(payslip.basic_salary)
                employee_bonus[employee.id]['salary_count'] += 1
        
        # Calculate averages and bonus ratios
        for emp_data in employee_bonus.values():
            if emp_data['salary_count'] > 0:
                emp_data['avg_basic_salary'] = emp_data['avg_basic_salary'] / emp_data['salary_count']
                emp_data['bonus_to_salary_ratio'] = (emp_data['total_bonus'] / emp_data['avg_basic_salary'] * 100) if emp_data['avg_basic_salary'] > 0 else 0
            else:
                emp_data['avg_basic_salary'] = 0
                emp_data['bonus_to_salary_ratio'] = 0
        
        # Convert to list and sort by total bonus
        result = list(employee_bonus.values())
        result.sort(key=lambda x: x['total_bonus'], reverse=True)
        
        return result[:20]  # Return top 20
    
# Continuing from the previous code...

    def _analyze_bonus_types(self, organization, payroll_periods, filters):
        """Analyze bonus types (simplified - you would need bonus_type field)"""
        # This is a simplified version. In a real scenario, you would track bonus types
        bonus_types = {
            'Performance Bonus': 0,
            'Annual Bonus': 0,
            'Festival Bonus': 0,
            'Retention Bonus': 0,
            'Spot Bonus': 0,
            'Other Bonus': 0
        }
        
        # For now, we'll estimate based on amount ranges and timing
        # In a real implementation, you would have a bonus_type field
        total_bonus = 0
        bonus_count = 0
        
        for period in payroll_periods:
            payslips = Payslip.objects.filter(
                organization=organization,
                payroll_period=period,
                is_generated=True,
                bonus__gt=0
            )
            
            if filters.get('department'):
                payslips = payslips.filter(employee__department_id=filters['department'])
            
            for payslip in payslips:
                bonus_amount = float(payslip.bonus)
                total_bonus += bonus_amount
                bonus_count += 1
                
                # Estimate bonus type based on amount and timing
                # This is simplified logic - in reality you'd have actual bonus types
                if bonus_amount >= 50000:
                    bonus_types['Annual Bonus'] += bonus_amount
                elif 20000 <= bonus_amount < 50000:
                    bonus_types['Performance Bonus'] += bonus_amount
                elif 5000 <= bonus_amount < 20000:
                    # Check if it's around festival season
                    if period.start_date.month in [10, 11, 12, 1]:  # Festival months
                        bonus_types['Festival Bonus'] += bonus_amount
                    else:
                        bonus_types['Spot Bonus'] += bonus_amount
                else:
                    bonus_types['Other Bonus'] += bonus_amount
        
        # Calculate percentages
        result = []
        for bonus_type, amount in bonus_types.items():
            percentage = (amount / total_bonus * 100) if total_bonus > 0 else 0
            result.append({
                'bonus_type': bonus_type,
                'total_amount': amount,
                'percentage': percentage,
                'avg_amount': amount / bonus_count if bonus_count > 0 else 0
            })
        
        return sorted(result, key=lambda x: x['total_amount'], reverse=True)
    
    def _calculate_bonus_summary(self, bonus_data, total_cost, total_employees):
        """Calculate bonus summary statistics"""
        if not bonus_data:
            return {}
        
        avg_period_bonus = total_cost / len(bonus_data) if bonus_data else 0
        avg_employee_bonus = total_cost / total_employees if total_employees > 0 else 0
        
        # Find highest and lowest bonus periods
        highest_period = max(bonus_data, key=lambda x: x['bonus_cost']) if bonus_data else {}
        lowest_period = min(bonus_data, key=lambda x: x['bonus_cost']) if bonus_data else {}
        
        # Calculate bonus frequency
        total_periods_with_bonus = len(bonus_data)
        bonus_frequency = (total_periods_with_bonus / len(bonus_data)) * 100 if bonus_data else 0
        
        return {
            'total_bonus_cost': total_cost,
            'total_employees_receiving_bonus': total_employees,
            'total_periods_with_bonus': total_periods_with_bonus,
            'avg_period_bonus': avg_period_bonus,
            'avg_employee_bonus': avg_employee_bonus,
            'highest_period': highest_period.get('period_name', 'N/A'),
            'highest_bonus': highest_period.get('bonus_cost', 0),
            'lowest_period': lowest_period.get('period_name', 'N/A'),
            'lowest_bonus': lowest_period.get('bonus_cost', 0),
            'bonus_frequency_rate': bonus_frequency
        }


class TaxLiabilityProjectionReport:
    def generate_tax_liability_projection(self, organization, filters=None):
        """
        Generate tax liability projections for the organization
        """
        filters = filters or {}
        
        # Date range for analysis
        end_date = timezone.now().date()
        if filters.get('end_date'):
            end_date = datetime.strptime(filters['end_date'], '%Y-%m-%d').date()
        
        start_date = end_date - timedelta(days=180)  # Default 6 months historical
        if filters.get('start_date'):
            start_date = datetime.strptime(filters['start_date'], '%Y-%m-%d').date()
        
        # Get historical payroll periods
        historical_periods = PayrollPeriod.objects.filter(
            organization=organization,
            status='completed',
            start_date__gte=start_date,
            end_date__lte=end_date
        ).order_by('start_date')
        
        # Calculate historical tax data
        historical_tax_data = self._calculate_historical_tax_data(organization, historical_periods, filters)
        
        # Project future tax liabilities
        projection_data = self._project_tax_liabilities(organization, historical_tax_data, filters)
        
        # Employee tax analysis
        employee_tax_analysis = self._analyze_employee_tax_liabilities(organization, historical_periods, filters)
        
        # Department-wise tax analysis
        department_tax_analysis = self._analyze_department_tax_liabilities(organization, historical_periods, filters)
        
        # Tax compliance status
        compliance_status = self._check_tax_compliance(organization, historical_periods)
        
        # Summary statistics
        summary = self._calculate_tax_summary(historical_tax_data, projection_data)
        
        return {
            'report_name': 'Tax Liability Projection Report',
            'generated_on': timezone.now().strftime('%d-%m-%Y %H:%M:%S'),
            'filters': filters,
            'summary': summary,
            'historical_tax_data': historical_tax_data,
            'projection_data': projection_data,
            'employee_tax_analysis': employee_tax_analysis,
            'department_tax_analysis': department_tax_analysis,
            'compliance_status': compliance_status,
            'analysis_period': {
                'start_date': start_date.strftime('%d %b %Y'),
                'end_date': end_date.strftime('%d %b %Y')
            }
        }
    
    def _calculate_historical_tax_data(self, organization, payroll_periods, filters):
        """Calculate historical tax data for analysis"""
        historical_data = []
        
        for period in payroll_periods:
            payslips = Payslip.objects.filter(
                organization=organization,
                payroll_period=period,
                is_generated=True
            )
            
            # Apply filters
            if filters.get('department'):
                payslips = payslips.filter(employee__department_id=filters['department'])
            
            if filters.get('employee_id'):
                payslips = payslips.filter(employee__employee_id__icontains=filters['employee_id'])
            
            period_tax = 0
            period_gross = 0
            period_employees = set()
            
            for payslip in payslips:
                tax_amount = float(payslip.tax_deduction)
                gross_amount = float(payslip.gross_salary)
                
                period_tax += tax_amount
                period_gross += gross_amount
                period_employees.add(payslip.employee_id)
            
            if period_gross > 0:
                tax_rate = (period_tax / period_gross * 100)
            else:
                tax_rate = 0
            
            historical_data.append({
                'period_name': period.name,
                'start_date': period.start_date,
                'end_date': period.end_date,
                'total_tax': period_tax,
                'total_gross': period_gross,
                'employee_count': len(period_employees),
                'tax_rate': tax_rate,
                'avg_tax_per_employee': period_tax / len(period_employees) if period_employees else 0
            })
        
        return historical_data
    
    def _project_tax_liabilities(self, organization, historical_data, filters):
        """Project future tax liabilities based on historical trends"""
        if len(historical_data) < 3:
            return []  # Need sufficient historical data for projections
        
        projections = []
        
        # Calculate average growth rate
        tax_growth_rates = []
        for i in range(1, len(historical_data)):
            prev_tax = historical_data[i-1]['total_tax']
            curr_tax = historical_data[i]['total_tax']
            if prev_tax > 0:
                growth_rate = (curr_tax - prev_tax) / prev_tax * 100
                tax_growth_rates.append(growth_rate)
        
        avg_growth_rate = sum(tax_growth_rates) / len(tax_growth_rates) if tax_growth_rates else 0
        
        # Project for next 6 periods
        last_period = historical_data[-1]
        base_tax = last_period['total_tax']
        base_date = last_period['end_date']
        
        for i in range(1, 7):  # Next 6 months
            projected_tax = base_tax * (1 + avg_growth_rate / 100) ** i
            projected_date = base_date + timedelta(days=30 * i)
            
            projections.append({
                'period': f"Projection {i}",
                'month': projected_date.strftime('%b %Y'),
                'projected_tax': projected_tax,
                'growth_rate': avg_growth_rate,
                'confidence_level': max(0, 100 - (i * 15))  # Decreasing confidence for farther projections
            })
        
        return projections
    
    def _analyze_employee_tax_liabilities(self, organization, payroll_periods, filters):
        """Analyze employee-wise tax liabilities"""
        employee_tax = {}
        
        for period in payroll_periods:
            payslips = Payslip.objects.filter(
                organization=organization,
                payroll_period=period,
                is_generated=True,
                tax_deduction__gt=0
            ).select_related('employee', 'employee__department')
            
            if filters.get('department'):
                payslips = payslips.filter(employee__department_id=filters['department'])
            
            for payslip in payslips:
                employee = payslip.employee
                if employee.id not in employee_tax:
                    employee_tax[employee.id] = {
                        'employee_id': employee.employee_id,
                        'full_name': employee.full_name,
                        'department': employee.department.name if employee.department else 'N/A',
                        'total_tax': 0,
                        'total_gross': 0,
                        'period_count': 0
                    }
                
                employee_tax[employee.id]['total_tax'] += float(payslip.tax_deduction)
                employee_tax[employee.id]['total_gross'] += float(payslip.gross_salary)
                employee_tax[employee.id]['period_count'] += 1
        
        # Calculate tax rates and averages
        for emp_data in employee_tax.values():
            if emp_data['total_gross'] > 0:
                emp_data['tax_rate'] = (emp_data['total_tax'] / emp_data['total_gross'] * 100)
            else:
                emp_data['tax_rate'] = 0
            
            if emp_data['period_count'] > 0:
                emp_data['avg_tax_per_period'] = emp_data['total_tax'] / emp_data['period_count']
                emp_data['avg_gross_per_period'] = emp_data['total_gross'] / emp_data['period_count']
            else:
                emp_data['avg_tax_per_period'] = 0
                emp_data['avg_gross_per_period'] = 0
        
        # Convert to list and sort by total tax
        result = list(employee_tax.values())
        result.sort(key=lambda x: x['total_tax'], reverse=True)
        
        return result[:15]  # Return top 15 taxpayers
    
    def _analyze_department_tax_liabilities(self, organization, payroll_periods, filters):
        """Analyze department-wise tax liabilities"""
        dept_tax = {}
        
        for period in payroll_periods:
            payslips = Payslip.objects.filter(
                organization=organization,
                payroll_period=period,
                is_generated=True
            ).select_related('employee__department')
            
            for payslip in payslips:
                dept_name = payslip.employee.department.name if payslip.employee.department else 'No Department'
                
                if dept_name not in dept_tax:
                    dept_tax[dept_name] = {
                        'total_tax': 0,
                        'total_gross': 0,
                        'employee_count': set(),
                        'period_count': set()
                    }
                
                dept_tax[dept_name]['total_tax'] += float(payslip.tax_deduction)
                dept_tax[dept_name]['total_gross'] += float(payslip.gross_salary)
                dept_tax[dept_name]['employee_count'].add(payslip.employee_id)
                dept_tax[dept_name]['period_count'].add(period.id)
        
        # Calculate metrics
        result = []
        for dept_name, data in dept_tax.items():
            employee_count = len(data['employee_count'])
            period_count = len(data['period_count'])
            
            if data['total_gross'] > 0:
                tax_rate = (data['total_tax'] / data['total_gross'] * 100)
            else:
                tax_rate = 0
            
            result.append({
                'department': dept_name,
                'total_tax': data['total_tax'],
                'total_gross': data['total_gross'],
                'employee_count': employee_count,
                'period_count': period_count,
                'tax_rate': tax_rate,
                'avg_tax_per_employee': data['total_tax'] / employee_count if employee_count > 0 else 0,
                'tax_per_period': data['total_tax'] / period_count if period_count > 0 else 0
            })
        
        return sorted(result, key=lambda x: x['total_tax'], reverse=True)
    
    def _check_tax_compliance(self, organization, payroll_periods):
        """Check tax compliance status"""
        compliance_checks = []
        
        for period in payroll_periods:
            payslips = Payslip.objects.filter(
                organization=organization,
                payroll_period=period,
                is_generated=True
            )
            
            total_tax_deducted = 0
            total_expected_tax = 0
            employees_with_tax = 0
            
            for payslip in payslips:
                tax_deducted = float(payslip.tax_deduction)
                gross_salary = float(payslip.gross_salary)
                
                total_tax_deducted += tax_deducted
                
                # Simple expected tax calculation (simplified)
                # In reality, you would use actual tax slabs and calculations
                expected_tax = self._calculate_expected_tax(gross_salary)
                total_expected_tax += expected_tax
                
                if tax_deducted > 0:
                    employees_with_tax += 1
            
            compliance_rate = (total_tax_deducted / total_expected_tax * 100) if total_expected_tax > 0 else 100
            status = 'Compliant' if compliance_rate >= 95 else 'Needs Review'
            
            compliance_checks.append({
                'period': period.name,
                'tax_deducted': total_tax_deducted,
                'expected_tax': total_expected_tax,
                'compliance_rate': compliance_rate,
                'status': status,
                'employees_with_tax': employees_with_tax
            })
        
        return compliance_checks
    
    def _calculate_expected_tax(self, gross_salary):
        """Calculate expected tax based on simplified tax slabs"""
        # Simplified tax calculation for demonstration
        # In reality, use actual tax laws and slabs
        annual_salary = gross_salary * 12
        
        if annual_salary <= 300000:  # 3 Lakhs
            return 0
        elif annual_salary <= 600000:  # 6 Lakhs
            return (annual_salary - 300000) * 0.05 / 12
        elif annual_salary <= 900000:  # 9 Lakhs
            return (15000 + (annual_salary - 600000) * 0.10) / 12
        elif annual_salary <= 1200000:  # 12 Lakhs
            return (45000 + (annual_salary - 900000) * 0.15) / 12
        elif annual_salary <= 1500000:  # 15 Lakhs
            return (90000 + (annual_salary - 1200000) * 0.20) / 12
        else:  # Above 15 Lakhs
            return (150000 + (annual_salary - 1500000) * 0.30) / 12
    
    def _calculate_tax_summary(self, historical_data, projection_data):
        """Calculate tax summary statistics"""
        if not historical_data:
            return {}
        
        total_historical_tax = sum(period['total_tax'] for period in historical_data)
        total_historical_gross = sum(period['total_gross'] for period in historical_data)
        avg_tax_rate = (total_historical_tax / total_historical_gross * 100) if total_historical_gross > 0 else 0
        
        # Projection summary
        if projection_data:
            total_projected_tax = sum(proj['projected_tax'] for proj in projection_data)
            avg_projection_growth = sum(proj['growth_rate'] for proj in projection_data) / len(projection_data)
        else:
            total_projected_tax = 0
            avg_projection_growth = 0
        
        # Find highest and lowest tax periods
        highest_period = max(historical_data, key=lambda x: x['total_tax']) if historical_data else {}
        lowest_period = min(historical_data, key=lambda x: x['total_tax']) if historical_data else {}
        
        return {
            'total_historical_tax': total_historical_tax,
            'total_historical_gross': total_historical_gross,
            'avg_tax_rate': avg_tax_rate,
            'total_projected_tax': total_projected_tax,
            'avg_projection_growth': avg_projection_growth,
            'highest_tax_period': highest_period.get('period_name', 'N/A'),
            'highest_tax_amount': highest_period.get('total_tax', 0),
            'lowest_tax_period': lowest_period.get('period_name', 'N/A'),
            'lowest_tax_amount': lowest_period.get('total_tax', 0),
            'analysis_periods': len(historical_data),
            'projection_periods': len(projection_data)
        }


class PayrollAnalyticsDashboard:
    """
    Comprehensive payroll analytics dashboard combining all reports
    """
    
    def __init__(self, organization):
        self.organization = organization
        self.cost_trends_report = PayrollCostTrendsReport()
        self.overtime_report = OvertimeCostAnalysisReport()
        self.bonus_report = BonusIncentiveAnalysisReport()
        self.tax_report = TaxLiabilityProjectionReport()
    
    def generate_comprehensive_dashboard(self, filters=None):
        """
        Generate comprehensive payroll analytics dashboard
        """
        filters = filters or {}
        
        # Generate all reports
        cost_trends = self.cost_trends_report.generate_payroll_cost_trends_report(self.organization, filters)
        overtime_analysis = self.overtime_report.generate_overtime_cost_analysis(self.organization, filters)
        bonus_analysis = self.bonus_report.generate_bonus_incentive_analysis(self.organization, filters)
        tax_projections = self.tax_report.generate_tax_liability_projection(self.organization, filters)
        
        # Calculate overall KPIs
        overall_kpis = self._calculate_overall_kpis(cost_trends, overtime_analysis, bonus_analysis, tax_projections)
        
        # Recent alerts and insights
        alerts = self._generate_alerts_and_insights(cost_trends, overtime_analysis, bonus_analysis, tax_projections)
        
        return {
            'dashboard_name': 'Payroll Analytics Dashboard',
            'generated_on': timezone.now().strftime('%d-%m-%Y %H:%M:%S'),
            'filters': filters,
            'overall_kpis': overall_kpis,
            'cost_trends': cost_trends,
            'overtime_analysis': overtime_analysis,
            'bonus_analysis': bonus_analysis,
            'tax_projections': tax_projections,
            'alerts_and_insights': alerts
        }
    
    def _calculate_overall_kpis(self, cost_trends, overtime_analysis, bonus_analysis, tax_projections):
        """Calculate overall KPIs for the dashboard"""
        
        # Extract relevant data from reports
        total_payroll_cost = cost_trends['summary'].get('total_gross_payroll', 0)
        avg_monthly_cost = cost_trends['summary'].get('avg_monthly_gross', 0)
        overall_growth = cost_trends['summary'].get('overall_growth_rate', 0)
        
        total_overtime_cost = overtime_analysis['summary'].get('total_overtime_cost', 0)
        total_bonus_cost = bonus_analysis['summary'].get('total_bonus_cost', 0)
        total_tax_liability = tax_projections['summary'].get('total_historical_tax', 0)
        
        # Calculate KPIs
        overtime_percentage = (total_overtime_cost / total_payroll_cost * 100) if total_payroll_cost > 0 else 0
        bonus_percentage = (total_bonus_cost / total_payroll_cost * 100) if total_payroll_cost > 0 else 0
        tax_percentage = (total_tax_liability / total_payroll_cost * 100) if total_payroll_cost > 0 else 0
        
        # Employee cost metrics (simplified)
        avg_employee_cost = avg_monthly_cost / cost_trends['summary'].get('total_months', 1) if cost_trends['summary'].get('total_months', 1) > 0 else 0
        
        return {
            'total_payroll_cost': total_payroll_cost,
            'avg_monthly_payroll': avg_monthly_cost,
            'payroll_growth_rate': overall_growth,
            'total_overtime_cost': total_overtime_cost,
            'total_bonus_cost': total_bonus_cost,
            'total_tax_liability': total_tax_liability,
            'overtime_percentage': overtime_percentage,
            'bonus_percentage': bonus_percentage,
            'tax_percentage': tax_percentage,
            'avg_employee_cost': avg_employee_cost,
            'cost_efficiency_score': self._calculate_cost_efficiency_score(
                overtime_percentage, bonus_percentage, overall_growth
            )
        }
    
    def _calculate_cost_efficiency_score(self, overtime_percentage, bonus_percentage, growth_rate):
        """Calculate a simplified cost efficiency score"""
        # Lower overtime and bonus percentages with healthy growth indicate better efficiency
        overtime_score = max(0, 100 - (overtime_percentage * 10))  # Penalize high overtime
        bonus_score = max(0, 100 - (bonus_percentage * 5))  # Penalize very high bonus ratios
        growth_score = min(100, max(0, growth_rate + 50))  # Reward growth, penalize decline
        
        return (overtime_score * 0.4 + bonus_score * 0.3 + growth_score * 0.3)
    
    def _generate_alerts_and_insights(self, cost_trends, overtime_analysis, bonus_analysis, tax_projections):
        """Generate alerts and insights based on analysis"""
        alerts = []
        insights = []
        
        # Cost trend alerts
        if cost_trends['summary'].get('overall_growth_rate', 0) < -5:
            alerts.append({
                'type': 'warning',
                'category': 'Cost Trends',
                'message': 'Payroll costs are declining significantly. Review staffing levels.',
                'priority': 'medium'
            })
        elif cost_trends['summary'].get('overall_growth_rate', 0) > 20:
            alerts.append({
                'type': 'warning',
                'category': 'Cost Trends',
                'message': 'Rapid payroll cost growth detected. Monitor sustainability.',
                'priority': 'medium'
            })
        
        # Overtime alerts
        overtime_percentage = (overtime_analysis['summary'].get('total_overtime_cost', 0) / 
                             cost_trends['summary'].get('total_gross_payroll', 1) * 100)
        if overtime_percentage > 15:
            alerts.append({
                'type': 'critical',
                'category': 'Overtime',
                'message': f'High overtime costs ({overtime_percentage:.1f}% of payroll). Consider hiring.',
                'priority': 'high'
            })
        
        # Bonus insights
        avg_bonus_per_employee = bonus_analysis['summary'].get('avg_employee_bonus', 0)
        if avg_bonus_per_employee > 50000:
            insights.append({
                'type': 'positive',
                'category': 'Compensation',
                'message': 'Substantial bonus payments indicate strong performance incentives.',
                'impact': 'high'
            })
        
        # Tax compliance insights
        compliance_issues = [check for check in tax_projections.get('compliance_status', []) 
                           if check.get('status') == 'Needs Review']
        if compliance_issues:
            alerts.append({
                'type': 'critical',
                'category': 'Tax Compliance',
                'message': f'{len(compliance_issues)} periods need tax compliance review.',
                'priority': 'high'
            })
        
        # Positive insights
        if cost_trends['summary'].get('overall_growth_rate', 0) > 0:
            insights.append({
                'type': 'positive',
                'category': 'Growth',
                'message': 'Payroll growth indicates business expansion or increased compensation.',
                'impact': 'medium'
            })
        
        return {
            'alerts': alerts[:5],  # Top 5 alerts
            'insights': insights[:5]  # Top 5 insights
        }

