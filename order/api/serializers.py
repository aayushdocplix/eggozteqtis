import decimal
import json
from datetime import datetime, timedelta

import pytz
from django.db.models import Max
from django.utils import timezone
from rest_framework import serializers

from Eggoz.settings import CURRENT_ZONE
from custom_auth.api.serializers import AddressSerializer
from distributionchain.models import DistributionPersonProfile, BeatAssignment
from ecommerce.models import Customer
from finance.models import FinanceProfile
from order.models import Order, OrderLine
from order.models.Order import PackingOrder, OrderReturnLine, PurchaseOrder, EcommerceOrder, ReturnOrderTransaction, \
    DebitNoteTransaction
from payment.models import SalesTransaction, Invoice, InvoiceLine, Payment
from product.api.serializers import ProductInlineSerializer
from product.models import ProductInline, BaseProduct
from saleschain.models import SalesPersonProfile, SalesDemandSKU, RetailerDemand
from warehouse.models import Inventory


class OrderCreateSerializer(serializers.ModelSerializer):
    retailer_note = serializers.CharField(required=False)

    class Meta:
        model = Order
        fields = ('name', 'retailer', 'shipping_address', 'order_type', 'warehouse', 'retailer_note', 'discount_name',
                  'discount_amount', 'status','beat_assignment', 'order_brand_type',
                  'order_price_amount')


class PurchaseOrderCreateSerializer(OrderCreateSerializer):

    class Meta:
        model = PurchaseOrder
        fields = ('retailer', 'order_price_amount')


class EcommerceOrderCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EcommerceOrder
        fields = ('shipping_address', 'retailer_note', 'order_price_amount', 'pay_by_wallet', 'desc', 'is_promo',
                  'discount_amount','promo_amount')


class EcommerceSubscriptionOrderCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EcommerceOrder
        fields = ('shipping_address', 'retailer_note','order_price_amount', 'pay_by_wallet', 'desc', 'is_promo',
                  'discount_amount','promo_amount')


class EcommerceOrderHistorySerializer(serializers.ModelSerializer):
    order_lines = serializers.SerializerMethodField()
    retailerName = serializers.SerializerMethodField()
    retailerSlab = serializers.SerializerMethodField()
    code = serializers.SerializerMethodField()
    customerName = serializers.SerializerMethodField()
    customerPhone = serializers.SerializerMethodField()
    customerAddress = serializers.SerializerMethodField()
    salesPersonName = serializers.SerializerMethodField()
    distributorName = serializers.SerializerMethodField()
    return_order_lines = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()

    class Meta:
        model = EcommerceOrder
        fields = (
            'id', 'name', 'orderId', 'order_type', 'retailer', 'customer', 'retailerName', 'code', 'salesPerson', 'desc',
            'salesPersonName', 'date', 'distributor', 'distributorName', 'retailerSlab', 'returned_bill', 'financePerson',
            'delivery_date', 'warehouse', 'generation_date', 'retailer_note', 'discount_name', 'discount_amount',
            'customerName','customerPhone','customerAddress', 'deviated_amount', 'secondary_status', 'is_promo',
            'promo_amount','order_price_amount', 'order_lines', 'status', 'return_order_lines')
        read_only_fields = ('orderId',)

    def get_retailerName(self, obj):
        if obj.retailer:
            return obj.retailer.name_of_shop
        else:
            return "No Name"

    def get_retailerSlab(self, obj):
        if obj.retailer:
            return int(obj.retailer.commission_slab.number)
        else:
            return 0

    def get_code(self, obj):
        if obj.retailer:
            return obj.retailer.code
        elif obj.customer:
            return obj.customer.code
        else:
            return "No Code"

    def get_salesPersonName(self, obj):
        if obj.salesPerson:
            return obj.salesPerson.user.name
        else:
            return "No SalesPerson"

    def get_distributorName(self, obj):
        if obj.distributor:
            return obj.distributor.user.name
        else:
            return "No Delivery Guy"

    def get_customerName(self, obj):
        if obj.customer:
            return obj.customer.user.name
        else:
            return "No Customer"

    def get_customerPhone(self, obj):
        if obj.customer:
            return str(obj.customer.phone_no)
        else:
            return None

    def get_customerAddress(self, obj):
        if obj.customer:
            shipping_address = obj.customer.shipping_address
            if shipping_address:
                return AddressSerializer(shipping_address).data
            else:
                return None
        else:
            return None

    def get_date(self, obj):
        order_date = obj.date
        return order_date

    def get_order_lines(self, obj):
        order_lines_dict = {}
        total_quantity = 0
        order_lines = obj.lines.all()
        order_lines_dict['total_items'] = len(order_lines)
        order_lines_dict['order_items'] = []

        # For Product(White Eggs,Brown Eggs in order history)
        cart_product_dict = {'name': []}
        for order_line in order_lines:
            order_item = {}
            if order_line.product:
                product_name = order_line.product.name + " " + order_line.product.productDivision.name
                if not product_name in cart_product_dict['name']:
                    cart_product_dict.get('name').append(product_name)
                order_item['name'] = product_name
                order_item['sku'] = order_line.product.SKU_Count
                order_item['price'] = order_line.product.current_price
                order_item['quantity'] = order_line.quantity
                order_item['order_line_id'] = order_line.id
                order_item['product_id'] = order_line.product.id
                order_item['single_sku_rate'] = order_line.single_sku_rate
                order_item['single_sku_mrp'] = order_line.single_sku_mrp
                order_return_lines = OrderReturnLine.objects.filter(orderLine=order_line)
                refund_quantity = 0
                replace_quantity = 0
                promo_quantity = 0
                for order_return_line in order_return_lines:
                    if order_return_line.line_type == 'Refund' or order_return_line.line_type == 'Return':
                        refund_quantity = refund_quantity + order_return_line.quantity
                    elif order_return_line.line_type == 'Replacement':
                        replace_quantity = replace_quantity + order_return_line.quantity
                    elif order_return_line.line_type == 'Promo':
                        promo_quantity = promo_quantity + order_return_line.quantity
                order_item['refund_quantity'] = refund_quantity
                order_item['replace_quantity'] = replace_quantity
                order_item['promo_quantity'] = promo_quantity
                productInLines = ProductInline.objects.filter(product=order_line.product)
                order_item['product_inlines'] = ProductInlineSerializer(productInLines, many=True).data
                order_lines_dict.get('order_items').append(order_item)
                total_quantity = total_quantity + order_line.quantity * order_line.product.SKU_Count
        order_lines_dict['products'] = ','.join(cart_product_dict.get('name'))
        order_lines_dict['total_quantity'] = total_quantity
        return order_lines_dict

    def get_return_order_lines(self, obj):
        return_lines_list = []
        return_status_list = ['refund','return',  'replace', 'partial_return','partial_refund', 'partial_replace', "partial_return_replace", 'partial_refund_replace']
        if obj.status in return_status_list:
            order_lines = obj.lines.all()
            order_return_lines = OrderReturnLine.objects.filter(orderLine__in=order_lines)
            if order_return_lines:
                for order_return_line in order_return_lines:
                    return_line_dict = {}
                    return_line_dict['id'] = order_return_line.id
                    return_line_dict['line_type'] = order_return_line.line_type
                    return_line_dict['quantity'] = order_return_line.quantity
                    return_line_dict['order_quantity'] = order_return_line.orderLine.quantity
                    return_line_dict['product'] = order_return_line.orderLine.product.name[0] + "-(SKU %s)" % (
                        str(order_return_line.orderLine.product.SKU_Count))
                    return_lines_list.append(return_line_dict)
        return return_lines_list


class OrderLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderLine
        fields = ('product', 'quantity', 'delivered_quantity', 'egg_type', 'deviated_quantity', 'promo_quantity', 'single_sku_rate', 'single_sku_mrp')


class PackingSerializer(serializers.ModelSerializer):
    order = serializers.SerializerMethodField()

    def get_order(self, obj):
        orderInlines = obj.order_set.all()
        return OrderHistorySerializer(orderInlines, many=True).data

    class Meta:
        model = PackingOrder
        fields = '__all__'


class OrderShortSerializer(serializers.ModelSerializer):
    code = serializers.SerializerMethodField()
    salesPersonName = serializers.SerializerMethodField()
    distributorName = serializers.SerializerMethodField()
    financeName = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = (
            'id', 'name', 'orderId', 'retailer', 'customer', 'code', 'salesPerson',
            'salesPersonName', 'date', 'distributor', 'distributorName','financePerson', 'financeName',
            'delivery_date','order_price_amount',  'status')
        read_only_fields = ('orderId',)


    def get_code(self, obj):
        if obj.retailer:
            return obj.retailer.code
        elif obj.customer:
            return obj.customer.user.name
        else:
            return "No Code"

    def get_salesPersonName(self, obj):
        if obj.salesPerson:
            return obj.salesPerson.user.name
        else:
            return "No SalesPerson"

    def get_financeName(self, obj):
        if obj.financePerson:
            return obj.financePerson.user.name
        else:
            return "No Name"

    def get_distributorName(self, obj):
        if obj.distributor:
            return obj.distributor.user.name
        else:
            return "No Delivery Guy"

    def get_date(self, obj):
        order_date = obj.delivery_date
        return order_date


class OrderExportSerializer(serializers.ModelSerializer):
    city_id = serializers.SerializerMethodField()
    city_name = serializers.SerializerMethodField()

    beat = serializers.SerializerMethodField()
    operator = serializers.SerializerMethodField()
    partyName = serializers.SerializerMethodField()
    salesPerson = serializers.SerializerMethodField()
    bill_no = serializers.SerializerMethodField()
    bill_id = serializers.SerializerMethodField()
    manual_bill_no = serializers.SerializerMethodField()
    amount = serializers.SerializerMethodField()
    beat_assignment = serializers.SerializerMethodField()
    payments = serializers.SerializerMethodField()
    order_line_dict = serializers.SerializerMethodField()

    IST = pytz.timezone('Asia/Kolkata')

    class Meta:
        model = Order
        fields = ('city_id', 'city_name', 'payments', 'beat', 'operator', 'delivery_date', 'date', 'partyName',
                  'salesPerson', 'bill_no', 'bill_id', 'manual_bill_no', 'amount',
                  'status', 'deviated_amount', 'secondary_status', 'order_brand_type', 'beat_assignment',
                  'order_line_dict', 'is_geb', 'is_geb_verified','order_price_amount')
        read_only_fields = ('orderId',)

    def get_city_id(self,obj):
        return obj.retailer.city.id if obj.retailer else \
                        obj.customer.shipping_address.city.id if obj.customer.shipping_address.city else ""

    def get_city_name(self,obj):
        return obj.retailer.city.city_name if obj.retailer else \
            obj.customer.shipping_address.city.city_name if obj.customer.shipping_address.city else ""

    def get_amount(self, obj):
        return int(obj.order_price_amount)

    def get_payments(self,obj):
        instant_amount = 0
        instant_mode = []
        later_amount = 0
        later_mode = []
        later_mode_date = []
        if obj.invoice:
            due = obj.invoice.invoice_due
            paidStatus = obj.invoice.invoice_status
            payments = Payment.objects.filter(invoice=obj.invoice, salesTransaction__is_trial=False)
            if payments:
                for payment in payments:
                    if payment.pay_choice == "InstantPay":
                        instant_amount += payment.pay_amount
                        instant_mode.append(payment.payment_mode)
                    else:
                        later_amount += payment.pay_amount
                        later_mode.append(payment.payment_mode)
                        later_date = payment.created_at + timedelta(hours=5, minutes=30, seconds=0)
                        later_mode_date.append(later_date.replace(tzinfo=self.IST).strftime('%d/%m/%Y %H:%M:%S'))

            instant_mode = "&".join(mode for mode in instant_mode) if instant_mode != [] else ""
            later_mode = "&".join(mode for mode in later_mode) if later_mode != [] else ""
            later_mode_date = "&".join(date_str for date_str in later_mode_date) if later_mode_date != [] else ""
            print("mode"+later_mode)
            print("mode date"+later_mode_date)
            return {"instant_amount": instant_amount, "instant_mode": instant_mode, "later_amount": later_amount,
                    "later_mode": later_mode, "later_mode_date": later_mode_date, "due": due,
                    "paidStatus": paidStatus}

    def get_beat(self,obj):
        return obj.retailer.beat_number if obj.retailer else 0
    
    def get_operator(self,obj):
        return obj.distributor.user.name if obj.distributor else obj.salesPerson.user.name if obj.salesPerson else ""

    def get_date(self,obj):
        order_date = obj.date + timedelta(hours=5, minutes=30, seconds=0)
        return order_date.replace(tzinfo=self.IST).strftime(
            '%d/%m/%Y %H:%M:%S') if obj.date else ""

    def get_delivery_date(self,obj):
        order_delivery_date = obj.delivery_date + timedelta(hours=5, minutes=30, seconds=0)
        return order_delivery_date.replace(tzinfo=self.IST).strftime(
            '%d/%m/%Y %H:%M:%S') if obj.delivery_date else ""
        
    def get_partyName(self,obj):
        return str(obj.retailer.code) if obj.retailer else obj.customer.user.name if obj.customer else ""
    
    def get_salesPerson(self,obj ):
        return obj.salesPerson.user.name if obj.salesPerson else ""
    
    def get_bill_no(self,obj):
        return obj.name

    def get_bill_id(self,obj):
        return obj.orderId
    
    def get_manual_bill_no(self,obj):
        return obj.bill_no if obj.bill_no else ""

    def get_beat_assignment(self,obj):
        return obj.beat_assignment.beat_number if obj.beat_assignment else ""

    def get_order_line_dict(self, order_obj):
        # Mapped Dict
        mapped_dict = {}
        mapped_dict['6W'] = ""
        mapped_dict['10W'] = ""
        mapped_dict['12W'] = ""
        mapped_dict['25W'] = ""
        mapped_dict['30W'] = ""

        mapped_dict['6B'] = ""
        mapped_dict['10B'] = ""
        mapped_dict['25B'] = ""
        mapped_dict['30B'] = ""

        mapped_dict['6N'] = ""
        mapped_dict['10N'] = ""

        mapped_rate_dict = {}
        mapped_rate_dict['6W R'] = ""
        mapped_rate_dict['10W R'] = ""
        mapped_rate_dict['12W R'] = ""
        mapped_rate_dict['25W R'] = ""
        mapped_rate_dict['30W R'] = ""

        mapped_rate_dict['6B R'] = ""
        mapped_rate_dict['10B R'] = ""
        mapped_rate_dict['25B R'] = ""
        mapped_rate_dict['30B R'] = ""

        mapped_rate_dict['6N R'] = ""
        mapped_rate_dict['10N R'] = ""

        order_lines = order_obj.lines.all()
        if order_lines:
            for order_line in order_lines:
                # print(str(order_line.product.SKU_Count) + order_line.product.name[:1])
                if str(order_line.product.name) == "White regular":
                    name = "White"
                else:
                    name = str(order_line.product.name)

                if str(order_line.product.SKU_Count) + name[:1] in mapped_dict.keys():
                    mapped_dict[str(order_line.product.SKU_Count) + name[:1]] = order_line.quantity
                    mapped_rate_dict[str(order_line.product.SKU_Count) + name[
                                                                         :1] + " R"] = order_line.single_sku_rate

        return {"Qty": mapped_dict, "Rate": mapped_rate_dict}


