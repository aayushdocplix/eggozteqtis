import uuid

from django.utils import timezone
from django.db import models
from uuid_upload_path import upload_to

from custom_auth.models import User
from farmer.models import Farmer
from procurement.constants import EGG_TYPES, UNBRANDED_TYPE
from product.models import Product
from warehouse.models import Warehouse


def batch_generator():
    return 'BAT_' + str(uuid.uuid4().int)[:9]

def un_branded_batch_generator():
    return 'UNB' + str(uuid.uuid4().int)[:9]


class Procurement(models.Model):
    farmer = models.ForeignKey(Farmer, on_delete=models.DO_NOTHING, null=True)
    procurement_bill_url = models.CharField(max_length=200, blank=True, null=True)
    additional_charge = models.FloatField(default=0)


class BatchModel(models.Model):
    batch_id = models.CharField(max_length=15, default=batch_generator, unique=True, db_index=True)
    egg_type = models.CharField(max_length=30, choices=EGG_TYPES, null=False, blank=False)
    procurement = models.ForeignKey(Procurement, on_delete=models.DO_NOTHING, unique=False)
    egg_ph = models.FloatField(default=0)
    batch_egg_image_url = models.CharField(blank=True, null=True, max_length=200)
    date = models.DateField(default=timezone.now, null=False)
    expected_egg_count = models.IntegerField(default=0, null=False)
    actual_egg_count = models.IntegerField(default=0, null=False)
    expected_egg_price = models.FloatField(default=0)
    actual_egg_price = models.FloatField(default=0)
    quality_param1 = models.CharField(null=True, blank=True, max_length=100)
    quality_param2 = models.CharField(null=True, max_length=100, blank=True)
    quality_param3 = models.CharField(null=True, max_length=100, blank=True)
    updated_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.batch_id


class BatchPerWarehouse(models.Model):
    batch = models.OneToOneField(BatchModel, on_delete=models.DO_NOTHING)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.DO_NOTHING, null=False, default=1)


class EggsIn(models.Model):
    batch = models.OneToOneField(BatchModel, on_delete=models.DO_NOTHING, null=True)
    date = models.DateTimeField(default=timezone.now, null=False)
    egg_loss = models.IntegerField(null=False, default=0)
    egg_chatki = models.IntegerField(null=False, default=0)
    egg_in = models.IntegerField(null=False, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=True, blank=True)


class EggQualityCheck(models.Model):
    batch = models.OneToOneField(BatchModel, db_column='batch_id', on_delete=models.DO_NOTHING, null=True)
    start_time = models.DateTimeField(default=timezone.now, null=False)
    end_time = models.DateTimeField(default=timezone.now, null=False)
    egg_chatki = models.IntegerField(default=0, null=False)
    egg_loss = models.IntegerField(default=0, null=False)
    egg_count = models.IntegerField(default=0, null=False)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    egg_ph = models.FloatField(default=0)
    haught_unit = models.FloatField(default=0)
    egg_color_unit = models.FloatField(default=0)
    chatki_percent = models.FloatField(default=0)
    avg_weight = models.FloatField(default=0)
    dirty_percent = models.FloatField(default=0)
    shape_size_percent = models.FloatField(default=0)
    egg_used = models.IntegerField(default=0, null=False)


class EggCleaning(models.Model):
    batch_id = models.ForeignKey(BatchModel, db_column='batch_id', on_delete=models.DO_NOTHING, null=True)
    team_name = models.CharField(max_length=20, null=True, blank=True)
    start_time = models.DateTimeField(default=timezone.now, null=True)
    end_time = models.DateTimeField(default=timezone.now, null=True)
    egg_chatki = models.IntegerField(default=0, null=False)
    egg_loss = models.IntegerField(default=0, null=False)
    egg_count = models.IntegerField(default=0, null=False)
    updated_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=True, blank=True)


class Package(models.Model):
    batch_id = models.ForeignKey(BatchModel, db_column='batch_id', on_delete=models.DO_NOTHING, null=True)
    product = models.ForeignKey(Product, on_delete=models.DO_NOTHING, null=True)
    start_time = models.DateTimeField(default=timezone.now, null=False)
    egg_chatki = models.IntegerField(default=0, null=False)
    egg_loss = models.IntegerField(default=0, null=False)
    # Flawless eggs or best quality eggs
    package_count = models.IntegerField(default=1, null=False)
    updated_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=True, blank=True)


class ReturnedPackage(models.Model):
    package = models.ForeignKey(Package, on_delete=models.DO_NOTHING, null=True)
    date = models.DateTimeField(default=timezone.now, null=False)
    egg_type = models.CharField(max_length=20, choices=EGG_TYPES, null=False)
    updated_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=True, blank=True)


class ImageUpload(models.Model):
    image = models.FileField(upload_to=upload_to)
    created_at = models.DateTimeField(default=timezone.now,)


# class MovetoUnbranded(models.Model):
#     batch = models.OneToOneField(BatchModel, on_delete=models.DO_NOTHING, null=True)
#     date = models.DateTimeField(default=timezone.now, null=False)
#     egg_in = models.IntegerField(null=False, default=0)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=True, blank=True)
#     type = models.CharField(max_length=30, choices=UNBRANDED_TYPE, null=False, blank=False)
#     is_active = models.BooleanField(default=True)
#
#
# class UnbrandedRecord(models.Model):
#     egg_in = models.IntegerField(null=False, default=0)
#     egg_type = models.CharField(max_length=30, choices=EGG_TYPES, null=False, blank=False)