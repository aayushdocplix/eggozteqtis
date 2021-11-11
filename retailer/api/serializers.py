import json
import decimal
from datetime import datetime

from django.utils import timezone
from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers

from Eggoz.settings import CURRENT_ZONE
from base.api.serializers import CitySerializer, ClusterSerializer
from base.models import City, Cluster
from custom_auth.api.serializers import AddressSerializer, AddressUpdateSerializer, AddressCreationSerializer
from custom_auth.models import User, Address
from order.models import Order
from payment.models import Invoice
from product.api.serializers import ProductShortSerializer, ProductMarginSerializer

from retailer.models.Retailer import Customer_Category, Customer_SubCategory, Retailer, RetailOwner, IncomeSlab, \
    CommissionSlab, RetailerEggsdata, Classification, DiscountSlab, RetailerShorts, RetailerPaymentCycle, RetailerBeat, \
    MarginRates


class CustomerCategorySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Customer_Category
        fields = ('id', 'name', 'description')


class RetailerBeatSerializer(serializers.ModelSerializer):
    class Meta:
        model = RetailerBeat
        fields = '__all__'


class CustomerSubCategorySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Customer_SubCategory
        fields = ('id', 'name', 'description')


class IncomeSlabSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = IncomeSlab
        fields = ('id', 'name')


class MarginRateSerializer(serializers.ModelSerializer):
    product = ProductMarginSerializer()

    class Meta:
        model = MarginRates
        fields = '__all__'


class CommissionSlabSerializer(serializers.ModelSerializer):
    # margin_commission = serializers.SerializerMethodField()

    class Meta:
        model = CommissionSlab
        fields = '__all__'

    # def get_margin_commission(self, obj):
    #     return MarginRateSerializer(obj.margin_commission.all(),many=True).data


class DiscountSlabSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = DiscountSlab
        fields = ('id', 'name', 'white_number', 'brown_number', 'nutra_number')


class ClassificationSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Classification
        fields = ('id', 'name')


class RetailerShortsSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = RetailerShorts
        fields = ('id', 'name')


class RetailerPaymentCycleSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = RetailerPaymentCycle
        fields = ('id', 'number', 'type', 'is_mt', 'is_gt')


class RetailOwnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = RetailOwner
        fields = (
            'id', 'owner_name', 'phone_no', 'owner_photo_url', 'email', 'aadhar_no', 'pancard_no', 'aadhar_status',
            'pancard_status', 'pancard_photo_url', 'aadhar_photo_url')


