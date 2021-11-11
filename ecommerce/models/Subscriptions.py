from django.db import models

# from ecommerce.models import Customer
from product.models import Product


class EcommerceSlot(models.Model):
    slot_id = models.PositiveIntegerField(default=1)
    name = models.CharField(max_length=200)
    type = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class MemberShip(models.Model):
    name = models.CharField(max_length=200)
    margin = models.PositiveIntegerField(default=10)
    is_visible = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class MemberShipData(models.Model):
    months = models.PositiveIntegerField(default=10)
    rate = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    membership = models.ForeignKey(MemberShip, on_delete=models.CASCADE, null=True, blank=True, related_name="data_membership")

    def __str__(self):
        return self.membership.name


class MemberShipBenefits(models.Model):
    membership = models.ForeignKey(MemberShip, on_delete=models.CASCADE, null=True, blank=True, related_name="benefit_membership")
    benefit = models.CharField(max_length=200, default="FREE 1 Nutra Plus (pack of 10)")

class MemberShipExtras(models.Model):
    membership = models.ForeignKey(MemberShip, on_delete=models.CASCADE, null=True, blank=True, related_name="extra_membership")
    extra = models.CharField(max_length=200, default="extra")


class Subscription(models.Model):
    name = models.CharField(max_length=200)
    margin = models.PositiveIntegerField(default=10)
    is_visible = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class SubscriptionBenefits(models.Model):
    # Subscription is a Parent to Subscription Benefit, so subscription can have multiple benefits
    # Ask front end dev to add them directly in code
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, null=True, blank=True,
                                     related_name="benefit_subscription")
    benefit = models.CharField(max_length=200, default="FREE 1 Nutra Plus (pack of 10)")
    is_visible = models.BooleanField(default=True)

    def __str__(self):
        return "{} - {}".format(self.subscription.name,self.benefit)


class SubscriptionExtras(models.Model):
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, null=True, blank=True,
                                     related_name="extra_subscription")
    extra = models.CharField(max_length=200, default="extra")
    is_visible = models.BooleanField(default=True)

    def __str__(self):
        return "{} - {}".format(self.subscription.name,self.extra)


class FrequencyDay(models.Model):
    day_id = models.PositiveIntegerField(unique=True)
    DAYS_LiST = (
        ("Monday", "Monday"),
        ("Tuesday", "Tuesday"),
        ("Wednesday", "Wednesday"),
        ("Thursday", "Thursday"),
        ("Friday", "Friday"),
        ("Saturday", "Saturday"),
        ("Sunday", "Sunday"),
    )
    day_name =models.CharField(choices=DAYS_LiST, max_length=200, default="Monday")

    def __str__(self):
        return self.day_name


class CustomerSubscription(models.Model):
    customer = models.ForeignKey('ecommerce.Customer', on_delete=models.CASCADE)
    subscription = models.ForeignKey('ecommerce.Subscription', on_delete=models.CASCADE, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    days = models.ManyToManyField(FrequencyDay, blank=True)
    subscription_type = models.CharField(max_length=200,default="Custom")
    single_sku_mrp = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    single_sku_rate = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    quantity = models.PositiveIntegerField(default=0)
    slot = models.ForeignKey(EcommerceSlot,on_delete=models.DO_NOTHING, default=1)
    start_date = models.DateTimeField()
    expiry_date = models.DateTimeField()

    def __str__(self):
        return self.customer.name

    class Meta:
        ordering=('-expiry_date',)


class CustomerMemberShip(models.Model):
    customer = models.ForeignKey('ecommerce.Customer', on_delete=models.CASCADE)
    memberShip = models.ForeignKey(MemberShip, on_delete=models.CASCADE)
    start_date = models.DateTimeField()
    expiry_date = models.DateTimeField()

    def __str__(self):
        return self.customer.name

    class Meta:
        ordering=('-expiry_date',)
