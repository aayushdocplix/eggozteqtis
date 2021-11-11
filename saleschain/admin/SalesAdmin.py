from django.contrib import admin

from saleschain.models import SalesPersonProfile, SalesEggsdata, RetailerDemand, RetailerDemandSKU, SalesDemandSKU, \
    SalesSupplySKU, SalesSMApprovalSKU, SalesRHApprovalSKU


class SalesEggsAdmin(admin.ModelAdmin):
    list_display = ('id', 'date', 'salesPerson', 'brown', 'white', 'nutra')
    search_fields = ('id','date', 'salesPerson__user__name')
    readonly_fields = ['id',]

    def get_queryset(self, request):
        queryset = super(SalesEggsAdmin, self).get_queryset(request)
        queryset = queryset.order_by('id')
        return queryset

class SalesPersonAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'warehouse', 'management_status'
                                               '')
    search_fields = ('id', 'user__name')
    readonly_fields = ['id',]

    def get_queryset(self, request):
        queryset = super(SalesPersonAdmin, self).get_queryset(request)
        queryset = queryset.order_by('id')
        return queryset

class RetailerDemandAdmin(admin.ModelAdmin):
    list_display = ('id', 'retailer', 'date', 'time', 'beatAssignment')
    search_fields = ('id', 'retailer__code')
    readonly_fields = ['id',]

    def get_queryset(self, request):
        queryset = super(RetailerDemandAdmin, self).get_queryset(request)
        queryset = queryset.order_by('id')
        return queryset


class RetailerDemandSKUAdmin(admin.ModelAdmin):
    list_display = ('id', 'retailerDemand', 'product', 'product_quantity',
                                               'product_supply_quantity')
    search_fields = ('id', 'retailerDemand__retailer__code')
    readonly_fields = ['id',]

    def get_queryset(self, request):
        queryset = super(RetailerDemandSKUAdmin, self).get_queryset(request)
        queryset = queryset.order_by('id')
        return queryset

class SalesDemandSKUAdmin(admin.ModelAdmin):
    list_display = ('id', 'beatAssignment', 'product', 'product_quantity', 'product_fresh_stock_validated', 'product_old_stock_validated',
                                               'product_supply_quantity','product_out_quantity',
                    'product_sold_quantity','product_replacement_quantity', 'product_return_quantity',
                    'product_in_quantity', 'product_fresh_in_quantity','product_return_repalce_in_quantity')
    search_fields = ('id', 'beatAssignment')
    readonly_fields = ['id',]

    def get_queryset(self, request):
        queryset = super(SalesDemandSKUAdmin, self).get_queryset(request)
        queryset = queryset.order_by('id')
        return queryset

class SalesSupplySKUAdmin(admin.ModelAdmin):
    list_display = ('id', 'beatWarehouseSupply', 'product', 'product_quantity')
    search_fields = ('id', 'beatWarehouseSupply')
    readonly_fields = ['id',]

    def get_queryset(self, request):
        queryset = super(SalesSupplySKUAdmin, self).get_queryset(request)
        queryset = queryset.order_by('id')
        return queryset


class SalesSMApprovalSKUAdmin(admin.ModelAdmin):
    list_display = ('id', 'beatSMApproval', 'product', 'product_quantity','demand_classification')
    search_fields = ('id', 'beatSMApproval')
    readonly_fields = ['id',]

    def get_queryset(self, request):
        queryset = super(SalesSMApprovalSKUAdmin, self).get_queryset(request)
        queryset = queryset.order_by('id')
        return queryset

class SalesRHApprovalSKUAdmin(admin.ModelAdmin):
    list_display = ('id', 'beatRHApproval', 'product', 'product_quantity')
    search_fields = ('id', 'beatRHApproval')
    readonly_fields = ['id',]

    def get_queryset(self, request):
        queryset = super(SalesRHApprovalSKUAdmin, self).get_queryset(request)
        queryset = queryset.order_by('id')
        return queryset


admin.site.register(SalesPersonProfile, SalesPersonAdmin)
admin.site.register(SalesEggsdata, SalesEggsAdmin)
admin.site.register(RetailerDemand, RetailerDemandAdmin)
admin.site.register(RetailerDemandSKU, RetailerDemandSKUAdmin)
admin.site.register(SalesDemandSKU, SalesDemandSKUAdmin)
admin.site.register(SalesSupplySKU, SalesSupplySKUAdmin)
admin.site.register(SalesSMApprovalSKU, SalesSMApprovalSKUAdmin)
admin.site.register(SalesRHApprovalSKU, SalesRHApprovalSKUAdmin)

