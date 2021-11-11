from django.db import models



class UserRetailerFilters(models.Model):
    beat = models.PositiveIntegerField(default=0)
    commission = models.PositiveIntegerField(default=0)
    retailer_status = models.CharField(default="Onboarded", max_length=100)
    salesPerson = models.IntegerField(default=0)
    name = models.CharField(max_length=100, default="Filter")

    class Meta:
        ordering = ('id',)
