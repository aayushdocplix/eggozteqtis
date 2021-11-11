from django.db import models


class FinanceProfile(models.Model):
    user = models.OneToOneField('custom_auth.User', on_delete=models.DO_NOTHING, related_name="finance")
    warehouse = models.ForeignKey('warehouse.Warehouse',
                                  related_name="warehouse_finance", on_delete=models.DO_NOTHING, null=True, blank=True)
    management_choice = (('Manager', 'Manager'),
                         ('Regional Manager', 'Regional Manager'),
                         ('Worker', 'Worker'))
    management_status = models.CharField(max_length=100, choices=management_choice, default="Worker")

    working_choice = (('Resigned', 'Resigned'), ('Onboarded', 'Onboarded'), ('Cold', 'Cold'))
    working_status = models.CharField(max_length=100, choices=working_choice, default="Onboarded")

    def __str__(self):
        return self.user.name

    class Meta:
        ordering = ('-management_status',)
