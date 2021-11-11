import decimal
from datetime import timedelta, datetime

from django.utils import timezone
from rest_framework import serializers

from Eggoz.settings import CURRENT_ZONE
from base.api.serializers import CitySerializer
from product.api.serializers import ProductSerializer, ProductShortSerializer
from retailer.api.serializers import CustomerCategorySerializer, CommissionSlabSerializer, RetailerShortsSerializer, \
    ShortBeatRetailerSerializer, RetailerSalesSerializer
from custom_auth.api.serializers import UserSerializer, UserShortSerializer, UserTinySerializer
from payment.models import SalesTransaction
from retailer.models import Retailer
from saleschain.models import SalesPersonProfile, SalesEggsdata, RetailerDemand, RetailerDemandSKU, SalesDemandSKU, \
    SalesSupplySKU, SalesRHApprovalSKU, SalesSMApprovalSKU, SalesSupplyPackedSKU


class SalesPersonProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = SalesPersonProfile
        fields = '__all__'


class SalesPersonShortSerializer(serializers.ModelSerializer):
    user = UserShortSerializer()

    class Meta:
        model = SalesPersonProfile
        fields = '__all__'


class SalesPersonTinySerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = SalesPersonProfile
        fields = ('id', 'name')

    def get_name(self, obj):
        return obj.user.name


class SalesManagerHistorySerializer(serializers.ModelSerializer):
    earnings = serializers.SerializerMethodField()
    retailers = serializers.SerializerMethodField()
    orders = serializers.SerializerMethodField()

    total_orders = serializers.SerializerMethodField()

    class Meta:
        model = SalesPersonProfile
        # fields = ('earnings', 'retailers', 'orders')
        fields = ('earnings', 'retailers', 'orders', 'total_orders')

    def get_earnings(self, obj):
        current_month = datetime.now(tz=CURRENT_ZONE).month
        if (current_month == 1):
            previous_month = 12
            current_year = datetime.now(tz=CURRENT_ZONE).year - 1
        else:
            previous_month = datetime.now(tz=CURRENT_ZONE).month - 1
            current_year = datetime.now(tz=CURRENT_ZONE).year
        print(current_year)
        print(current_month)
        sales_transactions = obj.transaction.filter(transaction_type="Credit", transaction_date__month=current_month,
                                                    transaction_date__year=current_year, )
        current_month_earning = decimal.Decimal(0.0)
        for sales_transaction in sales_transactions:
            current_month_earning = current_month_earning + sales_transaction.transaction_amount
        previous_month_earning = decimal.Decimal(0.0)
        previous_month_sales_transactions = sales_transactions.filter(transaction_type="Credit",
                                                                      transaction_date__month=previous_month,
                                                                      transaction_date__year=current_year, )
        for previous_month_sales_transaction in previous_month_sales_transactions:
            previous_month_earning = previous_month_earning + previous_month_sales_transaction.transaction_amount
        return {"current_month": current_month_earning, "previous_month": previous_month_earning}

    def get_retailers(self, obj):
        total_retailers = obj.salesPersonProfile.all()
        total_retailers_count = total_retailers.count()
        time_difference = datetime.now(tz=CURRENT_ZONE) - timedelta(days=7)
        month_time_difference = datetime.now(tz=CURRENT_ZONE) - timedelta(days=30)
        weekly_retailers = total_retailers.filter(onboarding_date__gte=time_difference).count()
        monthly_active_retailers = total_retailers.filter(
            onboarding_status__in=["Onboarded", "Pending Interested"],
            onboarding_date__gte=month_time_difference).count()
        month_inactive_retailers = total_retailers.filter(onboarding_status="Cold",
                                                          onboarding_date__gte=month_time_difference).count()
        return {"total": total_retailers_count, "weekly": weekly_retailers, "month_active": monthly_active_retailers,
                "month_inactive": month_inactive_retailers}

    def get_orders(self, obj):
        total_orders = obj.OrdersalesPerson.filter(status="delivered")
        total_orders_count = total_orders.count()
        time_difference = datetime.now(tz=CURRENT_ZONE) - timedelta(days=7)
        weekly_orders_count = total_orders.filter(date__gte=time_difference).count()
        return {"total": total_orders_count, "weekly": weekly_orders_count}

    def get_total_orders(self, obj):
        current_month = datetime.now(tz=CURRENT_ZONE).month
        if (current_month == 1):
            previous_month = 12
            current_year = datetime.now(tz=CURRENT_ZONE).year - 1
        else:
            previous_month = datetime.now(tz=CURRENT_ZONE).month - 1
            current_year = datetime.now(tz=CURRENT_ZONE).year
        eggs_sold_month = SalesEggsdata.objects.filter(salesPerson=obj, date__month=current_month,
                                                       date__year=current_year, )
        eggs_sold_previous_month = SalesEggsdata.objects.filter(salesPerson=obj, date__month=previous_month,
                                                                date__year=current_year, )
        orders_list_dict = {'Brown': 0, 'White': 0, 'Nutra': 0, 'current_month': 0, 'previous_month': 0}
        orders_list_dict_prev = {'Brown': 0, 'White': 0, 'Nutra': 0}
        for eggs_sold_day in eggs_sold_month:
            eggs_per_day(orders_list_dict, eggs_sold_day)
        for eggs_sold_day in eggs_sold_previous_month:
            eggs_per_day(orders_list_dict_prev, eggs_sold_day)
        orders_list_dict['current_month'] = orders_list_dict['Brown'] + orders_list_dict['White'] + orders_list_dict[
            'Nutra']
        orders_list_dict['previous_month'] = orders_list_dict_prev['Brown'] + orders_list_dict_prev['White'] + \
                                             orders_list_dict_prev['Nutra']
        return orders_list_dict


