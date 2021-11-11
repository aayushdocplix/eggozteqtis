from datetime import datetime

from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from Eggoz.settings import CURRENT_ZONE
# from base.models import City
from base.permissions import ProductPermissions
from base.translations import TranslationProxy


class ProductDivision(models.Model):
    name = models.CharField(max_length=150, help_text="name")
    description = models.CharField(max_length=254, help_text="description")
    code = models.CharField(max_length=150, help_text="code", unique=True, default="code")
    is_visible = models.BooleanField(default=True)
    hsn = models.CharField(default="0407", max_length=150)

    def __str__(self):
        return self.name


class ProductSubDivision(models.Model):
    name = models.CharField(max_length=150, help_text="name")
    description = models.CharField(max_length=254, help_text="description")
    productDivision = models.ForeignKey(ProductDivision, on_delete=models.DO_NOTHING)
    is_visible = models.BooleanField(default=True)
    code = models.CharField(max_length=150, help_text="code", unique=True, default="code")

    def __str__(self):
        return self.code


class Product(models.Model):
    name = models.CharField(max_length=150, help_text="name")
    description = models.CharField(max_length=254, help_text="description")
    city = models.ForeignKey('base.City', on_delete=models.DO_NOTHING)
    slug = models.SlugField(max_length=255, unique=True, allow_unicode=True)
    is_available = models.BooleanField(default=True)
    is_available_online = models.BooleanField(default=True)
    is_stock_available_online = models.BooleanField(default=False)
    is_prime_online = models.BooleanField(default=True)
    is_new_online = models.BooleanField(default=True)
    RATE_CHOCIES = (("margin","margin"),
                    ("dealer","dealer"))
    rate_type = models.CharField(max_length=254, help_text="rate type", default="margin", choices=RATE_CHOCIES)
    BRAND_CHOCIES = (("branded", "branded"),
                    ("unbranded", "unbranded"))
    brand_type = models.CharField(max_length=254, help_text="brand type", default="branded", choices=BRAND_CHOCIES)

    product_image = models.CharField(max_length=254, help_text="image s3 url", default="url")
    productDivision = models.ForeignKey(ProductDivision, on_delete=models.DO_NOTHING, related_name="product_division")
    productSubDivision = models.ForeignKey(ProductSubDivision, on_delete=models.DO_NOTHING, related_name="product_sub")
    SKU_Count = models.IntegerField(default=30)
    currency = models.CharField(
        max_length=3,
        default="INR",
    )

    oms_order = models.PositiveIntegerField(default=1)
    ecomm_order = models.PositiveIntegerField(default=1)

    current_price = models.DecimalField(max_digits=12,
                                        decimal_places=3, default=0)

    ecommerce_price = models.DecimalField(max_digits=12,
                                          decimal_places=3, default=0)
    shelf_life = models.CharField(max_length=254, default="21 days from the date of packaging")
    sku_weight = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    weight_type = models.CharField(max_length=200, default='gms', help_text='gms')
    updated_at = models.DateTimeField(null=True)
    charge_taxes = models.BooleanField(default=True)
    translated = TranslationProxy()

    class Meta:
        app_label = "product"
        ordering = ("oms_order",)
        permissions = (
            (ProductPermissions.MANAGE_PRODUCTS.codename, "Manage products."),
        )
        unique_together = ('SKU_Count', 'city', 'name', 'description')

    def __repr__(self) -> str:
        class_ = type(self)
        return "<%s.%s(pk=%r, name=%r)>" % (
            class_.__module__,
            class_.__name__,
            self.pk,
            self.name,
        )

    def __str__(self):
        return self.slug

    @staticmethod
    def sort_by_attribute_fields() -> list:
        return ["concatenated_values_order", "concatenated_values", "name"]

    __original_price = None

    def __init__(self, *args, **kwargs):
        super(Product, self).__init__(*args, **kwargs)
        self.__original_price = self.current_price

   # def save(self, *args, **kwargs):
    #    if self.current_price != self.__original_price:
     #       if Price.objects.filter(product=self).last():
      #          price = Price.objects.filter(product=self).last()
       #         price.end_date = datetime.now(tz=CURRENT_ZONE)
        #        price.save()
         #   current_price = Price.objects.create(product=self, start_date=datetime.now(tz=CURRENT_ZONE),
          #                                       price_value=self.current_price)
           # current_price.save()
        #self.updated_at = datetime.now(tz=CURRENT_ZONE)
       # super(Product, self).save(*args, **kwargs)


class ProductDescription(models.Model):
    description = models.CharField(max_length=254)
    product = models.ForeignKey(Product, null=False, blank=False, on_delete=models.DO_NOTHING,
                                related_name="descriptionProduct")

    def __str__(self):
        return "{}-{}".format(self.product.slug, self.description)


class ProductLongDescription(models.Model):
    description = models.CharField(max_length=254)
    product = models.ForeignKey(Product, null=False, blank=False, on_delete=models.DO_NOTHING,
                                related_name="longDescriptionProduct")

    def __str__(self):
        return "{}-{}".format(self.product.slug, self.description)


class ProductBenefit(models.Model):
    benefit = models.CharField(max_length=254)
    product = models.ForeignKey(Product, null=False, blank=False, on_delete=models.DO_NOTHING,
                                related_name="benefitProduct")

    def __str__(self):
        return "{}-{}".format(self.product.slug, self.benefit)


class ProductSpecification(models.Model):
    specification = models.CharField(max_length=254)
    product = models.ForeignKey(Product, null=False, blank=False, on_delete=models.DO_NOTHING,
                                related_name="specificationProduct")

    def __str__(self):
        return "{}-{}".format(self.product.slug, self.specification)


class ProductInformation(models.Model):
    information = models.CharField(max_length=254)
    product = models.ForeignKey(Product, null=False, blank=False, on_delete=models.DO_NOTHING,
                                related_name="informationProduct")

    def __str__(self):
        return "{}-{}".format(self.product.slug, self.information)


class ProductInformationLine(models.Model):
    name = models.CharField(max_length=254)
    info_value = models.DecimalField(max_digits=12,
                                     decimal_places=3, default=0)
    type = models.CharField(max_length=200, default='gms', help_text='gms')
    information = models.ForeignKey(ProductInformation, null=False, blank=False, on_delete=models.DO_NOTHING,
                                    related_name="inlineInformationProduct")

    def __str__(self):
        return "{}-{}".format(self.information.information, self.name)


class ProductInline(models.Model):
    name = models.CharField(max_length=254)
    product = models.ForeignKey(Product, null=False, blank=False, on_delete=models.DO_NOTHING,
                                related_name="inlineProduct")
    baseProduct = models.ForeignKey('BaseProduct', null=False, blank=False, on_delete=models.DO_NOTHING)
    quantity = models.IntegerField(default=0)

    def __str__(self):
        return "{}-{}".format(self.product.slug, self.name)


class Price(models.Model):
    product = models.ForeignKey(Product, on_delete=models.DO_NOTHING)
    price_value = models.DecimalField(max_digits=12,
                                      decimal_places=3, default=0)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.product.slug
