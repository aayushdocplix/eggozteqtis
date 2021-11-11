from django.db import models
from django.utils.timezone import now
from phonenumber_field.modelfields import PhoneNumberField

from product.models import Product


class DistributionPersonProfile(models.Model):
    user = models.OneToOneField('custom_auth.User', on_delete=models.DO_NOTHING, related_name="distribution")
    warehouse = models.ForeignKey('warehouse.Warehouse',
                                  related_name="warehouse_distribution", on_delete=models.DO_NOTHING)

    management_choice = (('Manager', 'Manager'),
                         ('Regional Manager', 'Regional Manager'),
                         ('Worker', 'Worker'))
    management_status = models.CharField(max_length=100, choices=management_choice, default="Worker")

    working_choice = (('Resigned', 'Resigned'), ('Onboarded', 'Onboarded'), ('Cold', 'Cold'))
    working_status = models.CharField(max_length=100, choices=working_choice, default="Onboarded")
    is_test_profile = models.BooleanField(default=False)
    is_ecomm = models.BooleanField(default=False)

    def __str__(self):
        return self.user.name

    class Meta:
        ordering = ('-management_status',)


class DistributionEggsdata(models.Model):
    distributionPerson = models.ForeignKey(DistributionPersonProfile,
                                  related_name="eggs_distributionperson", on_delete=models.DO_NOTHING)
    brown = models.PositiveIntegerField(default=0)
    white = models.PositiveIntegerField(default=0)
    nutra = models.PositiveIntegerField(default=0)
    date = models.DateField()


class BeatWarehouseSupply(models.Model):
    supply_white_percentage = models.PositiveIntegerField(default=0)
    supply_brown_percentage = models.PositiveIntegerField(default=0)
    supply_nutra_percentage = models.PositiveIntegerField(default=0)
    unpacked_white_eggs = models.PositiveIntegerField(default=0)
    unpacked_brown_eggs = models.PositiveIntegerField(default=0)
    unpacked_nutra_eggs = models.PositiveIntegerField(default=0)
    beat_date = models.DateField(null=True, blank=True)
    beat_supply_by = models.ForeignKey('warehouse.WarehousePersonProfile', on_delete=models.DO_NOTHING, null=True,
                                       blank=True,
                                       related_name="beatWarehouseSupplyPerson")

    def __str__(self):
        return str(self.beat_date)


