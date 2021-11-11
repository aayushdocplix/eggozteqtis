from django.contrib import admin

from order.models import Order
from warehouse.models import Vehicle, Driver, VehicleAssignment


class VehicleAdmin(admin.ModelAdmin):
    list_display = ('id',  'vehicle_identifier', 'default_driver','vendor', 'vehicle_no')
    search_fields = ('id', 'vehicle_identifier','default_driver','vendor', 'vehicle_no')
    readonly_fields = ['id']

    def get_queryset(self, request):
        queryset = super(VehicleAdmin, self).get_queryset(request)
        queryset = queryset.order_by('id')
        return queryset


class DriverAdmin(admin.ModelAdmin):
    list_display = ('id', 'driver_name', 'driver_desc',)
    search_fields = ('id', 'driver_name', 'driver_desc',)
    readonly_fields = ['id']

    def get_queryset(self, request):
        queryset = super(DriverAdmin, self).get_queryset(request)
        queryset = queryset.order_by('id')
        return queryset


class OrderInline(admin.StackedInline):
    model = Order
    extras = 0



class VehicleAssignmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'driver', 'operation_option', 'warehouseEmployee', 'desc', 'vehicle', 'orders')
    search_fields = ('id', 'driver', 'operation_option', 'warehouseEmployee', 'desc', 'vehicle')
    readonly_fields = ['id']
    inlines = [OrderInline]

    def orders(self, obj):
        items = []
        if obj.order_set.all():
            for ele in obj.order_set.all():
                items.append(ele.orderId)
        return '%s' % items


    def get_queryset(self, request):
        queryset = super(VehicleAssignmentAdmin, self).get_queryset(request)
        queryset = queryset.order_by('id')
        return queryset


admin.site.register(Vehicle, VehicleAdmin)
admin.site.register(Driver, DriverAdmin)
admin.site.register(VehicleAssignment, VehicleAssignmentAdmin)
