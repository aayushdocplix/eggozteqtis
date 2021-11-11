from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from base.models import City
from base.permissions import FeedProductPermissions
from base.translations import TranslationProxy


class FeedProductDivision(models.Model):
    name = models.CharField(max_length=150, help_text="name")
    description = models.CharField(max_length=254, help_text="description")
    code = models.CharField(max_length=150, help_text="code", unique=True, default="code")
    image = models.CharField(max_length=254, help_text="image s3 url", default="url")
    is_visible = models.BooleanField(default=True)
    hsn = models.CharField(default="0", max_length=150)

    def __str__(self):
        return self.name


class FeedProductSubDivision(models.Model):
    name = models.CharField(max_length=150, help_text="name")
    description = models.CharField(max_length=254, help_text="description")
    feedProductDivision = models.ForeignKey(FeedProductDivision, on_delete=models.DO_NOTHING)
    image = models.CharField(max_length=254, help_text="image s3 url", default="url")
    is_visible = models.BooleanField(default=True)
    code = models.CharField(max_length=150, help_text="code", unique=True, default="code")

    def __str__(self):
        return self.name


class ProductVendor(models.Model):
    name = models.CharField(max_length=150, help_text="name",unique=True)

    def __str__(self):
        return self.name


class FeedProduct(models.Model):
    name = models.CharField(max_length=150, help_text="name")
    description = models.CharField(max_length=254, help_text="description")
    vendor = models.ForeignKey(ProductVendor, on_delete=models.CASCADE,related_name="productVendor")
    slug = models.SlugField(max_length=255, unique=True, allow_unicode=True)
    is_available = models.BooleanField(default=True)
    is_popular=models.BooleanField(default=True)
    feed_product_image = models.CharField(max_length=254, help_text="image s3 url", default="url")
    feedProductDivision = models.ForeignKey(FeedProductDivision, on_delete=models.DO_NOTHING,
                                            related_name="feed_product_division")
    feedProductSubDivision = models.ForeignKey(FeedProductSubDivision, on_delete=models.DO_NOTHING,
                                               related_name="feed_product_sub")
    currency = models.CharField(
        max_length=3,
        default="INR",
    )

    current_price = models.DecimalField(max_digits=12,
                                        decimal_places=3, default=0)

    updated_at = models.DateTimeField(null=True)
    charge_taxes = models.BooleanField(default=True)
    translated = TranslationProxy()

    class Meta:
        ordering = ("name",)
        permissions = (
            (FeedProductPermissions.MANAGE_PRODUCTS.codename, "Manage feed products."),
        )

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


class FeedProductSpecification(models.Model):
    feedProduct = models.ForeignKey(FeedProduct, on_delete=models.CASCADE, related_name="feedSpecificationProduct")
    specification = models.CharField(max_length=200,default="specification")


class FeedPrice(models.Model):
    feedProduct = models.ForeignKey(FeedProduct, on_delete=models.DO_NOTHING)
    price_value = models.DecimalField(max_digits=12,
                                      decimal_places=3, default=0)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.feedProduct.slug


@receiver(post_save, sender=FeedPrice)
def update_product_price(sender, instance, created, **kwargs):
    if created:
        product_current = FeedProduct.objects.get(pk=instance.feedProduct.id)
        product_current.current_price = instance.price_value
        product_current.updated_at = instance.start_date
        if FeedPrice.objects.filter(feedProduct=product_current).last():
            prev_price = FeedPrice.objects.filter(feedProduct=product_current).last()
            prev_price.end_date = instance.start_date
            prev_price.save()
        product_current.save()


@receiver(post_save, sender=FeedProduct)
def create_price(sender, instance, created, **kwargs):
    if created:
        current_price = FeedPrice.objects.create(feedProduct=instance, start_date=instance.updated_at,
                                                 price_value=instance.current_price)
        current_price.save()
