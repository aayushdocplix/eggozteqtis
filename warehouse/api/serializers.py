from rest_framework import serializers

from custom_auth.api.serializers import AddressSerializer
from order.api.serializers import OrderHistorySerializer
from product.api.serializers import ProductSerializer
from warehouse.models import Vehicle, Driver, QCEntry, VehicleAssignment, Stock, StockInline, EggProductStockInline, \
    Warehouse, WarehousePersonProfile, QCLine, Inventory, PackedInventory, DailyPaymentLine, DailyPayments, Expense, \
    ExpenseRequest, ExpenseCategory, BankTransaction, BankDetails, BeatInventory, BeatInventoryLine, AdhocVehicle

from warehouse.models.Wastage import Wastage


class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = '__all__'

class AdhocVehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdhocVehicle
        fields = '__all__'


class VehicleOnboardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = ('vehicle_desc', 'vehicle_no', 'vehicle_identifier', 'vehicle_photo_url', 'vendor',
            'vendor_contact_no', 'per_day_charge', 'per_day_duration', 'per_day_distance', 'default_driver')


class DriverSerializer(serializers.ModelSerializer):

    class Meta:
        model = Driver
        fields = '__all__'


class InventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Inventory
        fields = '__all__'


class PackedInventorySerializer(serializers.ModelSerializer):
    product = serializers.SerializerMethodField()

    def get_product(self, obj):
        return ProductSerializer(obj.product).data

    class Meta:
        model = PackedInventory
        fields = '__all__'


class BeatInventorySerializer(serializers.ModelSerializer):

    class Meta:
        model = BeatInventory
        fields = '__all__'


class BeatInventoryLineSerializer(serializers.ModelSerializer):

    class Meta:
        model = BeatInventoryLine
        fields = ('product', 'quantity')


class BeatInventoryHistorySerializer(serializers.ModelSerializer):
    inlines = serializers.SerializerMethodField()

    def get_inlines(self, obj):
        beatInventoryInlines = obj.beat_inventory_line.all()
        return BeatInventoryLineSerializer(beatInventoryInlines, many=True).data

    class Meta:
        model = BeatInventory
        fields = ('beat_details', 'date' , 'inventory_status', 'warehouse',  'inlines', 'entered_by')


class DriverOnboardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Driver
        fields = ('driver_name', 'driver_desc', 'driver_no', 'driver_license_no', 'driver_photo', 'license_photo')


class DriverShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Driver
        fields = ('driver_name', 'driver_no','id')

class VehicleShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = ('id', 'vehicle_no', 'vehicle_identifier_type', 'vendor', 'vehicle_status')


class AdhocVehicleShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdhocVehicle
        fields = ('id', 'vehicle_no', 'vehicle_identifier_type', 'vendor', 'vehicle_status')



class VehicleAssignmentSendDeliverySerializer(serializers.ModelSerializer):
    order = serializers.SerializerMethodField()

    def get_order(self, obj):
        orderInlines = obj.order_set.all()
        return OrderHistorySerializer(orderInlines, many=True).data

    class Meta:
        model = VehicleAssignment
        fields = ('driver', 'vehicle', 'operation_option', 'desc', 'delivery_person', 'order')


class VehicleAssignmentSerializer(serializers.ModelSerializer):
    driver = DriverSerializer()
    vehicle = VehicleSerializer()
    order = serializers.SerializerMethodField()

    def get_order(self, obj):
        orderInlines = obj.order_set.all()
        return OrderHistorySerializer(orderInlines, many=True).data

    class Meta:
        model = VehicleAssignment
        fields = '__all__'


class QCLineValidationSerializer(serializers.ModelSerializer):
    class Meta:
        model = QCLine
        fields = ('name', 'ph_value')


class QCEntryValidationSerializer(serializers.ModelSerializer):
    qc_lines = QCLineValidationSerializer(many=True)

    class Meta:
        model = QCEntry
        fields = ('desc', 'qc_lines')

    def validate(self, data):

        qc_lines = data.get('qc_lines', None)
        if qc_lines is None:
            raise serializers.ValidationError("qc_lines required")
        if len(qc_lines) < 1:
            raise serializers.ValidationError("QC In Lines can not be empty")
        return data


class StockDuplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stock
        fields = (
            'batch_id', 'warehouse', 'farm', 'supplyPerson', 'warehousePerson', 'operationsPerson', 'driver', 'vehicle',
            'productDivision')