class RetailerSerializer(serializers.ModelSerializer):
    category = CustomerCategorySerializer()
    sub_category = CustomerSubCategorySerializer()
    city = CitySerializer()
    shipping_address = AddressSerializer()
    billing_address = AddressSerializer()
    email = serializers.SerializerMethodField()
    current_month_eggs_dict = serializers.SerializerMethodField()
    total_eggs_dict = serializers.SerializerMethodField()
    days_since_last_order = serializers.SerializerMethodField()
    last_order_date = serializers.SerializerMethodField()
    first_order_date = serializers.SerializerMethodField()
    cluster = ClusterSerializer()
    retail_owners = serializers.SerializerMethodField()
    annual_income = IncomeSlabSerializer()
    commission_slab = CommissionSlabSerializer()
    discount_slab = DiscountSlabSerializer()
    classification = ClassificationSerializer()
    short_name = RetailerShortsSerializer()
    payment_cycle = RetailerPaymentCycleSerializer()

    class Meta:
        model = Retailer

        fields = (
            'id', 'email', 'shop_photo_url', 'name_of_shop', 'billing_name_of_shop', 'short_name', 'shipping_address',
            'category', 'sub_category', 'city', 'billing_address', 'billing_shipping_address_same', 'commission_slab',
            'beat_number', 'beat_order_number', 'payment_cycle', 'code', 'payment_cycle',
            'discount_slab', 'classification', 'cluster', 'onboarding_status', 'current_month_eggs_dict',
            'total_eggs_dict', 'days_since_last_order', 'last_order_date', 'first_order_date', 'onboarding_date',
            'annual_income', 'GSTIN', 'gst_photo_url', 'phone_no',
            'retail_owners', 'amount_due')

    def get_email(self, obj):
        return obj.retailer.email

    def get_current_month_eggs_dict(self, obj):
        current_month = datetime.now(tz=CURRENT_ZONE).month
        if (current_month == 1):
            previous_month = 12
            current_year = datetime.now(tz=CURRENT_ZONE).year - 1
        else:
            previous_month = datetime.now(tz=CURRENT_ZONE).month - 1
            current_year = datetime.now(tz=CURRENT_ZONE).year
        eggs_sold_month = RetailerEggsdata.objects.filter(retailer=obj, date__month=current_month,
                                                          date__year=current_year, )
        orders_list_dict = {'Brown': 0, 'White': 0, 'Nutra': 0, 'Total': 0}
        for eggs_sold_day in eggs_sold_month:
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
        orders_list_dict['Total'] = orders_list_dict['Brown'] + orders_list_dict['White'] + orders_list_dict['Nutra']
        return orders_list_dict

    def get_total_eggs_dict(self, obj):
        eggs_sold_month = RetailerEggsdata.objects.filter(retailer=obj)
        orders_list_dict = {'Brown': 0, 'White': 0, 'Nutra': 0, 'Total': 0}
        for eggs_sold_day in eggs_sold_month:
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
        orders_list_dict['Total'] = orders_list_dict['Brown'] + orders_list_dict['White'] + orders_list_dict['Nutra']
        return orders_list_dict

    def get_days_since_last_order(self, obj):
        if Order.objects.filter(retailer=obj, status="delivered"):
            last_order = Order.objects.filter(retailer=obj, status="delivered").order_by('delivery_date').last()
            timediff = datetime.now(tz=CURRENT_ZONE) - last_order.delivery_date
            return (timediff.days)
        else:
            return "No Orders Yet"

    def get_last_order_date(self, obj):
        if Order.objects.filter(retailer=obj, status="delivered"):
            return Order.objects.filter(retailer=obj, status="delivered").order_by('delivery_date').last().delivery_date
        else:
            return "No Orders Yet"

    def get_first_order_date(self, obj):
        if Order.objects.filter(retailer=obj, status="delivered"):
            return Order.objects.filter(retailer=obj, status="delivered").order_by(
                'delivery_date').first().delivery_date
        else:
            return "No Orders Yet"

    def get_retail_owners(self, obj):
        retail_owners = obj.retail_owners.all()
        return RetailOwnerSerializer(retail_owners, many=True).data


class RetailerSalesSerializer(serializers.ModelSerializer):
    commission_slab = CommissionSlabSerializer()

    class Meta:
        model = Retailer
        fields = ('id', 'phone_no', 'amount_due',
                  'commission_slab', 'code', 'beat_number', 'beat_order_number', 'rate_type')


class ShortRetailerSerializer(serializers.ModelSerializer):
    commission_slab = CommissionSlabSerializer()
    discount_slab = DiscountSlabSerializer()

    # shipping_address = AddressSerializer()
    # cluster = ClusterSerializer()
    # short_name = RetailerShortsSerializer()
    # payment_cycle = RetailerPaymentCycleSerializer()

    class Meta:
        model = Retailer
        fields = ('id', 'phone_no', 'shipping_address',
                  'commission_slab', 'discount_slab', 'code', 'beat_number', 'beat_order_number', 'amount_due',
                  'onboarding_status')
        # fields = ('id', 'name_of_shop', 'billing_name_of_shop', 'short_name', 'phone_no', 'shipping_address',
        #           'commission_slab', 'discount_slab', 'code', 'onboarding_date',
        #           'classification', 'cluster', 'beat_number', 'beat_order_number', 'payment_cycle','amount_due', 'onboarding_status')


class ShortBeatRetailerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Retailer
        fields = ('id', 'code', 'beat_number', 'beat_order_number')


class RetailerMarginSerializer(serializers.ModelSerializer):
    commission_slab = CommissionSlabSerializer()

    class Meta:
        model = Retailer
        fields = ('id', 'code', 'beat_number', 'beat_order_number', 'commission_slab', 'onboarding_status')


class RetailerFinanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Retailer
        fields = ('id', 'code', 'onboarding_status')


