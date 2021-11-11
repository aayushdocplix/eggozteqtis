from datetime import datetime, timedelta

from rest_framework import serializers

from Eggoz.settings import CURRENT_ZONE
from custom_auth.api.serializers import UserSerializer, UserShortSerializer
from distributionchain.models import DistributionPersonProfile, BeatAssignment, BeatRHApproval, BeatSMApproval, \
    BeatWarehouseSupply, TripSKUTransfer, TransferSKU, SMRelativeNumber
from order.models import Order
from payment.api.serializers import PendingInvoiceForPrintSerializer
from payment.models import Invoice
from retailer.models import Retailer
from saleschain.api.serializers import RetailerDemandSerializer, SalesDemandSKUSerializer, SalesSupplySkuSerializer, \
    SalesSMApprovalSerializer, SalesRHApprovalSerializer, SalesSupplyPackedSkuSerializer
from warehouse.api.serializers import VehicleShortSerializer, DriverShortSerializer, AdhocVehicleShortSerializer
from warehouse.models import Vehicle


class DistributionPersonProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = DistributionPersonProfile
        fields = '__all__'


class DistributionPersonShortSerializer(serializers.ModelSerializer):
    user = UserShortSerializer()

    class Meta:
        model = DistributionPersonProfile
        fields = '__all__'


class DistributionManagerHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = DistributionPersonProfile
        fields = '__all__'


class DistributionPersonHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = DistributionPersonProfile
        fields = '__all__'


class BeatAssignmentSerializer(serializers.ModelSerializer):
    beat_date = serializers.DateField(required=True)
    beat_expected_time = serializers.TimeField(required=True)
    beat_number = serializers.IntegerField(required=True)

    class Meta:
        model = BeatAssignment
        fields = (
            'id', 'assigned_by', 'distributor', 'beat_person', 'beat_number', 'beat_status', 'beat_date', 'beat_name',
            'driver',
            'vehicle', 'beat_expected_time', 'beat_time', 'beat_demand_by', 'beat_supply_by', 'priority', 'warehouse',
            'beat_type',
            'demand_classification', 'beat_type_number', 'beat_supply_approved_by', 'beat_material_status')


class BeatUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BeatAssignment
        fields = '__all__'


class BeatWarehouseSupplySerializer(serializers.ModelSerializer):
    class Meta:
        model = BeatWarehouseSupply
        fields = '__all__'


class BeatWarehouseSupplyDetailSerializer(serializers.ModelSerializer):
    warehouse_supply_lines = serializers.SerializerMethodField()
    warehouse_supply_packed_lines = serializers.SerializerMethodField()

    class Meta:
        model = BeatWarehouseSupply
        fields = ('id', 'supply_white_percentage', 'supply_brown_percentage', 'supply_nutra_percentage', 'beat_date',
                  'unpacked_white_eggs', 'unpacked_brown_eggs', 'unpacked_nutra_eggs',
                  'beat_supply_by', 'warehouse_supply_lines', 'warehouse_supply_packed_lines')

    def get_warehouse_supply_lines(self, obj):
        salesSupplySKULines = obj.sales_supply_beat.all()
        return SalesSupplySkuSerializer(salesSupplySKULines, many=True).data

    def get_warehouse_supply_packed_lines(self, obj):
        salesSupplyPackedSKULines = obj.sales_packed_sku.all()
        return SalesSupplyPackedSkuSerializer(salesSupplyPackedSKULines, many=True).data


class BeatSMApprovalSerializer(serializers.ModelSerializer):
    class Meta:
        model = BeatSMApproval
        fields = '__all__'


class SMRelativeNumberSerializer(serializers.ModelSerializer):
    class Meta:
        model = SMRelativeNumber
        fields = '__all__'