class SMRelativeNumber(models.Model):
    egg_type = models.CharField(max_length=200, default='White')
    relative_number = models.PositiveIntegerField(default=100)
    demand_classification = models.CharField(max_length=200, default="Gurgaon-GT")
    name = models.CharField(max_length=200, default="GGT-W")
    date = models.DateField(null=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('date',)


class BeatSMApproval(models.Model):
    beat_warehouse_supply = models.ForeignKey(BeatWarehouseSupply, on_delete=models.DO_NOTHING, null=True, blank=True,
                                              related_name="sm_warehouse_supply")
    supply_white_relative = models.PositiveIntegerField(default=0)
    supply_brown_relative = models.PositiveIntegerField(default=0)
    supply_nutra_relative = models.PositiveIntegerField(default=0)

    beat_date = models.DateField(null=True, blank=True)
    demand_classification = models.CharField(max_length=200, default="Gurgaon-GT")
    beat_supply_approved_by = models.ForeignKey('saleschain.SalesPersonProfile', on_delete=models.DO_NOTHING, null=True,
                                                blank=True,
                                                related_name="beatSupplySMApprover")

    def __str__(self):
        return "{} - {}".format(self.demand_classification, str(self.beat_date))


class BeatRHApproval(models.Model):
    beatSMApproval = models.ForeignKey(BeatSMApproval, on_delete=models.DO_NOTHING, null=True, blank=True,
                                       related_name="beat_sm_approval")
    supply_white_percentage = models.PositiveIntegerField(default=0)
    supply_brown_percentage = models.PositiveIntegerField(default=0)
    supply_nutra_percentage = models.PositiveIntegerField(default=0)
    beat_date = models.DateField(null=True, blank=True)
    beat_supply_approved_by = models.ForeignKey('saleschain.SalesPersonProfile', on_delete=models.DO_NOTHING, null=True,
                                                blank=True,
                                                related_name="beatSupplyRHApprover")

    def __str__(self):
        return str(self.beat_date)


class BeatAssignment(models.Model):
    assigned_by = models.ForeignKey(DistributionPersonProfile, on_delete=models.DO_NOTHING, null=True, blank=True,
                                    related_name="asignee")
    distributor = models.ForeignKey(DistributionPersonProfile, on_delete=models.DO_NOTHING, null=True, blank=True,
                                    related_name="beatDistributor")
    beat_person = models.ForeignKey('custom_auth.User', blank=True, null=True, on_delete=models.DO_NOTHING,
                                        related_name="beat_person_assignment")
    beat_demand_by = models.ForeignKey('saleschain.SalesPersonProfile', on_delete=models.DO_NOTHING, null=True, blank=True,
                                    related_name="beatDemandPerson")
    beat_supply_by = models.ForeignKey('warehouse.WarehousePersonProfile', on_delete=models.DO_NOTHING, null=True, blank=True,
                                    related_name="beatSupplyPerson")
    beat_supply_approved_by = models.ForeignKey('saleschain.SalesPersonProfile', on_delete=models.DO_NOTHING, null=True, blank=True,
                                       related_name="beatDemandApprover")
    warehouse =models.ForeignKey('warehouse.Warehouse', on_delete=models.DO_NOTHING, null=True, blank=True,
                                    related_name="beatWarehouse")
    demand_classification = models.CharField(max_length=200,default="Gurgaon-GT")
    PRIORITY = (('High', 'High'), ('Medium', 'Medium'), ('Normal','Normal'))
    priority = models.CharField(choices=PRIORITY, max_length=200,default="Normal")
    TYPES = (('Demand','Demand'),
             ('Supply','Supply'),
             ('SMApproved','SMApproved'),
             ('RHApproved','RHApproved'),
             ('Approved','Approved'),
             ('Reported', 'Reported'),
             ('Loaded','Loaded'),
             ('Closed', 'Closed'))
    beat_material_status = models.CharField(max_length=200, default="Demand", choices=TYPES)
    beat_date = models.DateField(null=True, blank=True)
    beat_expected_time = models.TimeField(null=True, blank=True)
    beat_time = models.TimeField(null=True, blank=True)
    beat_number = models.PositiveIntegerField(default=0)
    BEAT_TYPES= (('Adhoc','Adhoc'),('Regular', 'Regular'))
    beat_type = models.CharField(choices=BEAT_TYPES, max_length=200, default="Regular")
    beat_type_number = models.PositiveIntegerField(default=0)
    beat_name = models.CharField(max_length=200, default="name")
    STATUSES = (('Ongoing', 'Ongoing'), ('Completed', 'Completed'),('Assigned', 'Assigned'), ("Scheduled", "Scheduled"),("Planned", "Planned"))
    beat_status = models.CharField(max_length=200, choices=STATUSES, default='Planned')
    driver = models.ForeignKey('warehouse.Driver', on_delete=models.DO_NOTHING, null=True, blank=True,
                               related_name="beat_driver_assignment")
    vehicle = models.ForeignKey('warehouse.Vehicle', on_delete=models.DO_NOTHING, null=True, blank=True,
                                related_name="beat_vehicle_assignment")
    adhoc_vehicle = models.ForeignKey('warehouse.AdhocVehicle', on_delete=models.DO_NOTHING, null=True, blank=True,
                                related_name="beat_vehicle_assignment")
    sc_in_time = models.TimeField(null=True,blank=True)
    in_time = models.TimeField(null=True,blank=True)
    out_time = models.TimeField(null=True, blank=True)
    return_time = models.TimeField(null=True, blank=True)
    ODO_in = models.IntegerField(default=0)
    ODO_return = models.IntegerField(default=0)
    STATUS = (('Open', 'Open'),('Closed', 'Closed'))
    distributor_trip_status = models.CharField(choices=STATUS, default="Open", max_length=150)
    warehouse_trip_status = models.CharField(choices=STATUS, default="Open", max_length=150)
    finance_trip_status = models.CharField(choices=STATUS, default="Open", max_length=150)
    beatRHApproval = models.ForeignKey(BeatRHApproval, on_delete=models.DO_NOTHING, null=True, blank=True,
                                related_name="beat_rh_approval")

    class Meta:
        unique_together=('beat_date', 'beat_number', 'beat_type', 'beat_type_number')
        ordering = ('beat_date',)

    def __str__(self):
        return "{} - {}".format(str(self.beat_number),str(self.beat_date))


class TripSKUTransfer(models.Model):
    TYPES = (('warehouse', 'warehouse'), ('beat', 'beat'), ('satellite', 'satellite'), ('w-beat','w-beat'))
    transfer_type = models.CharField(choices=TYPES, default='beat', max_length=200)
    transfer_status = models.CharField(default="Pending", max_length=200)
    from_distributor = models.ForeignKey(DistributionPersonProfile, on_delete=models.DO_NOTHING, null=True, blank=True,
                                    related_name="transferByDistributor")
    to_distributor = models.ForeignKey(DistributionPersonProfile, on_delete=models.DO_NOTHING, null=True, blank=True,
                                       related_name="transferToDistributor")
    from_warehouse = models.ForeignKey('warehouse.Warehouse', on_delete=models.DO_NOTHING, null=True, blank=True,
                                    related_name="transferFromWarehouse")
    to_warehouse = models.ForeignKey('warehouse.Warehouse', on_delete=models.DO_NOTHING, null=True, blank=True,
                                    related_name="transferToWarehouse")
    from_warehouse_person = models.ForeignKey('warehouse.WarehousePersonProfile', on_delete=models.DO_NOTHING, null=True, blank=True,
                                    related_name="transferSentBy")
    to_warehouse_person = models.ForeignKey('warehouse.WarehousePersonProfile', on_delete=models.DO_NOTHING, null=True, blank=True,
                                    related_name="transferAcceptedBy")
    from_beat = models.ForeignKey('distributionchain.BeatAssignment', on_delete=models.DO_NOTHING, null=True, blank=True,
                                    related_name="transferByBeat")
    to_beat = models.ForeignKey('distributionchain.BeatAssignment', on_delete=models.DO_NOTHING, null=True, blank=True,
                                  related_name="transferToBeat")
    beat_date =models.DateField(null=True)
    transferred_at =models.TimeField(default=now)

    def __str__(self):
        if self.from_beat:
            if self.to_beat:
                return "{} -To- {}".format(self.from_beat.beat_name, self.to_beat.beat_name)
            else:
                return "{} -To- {}".format(self.from_beat.beat_name, self.to_warehouse.name)
        else:
            if self.to_warehouse:
                return "{} -To- {}".format(self.from_warehouse.name, self.to_warehouse.name)
            else:
                return "{} -To- {}".format(self.from_warehouse.name, self.to_beat.beat_name)


class TransferSKU(models.Model):
    tripSKUTransfer = models.ForeignKey(TripSKUTransfer, on_delete=models.CASCADE,
                                             null=True, blank=True, related_name="tripTransferSKU")
    product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.CASCADE,
                                related_name="transferSKUProduct")
    quantity = models.PositiveIntegerField(default=0)