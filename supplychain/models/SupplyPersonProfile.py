from django.db import models


class SupplyPersonProfile(models.Model):
    user = models.OneToOneField('custom_auth.User', on_delete=models.CASCADE, related_name="supply")

    warehouse = models.ForeignKey('warehouse.Warehouse',
                                  related_name="warehouse_supply", on_delete=models.DO_NOTHING)

    management_choice = (('Manager', 'Manager'),
                         ('Regional Manager', 'Regional Manager'),
                         ('Worker', 'Worker'))
    management_status = models.CharField(max_length=100, choices=management_choice, default="Worker")


    def __str__(self):
        return self.user.name
