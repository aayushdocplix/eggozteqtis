from django.core.validators import MinValueValidator
from django.db import models

from Eggoz import settings
from base.models.Cluster import TimeStampedModel
from farmer.models import Farm, Farmer
from feedwarehouse.models import FeedProduct
from order.statuses import OrderStatus


class FeedOrder(TimeStampedModel):
    farm = models.ForeignKey(Farm, on_delete=models.DO_NOTHING,
                             related_name="feed_orders", null=True,blank=True)
    farmer = models.ForeignKey(Farmer, on_delete=models.DO_NOTHING,
                             related_name="feed_orders", null=True, blank=True)
    shipping_address = models.ForeignKey('custom_auth.Address', null=True, blank=True, on_delete=models.DO_NOTHING,
                                         related_name='address_feed_orders')
    status = models.CharField(
        max_length=32, default=OrderStatus.CREATED, choices=OrderStatus.CHOICES
    )
    order_price_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=0,
    )

    class Meta:
        ordering = ("-pk", '-created_at')

    def __str__(self):
        if self.farmer:
            return self.farmer.farmer.name
        else:
            return "No Farmer"


class FeedOrderLine(models.Model):
    feed_order = models.ForeignKey(
        FeedOrder, related_name="feed_order_lines", editable=False, on_delete=models.DO_NOTHING
    )
    feed_product = models.ForeignKey(
        FeedProduct,
        related_name="feed_order_lines",
        on_delete=models.DO_NOTHING
    )
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    class Meta:
        ordering = ("pk",)
        unique_together = ('feed_order', 'feed_product')

    def __str__(self):
        return "{}-{}".format(str(self.feed_order.id), self.feed_product.name)