class RetailerDashboardManagerDirectSerializer(serializers.ModelSerializer):
    from saleschain.api.serializers import SalesPersonTinySerializer
    commission_slab = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    discount_slab = serializers.SerializerMethodField()
    classification = serializers.SerializerMethodField()
    salesPersonProfile = SalesPersonTinySerializer()
    short_name = serializers.SerializerMethodField()
    payment_cycle = serializers.SerializerMethodField()

    class Meta:
        model = Retailer

        fields = (
            'id', 'name_of_shop', 'billing_name_of_shop', 'short_name', 'category', 'salesPersonProfile', 'beat_number',
            'beat_order_number', 'payment_cycle', 'code',
            'onboarding_status', 'last_order_date', 'onboarding_date',
            'commission_slab', 'discount_slab', 'classification', 'phone_no', 'amount_due')

    def get_SalesPersonProfile(self, obj):
        return obj.salesPersonProfile

    def get_short_name(self, obj):
        return obj.short_name.name if obj.short_name else None

    def get_commission_slab(self, obj):
        return obj.commission_slab.number

    def get_category(self, obj):
        return obj.category.name if obj.category else None

    def get_classification(self, obj):
        return obj.classification.name if obj.classification else None

    def get_discount_slab(self, obj):
        return obj.discount_slab.name if obj.discount_slab else None

    def get_payment_cycle(self, obj):
        return "{} {}".format(str(obj.payment_cycle.number), obj.payment_cycle.number) if obj.payment_cycle else None


class RetailerDashboardManagerShortSerializer(serializers.ModelSerializer):
    from saleschain.api.serializers import SalesPersonTinySerializer
    commission_slab = CommissionSlabSerializer()
    category = CustomerCategorySerializer()
    salesPersonProfile = SalesPersonTinySerializer()
    amount_due = serializers.SerializerMethodField()

    # discount_slab = DiscountSlabSerializer()
    # classification = ClassificationSerializer()
    # short_name = RetailerShortsSerializer()
    # payment_cycle = RetailerPaymentCycleSerializer()

    class Meta:
        model = Retailer
        fields = (
            'id', 'category', 'salesPersonProfile', 'beat_number',
            'code',
            'last_order_date', 'onboarding_date', 'onboarding_status',
            'commission_slab', 'phone_no', 'amount_due')
        # fields = ( 'id', 'name_of_shop', 'billing_name_of_shop', 'short_name', 'category', 'salesPersonProfile',
        # 'beat_number', 'beat_order_number', 'payment_cycle', 'code', 'onboarding_status', 'last_order_date',
        # 'onboarding_date', 'commission_slab', 'discount_slab', 'classification', 'phone_no', 'amount_due')

    def get_amount_due(self, obj):
        pending_invoices = Invoice.objects.filter(order__retailer=obj, invoice_status="Pending")
        amount_due = decimal.Decimal(0.000)
        for invoice in pending_invoices:
            amount_due += invoice.invoice_due
        return amount_due

    def get_SalesPersonProfile(self, obj):
        return obj.salesPersonProfile


class RetailerDashboardManagerSerializer(serializers.ModelSerializer):
    from saleschain.api.serializers import SalesPersonTinySerializer
    commission_slab = CommissionSlabSerializer()
    category = CustomerCategorySerializer()
    discount_slab = DiscountSlabSerializer()
    classification = ClassificationSerializer()
    salesPersonProfile = SalesPersonTinySerializer()
    short_name = RetailerShortsSerializer()
    payment_cycle = RetailerPaymentCycleSerializer()

    class Meta:
        model = Retailer

        fields = (
            'id', 'name_of_shop', 'billing_name_of_shop', 'short_name', 'category', 'salesPersonProfile', 'beat_number',
            'beat_order_number', 'payment_cycle', 'code',
            'onboarding_status', 'last_order_date', 'onboarding_date',
            'commission_slab', 'discount_slab', 'classification', 'phone_no', 'amount_due')

    def get_SalesPersonProfile(self, obj):
        return obj.salesPersonProfile


