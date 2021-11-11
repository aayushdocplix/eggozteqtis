from datetime import timedelta, datetime

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import JSONField
from django.utils import timezone
from django.utils.timezone import now
from django_prices.models import MoneyField as BaseMoneyField

from Eggoz import settings
from Eggoz.settings import CURRENT_ZONE
from base.models import TimeStampedModel
from base.permissions import OrderPermissions
from base.util.json_serializer import CustomJsonEncoder
from custom_auth.models import Address
from distributionchain.models import DistributionPersonProfile, BeatAssignment
from ecommerce.models import Customer, SubscriptionDate, EcommerceSlot
from finance.models import FinanceProfile
from order.statuses import OrderStatus, OrderEvents
from product.models import Product
from retailer.models import Retailer
from saleschain.models import SalesPersonProfile
from warehouse.models import Warehouse, VehicleAssignment


class MoneyField(BaseMoneyField):
    serialize = True
    unique_for_date = True
    unique_for_month = True
    unique_for_year = True


class PackingOrder(models.Model):
    packing_id = models.CharField(max_length=254)
    desc = models.CharField(max_length=200, default="desc")
    date = models.DateTimeField(auto_now=True)
    status = models.CharField(
        max_length=32, default=OrderStatus.PACKING, choices=OrderStatus.CHOICES
    )

    class Meta:
        ordering = ("-pk",)


class OrderQueryset(models.QuerySet):
    def drafts(self):
        """Return draft orders."""
        return self.filter(status=OrderStatus.DRAFT)

    def created(self):
        """Return created orders."""
        return self.filter(status=OrderStatus.CREATED)

    def confirmed(self):
        """Return confirmed orders."""
        return self.filter(status=OrderStatus.CONFIRMED)

    def packed(self):
        """Return packed orders."""
        return self.filter(status=OrderStatus.PACKED)

    def way_to_delivery(self):
        """Return orders that are on the way to be delivered.
        """
        statuses = {OrderStatus.ONTHEWAY}
        return self.filter(status=statuses)

    def delivered(self):
        """Return delivered orders."""
        return self.filter(status=OrderStatus.DELIVERED)

    def cancelled(self):
        """Return cancelled orders."""
        return self.filter(status=OrderStatus.CANCELLED)

    def last_no_days_orders(self, retailer, days):
        if self.filter(retailer=retailer):
            return self.filter(retailer=retailer, date__gte=datetime.now(tz=CURRENT_ZONE) - timedelta(days=int(days)))
        else:
            return 'No Orders Yet'

    def total_orders(self, retailer):
        return self.filter(retailer=retailer)

    def days_since_last_order(self, retailer):
        if self.filter(retailer=retailer):
            if self.filter(retailer=retailer, status="delivered"):
                last_order = self.filter(retailer=retailer, status="delivered").latest('delivery_date')
                timediff = datetime.now(tz=CURRENT_ZONE) - last_order.delivery_date
                return (timediff.days)
            else:
                return 'No Delivered Orders Yet'
        else:
            return 'No Orders Yet'

    def last_order_date(self, retailer):
        if self.filter(retailer=retailer):
            if self.filter(retailer=retailer, status="delivered"):
                last_order = self.filter(retailer=retailer, status="delivered").latest('delivery_date')
                return (last_order.delivery_date)
            else:
                return 'Not Delivered Yet'
        else:
            return 'None'


