import json
from datetime import datetime

from django.db.models import Max
from rest_framework import serializers, status
from rest_framework.response import Response

from Eggoz import settings
from Eggoz.settings import CURRENT_ZONE
from base.response import Forbidden, BadRequest
from custom_auth.models import UserProfile
from ecommerce.models import WalletRecharge, RechargeVoucher, CustomerWallet, CashFreeTransaction
from order.api.serializers import OrderCreateSerializer, OrderLineSerializer, OrderHistorySerializer, \
    OrderShortSerializer
from order.models import Order
from payment.models import SalesTransaction, Payment, Invoice
from saleschain.models import SalesPersonProfile


class InvoiceSerializer(serializers.ModelSerializer):
    order = OrderHistorySerializer()
    class Meta:
        model = Invoice
        fields = '__all__'


class InvoiceShortSerializer(serializers.ModelSerializer):
    order = OrderShortSerializer()
    class Meta:
        model = Invoice
        fields = '__all__'

class PendingInvoiceForPrintSerializer(serializers.ModelSerializer):
    bill_no=serializers.SerializerMethodField()
    class Meta:
        model = Invoice
        fields = ('id','invoice_due','created_at','bill_no','invoice_id')
    def get_bill_no(self,obj):
        return obj.order.name if obj.order else None

class PaymentValidationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ('payment_type', 'cheque_number', 'upi_id', 'pay_amount')


class PaymentSerializer(serializers.ModelSerializer):
    # invoice = InvoiceSerializer()
    invoice = InvoiceShortSerializer()
    class Meta:
        model = Payment
        fields = '__all__'


class PaymentHistorySerializer(serializers.ModelSerializer):
    invoice = InvoiceShortSerializer()

    class Meta:
        model = Payment
        fields = '__all__'




class SalesTransactionCreateSerializer(serializers.ModelSerializer):
    transaction_amount = serializers.DecimalField(max_digits=settings.DEFAULT_MAX_DIGITS,
                                                  decimal_places=settings.DEFAULT_DECIMAL_PLACES, required=True)

    class Meta:
        model = SalesTransaction
        fields = ('id', 'retailer', 'transaction_id', 'salesPerson', 'transaction_amount', 'remarks', 'invoices','beat_assignment',
                  'transaction_type', 'transaction_date', 'distributor')


class SalesTransactionSerializer(serializers.ModelSerializer):
    transaction_amount = serializers.DecimalField(max_digits=settings.DEFAULT_MAX_DIGITS,
                                                  decimal_places=settings.DEFAULT_DECIMAL_PLACES, required=True)
    retailerName = serializers.SerializerMethodField()
    salesPersonName = serializers.SerializerMethodField()

    class Meta:
        model = SalesTransaction
        fields = ('id', 'retailer', 'retailerName', 'salesPersonName', 'transaction_id', 'salesPerson', 'distributor',
                  'transaction_amount', 'remarks', 'invoices', 'financePerson',
                  'transaction_type', 'transaction_date')

    def get_retailerName(self, obj):
        if obj.retailer:
            return obj.retailer.code
        elif obj.customer:
            return obj.customer.user.name
        else:
            return "No user"

    def get_salesPersonName(self, obj):
        if obj.financePerson:
            return obj.financePerson.user.name
        if obj.salesPerson:
            return obj.salesPerson.user.name
        elif obj.distributor:
            return obj.distributor.user.name
        else:
            return "No Del or Sales Guy"

    def create(self, request, *args, **kwargs):
        data = request.data
        print(data)
        user_profile = UserProfile.objects.filter(user=request.user, department__name__in=['Sales']).first()
        if user_profile:
            order_create_serializer = OrderCreateSerializer(data=data)
            order_create_serializer.is_valid(raise_exception=True)
            delivery_date = datetime.strptime(data.get('delivery_date'), "%d-%m-%Y")
            order_type = "Retailer"
            if data.get('order_type'):
                order_type= data.get('order_type')
            cart_products = data.get('cart_products', [])
            if cart_products:
                cart_products = json.loads(cart_products)
                for cart_product in cart_products:
                    order_line_serializer = OrderLineSerializer(data=cart_product)
                    order_line_serializer.is_valid(raise_exception=True)
                salesPersonProfile = SalesPersonProfile.objects.filter(user=request.user).first()
                orders = Order.objects.all()
                # might be possible model has no records so make sure to handle None
                order_max_id = orders.aggregate(Max('id'))['id__max'] + 1 if orders else 1
                order_id = "OD-GGN-" + str(order_max_id)
                order_obj = order_create_serializer.save(orderId=order_id, order_type=order_type, salesPerson=salesPersonProfile,
                                                         delivery_date=delivery_date)

                for cart_product in cart_products:
                    order_line_serializer = OrderLineSerializer(data=cart_product)
                    order_line_serializer.is_valid(raise_exception=True)
                    order_line_serializer.save(order=order_obj)
                if order_obj.order_type == "Retailer":
                    # TODO Update Amount Due of Retailer while creating new order
                    # order_obj.retailer.amount_due = decimal.Decimal(order_obj.retailer.amount_due) + decimal.Decimal(
                    #     order_obj.order_price_amount)
                    # order_obj.retailer.save()

                    # Update Last Order Date of a Retailer
                    order_obj.retailer.last_order_date = datetime.now(tz=CURRENT_ZONE)
                    order_obj.retailer.save()
                else:
                    pass

                return Response({}, status=status.HTTP_201_CREATED)
            else:
                return BadRequest({'error_type': "Validation Error",
                                   'errors': [{'message': "Cart can not be empty"}]})

        else:
            return Forbidden({'error_type': "permission_denied",
                              'errors': [{'message': "You do not have permission to perform this action."}]})


