import random
import string
from datetime import datetime

from django.db import models
from django.db.models import JSONField
from django.db.models.signals import post_save
from django.dispatch import receiver
from phonenumber_field.modelfields import PhoneNumberField

from Eggoz import settings
from Eggoz.settings import CURRENT_ZONE
from base.util.json_serializer import CustomJsonEncoder
from custom_auth.models import User, Address
from ecommerce.models.Subscriptions import EcommerceSlot, MemberShip, Subscription, FrequencyDay, CustomerSubscription
from product.models import Product


class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.DO_NOTHING)
    name = models.CharField(max_length=200, null=True, blank=True)
    code_string = models.CharField(max_length=200, null=True, blank=True)
    code_int = models.PositiveIntegerField(null=True, blank=True)
    code = models.CharField(max_length=200, unique=True)
    shipping_address = models.ForeignKey(Address, null=True, blank=True, on_delete=models.DO_NOTHING,
                                         related_name='customer_shipping_address')
    billing_address = models.ForeignKey(Address, null=True, blank=True, on_delete=models.DO_NOTHING,
                                        related_name='customer_billing_address')
    billing_shipping_address_same = models.BooleanField(default=False)
    onboarding_date = models.DateTimeField(help_text='Onboarding Date', null=True, blank=True)
    last_order_date = models.DateTimeField(help_text='Last Order Date', null=True, blank=True)
    phone_no = PhoneNumberField(unique=True)
    is_test_profile = models.BooleanField(default=False)
    is_new_customer = models.BooleanField(default=True)

    current_order_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=0,
    )

    ecommerce_slot = models.ForeignKey(EcommerceSlot, on_delete=models.DO_NOTHING, null=True, blank=True)

    def get_customer_email(self):
        return self.user.email

    def __str__(self):
        if self.name:
            return self.name
        else:
            return str(self.phone_no)

    class Meta:
        ordering = ['-last_order_date']


class CustomerWallet(models.Model):
    customer = models.OneToOneField(Customer, on_delete=models.CASCADE)
    total_balance = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=0,
    )
    is_recharged_once = models.BooleanField(default=False)
    recharge_balance = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=0,
    )
    note = models.CharField(max_length=250)

    def __str__(self):
        if self.customer.name:
            return self.customer.name
        else:
            return str(self.customer.phone_no)


class CustomerPromoWallet(models.Model):
    wallet = models.ForeignKey(CustomerWallet, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    published_at = models.DateTimeField()
    expired_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    balance = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=0,
    )
    note = models.CharField(max_length=250)

    def __str__(self):
        if self.wallet.customer.name:
            return self.wallet.customer.name
        else:
            return str(self.wallet.customer.phone_no)


class RechargeVoucher(models.Model):
    amount = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    promo = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    voucher_colour = models.CharField(max_length=100, default="RGB")
    is_available = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expired_at = models.DateTimeField()
    note = models.CharField(max_length=250)

    def __str__(self):
        return str(self.amount)


class CustomerVoucherPromo(models.Model):
    voucher = models.ForeignKey(RechargeVoucher, on_delete=models.DO_NOTHING)
    created_at = models.DateTimeField(auto_now_add=True)
    published_at = models.DateTimeField()
    expired_at = models.DateTimeField()
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    note = models.CharField(max_length=250)

    def __str__(self):
        if self.customer.name:
            return self.customer.name + "-" + str(self.voucher.amount)
        else:
            return str(self.customer.phone_no) + "-" + str(self.voucher.amount)


class MemberShipRequest(models.Model):
    memberShip = models.ForeignKey(MemberShip, related_name="cashfree_transactions_membership",
                                   on_delete=models.CASCADE,
                                   null=True, blank=True)
    date = models.DateTimeField(auto_now=True)
    start_date = models.DateTimeField()
    expiry_date = models.DateTimeField()


