from django.contrib import admin

from payroll.models import *

# Register your models here.
admin.site.register(PayrollPeriod)

admin.site.register(Payslip)
admin.site.register(SalaryStructure)
admin.site.register(Allowance)
admin.site.register(Deduction)
admin.site.register(PayslipComponent)