class Order(models.Model):
    name = models.CharField(max_length=254, unique=True)
    bill_no = models.CharField(max_length=200, null=True, blank=True)
    orderId = models.CharField(max_length=254, unique=True)
    ORDER_TYPES = (('Purchase Order', 'Purchase Order'), ('Retailer', 'Retailer'), ('Customer', 'Customer'))
    order_type = models.CharField(choices=ORDER_TYPES, default="Retailer", max_length=254)

    BRAND_CHOICES = (('branded', 'branded'), ('unbranded', 'unbranded'))
    order_brand_type = models.CharField(choices=BRAND_CHOICES, default="branded", max_length=254)
    returned_bill = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True,
                                      related_name="order_returned_bill")
    pending_transaction = models.PositiveIntegerField(default=0)
    refund_transaction = models.PositiveIntegerField(default=0)
    retailer = models.ForeignKey(Retailer, on_delete=models.DO_NOTHING, blank=True, null=True,
                                 related_name="OrderRetailer")
    customer = models.ForeignKey(Customer, on_delete=models.DO_NOTHING, blank=True, null=True,
                                 related_name="OrderCustomer")
    pay_by_wallet = models.BooleanField(default=False)
    shipping_address = models.ForeignKey(Address, null=True, blank=True, on_delete=models.DO_NOTHING,
                                         related_name='address_orders')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.DO_NOTHING, blank=True, null=True,
                                  related_name="warehouse_orders")
    salesPerson = models.ForeignKey(SalesPersonProfile, blank=True, null=True, on_delete=models.DO_NOTHING,
                                    related_name="OrdersalesPerson")
    financePerson = models.ForeignKey(FinanceProfile, blank=True, null=True, on_delete=models.DO_NOTHING,
                                      related_name="OrderfinancePerson")
    distributor = models.ForeignKey(DistributionPersonProfile, on_delete=models.DO_NOTHING, null=True, blank=True,
                                    related_name="Orderdistributor")
    vehicle_assignment = models.ForeignKey(VehicleAssignment, null=True, blank=True, on_delete=models.DO_NOTHING)
    beat_assignment = models.ForeignKey(BeatAssignment, null=True, blank=True, on_delete=models.DO_NOTHING)
    packingOrder = models.ForeignKey(PackingOrder, null=True, blank=True, on_delete=models.DO_NOTHING)
    status = models.CharField(
        max_length=32, default=OrderStatus.CREATED, choices=OrderStatus.CHOICES
    )

    secondary_status = models.CharField(
        max_length=32, default=OrderStatus.CREATED, choices=OrderStatus.SECONDARY_CHOICES
    )

    date = models.DateTimeField(null=True, blank=True, help_text="date of creation")
    generation_date = models.DateTimeField(auto_now_add=True, help_text="date of generation")
    delivery_date = models.DateTimeField(null=True, blank=True, help_text="date of delivery")
    dispatch_date = models.DateTimeField(null=True, blank=True, help_text="date of dispatch")
    return_picked_date = models.DateTimeField(null=True, blank=True, help_text="date of return picked")
    retailer_note = models.CharField(max_length=254, default="retailer note", null=True, blank=True)

    deviated_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=0,
    )

    discount_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=0,
    )

    discount_name = models.CharField(max_length=255, blank=True, null=True)

    order_price_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=0,
    )

    PAYMENT_TYPES = (("Paid", "Paid"), ("Pending", "Pending"))
    order_payment_status = models.CharField(max_length=200, default="Pending", choices=PAYMENT_TYPES)

    order_final_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=0,
    )
    primary_order = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True)
    is_trial = models.BooleanField(default=False)

    is_geb = models.BooleanField(default=False)
    is_geb_verified = models.BooleanField(default=False)

    objects = OrderQueryset.as_manager()

    class Meta:
        ordering = ("-pk",)
        permissions = ((OrderPermissions.MANAGE_ORDERS.codename, "Manage orders."),)
        unique_together = ('name', 'retailer', 'date', 'delivery_date', 'order_price_amount')

    def get_customer_email(self):
        if self.retailer:
            return self.retailer.email
        else:
            return self.customer.user.email

    def retailer_phone(self):
        if self.retailer:
            return self.retailer.phone_no
        else:
            return self.customer.phone_no

    def retailer_shipping_address(self):
        if self.retailer:
            return self.retailer.shipping_address
        else:
            return self.customer.shipping_address

    def retailer_billing_address(self):
        if self.retailer:
            return self.retailer.billing_address
        else:
            return self.customer.billing_address

    def __iter__(self):
        return iter(self.lines.all())

    def __repr__(self):
        return "<Order #%r>" % (self.id,)

    def __str__(self):
        return "#%d" % (self.id,)

    def get_subtotal(self):
        subtotal_iterator = (line.get_total() for line in self)
        return sum(subtotal_iterator)

    def get_total_quantity(self):
        return sum([line.quantity for line in self])

    def is_draft(self):
        return self.status == OrderStatus.DRAFT

    def is_open(self):
        statuses = {OrderStatus.CREATED, OrderStatus.CONFIRMED, OrderStatus.PACKING, OrderStatus.PACKED,
                    OrderStatus.ONTHEWAY}
        return self.status in statuses


class ReturnOrderTransaction(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="order_return_transaction")
    beat_assignment = models.ForeignKey(BeatAssignment, null=True, blank=True, on_delete=models.DO_NOTHING)
    refund_transaction = models.PositiveIntegerField(default=0)
    return_picked_date = models.DateTimeField(null=True, blank=True, help_text="date of return picked")
    deviated_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=0,
    )

    def __str__(self):
        return self.order.name


class DebitNoteTransaction(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="debit_note_transaction")
    beat_assignment = models.ForeignKey(BeatAssignment, null=True, blank=True, on_delete=models.DO_NOTHING)
    debit_note_transaction = models.PositiveIntegerField(default=0)
    debit_note_date = models.DateTimeField(null=True, blank=True, help_text="date of debit note")
    amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=0,
    )

    def __str__(self):
        return self.order.name


class OrderPendingTransaction(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="order_pending_transaction")
    beat_assignment = models.ForeignKey(BeatAssignment, null=True, blank=True, on_delete=models.DO_NOTHING)
    pending_transaction = models.PositiveIntegerField(default=0)
    pending_collection_date = models.DateTimeField(null=True, blank=True, help_text="date of return picked")

    def __str__(self):
        return self.order.name


