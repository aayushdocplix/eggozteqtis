from django.db import models

from distributionchain.models import DistributionPersonProfile


class SalesPersonProfile(models.Model):
    user = models.OneToOneField('custom_auth.User', on_delete=models.DO_NOTHING, related_name="sales")
    warehouse = models.ForeignKey('warehouse.Warehouse',
                                  related_name="warehouse_sales", on_delete=models.DO_NOTHING)

    distributionPersonProfile = models.ForeignKey(DistributionPersonProfile, on_delete=models.DO_NOTHING, blank=True, null=True)

    management_choice = (('Manager', 'Manager'),
                         ('Regional Manager', 'Regional Manager'),
                         ('Worker', 'Worker'))
    management_status = models.CharField(max_length=100, choices=management_choice, default="Worker")
    demand_classification = models.CharField(max_length=200, default="Gurgaon-GT")

    working_choice = (('Resigned', 'Resigned'), ('Onboarded', 'Onboarded'), ('Cold', 'Cold'))
    working_status = models.CharField(max_length=100, choices=working_choice, default="Onboarded")
    is_test_profile = models.BooleanField(default=False)
    is_adhoc_profile = models.BooleanField(default=False)
    is_mt_profile = models.BooleanField(default=False)
    is_visible = models.BooleanField(default=False)

    def __str__(self):
        return self.user.name

    class Meta:
        ordering = ('-management_status',)


class SalesEggsdata(models.Model):
    salesPerson = models.ForeignKey(SalesPersonProfile,
                                  related_name="eggs_salesperson", on_delete=models.DO_NOTHING)
    brown = models.PositiveIntegerField(default=0)
    white = models.PositiveIntegerField(default=0)
    nutra = models.PositiveIntegerField(default=0)
    date = models.DateField()
