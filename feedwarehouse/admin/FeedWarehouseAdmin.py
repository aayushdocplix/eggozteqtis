from django.contrib import admin

from feedwarehouse.models import FeedProduct, FeedInventory, FeedWarehouse, FeedProductSubDivision, \
    FeedProductDivision, ProductVendor, FeedPrice, FeedProductSpecification, FeedOrder, FeedOrderLine


class ProductSpecificationInline(admin.StackedInline):
    model = FeedProductSpecification
    can_delete = True
    show_change_link = True
    extra = 0


class FeedProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug', 'current_price', 'is_available', )
    search_fields = ('id', 'name')
    readonly_fields = ['id']
    inlines = [ProductSpecificationInline]

    def get_queryset(self, request):
        queryset = super(FeedProductAdmin, self).get_queryset(request)
        queryset = queryset.order_by('id')
        return queryset


class FeedOrderInline(admin.StackedInline):
    model = FeedOrderLine
    can_delete = True
    show_change_link = True
    extra = 0


class FeedOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'farmer', 'created_at')
    search_fields = ('id', 'farmer_farmer__name')
    readonly_fields = ['id']
    inlines = [FeedOrderInline]
    filterset_fields = ('status',)

    def get_queryset(self, request):
        queryset = super(FeedOrderAdmin, self).get_queryset(request)
        queryset = queryset.order_by('id')
        return queryset


# class Admin(admin.ModelAdmin):
#     list_display = ('id', )
#     search_fields = ('id', )
#     readonly_fields = ['id']
#     filterset_fields = ('is_resolved',)
#
#     def get_queryset(self, request):
#         queryset = super(Admin, self).get_queryset(request)
#         queryset = queryset.order_by('id')
#         return queryset

admin.site.register(FeedProduct, FeedProductAdmin)
admin.site.register(FeedProductDivision)
admin.site.register(FeedProductSubDivision)
admin.site.register(FeedWarehouse)
admin.site.register(FeedInventory)
admin.site.register(ProductVendor)
admin.site.register(FeedPrice)
admin.site.register(FeedOrder, FeedOrderAdmin)
admin.site.register(FeedOrderLine)