class SalesTransactionShortSerializer(serializers.ModelSerializer):
    retailerName = serializers.SerializerMethodField()
    retailerGSTIN = serializers.SerializerMethodField()
    salesPersonName = serializers.SerializerMethodField()
    paymentType = serializers.SerializerMethodField()
    payments = serializers.SerializerMethodField()
    bill_no = serializers.SerializerMethodField()

    class Meta:
        model = SalesTransaction
        fields = ('id', 'retailer', 'retailerName', 'salesPersonName', 'transaction_id', 'salesPerson', 'distributor',
                  'transaction_amount', 'remarks', 'invoices', 'paymentType', 'financePerson', 'bill_no', 'payments',
                  'transaction_type', 'transaction_date', 'retailerGSTIN')

    def get_retailerName(self, obj):
        if obj.retailer:
            return obj.retailer.billing_name_of_shop if not obj.retailer.billing_name_of_shop == "Exact Name Of Shop" else obj.retailer.name_of_shop
        elif obj.customer:
            return obj.customer.user.name
        else:
            return "No User"

    def get_retailerGSTIN(self,obj):
        if obj.retailer and not obj.retailer.GSTIN == "GSTIN":
            return obj.retailer.GSTIN
        else:
            return ""

    def get_bill_no(self, obj):
        if obj.invoices.all():
            return ",".join(invoice.order.name for invoice in obj.invoices.all())
        else:
            return "No invoice"

    def get_paymentType(self,obj):
        if obj.paymentTransactions.all():
            payments = obj.paymentTransactions.all()[::1]
            # print(payments[0].payment_mode)
            mode = payments[0].payment_mode
            payment_mode = "&".join([payment.payment_mode for payment in payments])
            reference_ids = []
            for payment in payments:
                if payment.payment_mode == "PETTY CASH":
                    reference_ids.append("CASH")
                elif payment.payment_mode == "CHEQUE":
                    reference_ids.append(payment.cheque_number)
                else:
                    reference_ids.append(payment.upi_id)
            #reference_id = "&".join([id for id in reference_ids])
            reference_id = payments[0].cheque_number  if payments[0].payment_mode == "CHEQUE"\
                else payments[0].upi_id  if payments[0].payment_mode == "UPI" else "CASH"
            return {"mode":mode, "reference_id":reference_id, "payment_mode":payment_mode}
        else:
            return "Error"

    def get_payments(self,obj):
        if obj.paymentTransactions.all():
            payments = obj.paymentTransactions.all()
            return PaymentSerializer(payments, many=True).data
        else:
            return None


    def get_salesPersonName(self, obj):
        if obj.financePerson:
            return obj.financePerson.user.name
        elif obj.salesPerson:
            return obj.salesPerson.user.name
        elif obj.distributor:
            return obj.distributor.user.name
        else:
            return "No Del or Sales Guy"



class WalletRechargeValidationSerializer(serializers.Serializer):
    voucher = serializers.PrimaryKeyRelatedField(required=False, queryset=RechargeVoucher.objects.all())
    wallet = serializers.PrimaryKeyRelatedField(required=True, queryset=CustomerWallet.objects.all())
    amount = serializers.DecimalField(required=True, max_digits=12, decimal_places=3)
    name = serializers.CharField(required=False, max_length=200)
    email = serializers.CharField(required=False, max_length=200)


class MemberShipRechargeValidationSerializer(serializers.Serializer):
    amount = serializers.DecimalField(required=True, max_digits=12, decimal_places=3)
    wallet = serializers.PrimaryKeyRelatedField(required=True, queryset=CustomerWallet.objects.all())
    name = serializers.CharField(required=False, max_length=200)
    email = serializers.CharField(required=False, max_length=200)
    recharge_type = serializers.CharField(required=False, max_length=200)
    start_date = serializers.CharField(required=True, max_length=200)
    expiry_date = serializers.CharField(required=True, max_length=200)


class SubscriptionRechargeValidationSerializer(serializers.Serializer):
    amount = serializers.DecimalField(required=True, max_digits=12, decimal_places=3)
    wallet = serializers.PrimaryKeyRelatedField(required=True, queryset=CustomerWallet.objects.all())
    name = serializers.CharField(required=False, max_length=200)
    email = serializers.CharField(required=False, max_length=200)
    recharge_type = serializers.CharField(required=False, max_length=200)
    start_date = serializers.CharField(required=True, max_length=200)
    expiry_date = serializers.CharField(required=True, max_length=200)


class WalletRechargeSerializer(serializers.ModelSerializer):
    voucher = serializers.PrimaryKeyRelatedField(required=False, queryset=RechargeVoucher.objects.all())
    wallet = serializers.PrimaryKeyRelatedField(required=True, queryset=CustomerWallet.objects.all())
    amount = serializers.DecimalField(required=False, max_digits=12, decimal_places=3)
    transaction = serializers.PrimaryKeyRelatedField(required=False, queryset=CashFreeTransaction.objects.all())
    note = serializers.CharField(required=False, max_length=200)

    class Meta:
        model = WalletRecharge
        fields = '__all__'



class WalletRechargeHistorySerializer(serializers.ModelSerializer):

    class Meta:
        model = WalletRecharge
        fields = '__all__'
