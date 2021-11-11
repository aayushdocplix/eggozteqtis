from django.db import models

from distributionchain.models import DistributionPersonProfile


class TimeStampedModel(models.Model):
    """An abstract base class model that provides self-updating
    ``created`` and ``modified`` fields with UUID as primary_key field.
    """
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        abstract = True


class EditableTimeStampedModel(models.Model):
    """An abstract base class model that provides self-updating
    ``created`` and ``modified`` fields with UUID as primary_key field.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Zone(models.Model):
    zone_name = models.CharField(max_length=50, unique=True)
    is_ecommerce = models.BooleanField(default=False)

    def __str__(self):
        return self.zone_name


class City(models.Model):
    city_name = models.CharField(max_length=50, unique=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    city_string = models.CharField(max_length=5, default="G")
    zone = models.ForeignKey(Zone, on_delete=models.DO_NOTHING,related_name='cities', blank=True, null=True)
    is_ecommerce = models.BooleanField(default=False)

    def __str__(self):
        return self.city_name


class Cluster(models.Model):
    cluster_name = models.CharField(max_length=200, unique=True)
    city = models.ForeignKey(City, on_delete=models.DO_NOTHING)
    is_ecommerce = models.BooleanField(default=False)

    def __str__(self):
        return self.cluster_name


class Sector(models.Model):
    sector_name = models.CharField(max_length=50)
    cluster = models.ForeignKey(Cluster, on_delete=models.DO_NOTHING)
    is_ecommerce = models.BooleanField(default=False)

    def __str__(self):
        return self.sector_name

    class Meta:
        unique_together = ('sector_name', 'cluster')


class EcommerceSector(models.Model):
    sector_name = models.CharField(max_length=150)
    city = models.ForeignKey(City, on_delete=models.CASCADE,related_name='ecommerceSectors', null=True, blank=True)
    cluster = models.ForeignKey(Cluster, on_delete=models.CASCADE,related_name='ecommerceSectors', null=True, blank=True)
    is_ecommerce = models.BooleanField(default=False)
    pinCode = models.IntegerField(null=True, blank=True)
    distributor = models.ForeignKey(DistributionPersonProfile, on_delete=models.CASCADE,related_name='ecommerceDistributor', null=True, blank=True)

    def __str__(self):
        return self.sector_name

    class Meta:
        unique_together = ('sector_name', 'city')