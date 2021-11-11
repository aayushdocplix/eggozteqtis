import nested_admin
from django.contrib import admin

from product.models import Product, BaseProduct
from product.models.Product import Price, ProductDivision, ProductSubDivision, ProductInline, ProductDescription, \
    ProductBenefit, ProductLongDescription, ProductSpecification, ProductInformation, ProductInformationLine


# class PriceInline(nested_admin.NestedTabularInline):
#     model = Price
#     can_delete = True
#     show_change_link = True
#     extra = 0

class ProductLineInline(nested_admin.NestedStackedInline):
    model = ProductInline
    can_delete = True
    show_change_link = True
    extra = 0


class ProductDescriptionInline(nested_admin.NestedStackedInline):
    model = ProductDescription
    can_delete = True
    show_change_link = True
    extra = 0


class ProductBenefitInline(nested_admin.NestedStackedInline):
    model = ProductBenefit
    can_delete = True
    show_change_link = True
    extra = 0


class ProductLongDescriptionInline(nested_admin.NestedStackedInline):
    model = ProductLongDescription
    can_delete = True
    show_change_link = True
    extra = 0


class ProductSpecificationInline(nested_admin.NestedStackedInline):
    model = ProductSpecification
    can_delete = True
    show_change_link = True
    extra = 0


class ProductInformationLineInline(nested_admin.NestedStackedInline):
    model = ProductInformationLine
    can_delete = True
    show_change_link = True
    extra = 0


class ProductInformationInline(nested_admin.NestedStackedInline):
    model = ProductInformation
    inlines = [ProductInformationLineInline]
    can_delete = True
    show_change_link = True
    extra = 0


class ProductAdmin(nested_admin.NestedModelAdmin):
    list_display = ('id', 'name', 'slug', 'current_price', 'ecommerce_price', 'is_available', 'is_available_online', 'product_inlines')
    search_fields = ('id', 'name')
    readonly_fields = ['id']
    inlines = [ProductLineInline, ProductDescriptionInline, ProductBenefitInline, ProductLongDescriptionInline,
               ProductInformationInline, ProductSpecificationInline]

    def product_inlines(self, obj):
        items = []
        if obj.inlineProduct.all():
            for ele in obj.inlineProduct.all()[::1]:
                items.append(ele.name + " : " + str(ele.quantity))
        return '%s' % items

    def get_queryset(self, request):
        queryset = super(ProductAdmin, self).get_queryset(request)
        queryset = queryset.order_by('id')
        return queryset


class PriceAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'price_value', 'start_date', 'end_date')
    search_fields = ('id', 'price_value', 'start_date', 'end_date')
    readonly_fields = ['id']

    def get_queryset(self, request):
        queryset = super(PriceAdmin, self).get_queryset(request)
        queryset = queryset.order_by('id')
        return queryset


admin.site.register(Product, ProductAdmin)
admin.site.register(Price, PriceAdmin)
admin.site.register(ProductDivision)
admin.site.register(ProductSubDivision)
admin.site.register(BaseProduct)
