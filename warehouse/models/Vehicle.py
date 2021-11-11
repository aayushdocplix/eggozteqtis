from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

from warehouse.models.WarehouseEmployee import WarehousePersonProfile


class Vehicle(models.Model):
    vehicle_desc = models.CharField(max_length=256,null=True)
    vehicle_no = models.CharField(max_length=254, unique=True, default="Vehicle No")
    VEHICLE_TYPES = (('Echo', 'Echo'),
                     ('PIAGGIO', 'PIAGGIO'),
                     ('TATA ACE','TATA ACE'),
                     ('AUTO', 'AUTO'),
                     ('ASHOK LEYLAND','ASHOK LEYLAND'),
                     ('Bolero','Bolero'),
                     ('OTHER', 'OTHER'))
    vehicle_identifier = models.CharField(max_length=254, choices=VEHICLE_TYPES, default="Echo")
    vehicle_identifier_type = models.CharField(max_length=254, default="Echo")

    vendor = models.CharField(max_length=254, default="vendor name")
    vendor_contact_no = PhoneNumberField(region='IN', default="+911234567890")
    vehicle_photo_url = models.CharField(max_length=254, null=True)
    vendor_photo_url = models.CharField(max_length=254, null=True)
    STATUS_CHOICES = (('Online', 'Online'), ('Offline', 'Offline'),
                      ('In Transit', 'In Transit'),
                      ('In Trip', 'In Trip'))
    vehicle_status = models.CharField(max_length=100, choices=STATUS_CHOICES, default="Online")

    per_day_charge = models.DecimalField(max_digits=12,decimal_places=3, default=0)
    per_day_duration = models.PositiveIntegerField(default=12)
    per_day_duration_type = models.CharField(default="Hr", max_length=200)
    per_day_distance = models.PositiveIntegerField(default=89)
    per_day_distance_type = models.CharField(default="Km", max_length=200)
    default_driver = models.ForeignKey('warehouse.Driver', on_delete=models.DO_NOTHING, null=True, blank=True)

    class Meta:
        ordering = ("-pk",)

    def __str__(self):
        return self.vehicle_no


class AdhocVehicle(models.Model):
    vehicle_desc = models.CharField(max_length=256, null=True)
    vehicle_no = models.CharField(max_length=254, default="Vehicle No")

    vehicle_identifier_type = models.CharField(max_length=254, default="Echo")

    vendor = models.CharField(max_length=254, default="vendor name")
    vendor_contact_no = PhoneNumberField(region='IN', default="+911234567890")
    vehicle_photo_url = models.CharField(max_length=254, null=True)
    vendor_photo_url = models.CharField(max_length=254, null=True)
    STATUS_CHOICES = (('Online', 'Online'), ('Offline', 'Offline'),
                      ('In Transit', 'In Transit'),
                      ('In Trip', 'In Trip'))
    vehicle_status = models.CharField(max_length=100, choices=STATUS_CHOICES, default="Online")

    per_day_charge = models.DecimalField(max_digits=12,decimal_places=3, default=0)
    per_day_duration = models.PositiveIntegerField(default=12)
    per_day_duration_type = models.CharField(default="Hr", max_length=200)
    per_day_distance = models.PositiveIntegerField(default=89)
    per_day_distance_type = models.CharField(default="Km", max_length=200)
    driver_name = models.CharField(max_length=200, default="driver Name")

    class Meta:
        ordering = ("-pk",)

    def __str__(self):
        return self.vehicle_no

class Driver(models.Model):
    driver_name = models.CharField(max_length=256, default="name")
    driver_desc = models.CharField(max_length=256, default="desc")
    driver_no = PhoneNumberField(region='IN', default="+911234567890")
    driver_license_no = models.CharField(max_length=254, unique=True, default="license")
    driver_photo_url = models.CharField(max_length=254, null=True)
    license_photo_url = models.CharField(max_length=254, null=True)
    STATUS_CHOICES = (('Online', 'Online'), ('Offline', 'Offline'))
    driver_status = models.CharField(max_length=100, choices=STATUS_CHOICES, default="Online")

    def __str__(self):
        return self.driver_name


class VehicleAssignment(models.Model):
    date = models.DateTimeField()
    driver = models.ForeignKey(Driver, on_delete=models.DO_NOTHING, null=True, blank=True,
                               related_name="driver_assignment")
    vehicle = models.ForeignKey(Vehicle, on_delete=models.DO_NOTHING, null=True, blank=True,
                                related_name="vehicle_assignment")
    OPERATION_CHOICES = (('Egg Pick up', 'Egg Pick up'), ('Delivery', 'Delivery'))
    operation_option = models.CharField(max_length=100, choices=OPERATION_CHOICES)
    delivery_person = models.ForeignKey('custom_auth.User', blank=True, null=True, on_delete=models.DO_NOTHING,
                                        related_name="delivery_person_assignment")
    warehouseEmployee = models.ForeignKey(WarehousePersonProfile, blank=True, null=True, on_delete=models.DO_NOTHING)
    STATUS_CHOICES = (('Assigned', 'Assigned'), ('OnTheWay', 'OnTheWay'), ('Done', 'Done'))
    status = models.CharField(max_length=100, choices=STATUS_CHOICES, default="Assigned")
    desc = models.CharField(max_length=256)

    def __str__(self):
        return str(self.vehicle.vehicle_no)

    class Meta:
        ordering = ('-pk',)