class PurchaseOrder(Order):
    purchase_id = models.CharField(max_length=254, null=True, blank=True)
    desc = models.CharField(max_length=200, default="desc")
    PO_STATUS_TYPES = (('Open', 'Open'), ('Closed', 'Closed'))
    po_status = models.CharField(
        max_length=32, default="Open", choices=PO_STATUS_TYPES
    )

    class Meta:
        ordering = ("-pk",)


class EcommerceOrder(Order):
    desc = models.CharField(max_length=200, default="desc")
    promo_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=0,
    )
    SubscriptionDate = models.ForeignKey(SubscriptionDate, null=True, blank=True,
                                         related_name="ecomm_subscrption_dates",
                                         on_delete=models.CASCADE)
    ecommerce_slot = models.ForeignKey(EcommerceSlot, on_delete=models.DO_NOTHING, null=True, blank=True)
    is_promo = models.BooleanField(default=False)

    class Meta:
        ordering = ("-pk",)


class OrderLineQueryset(models.QuerySet):
    def digital(self):
        """Return lines with digital products."""
        for line in self.all():
            if line.is_digital:
                yield line

    def physical(self):
        """Return lines with physical products."""
        for line in self.all():
            if not line.is_digital:
                yield line


class OrderLine(models.Model):
    order = models.ForeignKey(
        Order, related_name="lines", editable=False, on_delete=models.DO_NOTHING
    )
    product = models.ForeignKey(
        Product,
        related_name="order_lines",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    EGG_TYPE = (('Normal', 'Normal'),
                ('Chatki', 'Chatki'),
                ('Hairline', 'Hairline'),
                ('Replaced', 'Replaced'),
                ('Melted', 'Melted'),
                )
    egg_type = models.CharField(default="Normal", choices=EGG_TYPE, max_length=200)
    quantity = models.PositiveIntegerField(default=0)
    delivered_quantity = models.PositiveIntegerField(default=0)
    deviated_quantity = models.IntegerField(default=0)
    promo_quantity = models.IntegerField(default=0)
    deviated_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=0,
    )
    single_sku_mrp = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=0,
    )
    single_sku_rate = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=0,
    )

    objects = OrderLineQueryset.as_manager()

    class Meta:
        ordering = ("pk",)

    def __str__(self):
        if self.product:
            return self.product.name
        else:
            return ""

    def get_total(self):
        if self.product:
            return self.product.current_price * self.quantity
        else:
            return 0


class OrderReturnLine(models.Model):
    date = models.DateTimeField(default=now, )
    pickup_date = models.DateTimeField(default=now, )
    return_transaction = models.IntegerField(default=0)
    cancelled_date = models.DateTimeField(default=now, )
    orderLine = models.ForeignKey(
        OrderLine, related_name="lines", on_delete=models.DO_NOTHING
    )
    beat_assignment = models.ForeignKey(BeatAssignment, null=True, blank=True, on_delete=models.DO_NOTHING)
    TYPES = (('Replacement', 'Replacement'), ('Refund', 'Refund'), ('Return', 'Return'), ('Cancelled', 'Cancelled'),
             ('Promo', 'Promo'))
    line_type = models.CharField(choices=TYPES, default="Replacement", max_length=200)
    quantity = models.PositiveIntegerField(default=0)
    amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=0,
    )
    salesPerson = models.ForeignKey(SalesPersonProfile, blank=True, null=True, on_delete=models.DO_NOTHING,
                                    related_name="returnSalesPerson")
    distributor = models.ForeignKey(DistributionPersonProfile, on_delete=models.DO_NOTHING, null=True, blank=True,
                                    related_name="returnDistributor")
    financePerson = models.ForeignKey(FinanceProfile, on_delete=models.DO_NOTHING, null=True, blank=True,
                                      related_name="returnFinance")
    cancelled_by = models.ForeignKey(DistributionPersonProfile, on_delete=models.DO_NOTHING, null=True, blank=True,
                                     related_name="cancelledDistributor")

    # class Meta:
    #     unique_together = ('orderLine', 'line_type')


class OrderEvent(models.Model):
    """Model used to store events that happened during the order lifecycle.
    Args:
        parameters: Values needed to display the event on the storefront
        type: Type of an order
    """

    date = models.DateTimeField(default=now)
    type = models.CharField(
        max_length=255,
        choices=OrderEvents.CHOICES,
        default="placed"
    )
    order = models.ForeignKey(Order, related_name="events", on_delete=models.CASCADE)
    parameters = JSONField(blank=True, default=dict, encoder=CustomJsonEncoder)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    class Meta:
        ordering = ("date",)

    def __repr__(self):
        return f"{self.__class__.__name__}(type={self.type!r}, user={self.user!r})"
