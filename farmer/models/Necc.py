from datetime import datetime

from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from Eggoz.settings import CURRENT_ZONE
from base.models.Cluster import EditableTimeStampedModel


class NECCZone(models.Model):
    name = models.CharField(max_length=200, unique=True)
    desc = models.CharField(max_length=254, default="desc")

    def __str__(self):
        return self.name


class NECCCity(models.Model):
    zone = models.ForeignKey(NECCZone, on_delete=models.DO_NOTHING, related_name="necczonecity", null=True, blank=True)
    name = models.CharField(max_length=200, unique=True)
    desc = models.CharField(max_length=254, default="desc")

    def __str__(self):
        return self.name


class CityNECCRate(EditableTimeStampedModel):
    necc_city = models.ForeignKey(NECCCity, related_name="necc_city_rate", on_delete=models.PROTECT)
    currency = models.CharField(
        max_length=3,
        default="INR",
    )
    current_rate = models.DecimalField(max_digits=12,
                                       decimal_places=3, default=0)

    def __str__(self):
        return self.necc_city.name

    __original_rate = None

    def __init__(self, *args, **kwargs):
        super(CityNECCRate, self).__init__(*args, **kwargs)
        self.__original_rate = self.current_rate

    def save(self, *args, **kwargs):
        if self.current_rate != self.__original_rate:
            if NECCPriceStamp.objects.filter(city_necc_rate=self).last():
                stamp = NECCPriceStamp.objects.filter(city_necc_rate=self).last()
                stamp.end_date = datetime.now(tz=CURRENT_ZONE)
                stamp.save()
            NECCPriceStamp.objects.create(city_necc_rate=self, start_date=datetime.now(tz=CURRENT_ZONE),
                                          rate_value=self.current_rate)
        self.modified_at = datetime.now(tz=CURRENT_ZONE)
        super(CityNECCRate, self).save(*args, **kwargs)


class NECCPriceStamp(models.Model):
    city_necc_rate = models.ForeignKey(CityNECCRate, on_delete=models.DO_NOTHING)
    rate_value = models.DecimalField(max_digits=12,
                                     decimal_places=3, default=0)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.city_necc_rate.necc_city.name