class OrderHistorySerializer(serializers.ModelSerializer):
    order_lines = serializers.SerializerMethodField()
    retailerName = serializers.SerializerMethodField()
    retailerGSTIN = serializers.SerializerMethodField()
    retailerSlab = serializers.SerializerMethodField()
    code = serializers.SerializerMethodField()
    customerName = serializers.SerializerMethodField()
    customerPhone = serializers.SerializerMethodField()
    customerAddress = serializers.SerializerMethodField()
    salesPersonName = serializers.SerializerMethodField()
    distributorName = serializers.SerializerMethodField()
    financeName = serializers.SerializerMethodField()
    return_order_lines = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = (
            'id', 'name', 'orderId', 'order_type', 'retailer', 'customer', 'retailerName', 'code', 'salesPerson', 'financePerson',
            'salesPersonName', 'date', 'distributor', 'distributorName', 'retailerSlab', 'returned_bill', 'retailerGSTIN',
            'delivery_date', 'warehouse', 'generation_date', 'retailer_note', 'discount_name', 'discount_amount','beat_assignment',
            'customerName','customerPhone','customerAddress', 'deviated_amount', 'secondary_status', 'financeName','order_brand_type',
            'order_price_amount', 'order_lines', 'status', 'return_order_lines')
        read_only_fields = ('orderId',)

    def get_retailerName(self, obj):
        if obj.retailer:
            return obj.retailer.billing_name_of_shop if not obj.retailer.billing_name_of_shop == "Exact Name Of Shop" \
                else obj.retailer.name_of_shop
        elif obj.customer:
            return obj.customer.user.name
        else:
            return "No User"

    def get_retailerGSTIN(self, obj):
        if obj.retailer and not obj.retailer.GSTIN == "GSTIN":
            return obj.retailer.GSTIN
        else:
            return ""

    def get_financeName(self, obj):
        if obj.financePerson:
            return obj.financePerson.user.name
        else:
            return "No Name"

    def get_retailerSlab(self, obj):
        if obj.retailer:
            return int(obj.retailer.commission_slab.number)
        else:
            return 0

    def get_code(self, obj):
        if obj.retailer:
            return obj.retailer.code
        elif obj.customer:
            return obj.customer.code
        else:
            return "No Code"

    def get_salesPersonName(self, obj):
        if obj.salesPerson:
            return obj.salesPerson.user.name
        else:
            return "No SalesPerson"

    def get_distributorName(self, obj):
        if obj.distributor:
            return obj.distributor.user.name
        else:
            return "No Delivery Guy"

    def get_customerName(self, obj):
        if obj.customer:
            return obj.customer.user.name
        else:
            return "No Customer"

    def get_customerPhone(self, obj):
        if obj.customer:
            return str(obj.customer.phone_no)
        else:
            return None

    def get_customerAddress(self, obj):
        if obj.customer:
            shipping_address = obj.customer.shipping_address
            if shipping_address:
                return AddressSerializer(shipping_address).data
            else:
                return None
        else:
            return None

    def get_date(self, obj):
        order_date = obj.date
        return order_date

    def get_order_lines(self, obj):
        order_lines_dict = {}
        total_quantity = 0
        order_lines = obj.lines.all()
        order_lines_dict['total_items'] = len(order_lines)
        order_lines_dict['order_items'] = []

        # For Product(White Eggs,Brown Eggs in order history)
        cart_product_dict = {'name': []}
        for order_line in order_lines:
            order_item = {}
            if order_line.product:
                product_name = order_line.product.name + " " + order_line.product.productDivision.name
                if not product_name in cart_product_dict['name']:
                    cart_product_dict.get('name').append(product_name)
                order_item['name'] = product_name
                order_item['sku'] = order_line.product.SKU_Count
                order_item['price'] = order_line.product.current_price
                order_item['quantity'] = order_line.quantity
                order_item['order_line_id'] = order_line.id
                order_item['product_id'] = order_line.product.id
                order_item['single_sku_rate'] = order_line.single_sku_rate
                order_item['single_sku_mrp'] = order_line.single_sku_mrp
                order_return_lines = OrderReturnLine.objects.filter(orderLine=order_line)
                refund_quantity = 0
                replace_quantity = 0
                for order_return_line in order_return_lines:
                    if order_return_line.line_type == 'Refund' or order_return_line.line_type == 'Return':
                        refund_quantity = refund_quantity + order_return_line.quantity
                    elif order_return_line.line_type == 'Replacement':
                        replace_quantity = replace_quantity + order_return_line.quantity
                order_item['refund_quantity'] = refund_quantity
                order_item['replace_quantity'] = replace_quantity
                productInLines = ProductInline.objects.filter(product=order_line.product)
                order_item['product_inlines'] = ProductInlineSerializer(productInLines, many=True).data
                order_lines_dict.get('order_items').append(order_item)
                total_quantity = total_quantity + order_line.quantity * order_line.product.SKU_Count
        order_lines_dict['products'] = ','.join(cart_product_dict.get('name'))
        order_lines_dict['total_quantity'] = total_quantity
        return order_lines_dict

    def get_return_order_lines(self, obj):
        return_lines_list = []
        return_status_list = ['refund','return',  'replace', 'partial_return','partial_refund', 'partial_replace', "partial_return_replace", 'partial_refund_replace']
        if obj.status in return_status_list:
            order_lines = obj.lines.all()
            order_return_lines = OrderReturnLine.objects.filter(orderLine__in=order_lines)
            if order_return_lines:
                for order_return_line in order_return_lines:
                    return_line_dict = {}
                    return_line_dict['id'] = order_return_line.id
                    return_line_dict['line_type'] = order_return_line.line_type
                    return_line_dict['quantity'] = order_return_line.quantity
                    return_line_dict['order_quantity'] = order_return_line.orderLine.quantity
                    return_line_dict['product'] = order_return_line.orderLine.product.name[0] + "-(SKU %s)" % (
                        str(order_return_line.orderLine.product.SKU_Count))
                    return_lines_list.append(return_line_dict)
        return return_lines_list


