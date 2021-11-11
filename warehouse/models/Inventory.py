from typing import Set

from django.db import models
from django.db.models import F, Sum
from django.db.models.functions import Coalesce

from base.models import Cluster, City
from custom_auth.models.Address import Address
from distributionchain.models import BeatAssignment
from farmer.models import Farm
from operationschain.models import OperationsPersonProfile
from product.models.BaseProduct import BaseProduct
from product.models.Product import ProductDivision, Product, ProductSubDivision
from supplychain.models import SupplyPersonProfile
from warehouse.models import WarehousePersonProfile
from .Vehicle import Vehicle, Driver


class WarehouseQueryset(models.QuerySet):
    def prefetch_data(self):
        return self.select_related("address").prefetch_related("city")

    def for_city(self, city: str):
        return (
            self.prefetch_data()
                .filter(city=city)
                .order_by("pk")
        )


class Warehouse(models.Model):
    name = models.CharField(max_length=250)
    slug = models.SlugField(max_length=255, unique=True, allow_unicode=True)
    city = models.ForeignKey(City, null=False, blank=False, on_delete=models.DO_NOTHING)
    cluster = models.ForeignKey(Cluster, null=True, blank=True, on_delete=models.DO_NOTHING)
    clusters = models.ManyToManyField(Cluster, blank=True, related_name="warehouseClusters")
    address = models.ForeignKey(Address, on_delete=models.PROTECT)
    TYPE = (('EPC', 'EPC'),
            ('Distribution', 'Distribution'))
    warehouse_type = models.CharField(choices=TYPE, default='EPC', max_length=100)
    objects = WarehouseQueryset.as_manager()

    class Meta:
        ordering = ("-slug",)

    def __str__(self):
        return self.name

    @property
    def city_code(self) -> Set[str]:
        return self.city.name

    @property
    def cluster_code(self) -> Set[str]:
        return self.cluster.cluster_name

    def delete(self, *args, **kwargs):
        address = self.address
        super().delete(*args, **kwargs)
        address.delete()


class StockSourceDestinationData(models.Model):
    dataId = models.IntegerField(default=0)
    dataName = models.CharField(max_length=200, default="Name")
    CHOICES = (('Farmer', 'Farmer'),
               ('Vehicle', 'Vehicle'),
               ('Warehouse', 'Warehouse'),
               ('Operations', 'Operations'),
               ('Qc', 'Qc'))
    dataProfile = models.CharField(choices=CHOICES, max_length=200, default="Farmer")


class Stock(models.Model):
    batch_id = models.CharField(max_length=200)
    warehouse = models.ForeignKey(Warehouse, null=True, blank=True, on_delete=models.CASCADE,
                                  related_name="warehouse_Stock")
    farm = models.ForeignKey(Farm, null=True, blank=True, on_delete=models.CASCADE)
    supplyPerson = models.ForeignKey(SupplyPersonProfile, on_delete=models.DO_NOTHING, related_name="stockSupplyPerson")
    warehousePerson = models.ForeignKey(WarehousePersonProfile, null=True, blank=True, on_delete=models.DO_NOTHING,
                                        related_name="stockWarehouseManager")
    operationsPerson = models.ForeignKey(OperationsPersonProfile, null=True, blank=True, on_delete=models.DO_NOTHING,
                                         related_name="stockOperationsManager")

    driver = models.ForeignKey(Driver, null=True, blank=True, on_delete=models.CASCADE)
    vehicle = models.ForeignKey(Vehicle, null=True, blank=True, on_delete=models.CASCADE)
    productDivision = models.ForeignKey(
        ProductDivision, null=False, on_delete=models.DO_NOTHING, related_name="stocksproductdivision"
    )

    from_source = models.ForeignKey(StockSourceDestinationData, on_delete=models.DO_NOTHING, null=True, blank=True,
                                    related_name="stock_from")
    to_destination = models.ForeignKey(StockSourceDestinationData, on_delete=models.DO_NOTHING, null=True, blank=True,
                                       related_name="stock_to")
    is_forwarded = models.BooleanField(default=False)
    STATUS = (('Picked up', 'Picked up'),
              ('Received', 'Received'),
              ('Qc Done', 'Qc Done'),
              ('Inventory', 'Inventory'))
    stock_status = models.CharField(choices=STATUS, default="Picked up", max_length=200)
    received_at = models.DateTimeField(null=True)
    picked_at = models.DateTimeField(null=True)
    qc_done_at = models.DateTimeField(null=True)

    class Meta:
        unique_together = ('batch_id', 'stock_status')
        ordering = ['-id']