class SubscriptionRequest(models.Model):
    subscription = models.ForeignKey(Subscription, related_name="cashfree_transactions_subscription",
                                   on_delete=models.CASCADE,
                                   null=True, blank=True)
    date = models.DateTimeField(auto_now=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    days = models.ManyToManyField(FrequencyDay, blank=True)
    subscription_type = models.CharField(max_length=200, default="Custom")
    single_sku_mrp = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    single_sku_rate = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    quantity = models.PositiveIntegerField(default=0)
    slot = models.ForeignKey(EcommerceSlot, on_delete=models.DO_NOTHING, default=1)
    start_date = models.DateTimeField()
    expiry_date = models.DateTimeField()


class SubscriptionDate(models.Model):
    date_string = models.CharField(max_length=100, null=True, blank=True)
    delivered_date = models.CharField(max_length=100, null=True, blank=True)
    shipping_address = models.IntegerField(default=0)
    subscriptionRequest = models.ForeignKey(SubscriptionRequest, null=True, blank=True,
                                            related_name="dates_subscrption_request", on_delete=models.CASCADE)
    customer_subscription = models.ForeignKey(CustomerSubscription, null=True, blank=True,
                                              related_name="dates_customer_subscription", on_delete=models.CASCADE)


class CashFreeTransaction(models.Model):
    order = models.ForeignKey('order.Order', related_name="cashfree_transactions_order", on_delete=models.CASCADE,
                              null=True, blank=True)

    memberShipRequest = models.ForeignKey(MemberShipRequest, related_name="cashfree_transactions_membership_request",
                                           null=True, blank=True,on_delete=models.CASCADE)

    subscriptionRequest = models.ForeignKey(SubscriptionRequest, related_name="cashfree_transactions_subscription_request",
                                          null=True, blank=True, on_delete=models.CASCADE)
    transaction_id = models.CharField(max_length=200)
    reference_id = models.CharField(max_length=200, default="")
    signature_response = models.CharField(max_length=200, default="")
    transaction_message = models.CharField(max_length=256, default="")
    transaction_type = models.CharField(max_length=150)
    transaction_amount = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    wallet_amount = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    transaction_status = models.CharField(max_length=150)
    payment_link = models.URLField(max_length=300)
    payment_return_response = models.JSONField(null=True, blank=True)
    transaction_time = models.DateTimeField(auto_now_add=True)
    recharge_type = models.CharField(max_length=250, default="Wallet")
    pay_by_wallet = models.BooleanField(default=True)
    note = models.CharField(max_length=250)
    wallet = models.ForeignKey(CustomerWallet, related_name='walletTransactions', on_delete=models.DO_NOTHING,
                               null=True, blank=True)
    voucher = models.ForeignKey(RechargeVoucher, related_name='voucherTransactions', on_delete=models.DO_NOTHING,
                                null=True, blank=True)
    parameters = JSONField(blank=True, default=dict, encoder=CustomJsonEncoder)

    def __str__(self):
        return self.transaction_id


class WalletRecharge(models.Model):
    transaction = models.OneToOneField(CashFreeTransaction, on_delete=models.CASCADE)
    wallet = models.ForeignKey(CustomerWallet, on_delete=models.CASCADE)
    voucher = models.ForeignKey(RechargeVoucher, on_delete=models.CASCADE, null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    promo_amount = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    recharged_at = models.DateTimeField(auto_now_add=True)
    note = models.CharField(max_length=250)

    def __str__(self):
        if self.wallet.customer.name:
            return self.wallet.customer.name
        else:
            return str(self.wallet.customer.phone_no)

    class Meta:
        ordering = ("-recharged_at",)


class NotifyCustomer(models.Model):
    customer = models.OneToOneField(Customer, on_delete=models.DO_NOTHING, related_name="customer_notify", null=True, blank=True)
    phone_no = PhoneNumberField()
    email = models.EmailField(max_length=254)
    product = models.IntegerField(default=0)
    is_notified = models.BooleanField(default=False)

    def __str__(self):
        return self.email

class ReferralData(models.Model):
    used_by = models.OneToOneField(Customer, on_delete=models.DO_NOTHING, related_name="used_customer_referrals")
    start_date = models.DateTimeField(null=True, blank=True)
    expiry_date = models.DateTimeField(null=True, blank=True)
    desc = models.CharField(max_length=200, default="desc")


class CustomerReferral(models.Model):
    customer = models.OneToOneField(Customer, on_delete=models.DO_NOTHING, related_name="customer_referrals")
    referral_code = models.CharField(unique=True, max_length=11)

    referral_data = models.ManyToManyField(ReferralData, related_name="referral_data")

    def __str__(self):
        return self.referral_code


@receiver(post_save, sender=Customer)
def create_customer_wallet(sender, instance, created, **kwargs):
    if created:
        referral_code = "EGGOZ" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        CustomerReferral.objects.create(customer=instance, referral_code=referral_code)
        customer_wallet = CustomerWallet.objects.create(customer=instance)
        customer_wallet.save()