class BeatSMApprovalDetailSerializer(serializers.ModelSerializer):
    sm_supply_lines = serializers.SerializerMethodField()

    class Meta:
        model = BeatSMApproval
        fields = (
            'id', 'beat_warehouse_supply', 'supply_white_relative', 'supply_brown_relative',
            'supply_nutra_relative',
            'beat_date',
            'demand_classification', 'beat_supply_approved_by', 'sm_supply_lines')

    def get_sm_supply_lines(self, obj):
        salesSMSKULines = obj.sales_sm_approval_beat.all()
        return SalesSMApprovalSerializer(salesSMSKULines, many=True).data


class BeatRHApprovalSerializer(serializers.ModelSerializer):
    class Meta:
        model = BeatRHApproval
        fields = '__all__'


class BeatRHApprovalDetailSerializer(serializers.ModelSerializer):
    rh_supply_lines = serializers.SerializerMethodField()

    class Meta:
        model = BeatRHApproval
        fields = (
            'id', 'beatSMApproval', 'supply_white_percentage', 'supply_brown_percentage', 'supply_nutra_percentage',
            'beat_date',
            'beat_supply_approved_by', 'rh_supply_lines')

    def get_rh_supply_lines(self, obj):
        salesSMSKULines = obj.sales_rh_approval_beat.all()
        return SalesRHApprovalSerializer(salesSMSKULines, many=True).data


class BeatAssignmentDetailSerializer(serializers.ModelSerializer):
    beat_date = serializers.DateField()
    beat_number = serializers.IntegerField()
    vehicle = serializers.SerializerMethodField()
    driver = DriverShortSerializer()
    retailerDemand = serializers.SerializerMethodField()
    salesDemand = serializers.SerializerMethodField()
    beat_demand_by_name = serializers.SerializerMethodField()
    distributor_name = serializers.SerializerMethodField()
    vehicle_no = serializers.SerializerMethodField()

    class Meta:
        model = BeatAssignment
        fields = (
            'id', 'assigned_by', 'distributor', 'beat_person', 'beat_number', 'beat_status', 'beat_date', 'beat_name',
            'driver', 'sc_in_time',
            'vehicle', 'retailerDemand', 'beat_expected_time', 'beat_time', 'beat_demand_by', 'beat_supply_by',
            'priority',
            'warehouse',
            'beat_demand_by_name', 'salesDemand', 'in_time', 'out_time', 'return_time', 'beat_type', 'distributor_name',
            'demand_classification',
            'beat_type_number', 'beat_supply_approved_by', 'beat_material_status', 'vehicle_no')

    def get_beat_demand_by_name(self, obj):
        if obj.beat_demand_by:
            return obj.beat_demand_by.user.name

    def get_vehicle(self, obj):
        if obj.vehicle:
            return VehicleShortSerializer(obj.vehicle).data
        elif obj.adhoc_vehicle:
            return AdhocVehicleShortSerializer(obj.adhoc_vehicle).data
        else:
            return None

    def get_vehicle_no(self, obj):
        if obj.vehicle:
            return obj.vehicle.vehicle_no
        elif obj.adhoc_vehicle:
            return obj.adhoc_vehicle.vehicle_no
        else:
            return "Not Assigned"

    def get_distributor_name(self, obj):
        if obj.distributor:
            return obj.distributor.user.name

    def get_retailerDemand(self, obj):
        demandInlines = obj.demand_beat_assignment.all()
        return RetailerDemandSerializer(demandInlines, many=True).data

    def get_salesDemand(self, obj):
        demandInlines = obj.sales_demand_beat.all()
        return SalesDemandSKUSerializer(demandInlines, many=True).data


class BeatAssignmentDummySerializer(serializers.ModelSerializer):
    class Meta:
        model = BeatAssignment
        fields = (
            'assigned_by', 'distributor', 'beat_person', 'beat_number', 'beat_status', 'beat_date', 'beat_name',
            'driver',
            'priority', 'warehouse',
            'vehicle')


