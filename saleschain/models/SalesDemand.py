from django.db import models

from distributionchain.models import BeatAssignment, BeatSMApproval, BeatWarehouseSupply, BeatRHApproval
from product.models import Product


class RetailerDemand(models.Model):
    retailer = models.ForeignKey('retailer.Retailer', null=True, blank=True, related_name="demand_retailer",
                                 on_delete=models.DO_NOTHING)
    beatAssignment = models.ForeignKey(BeatAssignment, null=True, blank=True, related_name="demand_beat_assignment",
                                       on_delete=models.DO_NOTHING)
    date = models.DateField()
    time = models.TimeField()

    PRIORITY = (('High', 'High'), ('Medium', 'Medium'), ('Normal', 'Normal'))
    priority = models.CharField(choices=PRIORITY, max_length=200, default="Normal")

    STATUSES = (('Declined', 'Declined'), ('Shop Stock Available', 'Shop Stock Available'),
                ('Trip Stock Over', 'Trip Stock Over'), ('Trip Time Over', 'Trip Time Over'),
                ('Cancelled', 'Cancelled'), ('Returned', 'Returned'), ('Replaced', 'Replaced'),
                ('Sales Booked', 'Sales Booked'), ('No Action', 'No Action'))
    retailer_status = models.CharField(choices=STATUSES, default="No Action", max_length=150)

    def __str__(self):
        return self.retailer.code


class RetailerDemandSKU(models.Model):
    retailerDemand = models.ForeignKey(RetailerDemand, null=True, blank=True, on_delete=models.CASCADE,
                                       related_name="demandSKU")
    product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.CASCADE,
                                related_name="demandSKUProduct")
    product_quantity = models.PositiveIntegerField(default=0)
    product_supply_quantity = models.PositiveIntegerField(default=0)
    product_out_quantity = models.PositiveIntegerField(default=0)
    product_replacement_quantity = models.PositiveIntegerField(default=0)
    product_return_quantity = models.PositiveIntegerField(default=0)
    product_sold_quantity = models.PositiveIntegerField(default=0)
    product_in_quantity = models.PositiveIntegerField(default=0)
    product_transfer_quantity = models.IntegerField(default=0)
    product_fresh_in_quantity = models.PositiveIntegerField(default=0)
    product_return_repalce_in_quantity = models.PositiveIntegerField(default=0)

    product_fresh_stock_validated = models.CharField(default="Not Yet", max_length=100)
    product_old_stock_validated = models.CharField(default="Not Yet", max_length=100)


def __str__(self):
    return self.retailerDemand.retailer.code


class SalesSupplySKU(models.Model):
    beatWarehouseSupply = models.ForeignKey(BeatWarehouseSupply, null=True, blank=True,
                                            related_name="sales_supply_beat",
                                            on_delete=models.DO_NOTHING)
    product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.CASCADE,
                                related_name="salesSupplySKUProduct")
    product_quantity = models.PositiveIntegerField(default=0)


class SalesSupplyPackedSKU(models.Model):
    beatWarehouseSupply = models.ForeignKey(BeatWarehouseSupply, null=True, blank=True,
                                            related_name="sales_packed_sku",
                                            on_delete=models.DO_NOTHING)
    product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.CASCADE,
                                related_name="salesPackedSKUProduct")
    product_quantity = models.PositiveIntegerField(default=0)


class SalesSMApprovalSKU(models.Model):
    beatSMApproval = models.ForeignKey(BeatSMApproval, null=True, blank=True, related_name="sales_sm_approval_beat",
                                       on_delete=models.DO_NOTHING)
    product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.CASCADE,
                                related_name="salesSMApprovalSKUProduct")
    product_quantity = models.PositiveIntegerField(default=0)
    demand_classification = models.CharField(max_length=200, default="Gurgaon-GT")


class SalesRHApprovalSKU(models.Model):
    beatRHApproval = models.ForeignKey(BeatRHApproval, null=True, blank=True, related_name="sales_rh_approval_beat",
                                       on_delete=models.DO_NOTHING)
    product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.CASCADE,
                                related_name="salesRHApprovalSKUProduct")
    product_quantity = models.PositiveIntegerField(default=0)


class SalesDemandSKU(models.Model):
    beatAssignment = models.ForeignKey(BeatAssignment, null=True, blank=True, related_name="sales_demand_beat",
                                       on_delete=models.DO_NOTHING)
    salesRHApprovalSKU = models.ForeignKey(SalesRHApprovalSKU, null=True, blank=True,
                                           related_name="sales_rh_approval_sku",
                                           on_delete=models.DO_NOTHING)
    product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.CASCADE,
                                related_name="salesdemandSKUProduct")
    product_quantity = models.PositiveIntegerField(default=0)
    product_supply_quantity = models.PositiveIntegerField(default=0)
    product_out_quantity = models.PositiveIntegerField(default=0)
    product_replacement_quantity = models.PositiveIntegerField(default=0)
    product_return_quantity = models.PositiveIntegerField(default=0)
    product_sold_quantity = models.PositiveIntegerField(default=0)
    product_in_quantity = models.PositiveIntegerField(default=0)
    product_transfer_quantity = models.IntegerField(default=0)
    product_fresh_in_quantity = models.PositiveIntegerField(default=0)
    product_return_repalce_in_quantity = models.PositiveIntegerField(default=0)

    product_fresh_stock_validated = models.CharField(default="Not Yet", max_length=100)
    product_old_stock_validated = models.CharField(default="Not Yet", max_length=100)

    def __str__(self):
        return "{}-{}".format(str(self.beatAssignment.beat_number), str(self.beatAssignment.beat_date))