class ReturnOrderHistorySerializer(serializers.ModelSerializer):
    order_lines = serializers.SerializerMethodField()
    retailerName = serializers.SerializerMethodField()
    retailerGSTIN = serializers.SerializerMethodField()
    retailerSlab = serializers.SerializerMethodField()
    code = serializers.SerializerMethodField()
    customerName = serializers.SerializerMethodField()
    customerPhone = serializers.SerializerMethodField()
    customerAddress = serializers.SerializerMethodField()
    salesPersonName = serializers.SerializerMethodField()
    distributorName = serializers.SerializerMethodField()
    financeName = serializers.SerializerMethodField()
    return_order_lines = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = (
            'id', 'name', 'orderId', 'order_type', 'retailer', 'customer', 'retailerName', 'code', 'salesPerson', 'financePerson',
            'salesPersonName', 'date', 'distributor', 'distributorName', 'retailerSlab', 'returned_bill', 'retailerGSTIN',
            'delivery_date', 'warehouse', 'generation_date', 'retailer_note', 'discount_name', 'discount_amount',
            'customerName','customerPhone','customerAddress', 'deviated_amount', 'secondary_status', 'financeName','order_brand_type',
            'order_price_amount', 'order_lines', 'status', 'return_order_lines')
        read_only_fields = ('orderId',)

    def get_retailerName(self, obj):
        if obj.retailer:
            return obj.retailer.billing_name_of_shop if not obj.retailer.billing_name_of_shop == "Exact Name Of Shop"\
                else obj.retailer.name_of_shop
        elif obj.customer:
            return obj.customer.user.name
        else:
            return "No User"

    def get_retailerGSTIN(self, obj):
        if obj.retailer and not obj.retailer.GSTIN == "GSTIN":
            return obj.retailer.GSTIN
        else:
            return ""

    def get_financeName(self, obj):
        if obj.financePerson:
            return obj.financePerson.user.name
        else:
            return "No Name"

    def get_retailerSlab(self, obj):
        if obj.retailer:
            return int(obj.retailer.commission_slab.number)
        else:
            return 0

    def get_code(self, obj):
        if obj.retailer:
            return obj.retailer.code
        elif obj.customer:
            return obj.customer.code
        else:
            return "No Code"

    def get_salesPersonName(self, obj):
        if obj.salesPerson:
            return obj.salesPerson.user.name
        else:
            return "No SalesPerson"

    def get_distributorName(self, obj):
        if obj.distributor:
            return obj.distributor.user.name
        else:
            return "No Delivery Guy"

    def get_customerName(self, obj):
        if obj.customer:
            return obj.customer.user.name
        else:
            return "No Customer"

    def get_customerPhone(self, obj):
        if obj.customer:
            return str(obj.customer.phone_no)
        else:
            return None

    def get_customerAddress(self, obj):
        if obj.customer:
            shipping_address = obj.customer.shipping_address
            if shipping_address:
                return AddressSerializer(shipping_address).data
            else:
                return None
        else:
            return None

    def get_date(self, obj):
        order_date = obj.date
        return order_date

    def get_order_lines(self, obj):
        order_lines_dict = {}
        total_quantity = 0
        order_lines = obj.lines.all()
        order_lines_dict['total_items'] = len(order_lines)
        order_lines_dict['order_items'] = []

        # For Product(White Eggs,Brown Eggs in order history)
        cart_product_dict = {'name': []}
        for order_line in order_lines:
            order_item = {}
            if order_line.product:
                product_name = order_line.product.name + " " + order_line.product.productDivision.name
                if not product_name in cart_product_dict['name']:
                    cart_product_dict.get('name').append(product_name)
                order_item['name'] = product_name
                order_item['sku'] = order_line.product.SKU_Count
                order_item['price'] = order_line.product.current_price
                order_item['quantity'] = order_line.quantity
                order_item['order_line_id'] = order_line.id
                order_item['product_id'] = order_line.product.id
                order_item['single_sku_rate'] = order_line.single_sku_rate
                order_item['single_sku_mrp'] = order_line.single_sku_mrp
                order_return_lines = OrderReturnLine.objects.filter(orderLine=order_line)
                refund_quantity = 0
                replace_quantity = 0
                return_line_date = None
                for order_return_line in order_return_lines:
                    if order_return_line.line_type == 'Refund' or order_return_line.line_type == 'Return':
                        refund_quantity = refund_quantity + order_return_line.quantity
                        return_line_date = order_return_line.date
                    elif order_return_line.line_type == 'Replacement':
                        replace_quantity = replace_quantity + order_return_line.quantity
                        return_line_date = order_return_line.date
                order_item['refund_quantity'] = refund_quantity
                order_item['replace_quantity'] = replace_quantity
                order_item['return_date'] = return_line_date
                productInLines = ProductInline.objects.filter(product=order_line.product)
                order_item['product_inlines'] = ProductInlineSerializer(productInLines, many=True).data
                order_lines_dict.get('order_items').append(order_item)
                total_quantity = total_quantity + order_line.quantity * order_line.product.SKU_Count
        order_lines_dict['products'] = ','.join(cart_product_dict.get('name'))
        order_lines_dict['total_quantity'] = total_quantity
        return order_lines_dict

    def get_return_order_lines(self, obj):
        return_lines_list = []
        return_status_list = ['refund','return',  'replace', 'partial_return','partial_refund', 'partial_replace', "partial_return_replace", 'partial_refund_replace']
        if obj.status in return_status_list:
            order_lines = obj.lines.all()
            order_return_lines = OrderReturnLine.objects.filter(orderLine__in=order_lines)
            if order_return_lines:
                for order_return_line in order_return_lines:
                    return_line_dict = {}
                    return_line_dict['id'] = order_return_line.id
                    return_line_dict['line_type'] = order_return_line.line_type
                    return_line_dict['quantity'] = order_return_line.quantity
                    return_line_dict['order_quantity'] = order_return_line.orderLine.quantity
                    return_line_dict['product'] = order_return_line.orderLine.product.name[0] + "-(SKU %s)" % (
                        str(order_return_line.orderLine.product.SKU_Count))
                    return_lines_list.append(return_line_dict)
        return return_lines_list


class PurchaseOrderHistorySerializer(OrderHistorySerializer):

    class Meta:
        model = PurchaseOrder
        fields = '__all__'



class OrderLineUpdateSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(required=False, queryset=OrderLine.objects.all())

    class Meta:
        model = OrderLine
        fields = ('id', 'product', 'quantity',)


