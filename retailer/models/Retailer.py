from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from uuid_upload_path import upload_to

from Eggoz import settings
from base.models.Cluster import Cluster, City, Sector
from custom_auth.models.Address import Address
from custom_auth.models.User import User
from distributionchain.models import DistributionPersonProfile
from product.models import Product
from saleschain.models import SalesPersonProfile


class Customer_Category(models.Model):
    name = models.CharField(max_length=200, unique=True)
    description = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Customer_SubCategory(models.Model):
    name = models.CharField(max_length=200, unique=False)
    description = models.CharField(max_length=200)
    category = models.ForeignKey(Customer_Category, on_delete=models.DO_NOTHING)

    def __str__(self):
        return self.name

    class Meta:
        unique_together = ('name', 'category')


class IncomeSlab(models.Model):
    name = models.CharField(max_length=254, unique=True, help_text='<10 Lakhs')

    def __str__(self):
        return self.name


class Classification(models.Model):
    name = models.CharField(max_length=200, unique=True, help_text='A B C')

    def __str__(self):
        return self.name


class CommissionSlab(models.Model):
    number = models.DecimalField(default=0, help_text='25', max_digits=settings.DEFAULT_MAX_DIGITS,
                                 decimal_places=settings.DEFAULT_DECIMAL_PLACES, )
    number_value = models.CharField(max_length=200, default='257', help_text='257')
    type = models.CharField(max_length=200, default='%', help_text='%')
    city = models.ForeignKey(City, null=True, blank=True, on_delete=models.DO_NOTHING)
    is_visible = models.BooleanField(default=True)
    is_available = models.BooleanField(default=True)

    class Meta:
        unique_together = ('number', 'type')

    def __str__(self):
        return str(self.number)


class MarginRates(models.Model):
    product = models.ForeignKey('product.Product', null=True, blank=True, on_delete=models.DO_NOTHING,
                                        related_name="margin_product")
    margin_rate = models.DecimalField(default=0, help_text='56', max_digits=settings.DEFAULT_MAX_DIGITS,
                                 decimal_places=settings.DEFAULT_DECIMAL_PLACES, )
    margin_mrp = models.DecimalField(default=0, help_text='56', max_digits=settings.DEFAULT_MAX_DIGITS,
                                      decimal_places=settings.DEFAULT_DECIMAL_PLACES, )
    margin = models.ForeignKey('retailer.CommissionSlab', null=True, blank=True, on_delete=models.DO_NOTHING,
                                        related_name="margin_commission")

    def __str__(self):
        return "{}-{}-{}".format(str(self.product.id), str(self.margin_rate), str(self.margin.number_value))

class DiscountSlab(models.Model):
    name = models.CharField(max_length=200, unique=True)
    white_number = models.DecimalField(default=0, help_text='5', max_digits=settings.DEFAULT_MAX_DIGITS,
                                 decimal_places=settings.DEFAULT_DECIMAL_PLACES, )
    brown_number = models.DecimalField(default=0, help_text='5', max_digits=settings.DEFAULT_MAX_DIGITS,
                                 decimal_places=settings.DEFAULT_DECIMAL_PLACES, )
    nutra_number = models.DecimalField(default=0, help_text='5', max_digits=settings.DEFAULT_MAX_DIGITS,
                                       decimal_places=settings.DEFAULT_DECIMAL_PLACES, )
    type = models.CharField(max_length=200, default='%', help_text='%')

    class Meta:
        unique_together = ('white_number', 'brown_number', 'nutra_number', 'type')

    def __str__(self):
        return str(self.name)


class RetailerShorts(models.Model):
    name = models.CharField(default="GT", max_length=200)

    def __str__(self):
        return self.name


class RetailerPaymentCycle(models.Model):
    number = models.PositiveIntegerField(default=0)
    type = models.CharField(default="Days", max_length=200)
    is_mt = models.BooleanField(default=False)
    is_gt = models.BooleanField(default=False)

    def __str__(self):
        return "{} {}".format(str(self.number), self.type)


class RetailerBeat(models.Model):
    beat_number = models.PositiveIntegerField(default=0)
    BEAT_TYPES = (('Adhoc', 'Adhoc'), ('Regular', 'Regular'))
    beat_type = models.CharField(choices=BEAT_TYPES, max_length=200, default="Regular")
    beat_area = models.CharField(max_length=200,default="beat area")
    distributor = models.ForeignKey(DistributionPersonProfile,null=True, blank=True, on_delete=models.DO_NOTHING)

    def __str__(self):
        return str(self.beat_number)


