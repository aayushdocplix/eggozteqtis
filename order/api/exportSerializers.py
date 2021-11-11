from rest_framework import serializers

from order.models.Order import Order


class OrderExportSerializer(serializers.ModelSerializer):
    retailerName = serializers.SerializerMethodField()
    salesPersonName = serializers.SerializerMethodField()
    warehouse_name = serializers.SerializerMethodField()
    order_items = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()
    delivery_date = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ('id', 'orderId', 'salesPersonName', 'retailerName', 'date',
                  'delivery_date', 'order_items', 'order_price_amount', 'status', 'warehouse_name', 'order_type',
                  'retailer_note')

    def get_retailerName(self, obj):
        if obj.retailer:
            return obj.retailer.name_of_shop
        else:
            return None

    def get_date(self, obj):
        return obj.date.strftime('%d/%m/%Y')

    def get_delivery_date(self, obj):
        return obj.delivery_date.strftime('%d/%m/%Y')

    def get_salesPersonName(self, obj):
        return obj.salesPerson.user.name

    def get_warehouse_name(self, obj):
        if obj.warehouse:
            return obj.warehouse.name
        return None

    def get_order_items(self, obj):
        order_items = None
        order_lines = obj.lines.all()
        for order_line in order_lines:
            if order_line.product:
                item_name = str(order_line.product.SKU_Count) + order_line.product.name[0] + "*" + str(
                    order_line.quantity) + "(" + str(order_line.quantity * order_line.single_sku_rate) + ")"
                if order_items:
                    order_items = order_items + " & " + str(item_name)
                else:
                    order_items = str(item_name)
        return order_items