class OrderUpdateSerializer(serializers.ModelSerializer):
    cart_products = serializers.CharField(required=False)
    retailer_note = serializers.CharField(required=False)
    id = serializers.PrimaryKeyRelatedField(required=True, queryset=Order.objects.all())

    class Meta:
        model = Order
        fields = ('id', 'retailer_note', 'cart_products', 'status', 'order_price_amount', 'order_brand_type',)

    def validate(self, data):
        print(data)
        order_obj = data.get('id')
        delivery_date = data.get('delivery_date', None)
        if delivery_date:
            try:
                # print(value)
                datetime.strptime(delivery_date, '%d-%m-%Y')
            except ValueError:
                raise serializers.ValidationError("Datetime has wrong format")

        order_lines = data.get('cart_products', [])
        if order_lines:
            order_lines = json.loads(order_lines)
            if len(order_lines) > 0:
                if not data.get('order_price_amount'):
                    raise serializers.ValidationError("order_price_amount required")
                for order_line in order_lines:
                    order_line_serializer = OrderLineUpdateSerializer(data=order_line)
                    order_line_serializer.is_valid(raise_exception=True)
                    order_line_id = order_line.get('id', None)
                    if order_line_id:

                        order_line_obj = OrderLine.objects.filter(id=int(order_line_id), order=order_obj).first()
                        if not order_line_obj:
                            raise serializers.ValidationError("order_line_id is not valid")
                        else:
                            line_edit_type = order_line.get('type', None)
                            if line_edit_type and line_edit_type == 'delete':
                                pass
                            else:
                                if order_line_obj.product.id != order_line.get('product'):
                                    raise serializers.ValidationError("product id not valid for order line")
                                if order_line.get('quantity') < 1:
                                    raise serializers.ValidationError("quantity must be greater then zero")
                    else:
                        if order_line.get('quantity') < 1:
                            raise serializers.ValidationError("quantity must be greater then zero")

            else:
                raise serializers.ValidationError("At least one order line required")
        return data

    def order_update(self, instance, data):
        order_within_status = ['created', 'on the way', 'revised']
        if instance.status in order_within_status:
            order_status = data.get('status', None)
            if order_status == 'cancelled':
                instance.status = 'cancelled'

        retailer_note = data.get('retailer_note', None)
        if retailer_note and retailer_note != instance.retailer_note:
            instance.retailer_note = retailer_note

        delivery_date = data.get('delivery_date', None)
        if delivery_date:
            delivery_date = datetime.strptime(data.get('delivery_date'), "%d-%m-%Y")
            if delivery_date != instance.delivery_date:
                instance.delivery_date = delivery_date
        if instance.status in order_within_status:
            order_lines = data.get('cart_products', [])
            if order_lines:
                order_lines = json.loads(order_lines)
                for order_line in order_lines:
                    if order_line.get('id'):
                        order_line_obj = OrderLine.objects.filter(id=order_line.get('id')).first()

                        product = order_line_obj.product
                        baseProduct_slug = str(product.city.city_name) + "-Egg-" + product.name[:2]
                        baseProduct = BaseProduct.objects.filter(slug=baseProduct_slug).first()
                        if baseProduct:
                            if instance.status == 'created':
                                inventory_statuses = ['available', 'in packing']
                            elif instance.status == 'on the way' or instance.status == 'revised':
                                inventory_statuses = ['packed', 'in transit']
                            inventories = Inventory.objects.filter(warehouse=order_line_obj.order.salesPerson.warehouse,
                                                                   baseProduct=baseProduct,
                                                                   inventory_status__in=inventory_statuses)

                        line_edit_type = order_line.get('type', None)
                        if line_edit_type and line_edit_type == 'delete':
                            for inventory in inventories:
                                if inventory.inventory_status == inventory_statuses[0]:
                                    inventory.quantity = inventory.quantity + (
                                            order_line_obj.product.SKU_Count * order_line_obj.quantity)
                                    inventory.branded_quantity = inventory.branded_quantity + (
                                            order_line_obj.product.SKU_Count * order_line_obj.quantity)
                                    inventory.save()
                                if inventory.inventory_status == inventory_statuses[1]:
                                    inventory.quantity = inventory.quantity - (
                                            order_line_obj.product.SKU_Count * order_line_obj.quantity)
                                    inventory.branded_quantity = inventory.branded_quantity - (
                                            order_line_obj.product.SKU_Count * order_line_obj.quantity)
                                    inventory.save()
                            order_line_obj.delete()
                        else:
                            quantity_diff = order_line_obj.quantity - order_line.get('quantity')
                            for inventory in inventories:
                                if inventory.inventory_status == inventory_statuses[0]:
                                    inventory.quantity = inventory.quantity + (
                                            order_line_obj.product.SKU_Count * quantity_diff)
                                    inventory.branded_quantity = inventory.branded_quantity + (
                                            order_line_obj.product.SKU_Count * quantity_diff)
                                    inventory.save()
                                if inventory.inventory_status == inventory_statuses[1]:
                                    inventory.quantity = inventory.quantity - (
                                            order_line_obj.product.SKU_Count * quantity_diff)
                                    inventory.branded_quantity = inventory.branded_quantity - (
                                            order_line_obj.product.SKU_Count * quantity_diff)
                                    inventory.save()
                            order_line_obj.quantity = order_line.get('quantity')
                            order_line_obj.single_sku_rate = order_line.get('single_sku_rate')
                            order_line_obj.single_sku_mrp = order_line.get('single_sku_mrp')
                            order_line_obj.save()
                    else:

                        order_line_obj = OrderLine.objects.create(order=instance, product_id=order_line.get('product'),
                                                                  quantity=order_line.get('quantity'),
                                                                  single_sku_rate=order_line.get('single_sku_rate'),
                                                                  single_sku_mrp=order_line.get('single_sku_mrp'))
                        product = order_line_obj.product
                        baseProduct_slug = str(product.city.city_name) + "-Egg-" + product.name[:2]
                        baseProduct = BaseProduct.objects.filter(slug=baseProduct_slug).first()
                        if baseProduct:
                            if instance.status == 'created':
                                inventory_statuses = ['available', 'in packing']
                            elif instance.status == 'on the way' or instance.status == 'revised':
                                inventory_statuses = ['packed', 'in transit']
                            inventories = Inventory.objects.filter(warehouse=order_line_obj.order.salesPerson.warehouse,
                                                                   baseProduct=baseProduct,
                                                                   inventory_status__in=inventory_statuses)
                        for inventory in inventories:
                            if inventory.inventory_status == inventory_statuses[0]:
                                inventory.quantity = inventory.quantity - (
                                        order_line_obj.product.SKU_Count * order_line_obj.quantity)
                                inventory.branded_quantity = inventory.branded_quantity - (
                                        order_line_obj.product.SKU_Count * order_line_obj.quantity)
                                inventory.save()
                            if inventory.inventory_status == inventory_statuses[1]:
                                inventory.quantity = inventory.quantity + (
                                        order_line_obj.product.SKU_Count * order_line_obj.quantity)
                                inventory.branded_quantity = inventory.branded_quantity + (
                                        order_line_obj.product.SKU_Count * order_line_obj.quantity)
                                inventory.save()
                        order_line_obj.save()
                instance.order_price_amount = data.get('order_price_amount')
        instance.save()
        return instance


class OrderReturnLineCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderReturnLine
        fields = ('orderLine', 'line_type', 'quantity','beat_assignment')



class OrderReturnLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderReturnLine
        fields = ('orderLine', 'line_type', 'quantity', 'beat_assignment', 'date', 'pickup_date', 'distributor', 'salesPerson', 'financePerson')


class OrderReturnLineUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderReturnLine
        fields = ('id', 'line_type', 'quantity')