class EggProductStockInlineValidationSerializer(serializers.ModelSerializer):
    class Meta:
        model = EggProductStockInline
        fields = ('name', 'desc', 'sku_type', 'quantity')


class WastageInlineValidationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wastage
        fields = ('wastage_type', 'expected_quantity', 'counted_quantity',)


class StockInlineValidationSerializer(serializers.ModelSerializer):
    eggProductStockInLines = EggProductStockInlineValidationSerializer(many=True)
    wastageInLines = WastageInlineValidationSerializer(many=True, required=False)
    stock_note = serializers.CharField(required=False)
    qc_entry = QCEntryValidationSerializer(required=False)

    class Meta:
        model = StockInline
        fields = ('baseProduct', 'eggProductStockInLines', 'stock_note', 'wastageInLines', 'qc_entry')

    def validate(self, data):
        context = self.context
        stock_type = context.get('stock_type')
        eggProductStockInLines = data.get('eggProductStockInLines', None)
        if eggProductStockInLines is None:
            raise serializers.ValidationError("Egg Product Stock In Lines can not be empty")
        if len(eggProductStockInLines) < 1:
            raise serializers.ValidationError("Egg Product Stock In Lines can not be empty")
        else:
            if stock_type == "receive":
                wastageInLines = data.get('wastageInLines', None)
                if wastageInLines is None:
                    raise serializers.ValidationError("Wastage In Lines can not be empty")
                if len(wastageInLines) < 1:
                    raise serializers.ValidationError("Wastage In Lines can not be empty")
            if stock_type == "qc_done":
                wastageInLines = data.get('wastageInLines', None)
                if wastageInLines is None:
                    raise serializers.ValidationError("Wastage In Lines can not be empty")
                if len(wastageInLines) < 1:
                    raise serializers.ValidationError("Wastage In Lines can not be empty")
                qc_entry = data.get('qc_entry', None)
                if qc_entry is None:
                    raise serializers.ValidationError("Qc Entry required")
            return data


class StockPickUpValidationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stock
        fields = ('farm', 'productDivision')


class WastageValidationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wastage
        fields = ('stock_inline', 'wastage_type', 'name', 'expected_quantity', 'counted_quantity', 'wastage_remark')

    def validate(self, data):
        request = self.context.get('request')
        stock_id = request.data.get('stock_id')
        stock_inline = data.get('stock_inline')
        stockInline = StockInline.objects.filter(stock__id=stock_id, id=stock_inline.id).first()
        if stockInline:
            wastages = Wastage.objects.filter(stock_inline=stock_inline)
            if wastages.count() > 0:
                raise serializers.ValidationError("Already wastage added")
            else:
                return data
        else:
            raise serializers.ValidationError("Stock In line mismatch")


class EggProductStockInlineSerializer(serializers.ModelSerializer):
    class Meta:
        model = EggProductStockInline
        fields = ('id', 'stock_inline', 'name', 'desc', 'sku_type', 'quantity')


class StockInlineSerializer(serializers.ModelSerializer):
    eggProductStockInline = serializers.SerializerMethodField()
    baseProduct_name = serializers.SerializerMethodField()
    total_quantity = serializers.SerializerMethodField()

    class Meta:
        model = StockInline
        fields = ('baseProduct', 'baseProduct_name', 'stock', 'stock_note', 'eggProductStockInline', 'total_quantity')

    def get_eggProductStockInline(self, obj):
        eggProductStockInlines = obj.product_type_stock_inline.all()
        return EggProductStockInlineSerializer(eggProductStockInlines, many=True).data

    def get_baseProduct_name(self, obj):
        return obj.baseProduct.name

    def get_products(self, obj):
        return "hello"

    def get_total_quantity(self, obj):
        total_quantity = 0
        eggProductStockInlines = obj.product_type_stock_inline.all()
        for EPSI in eggProductStockInlines:
            if EPSI.sku_type == "Full":
                total_quantity = total_quantity + EPSI.quantity * 30
            else:
                total_quantity = total_quantity + EPSI.quantity
        return str(total_quantity) + " " + obj.baseProduct.description