class Retailer(models.Model):
    retailer = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name="retailer")
    name_of_shop = models.CharField(max_length=200)
    shop_photo_url = models.CharField(max_length=254, null=True, blank=True)
    billing_name_of_shop = models.CharField(max_length=200, default="Exact Name Of Shop")
    short_name = models.ForeignKey(RetailerShorts, on_delete=models.DO_NOTHING, default=1,null=True, blank=True,)
    category = models.ForeignKey(Customer_Category, on_delete=models.DO_NOTHING)
    classification = models.ForeignKey(Classification, null=True, blank=True, on_delete=models.DO_NOTHING, default=1,)
    sub_category = models.ForeignKey(Customer_SubCategory, on_delete=models.DO_NOTHING)
    code_string = models.CharField(max_length=200, null=True, blank=True)
    code_int = models.PositiveIntegerField(null=True, blank=True)
    code = models.CharField(max_length=200, unique=True)
    city = models.ForeignKey(City, on_delete=models.DO_NOTHING)
    cluster = models.ForeignKey(Cluster, on_delete=models.DO_NOTHING)
    sector = models.ForeignKey(Sector,null=True,blank=True, on_delete=models.DO_NOTHING)
    shipping_address = models.ForeignKey(Address, null=True, blank=True, on_delete=models.DO_NOTHING,
                                         related_name='retailer_shipping_address')
    billing_address = models.ForeignKey(Address, null=True, blank=True, on_delete=models.DO_NOTHING,
                                        related_name='retailer_billing_address')
    billing_shipping_address_same = models.BooleanField(default=False)
    onboarded_salesPerson = models.ForeignKey(SalesPersonProfile, null=True, blank=True, on_delete=models.DO_NOTHING,
                                           related_name="onBoardedSalesPerson")
    salesPersonProfile = models.ForeignKey(SalesPersonProfile, null=True, blank=True, on_delete=models.DO_NOTHING,
                                           related_name="salesPersonProfile")
    retailerBeat = models.ForeignKey(RetailerBeat, null=True, blank=True, on_delete=models.DO_NOTHING,
                                           related_name="retailerBeat")
    annual_income = models.ForeignKey(IncomeSlab, null=True, blank=True, on_delete=models.DO_NOTHING,
                                      related_name="annual_income")
    commission_slab = models.ForeignKey(CommissionSlab, null=True, blank=True, on_delete=models.DO_NOTHING,
                                        related_name="commission_slab")
    discount_slab = models.ForeignKey(DiscountSlab, null=True, blank=True, on_delete=models.DO_NOTHING, default=1,
                                        related_name="discount_slab")
    beat_number = models.PositiveIntegerField(default=0)
    beat_order_number = models.PositiveIntegerField(default=0)
    RATE_CHOCIES = (("margin", "margin"),
                    ("dealer", "dealer"),
                    ("mt", "mt"),
                    ("unbranded", "unbranded"))
    rate_type = models.CharField(max_length=254, help_text="rate type", default="margin", choices=RATE_CHOCIES)
    payment_cycle = models.ForeignKey(RetailerPaymentCycle, on_delete=models.DO_NOTHING, null=True, blank=True, default=1)
    GSTIN = models.CharField(max_length=200, default="GSTIN")
    gst_photo_url = models.CharField(max_length=254, null=True, blank=True)
    status_choices = (('not-verified', 'not-verified'), ('uploaded', 'uploaded'), ('verified', 'verified'))
    gstin_status = models.CharField(max_length=20, choices=status_choices, default='not-verified')
    ONBOARDING_STATUSES = (('Onboarded', 'Onboarded'),
                           ('Cold', 'Cold'),
                           ('Pending Interested', 'Pending Interested'),
                           ('Closed', 'Closed'),
                           ('Duplicate', 'Duplicate'))
    onboarding_status = models.CharField(max_length=200, choices=ONBOARDING_STATUSES, default='Onboarded')
    onboarding_date = models.DateTimeField(help_text='Onboarding Date', null=True, blank=True)
    last_order_date = models.DateTimeField(help_text='Last Order Date', null=True, blank=True)
    phone_no = PhoneNumberField()

    amount_due = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=0,
    )
    calc_amount_due = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=0,
    )
    net_amount_due = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=0,
    )

    def get_retailer_email(self):
        return self.retailer.email


    def __str__(self):
        return self.code

    class Meta:
        # unique_together = ["beat_number", "beat_order_number"]
        ordering = ['-last_order_date']


class RetailOwner(models.Model):
    retail_shop = models.ForeignKey(Retailer, on_delete=models.DO_NOTHING, related_name="retail_owners")
    owner_name = models.CharField(max_length=200, null=True, blank=True)
    phone_no = PhoneNumberField()

    owner_photo_url = models.CharField(max_length=254, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    status_choices = (('not-verified', 'not-verified'), ('uploaded', 'uploaded'), ('verified', 'verified'))

    aadhar_photo_url = models.CharField(max_length=254, null=True, blank=True)
    aadhar_no = models.CharField(max_length=100, null=True, blank=True)
    aadhar_status = models.CharField(max_length=20, choices=status_choices, default='not-verified')

    pancard_photo_url = models.CharField(max_length=254, null=True, blank=True)
    pancard_no = models.CharField(max_length=100, null=True, blank=True)
    pancard_status = models.CharField(max_length=20, choices=status_choices, default='not-verified')


class RetailerEggsdata(models.Model):
    retailer = models.ForeignKey(Retailer,
                                  related_name="eggs_retailer", on_delete=models.DO_NOTHING)
    brown = models.PositiveIntegerField(default=0)
    white = models.PositiveIntegerField(default=0)
    nutra = models.PositiveIntegerField(default=0)
    date = models.DateField()