class RetailerDashboardShortSerializer(serializers.ModelSerializer):
    from saleschain.api.serializers import SalesPersonShortSerializer
    current_month_eggs_dict = serializers.SerializerMethodField()
    days_since_last_order = serializers.SerializerMethodField()
    last_order_date = serializers.SerializerMethodField()
    first_order_date = serializers.SerializerMethodField()
    commission_slab = CommissionSlabSerializer()
    category = CustomerCategorySerializer()
    discount_slab = DiscountSlabSerializer()
    classification = ClassificationSerializer()
    salesPersonProfile = SalesPersonShortSerializer()
    short_name = RetailerShortsSerializer()
    payment_cycle = RetailerPaymentCycleSerializer()

    class Meta:
        model = Retailer

        fields = (
            'id', 'name_of_shop', 'billing_name_of_shop', 'short_name', 'category', 'salesPersonProfile', 'beat_number',
            'beat_order_number', 'payment_cycle', 'code',
            'onboarding_status', 'current_month_eggs_dict', 'last_order_date', 'first_order_date',
            'days_since_last_order', 'onboarding_date',
            'commission_slab', 'discount_slab', 'classification', 'phone_no', 'amount_due')

    def get_SalesPersonProfile(self, obj):
        return obj.salesPersonProfile

    def get_current_month_eggs_dict(self, obj):
        current_month = datetime.now(tz=CURRENT_ZONE).month
        if (current_month == 1):
            previous_month = 12
            current_year = datetime.now(tz=CURRENT_ZONE).year - 1
        else:
            previous_month = datetime.now(tz=CURRENT_ZONE).month - 1
            current_year = datetime.now(tz=CURRENT_ZONE).year
        eggs_sold_month = RetailerEggsdata.objects.filter(retailer=obj, date__month=current_month,
                                                          date__year=current_year, )
        orders_list_dict = {'Brown': 0, 'White': 0, 'Nutra': 0, 'Total': 0}
        for eggs_sold_day in eggs_sold_month:
            orders_list_dict['Total'] = orders_list_dict[
                                            'Total'] + eggs_sold_day.brown + eggs_sold_day.white + eggs_sold_day.nutra
            orders_list_dict['Brown'] = orders_list_dict['Brown'] + eggs_sold_day.brown
            orders_list_dict['White'] = orders_list_dict['White'] + eggs_sold_day.white
            orders_list_dict['Nutra'] = orders_list_dict['Nutra'] + eggs_sold_day.nutra
        return orders_list_dict

    def get_days_since_last_order(self, obj):
        if Order.objects.filter(retailer=obj, status="delivered"):
            last_order = Order.objects.filter(retailer=obj, status="delivered").order_by('delivery_date').last()
            timediff = datetime.now(tz=CURRENT_ZONE) - last_order.delivery_date
            return (timediff.days)
        else:
            return "No Orders Yet"

    def get_last_order_date(self, obj):
        if Order.objects.filter(retailer=obj, status="delivered"):
            return Order.objects.filter(retailer=obj, status="delivered").order_by('delivery_date').last().delivery_date
        else:
            return "No Orders Yet"

    def get_first_order_date(self, obj):
        if Order.objects.filter(retailer=obj, status="delivered"):
            return Order.objects.filter(retailer=obj, status="delivered").order_by(
                'delivery_date').first().delivery_date
        else:
            return "No Orders Yet"


