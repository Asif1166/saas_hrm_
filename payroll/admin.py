from django.contrib import admin

from payroll.models import *

# Register your models here.
admin.site.register(PayrollPeriod)

class PayslipAdmin(admin.ModelAdmin):
    list_display = ['employee', 'payroll_period', 'net_salary', 'is_generated', 'deleted_at']
    list_filter = ['deleted_at']
    actions = ['restore_payslips']

    def get_queryset(self, request):
        # Include all payslips including soft-deleted
        return Payslip.objects.all_with_deleted()

    @admin.action(description="Restore selected soft-deleted payslips")
    def restore_payslips(self, request, queryset):
        restored_count = 0
        for payslip in queryset:
            if payslip.is_deleted:
                payslip.deleted_at = None
                payslip.save()
                restored_count += 1
        self.message_user(request, f"{restored_count} payslip(s) restored successfully.")

admin.site.register(Payslip, PayslipAdmin)


admin.site.register(SalaryStructure)
admin.site.register(Allowance)
admin.site.register(Deduction)
admin.site.register(PayslipComponent)
# admin.site.register(SoftDeleteManager)