class SalesPersonHistorySerializer(serializers.ModelSerializer):
    earnings = serializers.SerializerMethodField()
    retailers = serializers.SerializerMethodField()
    orders = serializers.SerializerMethodField()

    total_orders = serializers.SerializerMethodField()

    class Meta:
        model = SalesPersonProfile
        # fields = ('earnings', 'retailers', 'orders')
        fields = ('earnings', 'retailers', 'orders', 'total_orders')

    def get_earnings(self, obj):
        current_month = datetime.now(tz=CURRENT_ZONE).month
        if (current_month == 1):
            previous_month = 12
            current_year = datetime.now(tz=CURRENT_ZONE).year - 1
        else:
            previous_month = datetime.now(tz=CURRENT_ZONE).month - 1
            current_year = datetime.now(tz=CURRENT_ZONE).year
        print(current_year)
        print(current_month)
        sales_transactions = obj.transaction.filter(transaction_type="Credit", transaction_date__month=current_month,
                                                    transaction_date__year=current_year, )
        current_month_earning = decimal.Decimal(0.0)
        for sales_transaction in sales_transactions:
            current_month_earning = current_month_earning + sales_transaction.transaction_amount
        previous_month_earning = decimal.Decimal(0.0)
        previous_month_sales_transactions = sales_transactions.filter(transaction_type="Credit",
                                                                      transaction_date__month=previous_month,
                                                                      transaction_date__year=current_year, )
        for previous_month_sales_transaction in previous_month_sales_transactions:
            previous_month_earning = previous_month_earning + previous_month_sales_transaction.transaction_amount
        return {"current_month": current_month_earning, "previous_month": previous_month_earning}

    def get_retailers(self, obj):
        total_retailers = obj.salesPersonProfile.all()
        total_retailers_count = total_retailers.count()
        time_difference = datetime.now(tz=CURRENT_ZONE) - timedelta(days=7)
        month_time_difference = datetime.now(tz=CURRENT_ZONE) - timedelta(days=30)
        weekly_retailers = total_retailers.filter(onboarding_date__gte=time_difference).count()
        monthly_active_retailers = total_retailers.filter(
            onboarding_status__in=["Onboarded", "Pending Interested"],
            onboarding_date__gte=month_time_difference).count()
        month_inactive_retailers = total_retailers.filter(onboarding_status="Cold",
                                                          onboarding_date__gte=month_time_difference).count()
        return {"total": total_retailers_count, "weekly": weekly_retailers, "month_active": monthly_active_retailers,
                "month_inactive": month_inactive_retailers}

    def get_orders(self, obj):
        total_orders = obj.OrdersalesPerson.filter(status="delivered")
        total_orders_count = total_orders.count()
        time_difference = datetime.now(tz=CURRENT_ZONE) - timedelta(days=7)
        weekly_orders_count = total_orders.filter(date__gte=time_difference).count()
        return {"total": total_orders_count, "weekly": weekly_orders_count}

    def get_total_orders(self, obj):
        current_month = datetime.now(tz=CURRENT_ZONE).month
        if (current_month == 1):
            previous_month = 12
            current_year = datetime.now(tz=CURRENT_ZONE).year - 1
        else:
            previous_month = datetime.now(tz=CURRENT_ZONE).month - 1
            current_year = datetime.now(tz=CURRENT_ZONE).year
        eggs_sold_month = SalesEggsdata.objects.filter(salesPerson=obj, date__month=current_month,
                                                       date__year=current_year, )
        eggs_sold_previous_month = SalesEggsdata.objects.filter(salesPerson=obj, date__month=previous_month,
                                                                date__year=current_year, )
        orders_list_dict = {'Brown': 0, 'White': 0, 'Nutra': 0, 'current_month': 0, 'previous_month': 0}
        orders_list_dict_prev = {'Brown': 0, 'White': 0, 'Nutra': 0}
        for eggs_sold_day in eggs_sold_month:
            eggs_per_day(orders_list_dict, eggs_sold_day)
        for eggs_sold_day in eggs_sold_previous_month:
            eggs_per_day(orders_list_dict_prev, eggs_sold_day)
        orders_list_dict['current_month'] = orders_list_dict['Brown'] + orders_list_dict['White'] + orders_list_dict[
            'Nutra']
        orders_list_dict['previous_month'] = orders_list_dict_prev['Brown'] + orders_list_dict_prev['White'] + \
                                             orders_list_dict_prev['Nutra']
        return orders_list_dict


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