class StockInline(models.Model):
    baseProduct = models.ForeignKey(
        BaseProduct, null=False, blank=False, on_delete=models.DO_NOTHING, related_name="stock_base_products"
    )
    stock = models.ForeignKey(Stock, related_name="stock_inline",
                              on_delete=models.CASCADE)

    stock_note = models.CharField(max_length=200, default="remarks")


class EggProductStockInline(models.Model):
    stock_inline = models.ForeignKey(StockInline, related_name="product_type_stock_inline",
                                     on_delete=models.CASCADE)
    name = models.CharField(max_length=256)
    desc = models.CharField(max_length=256)
    SKU_CHOICES = (('Full', 'Full Tray'),
                   ('Single', 'Single'),
                   ('Chatki', 'Chatki'))
    sku_type = models.CharField(choices=SKU_CHOICES, max_length=100)
    quantity = models.IntegerField()


class InventoryQuerySet(models.QuerySet):
    def annotate_available_quantity(self):
        return self.annotate(
            available_quantity=F("quantity")
                               - Coalesce(Sum("allocations__quantity_allocated"), 0)
        )

    def for_city(self, city_code: str):
        query_warehouse = models.Subquery(
            Warehouse.objects.filter(
                city__contains=city_code
            ).values("pk")
        )
        return self.select_related("product", "warehouse").filter(
            warehouse__in=query_warehouse
        )

    def get_inventory_for_city(
            self, city_code: str, product: BaseProduct
    ):
        """Return the stock information about the a stock for a given city.
        Note it will raise a 'Stock.DoesNotExist' exception if no such stock is found.
        """
        return self.for_city(city_code).filter(product=product, inventory_status="available")

    def get_product_inventories_for_city(self, city_code: str, product: BaseProduct):
        return self.for_city(city_code).filter(
            product_id=product.pk
        )


class Inventory(models.Model):
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)

    name = models.CharField(max_length=254, default="inventory name")
    desc = models.CharField(max_length=256, default="desc")
    baseProduct = models.ForeignKey(
        BaseProduct, null=False, blank=False, on_delete=models.DO_NOTHING, related_name="inventoryBaseProducts"
    )

    quantity = models.PositiveIntegerField(default=0)
    branded_quantity = models.PositiveIntegerField(default=0)
    unbranded_quantity = models.PositiveIntegerField(default=0)
    chatki_quantity = models.PositiveIntegerField(default=0)
    STATUS = (('picked up', 'picked up'),
              ('received', 'received'),
              ('Qc Done', 'Qc Done'),
              ('available', 'available'),
              ('in packing', 'in packing'),
              ('packed', 'packed'),
              ('in transit', 'in transit'),
              ('delivered', 'delivered'))
    inventory_status = models.CharField(choices=STATUS, default="available", max_length=200)
    objects = InventoryQuerySet.as_manager()

    class Meta:
        ordering = ("pk",)
        unique_together = ('warehouse', 'name','baseProduct','inventory_status')

    def increase_branded_inventory(self, quantity: int, commit: bool = True):
        """Return given quantity of product to a stock."""
        self.branded_quantity = F("branded_quantity") + quantity
        self.quantity = F("quantity") + quantity
        if commit:
            self.save(update_fields=["quantity", "branded_quantity"])

    def decrease_branded_inventory(self, quantity: int, commit: bool = True):
        self.branded_quantity = F("branded_quantity") - quantity
        self.quantity = F("quantity") - quantity
        if commit:
            self.save(update_fields=["quantity", "branded_quantity"])

    def increase_unbranded_inventory(self, quantity: int, commit: bool = True):
        """Return given quantity of product to a stock."""
        self.unbranded_quantity = F("unbranded_quantity") + quantity
        self.quantity = F("quantity") + quantity
        if commit:
            self.save(update_fields=["quantity", "unbranded_quantity"])

    def decrease_unbranded_inventory(self, quantity: int, commit: bool = True):
        self.unbranded_quantity = F("unbranded_quantity") + quantity
        self.quantity = F("quantity") - quantity
        if commit:
            self.save(update_fields=["quantity", "unbranded_quantity"])