def eggs_per_day(orders_list_dict, eggs_sold_day):
    if orders_list_dict['Brown'] > 0 and eggs_sold_day.brown > 0:
        orders_list_dict['Brown'] = orders_list_dict['Brown'] \
                                    + eggs_sold_day.brown
    elif eggs_sold_day.brown > 0:
        orders_list_dict['Brown'] = eggs_sold_day.brown

    if orders_list_dict['White'] > 0 and eggs_sold_day.white > 0:
        orders_list_dict['White'] = orders_list_dict['White'] \
                                    + eggs_sold_day.white
    elif eggs_sold_day.white > 0:
        orders_list_dict['White'] = eggs_sold_day.white


class BeatWiseRetailerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Retailer
        fields = ('id', 'code', 'onboarding_status', 'name_of_shop', 'beat_number', 'beat_order_number',)


class RetailerBeatWiseSerializer(serializers.ModelSerializer):
    pending_invoices = serializers.SerializerMethodField()
    last_order_date = serializers.SerializerMethodField()
    weekly_average = serializers.SerializerMethodField()
    sales_person = serializers.SerializerMethodField()

    class Meta:
        model = Retailer
        fields = (
            'id', 'code', 'onboarding_status', 'name_of_shop', 'beat_number', 'beat_order_number', 'last_order_date',
            'sales_person', 'pending_invoices', 'weekly_average')

    def get_pending_invoices(self, obj):
        pending_invoices = Invoice.objects.filter(order__retailer=obj, invoice_status="Pending")
        return PendingInvoiceForPrintSerializer(pending_invoices, many=True).data

    def get_last_order_date(self, obj):
        if Order.objects.filter(retailer=obj, status="delivered"):
            return Order.objects.filter(retailer=obj, status="delivered").order_by('delivery_date').last().delivery_date
        else:
            return "No Orders Yet"

    def get_sales_person(self, obj):
        if obj.salesPersonProfile:
            return {"name": obj.salesPersonProfile.user.name, "id": obj.salesPersonProfile.id}
        else:
            return None

    def get_weekly_average(self, obj):
        time_diffrence = datetime.now(tz=CURRENT_ZONE) - timedelta(days=7)
        orders = Order.objects.filter(retailer=obj, status="delivered", delivery_date__gte=time_diffrence,
                                      delivery_date__lte=datetime.now(tz=CURRENT_ZONE))
        order_dict = {"6W": 0, "10W": 0, "25W": 0, "30W": 0, "6B": 0, "10B": 0, "25B": 0, "30B": 0, "6N": 0, "10N": 0}
        for order in orders:
            order_lines = order.lines.all()
            for order_line in order_lines:
                if order_dict.get(str(order_line.product.SKU_Count) + order_line.product.name[:1]):
                    order_dict[str(order_line.product.SKU_Count) + order_line.product.name[:1]] += order_line.quantity
        order_avg_dict = {k: int(v / 7) for k, v in order_dict.items()}
        return order_avg_dict


class RetailerBeatUpdateSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(required=True, queryset=Retailer.objects.all())

    class Meta:
        model = Retailer
        fields = ('id', 'beat_number', 'beat_order_number')

    def beat_update(self, validated_data):
        instance = validated_data.get('id')
        beat_number = validated_data.get('beat_number', instance.beat_number)
        beat_order_number = validated_data.get('beat_order_number', instance.beat_order_number)
        instance.beat_number = beat_number
        instance.beat_order_number = beat_order_number
        instance.save()
        return instance


class TransferSKUDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransferSKU
        fields = ('product', 'quantity')


class TransferSKUSerializer(serializers.ModelSerializer):
    tripTransferSKU = serializers.SerializerMethodField()

    class Meta:
        model = TripSKUTransfer
        fields = '__all__'

    def get_tripTransferSKU(self, obj):
        inlines = obj.tripTransferSKU.all()
        return TransferSKUDataSerializer(inlines, many=True).data