class RetailerDashboardSerializer(serializers.ModelSerializer):
    from saleschain.api.serializers import SalesPersonShortSerializer
    current_month_eggs_dict = serializers.SerializerMethodField()
    days_since_last_order = serializers.SerializerMethodField()
    last_order_date = serializers.SerializerMethodField()
    first_order_date = serializers.SerializerMethodField()
    commission_slab = CommissionSlabSerializer()
    category = CustomerCategorySerializer()
    discount_slab = DiscountSlabSerializer()
    classification = ClassificationSerializer()
    salesPersonProfile = SalesPersonShortSerializer()
    short_name = RetailerShortsSerializer()
    payment_cycle = RetailerPaymentCycleSerializer()
    amount_due = serializers.SerializerMethodField()

    class Meta:
        model = Retailer

        fields = (
            'id', 'name_of_shop', 'billing_name_of_shop', 'short_name', 'category', 'salesPersonProfile',
            'onboarding_status', 'days_since_last_order', 'current_month_eggs_dict', 'beat_number', 'beat_order_number',
            'payment_cycle', 'onboarding_date', 'code',
            'commission_slab', 'discount_slab', 'classification', 'phone_no', 'last_order_date', 'first_order_date',
            'amount_due')

    def get_SalesPersonProfile(self, obj):
        return obj.salesPersonProfile

    def get_amount_due(self, obj):
        pending_invoices = Invoice.objects.filter(order__retailer=obj, invoice_status="Pending")
        amount_due = decimal.Decimal(0.000)
        for invoice in pending_invoices:
            amount_due += invoice.invoice_due
        return amount_due

    def get_current_month_eggs_dict(self, obj):
        current_month = datetime.now(tz=CURRENT_ZONE).month
        if (current_month == 1):
            previous_month = 12
            current_year = datetime.now(tz=CURRENT_ZONE).year - 1
        else:
            previous_month = datetime.now(tz=CURRENT_ZONE).month - 1
            current_year = datetime.now(tz=CURRENT_ZONE).year
        eggs_sold_month = RetailerEggsdata.objects.filter(retailer=obj, date__month=current_month,
                                                          date__year=current_year, )
        orders_list_dict = {'Brown': 0, 'White': 0, 'Nutra': 0, 'Total': 0}
        for eggs_sold_day in eggs_sold_month:
            orders_list_dict['Total'] = orders_list_dict[
                                            'Total'] + eggs_sold_day.brown + eggs_sold_day.white + eggs_sold_day.nutra
            orders_list_dict['Brown'] = orders_list_dict['Brown'] + eggs_sold_day.brown
            orders_list_dict['White'] = orders_list_dict['White'] + eggs_sold_day.white
            orders_list_dict['Nutra'] = orders_list_dict['Nutra'] + eggs_sold_day.nutra
        return orders_list_dict

    # def get_days_since_last_order(self, obj):
    #     if Order.objects.days_since_last_order(retailer=obj):
    #         return Order.objects.days_since_last_order(retailer=obj)
    #     else:
    #         return "No Orders Yet"
    #
    # def get_last_order_date(self, obj):
    #     if Order.objects.last_order_date(retailer=obj):
    #         return Order.objects.last_order_date(retailer=obj)
    #     else:
    #         return "No Orders Yet"

    def get_days_since_last_order(self, obj):
        if Order.objects.filter(retailer=obj, status="delivered"):
            last_order = Order.objects.filter(retailer=obj, status="delivered").order_by('delivery_date').last()
            print(last_order.delivery_date)
            print(datetime.now(tz=CURRENT_ZONE))
            timediff = datetime.now(tz=CURRENT_ZONE) - last_order.delivery_date
            return (timediff.days)
        else:
            return "No Orders Yet"

    def get_last_order_date(self, obj):
        if Order.objects.filter(retailer=obj, status="delivered"):
            return Order.objects.filter(retailer=obj, status="delivered").order_by('delivery_date').last().delivery_date
        else:
            return "No Orders Yet"

    def get_first_order_date(self, obj):
        if Order.objects.filter(retailer=obj, status="delivered"):
            return Order.objects.filter(retailer=obj, status="delivered").order_by(
                'delivery_date').first().delivery_date
        else:
            return "No Orders Yet"


class RetailOwnerCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RetailOwner
        fields = (
            'owner_name', 'phone_no', 'owner_photo_url', 'email', 'aadhar_no', 'pancard_no', 'pancard_photo_url',
            'aadhar_photo_url')


class RetailerOnboardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Retailer
        fields = (
            'name_of_shop', 'billing_name_of_shop', 'shop_photo_url', 'billing_shipping_address_same', 'short_name',
            'category', 'sub_category', 'beat_number', 'classification', 'payment_cycle',
            'city', 'cluster', 'sector', 'annual_income', 'GSTIN', 'gst_photo_url', 'phone_no')


class RetailerUpdateSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(required=True, queryset=Retailer.objects.all())
    email = serializers.EmailField(required=False)
    beat_number = serializers.IntegerField(required=False)
    shipping_address = serializers.CharField(required=False)
    billing_address = serializers.CharField(required=False)
    category = serializers.PrimaryKeyRelatedField(required=False, queryset=Customer_Category.objects.all())
    sub_category = serializers.PrimaryKeyRelatedField(required=False, queryset=Customer_SubCategory.objects.all())
    city = serializers.PrimaryKeyRelatedField(required=False, queryset=City.objects.all())
    cluster = serializers.PrimaryKeyRelatedField(required=False, queryset=Cluster.objects.all())
    phone_no = PhoneNumberField(required=False)
    commission_slab = serializers.PrimaryKeyRelatedField(required=False, queryset=CommissionSlab.objects.all())
    discount_slab = serializers.PrimaryKeyRelatedField(required=False, queryset=DiscountSlab.objects.all())
    classification = serializers.PrimaryKeyRelatedField(required=False, queryset=Classification.objects.all())
    short_name = serializers.PrimaryKeyRelatedField(required=False, queryset=RetailerShorts.objects.all())
    payment_cycle = serializers.PrimaryKeyRelatedField(required=False, queryset=RetailerPaymentCycle.objects.all())

    class Meta:
        model = Retailer
        fields = ('id', 'email', 'shop_photo_url', 'short_name', 'beat_number', 'GSTIN', 'gst_photo_url',
                  'onboarding_status', 'phone_no', 'category', 'sub_category', 'city', 'cluster', 'sector',
                  'shipping_address', 'billing_address', 'billing_shipping_address_same', 'commission_slab',
                  'discount_slab', 'classification', 'retail_owners', 'payment_cycle')

    def validate(self, data):
        print(data)
        retailer_obj = data.get('id')
        email = data.get('email', None)
        if email:
            if email == retailer_obj.retailer.email:
                pass
            else:
                if User.objects.filter(email=email).first():
                    raise serializers.ValidationError("Email already exist")
        phone_no = data.get('phone_no', None)
        if phone_no:
            if phone_no == retailer_obj.retailer.phone_no:
                pass
            else:
                if User.objects.filter(phone_no=phone_no).first():
                    raise serializers.ValidationError("Phone No. already exist")
        shipping_address = data.get('shipping_address', None)
        if shipping_address:
            shipping_address = json.loads(shipping_address)
            shipping_address_id = shipping_address.get('shipping_address_id', None)
            if retailer_obj.shipping_address:
                if shipping_address_id is None:
                    raise serializers.ValidationError("shipping_address_id required")
                if not retailer_obj.shipping_address.id == shipping_address_id:
                    raise serializers.ValidationError("shipping_address_id invalid")
            shipping_address_update_serializer = AddressUpdateSerializer(data=shipping_address)
            shipping_address_update_serializer.is_valid(raise_exception=True)

        billing_address = data.get('billing_address', None)
        if billing_address:
            billing_address = json.loads(billing_address)
            billing_address_update_serializer = AddressUpdateSerializer(data=billing_address)
            billing_address_update_serializer.is_valid(raise_exception=True)

        retail_owners = data.get('retail_owners', [])
        if retail_owners:
            retail_owners = json.loads(retail_owners)
            if len(retail_owners) > 0:
                for retail_owner in retail_owners:
                    retail_owner_id = retail_owner.get('id', None)
                    if retail_owner_id:
                        if RetailOwner.objects.filter(id=retail_owner_id).first():
                            type = retail_owner.get('type', None)
                            if type and type in ['edit', 'delete']:
                                retail_owner_serializer = RetailOwnerCreateSerializer(data=retail_owner)
                                retail_owner_serializer.is_valid(raise_exception=True)
                            else:
                                raise serializers.ValidationError("type is required or invalid")
                        else:
                            raise serializers.ValidationError("invalid retail owner id")
                    else:
                        retail_owner_serializer = RetailOwnerCreateSerializer(data=retail_owner)
                        retail_owner_serializer.is_valid(raise_exception=True)
            else:
                raise serializers.ValidationError("At least one Retail owner required")
        return data

    def retailer_update(self, instance, data):
        email = data.get('email', None)
        if email:
            instance.retailer.email = email
        phone_no = data.get('phone_no', None)
        if phone_no:
            instance.retailer.phone_no = phone_no
            instance.phone_no = phone_no
        shop_photo_url = data.get('shop_photo_url', None)
        if shop_photo_url:
            instance.shop_photo_url = shop_photo_url

        name_of_shop = data.get('name_of_shop', None)
        if name_of_shop:
            instance.name_of_shop = name_of_shop

        short_name = data.get('short_name', None)
        if short_name:
            instance.short_name_id = short_name

        payment_cycle = data.get('payment_cycle', None)
        if short_name:
            instance.payment_cycle_id = payment_cycle

        beat_number = data.get('beat_number', None)
        if beat_number:
            instance.beat_number = beat_number

        GSTIN = data.get('GSTIN', None)
        if GSTIN:
            instance.GSTIN = GSTIN

        gst_photo_url = data.get('gst_photo_url', None)
        if gst_photo_url:
            instance.gst_photo_url = gst_photo_url

        onboarding_status = data.get('onboarding_status', None)
        if onboarding_status:
            instance.onboarding_status = onboarding_status

        category = data.get('category', None)
        if category:
            instance.category_id = category

        sub_category = data.get('sub_category', None)
        if sub_category:
            instance.sub_category_id = sub_category

        classification = data.get('classification', None)
        if classification:
            instance.classification_id = classification

        discount_slab = data.get('discount_slab', None)
        if discount_slab:
            instance.discount_slab_id = discount_slab

        city = data.get('city', None)
        if city:
            instance.city_id = city

        cluster = data.get('cluster', None)
        if cluster:
            instance.cluster_id = cluster

        sector = data.get('sector', None)
        if sector:
            instance.sector_id = sector

        beat_number = data.get('beat_number', 0)
        print(str(beat_number))
        if beat_number:
            instance.beat_number = int(beat_number)

        commission_slab_number = data.get('commission_slab_number', None)
        print(commission_slab_number)
        if commission_slab_number:
            if CommissionSlab.objects.get(id=int(commission_slab_number)):
                cs = CommissionSlab.objects.get(id=int(commission_slab_number))
                print(cs)
                instance.commission_slab = cs

        shipping_address_instance = instance.shipping_address
        shipping_address = data.get('shipping_address', None)
        if shipping_address:
            shipping_address = json.loads(shipping_address)
            shipping_address_obj = Address.objects.filter(id=shipping_address.get('shipping_address_id')).first()
            shipping_address_update_serializer = AddressUpdateSerializer(data=shipping_address)
            shipping_address_update_serializer.is_valid(raise_exception=True)
            shipping_address_instance = shipping_address_update_serializer.update(shipping_address_obj,
                                                                                  shipping_address_update_serializer.validated_data)

        billing_shipping_address_same = data.get('billing_shipping_address_same', None)
        if billing_shipping_address_same:
            instance.billing_address = shipping_address_instance
        else:
            billing_address = data.get('billing_address', None)
            if billing_address:
                billing_address = json.loads(billing_address)
                billing_address_update_serializer = AddressCreationSerializer(data=billing_address)
                billing_address_update_serializer.is_valid(raise_exception=True)
                instance.billing_address = billing_address_update_serializer.save()

        retail_owners = data.get('retail_owners', [])
        if retail_owners:
            retail_owners = json.loads(retail_owners)
            for retail_owner in retail_owners:
                retail_owner_id = retail_owner.get('id', None)
                if retail_owner_id:
                    retail_owner_obj = RetailOwner.objects.filter(id=retail_owner_id).first()
                    if retail_owner.get('type') == "delete":
                        retail_owner_obj.delete()
                    else:
                        retail_owner_serializer = RetailOwnerCreateSerializer(data=retail_owner)
                        retail_owner_serializer.is_valid(raise_exception=True)
                        retail_owner_serializer.update(retail_owner_obj, retail_owner_serializer.validated_data)
                else:
                    retail_owner_serializer = RetailOwnerCreateSerializer(data=retail_owner)
                    retail_owner_serializer.is_valid(raise_exception=True)
                    retail_owner_serializer.save(retail_shop=instance)

        instance.retailer.save()
        instance.save()
        return instance