class SalesRetailerListSerializer(serializers.ModelSerializer):
    category = CustomerCategorySerializer()
    city = CitySerializer()
    email = serializers.SerializerMethodField()
    commission_slab = CommissionSlabSerializer()
    short_name = RetailerShortsSerializer()

    class Meta:
        model = Retailer
        fields = ('id', 'email', 'name_of_shop', 'billing_name_of_shop', 'code', 'short_name', 'category', 'city',
                  'phone_no', 'code', 'shop_photo_url', 'last_order_date', 'amount_due', 'onboarding_status',
                  'commission_slab', 'amount_due', 'calc_amount_due')

    def get_email(self, obj):
        return obj.retailer.email


class SalesRetailerLedgerSerializer(serializers.ModelSerializer):
    bills = serializers.SerializerMethodField()
    deliveryName = serializers.SerializerMethodField()

    class Meta:
        model = SalesTransaction
        fields = (
            'id', 'transaction_id', 'transaction_type', 'transaction_date', 'transaction_amount', 'deliveryName',
            'current_balance', 'bills',
            'remarks')

    def get_bills(self, obj):
        if obj.invoices.all():
            return "\n, ".join([i.order.name for i in obj.invoices.all()])
        else:
            return ""

    def get_deliveryName(self, obj):
        if obj.distributor:
            return obj.distributor.user.name
        elif obj.salesPerson:
            return obj.salesPerson.user.name
        else:
            return ""


