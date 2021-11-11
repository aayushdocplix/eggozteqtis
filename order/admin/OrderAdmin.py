from django.contrib import admin

from order.models import Order, OrderLine
from order.models.Order import PackingOrder, OrderEvent, OrderReturnLine, PurchaseOrder, EcommerceOrder, \
    OrderPendingTransaction, ReturnOrderTransaction


class OrderLineInline(admin.StackedInline):
    model = OrderLine
    extra = 0


class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'order_price_amount', 'orderId', 'retailer', 'salesPerson','distributor', 'status', 'warehouse',
                    'generation_date', 'date', 'delivery_date')
    search_fields = ('id', 'name', 'orderId', 'salesPerson__user__name', 'retailer__retailer__name')
    readonly_fields = ['id',]
    inlines = [OrderLineInline]
    filterset_fields = ('status','delivery_date', 'retailer', 'salesPerson', 'customer','distributor')

    def get_queryset(self, request):
        queryset = super(OrderAdmin, self).get_queryset(request)
        queryset = queryset.order_by('id')
        return queryset

    # def save_model(self, request, obj, form, change):
    #     pass


class OrderLineAdmin(admin.ModelAdmin):
    list_display = ('id', 'quantity', 'single_sku_rate','order')
    search_fields = ('id',)
    readonly_fields = ['id']

    def get_queryset(self, request):
        queryset = super(OrderLineAdmin, self).get_queryset(request)
        queryset = queryset.order_by('id')
        return queryset


class OrderReturnLineAdmin(admin.ModelAdmin):
    list_display = ('id', 'quantity', 'amount', 'date', 'line_type', 'order_name')
    search_fields = ('id',)
    readonly_fields = ['id']

    def order_name(self, obj):
        return '%s' % obj.orderLine.order.name


    def get_queryset(self, request):
        queryset = super(OrderReturnLineAdmin, self).get_queryset(request)
        queryset = queryset.order_by('id')
        return queryset


admin.site.register(Order, OrderAdmin)
admin.site.register(PurchaseOrder, OrderAdmin)
admin.site.register(EcommerceOrder, OrderAdmin)
admin.site.register(OrderLine, OrderLineAdmin)
admin.site.register(PackingOrder)
admin.site.register(OrderEvent)
admin.site.register(OrderPendingTransaction)
admin.site.register(ReturnOrderTransaction)
admin.site.register(OrderReturnLine, OrderReturnLineAdmin)
