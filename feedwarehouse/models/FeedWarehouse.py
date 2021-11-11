from typing import Set

from django.db import models
from django.db.models import F, Sum
from django.db.models.functions import Coalesce

from base.models import City, Cluster
from custom_auth.models import Address
from farmer.models import FeedMedicine
from feedwarehouse.models.FeedProduct import FeedProduct


class FeedWarehouseQueryset(models.QuerySet):
    def prefetch_data(self):
        return self.select_related("address").prefetch_related("city")

    def for_city(self, city: str):
        return (
            self.prefetch_data()
                .filter(city=city)
                .order_by("pk")
        )


class FeedWarehouse(models.Model):
    name = models.CharField(max_length=250)
    slug = models.SlugField(max_length=255, unique=True, allow_unicode=True)
    city = models.CharField(max_length=100, default="City Name")
    address = models.ForeignKey(Address, on_delete=models.PROTECT)
    objects = FeedWarehouseQueryset.as_manager()

    class Meta:
        ordering = ("-slug",)

    def __str__(self):
        return self.name

    @property
    def city_code(self):
        return self.city

    def delete(self, *args, **kwargs):
        address = self.address
        super().delete(*args, **kwargs)
        address.delete()


class FeedInventoryQuerySet(models.QuerySet):
    def annotate_available_quantity(self):
        return self.annotate(
            available_quantity=F("quantity")
                               - Coalesce(Sum("allocations__quantity_allocated"), 0)
        )

    def for_city(self, city_code: str):
        query_warehouse = models.Subquery(
            FeedWarehouse.objects.filter(
                city__icontains=city_code
            ).values("pk")
        )
        return self.select_related("feedProduct", "feedWarehouse").filter(
            feedWarehouse__in=query_warehouse
        )

    def get_inventory_for_city(
            self, city_code: str, feed_product: FeedProduct
    ):
        """Return the stock information about the a stock for a given city.
        Note it will raise a 'Stock.DoesNotExist' exception if no such stock is found.
        """
        return self.for_city(city_code).filter(feedProduct=feed_product, inventory_status="available")

    def get_product_inventories_for_city(self, city_code: str, feed_product: FeedProduct):
        return self.for_city(city_code).filter(
            feedProduct_id=feed_product.pk
        )


class FeedInventory(models.Model):
    feedWarehouse = models.ForeignKey(FeedWarehouse, on_delete=models.CASCADE)

    name = models.CharField(max_length=254, default="inventory name")
    desc = models.CharField(max_length=256, default="desc")
    feedProduct = models.ForeignKey(
        FeedProduct, null=False, blank=False, on_delete=models.DO_NOTHING, related_name="inventoryFeedProducts"
    )

    quantity = models.PositiveIntegerField(default=0)
    STATUS = (('available', 'available'),
              ('in transit', 'in transit'),
              ('delivered', 'delivered'))
    inventory_status = models.CharField(choices=STATUS, default="available", max_length=200)
    objects = FeedInventoryQuerySet.as_manager()

    class Meta:
        ordering = ("pk",)
        unique_together = ('feedWarehouse', 'name', 'feedProduct', 'inventory_status')

    def increase_inventory(self, quantity: int, commit: bool = True):
        """Return given quantity of product to a stock."""
        self.quantity = F("quantity") + quantity
        if commit:
            self.save(update_fields=["quantity"])

    def decrease_inventory(self, quantity: int, commit: bool = True):
        self.quantity = F("quantity") - quantity
        if commit:
            self.save(update_fields=["quantity"])