class RetailerDemandSKUSerializer(serializers.ModelSerializer):
    product = ProductShortSerializer()

    class Meta:
        model = RetailerDemandSKU
        fields = ('id', 'retailerDemand', 'product', 'product_quantity', 'product_supply_quantity',
                  'product_out_quantity', 'product_return_quantity', 'product_replacement_quantity',
                  'product_sold_quantity', 'product_in_quantity')


class RetailerDemandSKUCreateSerializer(serializers.ModelSerializer):
    product_quantity = serializers.IntegerField(required=True)

    class Meta:
        model = RetailerDemandSKU
        fields = ('id', 'product', 'product_quantity', 'product_supply_quantity',
                  'product_out_quantity', 'product_return_quantity', 'product_replacement_quantity',
                  'product_sold_quantity', 'product_in_quantity')


class SalesDemandSKUSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesDemandSKU
        fields = ('id', 'product', 'product_quantity', 'product_supply_quantity', 'product_fresh_stock_validated',
                  'product_old_stock_validated',
                  'product_out_quantity', 'product_return_quantity', 'product_replacement_quantity',
                  'product_sold_quantity', 'product_in_quantity', 'product_transfer_quantity',
                  'product_fresh_in_quantity', 'product_return_repalce_in_quantity')


class SalesDemandSKUCreateSerializer(serializers.ModelSerializer):
    product_quantity = serializers.IntegerField(required=True)

    class Meta:
        model = SalesDemandSKU
        fields = ('id', 'product', 'product_quantity', 'product_supply_quantity', 'product_fresh_stock_validated',
                  'product_old_stock_validated',
                  'product_out_quantity', 'product_return_quantity', 'product_replacement_quantity',
                  'product_sold_quantity', 'product_in_quantity', 'product_transfer_quantity',
                  'product_fresh_in_quantity', 'product_return_repalce_in_quantity')


class SalesDemandSKUUpdateSerializer(serializers.ModelSerializer):
    product_supply_quantity = serializers.IntegerField(required=True)

    class Meta:
        model = SalesDemandSKU
        fields = ('id', 'product', 'product_quantity', 'product_supply_quantity', 'product_fresh_stock_validated',
                  'product_old_stock_validated',
                  'product_out_quantity', 'product_return_quantity', 'product_replacement_quantity',
                  'product_sold_quantity', 'product_in_quantity', 'product_transfer_quantity',
                  'product_fresh_in_quantity', 'product_return_repalce_in_quantity')


class RetailerDemandSKUUpdateSerializer(serializers.ModelSerializer):
    product_supply_quantity = serializers.IntegerField(required=True)

    class Meta:
        model = RetailerDemandSKU
        fields = ('id', 'product', 'product_quantity', 'product_supply_quantity', 'product_out_quantity',
                  'product_return_quantity', 'product_replacement_quantity', 'product_sold_quantity',
                  'product_in_quantity')


class RetailerDemandCreateSerializer(serializers.ModelSerializer):
    date = serializers.DateField(required=True)
    time = serializers.TimeField(required=True)

    class Meta:
        model = RetailerDemand
        fields = ('id', 'retailer', 'date', 'time')


class RetailerDemandSerializer(serializers.ModelSerializer):
    # retailer = ShortBeatRetailerSerializer()
    retailer = RetailerSalesSerializer()
    retailerDemandSKU = serializers.SerializerMethodField()

    class Meta:
        model = RetailerDemand
        fields = ('id', 'retailer', 'date', 'time', 'retailerDemandSKU', 'priority', 'retailer_status')

    def get_retailerDemandSKU(self, obj):
        demandSKUQueryset = obj.demandSKU.all()
        return RetailerDemandSKUSerializer(demandSKUQueryset, many=True).data


class SalesSupplyPackedSkuSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesSupplyPackedSKU
        fields = ('product', 'product_quantity')


class SalesSupplySkuSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesSupplySKU
        fields = ('product', 'product_quantity')


class SalesSMApprovalSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesSMApprovalSKU
        fields = ('product', 'product_quantity', 'demand_classification')


class SalesRHApprovalSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesRHApprovalSKU
        fields = ('product', 'product_quantity')