class OrderReturnSerializer(serializers.Serializer):
    order_return_lines = serializers.CharField(required=True)
    secondary_status = serializers.CharField(required=True)
    id = serializers.PrimaryKeyRelatedField(required=True, queryset=Order.objects.all())

    def validate(self, data):
        order_obj = data.get('id')
        if order_obj.status == 'delivered' or order_obj.status == 'completed':
            order_return_lines = json.loads(data.get('order_return_lines'))
            if len(order_return_lines) > 0:
                for order_return_line in order_return_lines:
                    print(order_return_line)
                    order_line_serializer = OrderReturnLineCreateSerializer(data=order_return_line)
                    order_line_serializer.is_valid(raise_exception=True)
                    order_line_id = order_return_line.get('orderLine')
                    order_line_obj = OrderLine.objects.filter(id=int(order_line_id), order=order_obj).first()
                    if not order_line_obj:
                        raise serializers.ValidationError("order_line_id is not valid")
            else:
                raise serializers.ValidationError("At least one order return line required")
        else:
            raise serializers.ValidationError("Order can be returned after delivery")
        print("return serializer validate true")
        return data

    def order_return_replace(self, instance, data, user, is_sales):
        order_return_lines = json.loads(data.get('order_return_lines'))
        date = datetime.strptime(data.get('date'), "%d-%m-%Y %H:%M:%S")
        date = CURRENT_ZONE.localize(date)
        order_deviated_amount = decimal.Decimal(0.000)
        transaction_type = data.get("secondary_status")

        if data.get('beat_assignment'):
            beat_assignment = BeatAssignment.objects.get(id=data.get('beat_assignment'))
        else:
            beat_assignment = None

        is_trial = False
        if instance.retailer.code == "T1001* Trial" or instance.retailer.code == "D2670* Paul Trial":
            is_trial = True
        # order_return_line = None
        for order_return_line in order_return_lines:
            order_return_serializer = OrderReturnLineCreateSerializer(data=order_return_line)
            order_return_serializer.is_valid(raise_exception=True)
            orderLine = OrderLine.objects.get(pk=order_return_line.get('orderLine'))
            order_return_line = order_return_serializer.save(orderLine_id=order_return_line.get('orderLine'),
                                                             date=date,
                                                             beat_assignment=beat_assignment,
                                                             return_transaction=-1,
                                                             pickup_date=date)

            if DistributionPersonProfile.objects.filter(user=user).first():
                distributionPersonProfile = DistributionPersonProfile.objects.filter(user=user).first()
                order_return_line.distributor = distributionPersonProfile
                order_return_line.save()
            if SalesPersonProfile.objects.filter(user=user).first():
                salesPersonProfile = SalesPersonProfile.objects.filter(user=user).first()
                order_return_line.salesPerson = salesPersonProfile
                order_return_line.save()

            if FinanceProfile.objects.filter(user=user).first():
                financePerson = FinanceProfile.objects.filter(user=user).first()
                order_return_line.financePerson = financePerson
                order_return_line.save()


            original_sku_rate = order_return_line.orderLine.single_sku_rate

            deviated_quantity = order_return_line.quantity

            if order_return_line.line_type == "Return" or order_return_line.line_type == "Refund":

                if beat_assignment and instance.order_brand_type == "branded":
                    if int(instance.retailer.id) == 1386 or int(instance.retailer.id) == 1612:
                        pass
                    else:
                        salesDemand = SalesDemandSKU.objects.get(beatAssignment=beat_assignment,
                                                                 product=order_return_line.orderLine.product)
                        salesDemand.product_return_quantity += order_return_line.quantity
                        salesDemand.save()
                        # retailerDemand = RetailerDemand.objects.get(beatAssignment=beat_assignment, retailer=int(data.get('retailer')))
                        # retailerDemand.retailer_status = "Returned"
                        # retailerDemand.save()
                        if RetailerDemand.objects.filter(beatAssignment=beat_assignment, retailer=instance.retailer):
                            retailerDemand = RetailerDemand.objects.get(beatAssignment=beat_assignment,
                                                                        retailer=instance.retailer)
                            retailerDemand.retailer_status = "Returned"
                            retailerDemand.save()
                        else:
                            retailerDemand = RetailerDemand.objects.create(beatAssignment=beat_assignment,
                                                                           retailer_status="Returned",
                                                                           date=datetime.now().date(),
                                                                           time=datetime.now().time(),
                                                                           retailer=instance.retailer)
                deviated_amount = original_sku_rate * deviated_quantity
                order_deviated_amount += deviated_amount
            else:
                if beat_assignment:
                    if int(instance.retailer.id) == 1386 or int(instance.retailer.id) == 1612:
                        pass
                    else:
                        salesDemand = SalesDemandSKU.objects.get(beatAssignment=beat_assignment,
                                                                 product=order_return_line.orderLine.product)
                        salesDemand.product_replacement_quantity += order_return_line.quantity
                        salesDemand.save()
                        # retailerDemand = RetailerDemand.objects.get(beatAssignment=beat_assignment, retailer=int(data.get('retailer')))
                        # retailerDemand.retailer_status = "Replaced"
                        # retailerDemand.save()
                        if RetailerDemand.objects.filter(beatAssignment=beat_assignment, retailer=instance.retailer):
                            retailerDemand = RetailerDemand.objects.get(beatAssignment=beat_assignment,
                                                                        retailer=instance.retailer)
                            retailerDemand.retailer_status = "Replaced"
                            retailerDemand.save()
                        else:
                            retailerDemand = RetailerDemand.objects.create(beatAssignment=beat_assignment,
                                                                           retailer_status="Replaced",
                                                                           date=datetime.now().date(),
                                                                           time=datetime.now().time(),
                                                                           retailer=instance.retailer)
                if instance.retailer:
                    retailer_commission = instance.retailer.commission_slab.number
                    deviated_amount = deviated_quantity * (
                            original_sku_rate -
                            (order_return_line.orderLine.product.current_price * ((100 - retailer_commission) / 100))
                    )
                else:
                    deviated_amount = 0.000
                deviated_amount = decimal.Decimal(int(deviated_amount))
                order_deviated_amount += deviated_amount
                # order_deviated_amount += decimal.Decimal(0.000)
                # Recheck invoice Due and clear
            order_return_line.amount += deviated_amount
            order_return_line.save()

            orderLine.deviated_quantity += deviated_quantity
            orderLine.deviated_amount += deviated_amount
            orderLine.save()

        return_extra_amount = decimal.Decimal(0.000)
        bill_data = {"order_ids":[]}
        order_ids = []
        if int(order_deviated_amount) > 0 :
            # TODO  clear invoice and due

            if Invoice.objects.filter(order=instance):
                invoice = Invoice.objects.filter(order=instance).first()
                if invoice.invoice_status == "Pending":
                    if int(invoice.invoice_due) > int(order_deviated_amount):
                        invoice.invoice_due -= order_deviated_amount
                        order_ids.append(invoice.order.name)
                    elif int(invoice.invoice_due) == int(order_deviated_amount):
                        invoice.invoice_due -= order_deviated_amount
                        invoice.invoice_status = "Paid"
                        order_ids.append(invoice.order.name)
                    else:
                        invoice.invoice_due = decimal.Decimal(0.000)
                        return_extra_amount = order_deviated_amount - invoice.invoice_due
                        invoice.invoice_status = "Paid"
                        order_ids.append(invoice.order.name)
                elif invoice.invoice_status == "Paid":
                    print("already paid")
                    return_extra_amount = order_deviated_amount
                invoice.save()
                bill_data["order_ids"] = order_ids
        else:
            pass
        instance.deviated_amount += order_deviated_amount
        instance.status = "completed"
        instance.secondary_status = data.get('secondary_status').lower()

        # if FinanceProfile.objects.filter(user=user).first():
        #     financePerson = FinanceProfile.objects.filter(user=user).first()
        # else:
        #     financePerson = FinanceProfile.objects.none()

        # TODO create a debit note depending on the situation
        # Check if amount is positive or negative
        transactions = SalesTransaction.objects.all()
        # might be possible model has no records so make sure to handle None
        transaction_max_id = transactions.aggregate(Max('id'))['id__max'] + 1 if transactions else 1
        transaction_id = "TR" + str(transaction_max_id)
        transaction_date = datetime.strptime(data.get('date'), "%d-%m-%Y %H:%M:%S")
        transaction_date = CURRENT_ZONE.localize(transaction_date)
        sales_transaction_debit_note = None
        if FinanceProfile.objects.filter(user=user).first():
            financePerson = FinanceProfile.objects.filter(user=user).first()
            if order_ids:
                transaction_amount = order_deviated_amount
            else:
                transaction_amount = order_deviated_amount - return_extra_amount
            sales_transaction = SalesTransaction.objects.create(transaction_amount=transaction_amount,
                                                                salesPerson=instance.salesPerson,
                                                                financePerson=financePerson,
                                                                transaction_date=transaction_date,
                                                                transaction_type=transaction_type,
                                                                beat_assignment = beat_assignment,
                                                                transaction_id=transaction_id,
                                                                is_trial=is_trial,
                                                                retailer=instance.retailer)
            if int(return_extra_amount) > 0 and not is_sales:
                sales_transaction_debit_note = SalesTransaction.objects.create(
                    transaction_amount=return_extra_amount,
                    salesPerson=instance.salesPerson,
                    financePerson=financePerson,
                    transaction_date=transaction_date,
                    beat_assignment=beat_assignment,
                    transaction_type="Debit Note",
                    transaction_id=transaction_id,
                    is_trial=is_trial,
                    retailer=instance.retailer)
        else:
            distributionPersonProfile = DistributionPersonProfile.objects.filter(user=user).first()
            if order_ids:
                transaction_amount = order_deviated_amount
            else:
                transaction_amount = order_deviated_amount - return_extra_amount
            sales_transaction = SalesTransaction.objects.create(transaction_amount=transaction_amount,
                                                                salesPerson=instance.salesPerson,
                                                                distributor = distributionPersonProfile if distributionPersonProfile else None,
                                                                transaction_date=transaction_date,
                                                                transaction_type=transaction_type,
                                                                beat_assignment=beat_assignment,
                                                                transaction_id=transaction_id,
                                                                is_trial=is_trial,
                                                                retailer=instance.retailer)
            if int(return_extra_amount) > 0 and not is_sales:
                sales_transaction_debit_note = SalesTransaction.objects.create(
                    transaction_amount=return_extra_amount,
                    salesPerson=instance.salesPerson,
                    distributor=distributionPersonProfile if distributionPersonProfile else None,
                    transaction_date=transaction_date,
                    transaction_type="Debit Note",
                    beat_assignment =beat_assignment,
                    transaction_id=transaction_id,
                    is_trial=is_trial,
                    retailer=instance.retailer)

        instance.refund_transaction = sales_transaction.id

        ReturnOrderTransaction.objects.create(refund_transaction=sales_transaction.id,
                                              return_picked_date=sales_transaction.transaction_date,
                                              beat_assignment = beat_assignment,
                                              deviated_amount=order_deviated_amount,
                                              order=instance)
        for order_return_line in order_return_lines:
            return_line = OrderReturnLine.objects.get(orderLine_id=order_return_line.get('orderLine'),
                                                                 date=date,
                                                                 beat_assignment=beat_assignment,
                                                                 return_transaction=-1,
                                                                 pickup_date=date)
            return_line.return_transaction = sales_transaction.id

        if sales_transaction_debit_note:
            DebitNoteTransaction.objects.create(debit_note_transaction=sales_transaction_debit_note.id,
                                              debit_note_date=sales_transaction_debit_note.transaction_date,
                                              beat_assignment = beat_assignment,
                                              amount=sales_transaction_debit_note.transaction_amount,
                                              order=instance)
        instance.save()

        sales_transaction.retailer.amount_due = decimal.Decimal(
            sales_transaction.retailer.amount_due) - decimal.Decimal(sales_transaction.transaction_amount)
        sales_transaction.retailer.save()
        sales_transaction.current_balance = sales_transaction.retailer.amount_due
        sales_transaction.save()
        invoice_obj = Invoice.objects.filter(order=instance).first()
        if invoice_obj:
            sales_transaction.invoices.add(invoice_obj)
            if sales_transaction_debit_note:

                sales_transaction_debit_note.retailer.amount_due = decimal.Decimal(
                    sales_transaction_debit_note.retailer.amount_due) - decimal.Decimal(sales_transaction_debit_note.transaction_amount)
                sales_transaction_debit_note.retailer.save()
                sales_transaction_debit_note.current_balance = sales_transaction_debit_note.retailer.amount_due
                sales_transaction_debit_note.save()

                sales_transaction_debit_note.invoices.add(invoice_obj)




        return {"instance":instance, "return_extra_amount": return_extra_amount, "bill_data":bill_data}


