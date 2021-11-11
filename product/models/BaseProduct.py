from django.db import models

# from base.models import City
from base.permissions import ProductPermissions
from base.translations import TranslationProxy
from .Product import ProductDivision, ProductSubDivision


class BaseProduct(models.Model):
    name = models.CharField(max_length=150, help_text="name")
    description = models.CharField(max_length=254, help_text="description")
    city = models.ForeignKey('base.City', on_delete=models.DO_NOTHING)
    slug = models.SlugField(max_length=255, unique=True, allow_unicode=True)
    productDivision = models.ForeignKey(ProductDivision, on_delete=models.DO_NOTHING, related_name="base_product_division")
    productSubDivision = models.ForeignKey(ProductSubDivision, on_delete=models.DO_NOTHING, related_name="base_product_sub")
    currency = models.CharField(
        max_length=3,
        default="INR",
    )
    updated_at = models.DateTimeField(null=True)
    paper_price = models.DecimalField(max_digits=12,
                                      decimal_places=3, default=0)
    chatki_price = models.DecimalField(max_digits=12,
                                       decimal_places=3, default=0)
    paper_price_updated_at = models.DateTimeField(null=True)
    chatki_price_updated_at = models.DateTimeField(null=True)
    translated = TranslationProxy()

    class Meta:
        ordering = ("name",)
        permissions = (
            (ProductPermissions.MANAGE_PRODUCTS.codename, "Manage products."),
        )
        unique_together = ('city', 'name')

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