class StockSerializer(serializers.ModelSerializer):
    stockInline = serializers.SerializerMethodField()
    farm_name = serializers.SerializerMethodField()
    warehouse_name = serializers.SerializerMethodField()
    warehousePerson_name = serializers.SerializerMethodField()
    operationsPerson_name = serializers.SerializerMethodField()
    supplyPerson_name = serializers.SerializerMethodField()
    driver_name = serializers.SerializerMethodField()
    vehicle_no = serializers.SerializerMethodField()
    total_quantity = serializers.SerializerMethodField()
    total_products = serializers.SerializerMethodField()

    class Meta:
        model = Stock
        fields = (
            'id', 'batch_id', 'warehouse', 'warehouse_name', 'farm', 'farm_name', 'is_forwarded', 'supplyPerson',
            'supplyPerson_name',
            'warehousePerson',
            'warehousePerson_name', 'operationsPerson', 'operationsPerson_name', 'driver', 'driver_name',
            'vehicle', 'vehicle_no', 'productDivision', 'from_source', 'to_destination', 'stock_status', 'stockInline',
            'received_at',
            'picked_at', 'qc_done_at', 'total_quantity', 'total_products')

    def get_stockInline(self, obj):
        stockInlines = obj.stock_inline.all()
        return StockInlineSerializer(stockInlines, many=True).data

    def get_warehouse_name(self, obj):
        name = None
        if obj.warehouse:
            name = obj.warehouse.name
        return name

    def get_farm_name(self, obj):
        name = None
        if obj.farm:
            name = obj.farm.farm_name
        return name

    def get_warehousePerson_name(self, obj):
        name = None
        if obj.warehousePerson:
            name = obj.warehousePerson.user.name
        return name

    def get_supplyPerson_name(self, obj):
        name = None
        if obj.supplyPerson:
            name = obj.supplyPerson.user.name
        return name

    def get_operationsPerson_name(self, obj):
        name = None
        if obj.operationsPerson:
            name = obj.operationsPerson.user.name
        return name

    def get_driver_name(self, obj):
        name = None
        if obj.driver:
            name = obj.driver.driver_name
        return name

    def get_vehicle_no(self, obj):
        number = None
        if obj.vehicle:
            number = obj.vehicle.vehicle_no
        return number

    def get_total_quantity(self, obj):
        stockInlines = obj.stock_inline.all()
        data = StockInlineSerializer(stockInlines, many=True).data
        quantity = []
        for item in data:
            quantity.append(item['total_quantity'])
        return ' , '.join(quantity)

    def get_total_products(self, obj):
        stockInlines = obj.stock_inline.all()
        data = StockInlineSerializer(stockInlines, many=True).data
        product = []
        for item in data:
            product.append(item['baseProduct_name'])
        return ' , '.join(product)


class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = '__all__'


class WarehouseEmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = WarehousePersonProfile
        fields = '__all__'


class InventoryUpdateSerializer(serializers.ModelSerializer):
    branded_quantity = serializers.IntegerField(required=True)
    unbranded_quantity = serializers.IntegerField(required=True)

    class Meta:
        model = Inventory
        fields = ('warehouse', 'name', 'branded_quantity', 'unbranded_quantity','chatki_quantity')


class PackedInventoryUpdateSerializer(serializers.ModelSerializer):
    quantity = serializers.IntegerField(required=True)

    class Meta:
        model = PackedInventory
        fields = ('warehouse', 'name', 'quantity')


class DailyPaymentLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyPaymentLine
        fields = '__all__'


class DailyPaymentsSerializer(serializers.ModelSerializer):
    payment_lines = serializers.SerializerMethodField()
    salesPersonName = serializers.SerializerMethodField()
    time = serializers.CharField(required=False)

    class Meta:
        model = DailyPayments
        fields = ('warehouse', 'payment_lines','salesPersonName', 'date', 'time', 'salesPerson', 'remark', 'total_amount', 'is_verified')

    def get_time(self, obj):
        return self.time

    def get_salesPersonName(self, obj):
        if obj.salesPerson:
            return obj.salesPerson.user.name
        
    def get_payment_lines(self, obj):
        paymentInlines = obj.daily_payment_lines.all()
        return DailyPaymentLineSerializer(paymentInlines, many=True).data


class ExpenseRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseRequest
        fields = '__all__'



class BankDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankDetails
        fields = '__all__'



class BankDepositSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankTransaction
        fields = '__all__'


class ExpenseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseCategory
        fields = '__all__'


class ExpenseSerializer(serializers.ModelSerializer):
    userName = serializers.SerializerMethodField()
    expenseCategory = serializers.SerializerMethodField()

    class Meta:
        model = Expense
        fields = '__all__'

    def get_time(self, obj):
        return self.date_time

    def get_userName(self, obj):
        if obj.user:
            return obj.user.name

    def get_expenseCategory(self, obj):
        if obj.expense_category:
            return obj.expense_category.name