class OrderReturnReplacementSerializer(serializers.Serializer):
    order_return_lines = serializers.CharField(required=True)
    id = serializers.PrimaryKeyRelatedField(required=True, queryset=Order.objects.all())

    def validate(self, data):
        order_obj = data.get('id')
        if order_obj.status == 'delivered':
            order_return_lines = json.loads(data.get('order_return_lines'))
            if len(order_return_lines) > 0:
                for order_return_line in order_return_lines:
                    order_line_serializer = OrderReturnLineCreateSerializer(data=order_return_line)
                    order_line_serializer.is_valid(raise_exception=True)
                    order_line_id = order_return_line.get('orderLine')
                    order_line_obj = OrderLine.objects.filter(id=int(order_line_id), order=order_obj).first()
                    if not order_line_obj:
                        raise serializers.ValidationError("order_line_id is not valid")
            else:
                raise serializers.ValidationError("At least one order return line required")
        else:
            raise serializers.ValidationError("Order can be returned after delivery")
        print("return serializer validate true")
        return data

    def order_return(self, instance, data):
        order_return_lines = json.loads(data.get('order_return_lines'))
        order_return_status_types = []
        for order_return_line in order_return_lines:
            order_return_serializer = OrderReturnLineCreateSerializer(data=order_return_line)
            order_return_serializer.is_valid(raise_exception=True)
            order_return_line = order_return_serializer.save(orderLine_id=order_return_line.get('orderLine'))
            order_return_line.amount = order_return_line.orderLine.single_sku_rate * order_return_line.quantity
            order_return_line.save()
            if order_return_line.line_type == 'Refund':
                if 'partial_refund' not in order_return_status_types:
                    if order_return_line.quantity == order_return_line.orderLine.quantity:
                        if 'refund' not in order_return_status_types:
                            order_return_status_types.append('refund')
                    else:
                        if 'refund' in order_return_status_types:
                            order_return_status_types.remove('refund')
                        if 'partial_refund' not in order_return_status_types:
                            order_return_status_types.append('partial_refund')
            elif order_return_line.line_type == 'Replacement':
                if 'partial_replace' not in order_return_status_types:
                    if order_return_line.quantity == order_return_line.orderLine.quantity:
                        if 'replace' not in order_return_status_types:
                            order_return_status_types.append('replace')
                    else:
                        if 'replace' in order_return_status_types:
                            order_return_status_types.remove('replace')
                        if 'partial_replace' not in order_return_status_types:
                            order_return_status_types.append('partial_replace')

            order_return_status_types = list(set(order_return_status_types))
            if len(order_return_status_types) == 1:
                instance.status = order_return_status_types[0]
                instance.save()
            else:
                if len(order_return_status_types) > 1:
                    instance.status = 'partial_refund_replace'
                    instance.save()
        return instance