class PackedInventoryQuerySet(models.QuerySet):
    def annotate_available_quantity(self):
        return self.annotate(
            available_quantity=F("quantity")
                               - Coalesce(Sum("allocations__quantity_allocated"), 0)
        )

    def for_city(self, city_code: str):
        query_warehouse = models.Subquery(
            Warehouse.objects.filter(
                city__contains=city_code
            ).values("pk")
        )
        return self.select_related("product", "warehouse").filter(
            warehouse__in=query_warehouse
        )

    def get_packed_inventory_for_city(
            self, city_code: str, product: Product
    ):
        """Return the stock information about the a stock for a given city.
        Note it will raise a 'Stock.DoesNotExist' exception if no such stock is found.
        """
        return self.for_city(city_code).filter(product=product, inventory_status="available")

    def get_product_inventories_for_city(self, city_code: str, product: Product):
        return self.for_city(city_code).filter(
            product_id=product.pk
        )


class PackedInventory(models.Model):
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)

    name = models.CharField(max_length=254, default="packed inventory name")
    desc = models.CharField(max_length=256, default="desc")
    product = models.ForeignKey(
        Product, null=False, blank=False, on_delete=models.DO_NOTHING, related_name="inventoryPackedProducts"
    )
    TYPES = (('White', 'White'),('Brown', 'Brown'), ('Nutra', 'Nutra'))
    category_type = models.CharField(max_length=200, choices=TYPES, default='White')
    quantity = models.PositiveIntegerField(default=0)
    STATUS = (('available', 'available'),
              ('in transit', 'in transit'),
              ('delivered', 'delivered'))
    inventory_status = models.CharField(choices=STATUS, default="available", max_length=200)
    objects = PackedInventoryQuerySet.as_manager()

    class Meta:
        ordering = ("pk",)
        unique_together = ('warehouse', 'name', 'product', 'inventory_status')

    def increase_inventory(self, quantity: int, commit: bool = True):
        """Return given quantity of product to a stock."""
        self.quantity = F("quantity") + quantity
        if commit:
            self.save(update_fields=["quantity"])

    def decrease_inventory(self, quantity: int, commit: bool = True):
        self.quantity = F("quantity") - quantity
        if commit:
            self.save(update_fields=["quantity"])


class BeatInventory(models.Model):
    beat_details = models.ForeignKey(BeatAssignment, on_delete=models.CASCADE,null=True, blank=True)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    date = models.DateField(null=True)
    desc = models.CharField(max_length=256, default="desc")
    STATUS = (('In', 'In'),
              ('Out', 'Out'))
    inventory_status = models.CharField(choices=STATUS, default="Out", max_length=200)
    entered_by = models.ForeignKey('WarehousePersonProfile', on_delete=models.DO_NOTHING,
                             related_name="beatInventoryAdmin", null=True, blank=True)

    def __str__(self):
        return self.beat_details.beat_name

class BeatInventoryLine(models.Model):
    beat_inventory = models.ForeignKey(BeatInventory, on_delete=models.CASCADE, null=True, blank=True, related_name="beat_inventory_line")
    product = models.ForeignKey(
        Product, null=False, blank=False, on_delete=models.DO_NOTHING, related_name="inventoryBeatProducts"
    )
    quantity = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("pk",)
        unique_together = ('product', 'beat_inventory')

    def increase_inventory(self, quantity: int, commit: bool = True):
        """Return given quantity of product to a stock."""
        self.quantity = F("quantity") + quantity
        if commit:
            self.save(update_fields=["quantity"])

    def decrease_inventory(self, quantity: int, commit: bool = True):
        self.quantity = F("quantity") - quantity
        if commit:
            self.save(update_fields=["quantity"])

    def __str__(self):
        return "{}-{}{}".format(self.beat_inventory.beat_details.beat_name, str(self.product.SKU_Count), self.product.name[:1])