class OrderReturnPickupSerializer(serializers.Serializer):
    order_return_lines = serializers.CharField(required=True)
    id = serializers.PrimaryKeyRelatedField(required=True, queryset=Order.objects.all())

    def validate(self, data):
        order_obj = data.get('id')
        return_status_list = ['refund', 'replace', 'partial_refund', 'partial_replace', 'partial_refund_replace']
        if order_obj.status in return_status_list:
            order_return_lines = json.loads(data.get('order_return_lines'))
            if len(order_return_lines) > 0:
                for order_return_line in order_return_lines:
                    order_line_serializer = OrderReturnLineUpdateSerializer(data=order_return_line)
                    order_line_serializer.is_valid(raise_exception=True)
            else:
                raise serializers.ValidationError("At least one order return line required to update")
        else:
            raise serializers.ValidationError("Order not valid to return pickup")
        return data

    def order_pickup(self, instance, data):
        order_return_lines = json.loads(data.get('order_return_lines'))
        for order_return_line in order_return_lines:
            print(order_return_line)
            order_line_serializer = OrderReturnLineUpdateSerializer(data=order_return_line)
            order_line_serializer.is_valid(raise_exception=True)
            order_return_line_obj = OrderReturnLine.objects.filter(id=order_return_line.get('id'),
                                                                   line_type=order_return_line.get('line_type')).first()
            order_return_line_obj.quantity = order_return_line.get('quantity')
            if order_return_line.get('line_type') == "Refund":
                order_return_line_obj.amount = order_return_line_obj.orderLine.single_sku_rate * order_return_line.get(
                    'quantity')
            else:
                retailer_commission = instance.retailer.commission_slab.number
                if int(order_return_line_obj.orderLine.single_sku_mrp) != 0:
                    retailer_commission_amount = order_return_line_obj.orderLine.single_sku_rate / order_return_line_obj.orderLine.single_sku_mrp
                    order_return_line_obj.amount = (
                                                               order_return_line_obj.orderLine.single_sku_rate * order_return_line.get(
                                                           'quantity')) - (
                                                               order_return_line_obj.orderLine.product.current_price * order_return_line.get(
                                                           'quantity') * (retailer_commission_amount))
                else:

                    order_return_line_obj.amount = (order_return_line_obj.orderLine.single_sku_rate * order_return_line.get(
                        'quantity')) - (order_return_line_obj.orderLine.product.current_price * order_return_line.get(
                        'quantity') * ((100 - retailer_commission) / 100))
            order_return_line_obj.pickup_date = datetime.now(tz=CURRENT_ZONE)
            order_return_line_obj.save()

        instance.status = 'return_picked'
        instance.save()

        adjust_amount = 0
        order_lines = instance.lines.all()
        order_return_lines = OrderReturnLine.objects.filter(orderLine__in=order_lines)
        if order_return_lines:
            for order_return_line in order_return_lines:
                adjust_amount = decimal.Decimal(adjust_amount) + order_return_line.amount
            if adjust_amount > 0:
                transactions = SalesTransaction.objects.all()
                # might be possible model has no records so make sure to handle None
                transaction_max_id = transactions.aggregate(Max('id'))['id__max'] + 1 if transactions else 1
                transaction_id = "TR" + str(transaction_max_id)
                transaction_date = datetime.now(tz=CURRENT_ZONE)
                sales_transaction = SalesTransaction.objects.create(retailer=instance.retailer,
                                                                    transaction_id=transaction_id,
                                                                    transaction_type="Refund",
                                                                    salesPerson=instance.retailer.salesPersonProfile,
                                                                    transaction_date=transaction_date,
                                                                    transaction_amount=adjust_amount)
                sales_transaction.retailer.amount_due = decimal.Decimal(
                    sales_transaction.retailer.amount_due) - decimal.Decimal(sales_transaction.transaction_amount)
                sales_transaction.retailer.save()
                sales_transaction.current_balance = sales_transaction.retailer.amount_due
                sales_transaction.save()

                # Handle Retailer Pending Invoices
                transaction_amount = sales_transaction.transaction_amount
                latest_invoice = Invoice.objects.filter(order=instance, invoice_status="Pending").first()
                if latest_invoice and latest_invoice.invoice_due > 0:
                    if transaction_amount > 0:
                        if latest_invoice.invoice_due == transaction_amount:
                            InvoiceLine.objects.create(invoice=latest_invoice,
                                                       amount_received=latest_invoice.invoice_due)
                            transaction_amount = transaction_amount - latest_invoice.invoice_due
                            latest_invoice.invoice_status = 'Paid'
                            latest_invoice.invoice_due = decimal.Decimal(0)
                            latest_invoice.save()
                            sales_transaction.invoices.add(latest_invoice)
                        elif latest_invoice.invoice_due < transaction_amount:
                            InvoiceLine.objects.create(invoice=latest_invoice,
                                                       amount_received=latest_invoice.invoice_due)
                            transaction_amount = transaction_amount - latest_invoice.invoice_due
                            latest_invoice.invoice_status = 'Paid'
                            latest_invoice.invoice_due = decimal.Decimal(0)
                            latest_invoice.save()
                            sales_transaction.invoices.add(latest_invoice)
                            pending_invoices = Invoice.objects.filter(order__in=instance.retailer.OrderRetailer.all(),
                                                                      invoice_status="Pending")
                            for pending_invoice in pending_invoices:
                                if int(transaction_amount) > 0:
                                    if pending_invoice.invoice_due <= transaction_amount:
                                        InvoiceLine.objects.create(invoice=pending_invoice,
                                                                   amount_received=pending_invoice.invoice_due)
                                        transaction_amount = transaction_amount - pending_invoice.invoice_due
                                        pending_invoice.invoice_status = 'Paid'
                                        pending_invoice.invoice_due = decimal.Decimal(0)
                                        pending_invoice.save()
                                        sales_transaction.invoices.add(pending_invoice)
                                    else:
                                        InvoiceLine.objects.create(invoice=pending_invoice,
                                                                   amount_received=transaction_amount)
                                        pending_invoice.invoice_due = pending_invoice.invoice_due - decimal.Decimal(
                                            transaction_amount)
                                        pending_invoice.save()
                                        sales_transaction.invoices.add(pending_invoice)
                                        break
                                else:
                                    break
                        else:
                            InvoiceLine.objects.create(invoice=latest_invoice,
                                                       amount_received=transaction_amount)
                            latest_invoice.invoice_due = latest_invoice.invoice_due - decimal.Decimal(
                                transaction_amount)
                            latest_invoice.save()
                            sales_transaction.invoices.add(latest_invoice)

                else:
                    pending_invoices = Invoice.objects.filter(order__in=instance.retailer.OrderRetailer.all(),
                                                              invoice_status="Pending")
                    for pending_invoice in pending_invoices:
                        if transaction_amount > 0:
                            if pending_invoice.invoice_due > 0:
                                if pending_invoice.invoice_due <= transaction_amount:
                                    InvoiceLine.objects.create(invoice=pending_invoice,
                                                               amount_received=pending_invoice.invoice_due)
                                    transaction_amount = transaction_amount - pending_invoice.invoice_due
                                    pending_invoice.invoice_status = 'Paid'
                                    pending_invoice.invoice_due = decimal.Decimal(0)
                                    pending_invoice.save()
                                    sales_transaction.invoices.add(pending_invoice)
                                else:
                                    InvoiceLine.objects.create(invoice=pending_invoice,
                                                               amount_received=transaction_amount)
                                    pending_invoice.invoice_due = pending_invoice.invoice_due - decimal.Decimal(
                                        transaction_amount)
                                    pending_invoice.save()
                                    sales_transaction.invoices.add(pending_invoice)
                                    break
                            else:
                                continue

                        else:
                            break
            elif adjust_amount < 0:
                transactions = SalesTransaction.objects.all()
                # might be possible model has no records so make sure to handle None
                transaction_max_id = transactions.aggregate(Max('id'))['id__max'] + 1 if transactions else 1
                transaction_id = "TR" + str(transaction_max_id)
                transaction_date = datetime.now(tz=CURRENT_ZONE)
                sales_transaction = SalesTransaction.objects.create(retailer=instance.retailer,
                                                                    transaction_id=transaction_id,
                                                                    transaction_type="Debit",
                                                                    salesPerson=instance.retailer.salesPersonProfile,
                                                                    transaction_date=transaction_date,
                                                                    transaction_amount=adjust_amount)
                sales_transaction.retailer.amount_due = decimal.Decimal(
                    sales_transaction.retailer.amount_due) + decimal.Decimal(sales_transaction.transaction_amount)
                sales_transaction.retailer.save()
                sales_transaction.current_balance = sales_transaction.retailer.amount_due
                sales_transaction.save()
                # TODO Make Replacement Invoice

        return instance
