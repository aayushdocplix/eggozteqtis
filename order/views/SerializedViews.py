import base64
import decimal
import json
from ast import literal_eval
from datetime import datetime, timedelta
from order.tasks import create_invoice
import pyotp
import pytz
import requests
from django.core.mail import send_mail
from django.db.models import Max, Q
from django.shortcuts import get_object_or_404
from django.template import loader
from django.utils import timezone
from django.utils.timezone import now
from django_filters import rest_framework as filters
from num2words import num2words
from rest_framework import permissions, viewsets, status, decorators, mixins
from rest_framework.response import Response

from Eggoz import settings
from Eggoz.settings import CASHFREE_BASE_URL, CASHFREE_APP_ID, CASHFREE_SECRET_KEY, IST, CURRENT_ZONE, FROM_EMAIL
from base.response import BadRequest, Forbidden, Created, Ok, InternalServerError
from base.views import PaginationWithNoLimit
from custom_auth.api.serializers import GenerateOtpSerializer, AddressCreationSerializer
from custom_auth.models import UserProfile, PhoneModel, User
from custom_auth.tasks import send_sms_message
from custom_auth.views import GenerateKey
from distributionchain.api import BeatAssignmentDetailSerializer
from distributionchain.models import DistributionPersonProfile, DistributionEggsdata, BeatAssignment
from ecommerce.models import Customer, CustomerWallet, CustomerPromoWallet, CashFreeTransaction
from finance.models import FinanceProfile
from operationschain.models import OperationsPersonProfile
from order.api.serializers import OrderCreateSerializer, OrderLineSerializer, OrderHistorySerializer, PackingSerializer, \
    OrderUpdateSerializer, OrderReturnReplacementSerializer, OrderReturnPickupSerializer, \
    EcommerceOrderCreateSerializer, OrderReturnSerializer, OrderReturnLineSerializer, OrderShortSerializer, \
    PurchaseOrderHistorySerializer, PurchaseOrderCreateSerializer, EcommerceOrderHistorySerializer, \
    ReturnOrderHistorySerializer
from order.models import Order
from order.models.Order import PackingOrder, OrderEvent, PurchaseOrder, EcommerceOrder, OrderReturnLine
from order.statuses import OrderStatus
from payment.api.serializers import PaymentValidationSerializer, SalesTransactionCreateSerializer, \
    SalesTransactionShortSerializer, PaymentSerializer
from payment.models import SalesTransaction, Payment, Invoice, InvoiceLine
from payment.views.InvoiceView import generate_invoice
from product.models import BaseProduct
from retailer.models import RetailerEggsdata, Retailer
from saleschain.models import SalesPersonProfile, SalesEggsdata, SalesDemandSKU, RetailerDemand
from warehouse.models import Warehouse, WarehousePersonProfile, Inventory


class PackingViewSet(viewsets.GenericViewSet, mixins.CreateModelMixin, mixins.ListModelMixin,
                     mixins.RetrieveModelMixin):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = PackingSerializer
    queryset = PackingOrder.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ('status',)

    def create(self, request, *args, **kwargs):
        user_profile = UserProfile.objects.filter(user=request.user, department__name__in=['Warehouse']).first()
        if user_profile:
            warehousePersonProfile = WarehousePersonProfile.objects.filter(user=request.user).first()
            if warehousePersonProfile:

                orders = request.GET.get('orders', [])
                if orders and orders != "undefined":
                    orders = json.loads(orders)
                    orders = [int(c) for c in orders]
                    if len(orders) > 0:
                        for order in orders:
                            get_object_or_404(Order, pk=order, status="created")
                    else:
                        return BadRequest({'error_type': "Validation Error",
                                           'errors': [{'message': "please provide at least one order to assign"}]})
                else:
                    return BadRequest({'error_type': "Validation Error",
                                       'errors': [{'message': "please provide at least one order to assign"}]})
                packing_orders = PackingOrder.objects.all()
                # might be possible model has no records so make sure to handle None
                packing_order_max_id = packing_orders.aggregate(Max('id'))['id__max'] + 1 if packing_orders else 1
                packing_order_id = "PK" + str(packing_order_max_id)
                packing_obj = PackingOrder.objects.create(packing_id=packing_order_id, desc="desc")
                for order in orders:
                    order_obj = Order.objects.get(pk=order)
                    order_obj.packingOrder = packing_obj
                    order_obj.status = "packing"
                    order_obj.save()

                    # Update Inventory
                    order_lines = order_obj.lines.all()
                    for order_line in order_lines:
                        product = order_line.product
                        baseProduct_slug = str(product.city.city_name) + "-Egg-" + product.name[:2]
                        baseProduct = BaseProduct.objects.filter(slug=baseProduct_slug).first()
                        if baseProduct:
                            # TODO Filter according to warehouse
                            inventory_statuses = ['in packing', 'packed']
                            if order_obj.salesPerson:
                                warehouse = order_obj.salesPerson.warehouse
                            else:
                                warehouse = order_obj.warehouse
                            inventories = Inventory.objects.filter(warehouse=warehouse,
                                                                   baseProduct=baseProduct,
                                                                   inventory_status__in=inventory_statuses)
                            print(inventories)
                            for inventory in inventories:
                                print(inventory)
                                if inventory.inventory_status == inventory_statuses[0]:
                                    inventory.quantity = inventory.quantity - (
                                            order_line.product.SKU_Count * order_line.quantity)
                                    inventory.branded_quantity = inventory.branded_quantity - (
                                            order_line.product.SKU_Count * order_line.quantity)
                                    inventory.save()
                                if inventory.inventory_status == inventory_statuses[1]:
                                    inventory.quantity = inventory.quantity + (
                                            order_line.product.SKU_Count * order_line.quantity)
                                    inventory.branded_quantity = inventory.branded_quantity + (
                                            order_line.product.SKU_Count * order_line.quantity)
                                    inventory.save()

                return Response({})
            else:
                return Forbidden({'error_type': "Internal Error",
                                  'errors': [{'message': "Warehouse Person profile not found"}]})
        else:
            return Forbidden({'error_type': "permission_denied",
                              'errors': [{'message': "You do not have permission to perform this action."}]})


class PurchaseOrderViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin,
                           mixins.CreateModelMixin):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = PurchaseOrderCreateSerializer
    pagination_class = PaginationWithNoLimit
    queryset = PurchaseOrder.objects.all().order_by('delivery_date')
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = (
    'retailer', 'secondary_status', 'distributor', 'order_type', 'salesPerson', 'status', 'warehouse', 'delivery_date',
    'date',
    'customer')

    @decorators.action(detail=False, methods=['post'], url_path="po_create")
    def po_create(self, request, *args, **kwargs):
        data = request.data
        user = request.user
        print(data)

        # orderResponse = {"orders": {}, "returns":{}}
        orderResponse = {}
        sales_profile = UserProfile.objects.filter(user=request.user, department__name__in=['Sales']).first()

        if sales_profile:
            # TODO Returns / Replacements Amount into current bill
            po_create_serializer = PurchaseOrderCreateSerializer(data=data)
            po_create_serializer.is_valid(raise_exception=True)
            delivery_date = datetime.strptime(data.get('delivery_date'), "%d-%m-%Y %H:%M:%S")
            delivery_date = CURRENT_ZONE.localize(delivery_date)
            print(delivery_date)
            date = datetime.strptime(data.get('date'), "%d-%m-%Y %H:%M:%S")
            date = CURRENT_ZONE.localize(date)
            print(delivery_date)
            print(date)
            cart_products = data.get('cart_products', [])
            if cart_products:
                print(cart_products)
                cart_products = json.loads(cart_products)
                order_line_serializer = OrderLineSerializer(data=cart_products, many=True)
                order_line_serializer.is_valid(raise_exception=True)

                orderRetailer = Retailer.objects.get(id=int(data.get('retailer')))
                is_trial = False
                if orderRetailer.code == "T1001* Trial" or orderRetailer.code == "D2670* Paul Trial":
                    is_trial = True
                # Creating Order Obj
                orders = Order.objects.all()
                # might be possible model has no records so make sure to handle None
                order_max_id = orders.aggregate(Max('id'))['id__max'] + 1 if orders else 1
                retailer_order_max_id = Order.objects.filter(retailer=data.get('retailer')).count()
                max_retailer_id = retailer_order_max_id + 1
                code = data.get('retailerCode', "T1234*")
                bill_no = data.get('bill_no', "")
                max_retailer_str = str(max_retailer_id)
                salesPersonProfile = SalesPersonProfile.objects.filter(user=request.user).first()
                if '*' in str(code):
                    bill_name = code[:str(code).index('*')] + "-S" + str(salesPersonProfile.id) + "-" + str(
                        order_max_id)
                    order_id = code[:str(code).index('*')] + "-" + max_retailer_str
                else:
                    bill_name = code[:5] + "-S" + str(salesPersonProfile.id) + "-" + str(order_max_id)
                    order_id = code[:5] + "-" + max_retailer_str

                order_obj = po_create_serializer.save(orderId=order_id, name=bill_name, bill_no=bill_no,
                                                      salesPerson=salesPersonProfile, po_status="Open",
                                                      order_type="Purchase Order", purchase_id=bill_no,
                                                      delivery_date=delivery_date, is_trial=is_trial,
                                                      status="open_po",
                                                      date=date)

                # Saving Order Lines
                order_line_serializer.save(order=order_obj)

                orderResponse["orders"] = PurchaseOrderHistorySerializer(order_obj).data

                return Response(orderResponse, status=status.HTTP_201_CREATED)
            else:
                return BadRequest({'error_type': "Validation Error",
                                   'errors': [{'message': "Cart can not be empty"}]})

        else:
            return Forbidden({'error_type': "permission_denied",
                              'errors': [{'message': "You do not have permission to perform this action."}]})

    @decorators.action(detail=False, methods=['get'], url_path="po_list")
    def po_list(self, request, *args, **kwargs):
        data = request.data
        user = request.user
        print(data)
        sales_profile = UserProfile.objects.filter(user=request.user, department__name__in=['Sales']).first()

        if sales_profile:
            salesPersonProfile = SalesPersonProfile.objects.filter(user=request.user).first()
            orders = PurchaseOrder.objects.filter(salesPerson=salesPersonProfile)
            results = PurchaseOrderHistorySerializer(orders, many=True).data
            return Response({"results": results}, status=status.HTTP_201_CREATED)
        else:
            return BadRequest({'error_type': "Validation Error",
                               'errors': [{'message': "Not authorised"}]})

    @decorators.action(detail=False, methods=['post'], url_path="close_po")
    def close_po(self, request, *args, **kwargs):
        data = request.data
        user = request.user
        print(data)
        sales_profile = UserProfile.objects.filter(user=request.user, department__name__in=['Sales']).first()

        if sales_profile:
            salesPersonProfile = SalesPersonProfile.objects.filter(user=request.user).first()
            po = PurchaseOrder.objects.filter(id=data.get('po_id')).first()
            if po and po.po_status == "Open":
                po.status = "closed_po"
                po.po_status = "Closed"
                po.save()
                return Response({}, status=status.HTTP_201_CREATED)
            else:
                return BadRequest({'error_type': "Validation Error",
                                   'errors': [{'message': "Not authorised"}]})

        else:
            return BadRequest({'error_type': "Validation Error",
                               'errors': [{'message': "Not authorised"}]})


class OrderViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = OrderHistorySerializer
    pagination_class = PaginationWithNoLimit
    queryset = Order.objects.all().order_by('delivery_date')
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ('retailer', 'secondary_status', 'distributor', 'order_type', 'salesPerson', 'status',
                        'warehouse', 'delivery_date', 'date', 'order_brand_type',
                        'financePerson', 'customer')

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        data_limit = request.GET.get('limit', 'false')
        if data_limit == 'true':
            queryset = queryset.filter(
                pk__in=list(queryset.values_list('id', flat=True)[:int(request.GET.get('limit_by', 100))]))

        no_retailer = self.request.GET.get('no_retailer', False)
        if no_retailer == 'true':
            queryset = self.filter_queryset(self.get_queryset()).filter(Q(retailer=None), ~Q(order_type="Customer"))
            # query_set = queryset.filter(~Q(order_type="Customer"))
        sales_order = self.request.GET.get('sales_order', False)
        if sales_order == 'true':
            order_days = self.request.GET.get('order_days', 60)
            time_difference = datetime.now(tz=CURRENT_ZONE) - timedelta(days=int(order_days))
            queryset = queryset.filter(delivery_date__gte=time_difference)
        clusters = request.GET.get('clusters', [])
        if clusters and clusters != "undefined":
            clusters = [int(c) for c in clusters.split(",")]
            if len(clusters) > 0:
                queryset = self.filter_queryset(self.get_queryset()).filter(retailer__cluster__in=clusters)

        # page = self.paginate_queryset(queryset)
        # if page is not None:
        #     serializer = self.get_serializer(page, many=True)
        #     print(serializer.data)
        #     return self.get_paginated_response(serializer.data)
        from_date = None
        to_date = None
        statuses = request.GET.get('statuses', [])
        print(queryset)
        print(statuses)
        if statuses and statuses != "undefined":
            statuses = json.loads(statuses)
            status_list = []
            for st in statuses:
                status_list.append(st)
            print(status_list)
            queryset = queryset.filter(status__in=status_list)
        today_order = request.GET.get('today_order', 'false')
        if today_order == 'true':
            dt = datetime.now()
            start = dt.replace(hour=0, minute=0, second=0, microsecond=0)
            end = dt.replace(hour=23, minute=59, second=59, microsecond=999999)
            queryset = queryset.filter(delivery_date__range=(start, end))
        if queryset.first() and queryset.first().delivery_date:
            from_date = queryset.first().delivery_date
        if queryset.last() and queryset.last().delivery_date:
            to_date = queryset.last().delivery_date
        serializer = self.get_serializer(queryset, many=True)
        return Response({"from_date": from_date, "to_date": to_date, "results": serializer.data})

    @decorators.action(detail=False, methods=['get'], url_path="action_list")
    def action_list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        returnQueryset = self.filter_queryset(self.get_queryset())
        if request.GET.get('from_date') and request.GET.get('to_date'):
            from_date = datetime.strptime(request.GET.get('from_date'), '%d/%m/%Y')
            to_date = datetime.strptime(request.GET.get('to_date'), '%d/%m/%Y')

            from_date = from_date.replace(hour=0, minute=0, second=0)
            to_date = to_date.replace(hour=0, minute=0, second=0)

            delta = timedelta(hours=23, minutes=59, seconds=59)
            from_date = from_date
            to_date = to_date + delta
            print(from_date)
            print(to_date)

            statuses = request.GET.get('statuses', [])
            if statuses and statuses != "undefined":
                statuses = json.loads(statuses)
                status_list = []
                for st in statuses:
                    status_list.append(st)
                queryset = queryset.filter(status__in=status_list, delivery_date__range=(from_date, to_date))
            else:
                queryset = queryset.filter(delivery_date__range=(from_date, to_date))
            returned_bills = []
            colelction_ids = []
            paymentResponse = {"payment": []}
            for order in queryset:
                if order.returned_bill:
                    returned_bills.append(order.returned_bill.id)
                if order.pending_transaction > 0:
                    colelction_ids.append(order.pending_transaction)

            returnQueryset = returnQueryset.filter(return_picked_date__range=(from_date, to_date), status="completed")
            returnQueryset = returnQueryset.filter(~Q(id__in=returned_bills))
            # serializer = self.get_serializer(queryset, many=True)
            serializer = ReturnOrderHistorySerializer(queryset, many=True)
            # retrunSerializer = self.get_serializer(returnQueryset, many=True)
            retrunSerializer = ReturnOrderHistorySerializer(returnQueryset, many=True)
            if request.GET.get('distributor'):
                salesTransactions = SalesTransaction.objects.filter(distributor=request.GET.get('distributor'),
                                                                    transaction_type="Credit",
                                                                    transaction_date__range=(from_date, to_date))
            else:
                salesTransactions = SalesTransaction.objects.filter(salesPerson=request.GET.get('salesPerson'),
                                                                    transaction_type="Credit",
                                                                    transaction_date__range=(from_date, to_date))
            salesTransactions = salesTransactions.filter(~Q(id__in=colelction_ids))
            # for salesTransaction in salesTransactions:
            #     payments = salesTransaction.paymentTransactions.all()
            #     paymentResponse["payment"].append(PaymentSerializer(payments, many=True).data)
            salesTransactionSerializer = SalesTransactionShortSerializer(salesTransactions, many=True)
            return Response({"from_date": from_date, "to_date": to_date, "results": serializer.data,
                             "returns": retrunSerializer.data, "collections": salesTransactionSerializer.data})
        else:
            return BadRequest({'error_type': "Validation Error",
                               'errors': [{'message': "dates are invalid"}]})

    @decorators.action(detail=False, methods=['post'], url_path="order_update")
    def order_update(self, request, *args, **kwargs):
        if request.data.get('status') and request.data.get('id'):
            warehouse_obj = None
            if request.data.get('status') == "confirmed":
                warehouse_id = request.data.get('warehouse_id', None)
                if warehouse_id:
                    warehouse = Warehouse.objects.filter(id=warehouse_id).first()
                    if warehouse:
                        warehouse_obj = warehouse
                    else:
                        return BadRequest({'error_type': "Validation Error",
                                           'errors': [{'message': "warehouse id is invalid"}]})
                else:
                    return BadRequest({'error_type': "Validation Error",
                                       'errors': [{'message': "please provide warehouse_id"}]})
            instance = get_object_or_404(self.get_queryset(), pk=request.data.get('id'))
            serializer = self.get_serializer(instance, data=request.data)
            serializer.is_valid(raise_exception=True)
            instance.status = request.data.get('status')
            if warehouse_obj:
                instance.warehouse = warehouse_obj
            instance.save()
            return Response({})
        else:
            return BadRequest({'error_type': "Validation Error",
                               'errors': [{'message': "please provide status and id"}]})

    @decorators.action(detail=False, methods=['put'], url_path="edit_order")
    def order_edit(self, request, *args, **kwargs):
        data = request.data
        if data.get('id'):
            instance = get_object_or_404(self.get_queryset(), pk=data.get('id'))
            print(data)
            order_update_serializer = OrderUpdateSerializer(data=data)
            order_update_serializer.is_valid(raise_exception=True)
            order_update_serializer.order_update(instance=instance, data=data)
            order_within_status = ['on the way']
            if instance.status in order_within_status:
                instance.status = 'revised'
                instance.save()

            return Response({})
        else:
            return BadRequest({'error_type': "Validation Error",
                               'errors': [{'message': "please provide id"}]})

    @decorators.action(detail=False, methods=['post'], url_path="request_cancel")
    def request_cancel(self, request, *args, **kwargs):
        data = request.data
        if data.get('id'):
            instance = get_object_or_404(self.get_queryset(), pk=data.get('id'))
            # instance.secondary_status="cancel_requested"
            # instance.save()
            if instance.secondary_status == "created":
                invoice_obj = Invoice.objects.filter(order=instance).first()
                debit_amount = decimal.Decimal(0.000)
                return_amount = decimal.Decimal(0.000)
                paid_amount = decimal.Decimal(0.000)
                print(invoice_obj)
                if invoice_obj:
                    instance_debit_transaction = SalesTransaction.objects.filter(invoices__id=invoice_obj.id,
                                                                                 transaction_type__in=["Debit"])
                    if instance_debit_transaction:
                        print(instance_debit_transaction)
                        instance_debit_transaction = instance_debit_transaction.first()

                        instance_debit_transaction.transaction_type = "Cancelled"
                        debit_amount = instance_debit_transaction.transaction_amount
                        instance_debit_transaction.save()

                    if instance.returned_bill:
                        returned_deviated_amount = decimal.Decimal(0.000)
                        returned_order = instance.returned_bill
                        returned_bill_order_lines = returned_order.lines.all()
                        for returned_bill_order_line in returned_bill_order_lines:
                            if returned_bill_order_line.lines.filter():
                                returned_lines = returned_bill_order_line.lines.all()
                                for returned_line in returned_lines:
                                    returned_line.line_type = "Cancelled"
                                    returned_line.save()
                                    returned_deviated_amount -= returned_line.amount
                            returned_bill_order_line.deviated_quantity = 0
                            returned_bill_order_line.deviated_amount = 0.000
                            returned_bill_order_line.save()

                        returned_order.deviated_amount = 0.000
                        returned_order.secondary_status = "created"
                        returned_order.status = "delivered"
                        returned_order.save()

                        if int(returned_order.refund_transaction) > 0:
                            sales_transaction_obj = SalesTransaction.objects.filter(
                                id=int(returned_order.refund_transaction)).first()
                            sales_transaction_obj.transaction_type = "Cancelled"
                            return_amount += sales_transaction_obj.transaction_amount
                            sales_transaction_obj.save()
                            # TODO refunded amount in invoice

                    if instance.pending_transaction > 0:
                        sales_transaction_obj = SalesTransaction.objects.filter(
                            id=instance.pending_transaction).first()
                        sales_transaction_obj.transaction_type = "Cancelled"
                        paid_amount += sales_transaction_obj.transaction_amount
                        payments = Payment.objects.filter(salesTransaction=sales_transaction_obj)
                        for payment in payments:
                            payment.invoice.invoice_due += payment.pay_amount
                            payment.invoice.invoice_status = "Pending"
                            payment.invoice.save()
                        sales_transaction_obj.save()

                    instance.retailer.amount_due = instance.retailer.amount_due - debit_amount + return_amount + paid_amount
                    instance.retailer.save()
                    instance.secondary_status = "cancel_approved"
                    instance.status = "cancelled"
                    invoice_obj.invoice_status = "Cancelled"
                    # invoice_obj.invoice_due = 0.000
                    invoice_obj.save()
                    instance.save()

                    if instance.beat_assignment and instance.order_brand_type == "branded":
                        if int(instance.retailer.id) == 1386 or int(instance.retailer.id) == 1612:
                            pass
                        else:
                            beat_assignment = instance.beat_assignment
                            order_lines = instance.lines.all()
                            for order_line in order_lines:
                                salesDemand = SalesDemandSKU.objects.get(beatAssignment=beat_assignment,
                                                                         product=order_line.product)
                                salesDemand.product_sold_quantity -= int(order_line.quantity)
                                salesDemand.save()

                            if RetailerDemand.objects.filter(beatAssignment=beat_assignment,
                                                             retailer=instance.retailer):
                                retailerDemand = RetailerDemand.objects.get(beatAssignment=beat_assignment,
                                                                            retailer=instance.retailer)
                                retailerDemand.retailer_status = "Cancelled"
                                retailerDemand.save()
                            else:
                                retailerDemand = RetailerDemand.objects.create(beatAssignment=beat_assignment,
                                                                               retailer_status="Cancelled",
                                                                               date=datetime.now().date(),
                                                                               time=datetime.now().time(),
                                                                               retailer=instance.retailer)

                    # eggs_sort_date = instance.delivery_date
                    # orders_list_dict = {'Brown': 0, 'White': 0, 'Nutra': 0}
                    # order_lines = instance.lines.all()
                    # for order_line in order_lines:
                    #     # For Eggs Data
                    #     if order_line.product:
                    #         if order_line.product.name == "White Regular":
                    #             name = "White"
                    #         else:
                    #             name = order_line.product.name
                    #         if orders_list_dict[name] > 0:
                    #             orders_list_dict[name] = orders_list_dict[name] + order_line.quantity * order_line.product.SKU_Count
                    #         else:
                    #             orders_list_dict[name] = order_line.quantity * order_line.product.SKU_Count
                    # brown_eggs = orders_list_dict['Brown']
                    # white_eggs = orders_list_dict['White']
                    # nutra_eggs = orders_list_dict['Nutra']
                    # if instance.distributor:
                    #     distributionEggsdata = DistributionEggsdata.objects.filter(date=eggs_sort_date,
                    #                                                                distributionPerson=instance.distributor).first()
                    #     if distributionEggsdata:
                    #         distributionEggsdata.brown -= brown_eggs
                    #         distributionEggsdata.white -= white_eggs
                    #         distributionEggsdata.nutra -= nutra_eggs
                    #         distributionEggsdata.save()
                    # else:
                    #     salesEggdata = SalesEggsdata.objects.filter(date=eggs_sort_date,
                    #                                                 salesPerson=instance.salesPerson).first()
                    #     if salesEggdata:
                    #         salesEggdata.brown -= brown_eggs
                    #         salesEggdata.white -= white_eggs
                    #         salesEggdata.nutra -= nutra_eggs
                    #         salesEggdata.save()
                    #
                    # retailerEggdata = RetailerEggsdata.objects.filter(date=eggs_sort_date,
                    #                                                   retailer=instance.retailer).first()
                    # if retailerEggdata:
                    #     retailerEggdata.brown -= brown_eggs
                    #     retailerEggdata.white -= white_eggs
                    #     retailerEggdata.nutra -= nutra_eggs
                    #     retailerEggdata.save()
            else:
                return BadRequest({'error_type': "Validation Error",
                                   'errors': [{'message': "Not enough access, please inform it to your manager"}]})

            return Response({"Cancelled Successfully"})

        elif data.get('return_id'):
            instance = get_object_or_404(self.get_queryset(), pk=data.get('return_id'))
            if instance.status == "completed":
                order_lines = instance.lines.all()
                for order_line in order_lines:
                    return_lines = order_line.lines.all()
                    for return_line in return_lines:
                        print(return_line.id)
            return Response({"Cancelled Successfully"})

        elif data.get('transaction_id'):
            sales_transaction = SalesTransaction.objects.filter(id=data.get('transaction_id'))
            if sales_transaction:
                sales_transaction = sales_transaction.first()
                sales_transaction.retailer.amount_due = decimal.Decimal(
                    sales_transaction.retailer.amount_due) + decimal.Decimal(
                    sales_transaction.transaction_amount)
                sales_transaction.retailer.save()
                sales_transaction.current_balance = sales_transaction.retailer.amount_due
                payments = Payment.objects.filter(salesTransaction=sales_transaction)
                for payment in payments:
                    payment.invoice.invoice_due += payment.pay_amount
                    if sales_transaction.transaction_type == "Debit":
                        payment.invoice.invoice_status = "Cancelled"
                    else:
                        payment.invoice.invoice_status = "Pending"
                    payment.invoice.save()
                sales_transaction.transaction_type = "Cancelled"
                sales_transaction.save()

            return Response({"Cancelled Successfully"})
        else:
            return BadRequest({'error_type': "Validation Error",
                               'errors': [{'message': "please provide id"}]})

    @decorators.action(detail=False, methods=['post'], url_path="request_print")
    def request_print(self, request, *args, **kwargs):
        data = request.data
        if data.get('id'):
            orderResponse = {}
            instance = get_object_or_404(self.get_queryset(), pk=data.get('id'))
            orderResponse["orders"] = OrderHistorySerializer(instance).data
            if instance.returned_bill:
                orderResponse["returns"] = ReturnOrderHistorySerializer(instance.returned_bill).data
            if instance.pending_transaction > 0:
                sales_transaction_obj = SalesTransaction.objects.filter(
                    id=instance.pending_transaction).first()
                payments = Payment.objects.filter(salesTransaction_id=instance.pending_transaction)
                orderResponse["sales_transaction"] = SalesTransactionShortSerializer(sales_transaction_obj).data
                if payments:
                    orderResponse["payment"] = PaymentSerializer(payments, many=True).data
            return Response(orderResponse, status=status.HTTP_201_CREATED)
        else:
            return BadRequest({'error_type': "Validation Error",
                               'errors': [{'message': "please provide id"}]})

    @decorators.action(detail=False, methods=['post'], url_path="confirm_cancel")
    def confirm_cancel(self, request, *args, **kwargs):
        data = request.data
        orders = request.GET.get('order_ids', [])
        if orders and orders != "undefined":
            orders = json.loads(orders)
            orders = [int(c) for c in orders]
            if len(orders) > 0:
                for order in orders:
                    print(order)
                    instance = get_object_or_404(Order, pk=int(order))
                    if instance.secondary_status == "cancel_requested":
                        invoice_obj = Invoice.objects.filter(order=instance).first()
                        debit_amount = decimal.Decimal(0.000)
                        return_amount = decimal.Decimal(0.000)
                        paid_amount = decimal.Decimal(0.000)
                        print(invoice_obj)
                        if invoice_obj:
                            instance_debit_transaction = SalesTransaction.objects.filter(invoices__id=invoice_obj.id,
                                                                                         transaction_type="Debit").first()
                            print(instance_debit_transaction)
                            instance_debit_transaction.transaction_type = "Cancelled"
                            debit_amount = instance_debit_transaction.transaction_amount
                            instance_debit_transaction.save()
                            # refund_amount = instance.order_price_amount - invoice_obj.invoice_due
                            if instance.returned_bill:
                                returned_deviated_amount = decimal.Decimal(0.000)
                                returned_order = instance.returned_bill
                                returned_order_lines = returned_order.lines.all()
                                for returned_order_line in returned_order_lines:
                                    if returned_order_line.lines.all():
                                        returned_lines = returned_order_line.lines.all()
                                        for returned_line in returned_lines:
                                            returned_line.line_type = "Cancelled"
                                            returned_line.save()
                                            returned_deviated_amount += returned_line.amount
                                    returned_order_line.deviated_quantity = 0
                                    returned_order_line.deviated_amount = 0.000
                                    returned_order_line.save()
                                # TODO revert salesTransaction of return/replacement
                                returned_order.deviated_amount = 0.000
                                returned_order.secondary_status = "created"
                                returned_order.status = "delivered"
                                returned_order.save()
                                if int(returned_order.refund_transaction) > 0:
                                    sales_transaction_obj = SalesTransaction.objects.filter(
                                        id=int(returned_order.refund_transaction)).first()
                                    sales_transaction_obj.transaction_type = "Cancelled"
                                    return_amount += sales_transaction_obj.transaction_amount
                                    sales_transaction_obj.save()

                            if instance.pending_transaction > 0:
                                sales_transaction_obj = SalesTransaction.objects.filter(
                                    id=instance.pending_transaction).first()
                                sales_transaction_obj.transaction_type = "Cancelled"
                                paid_amount += sales_transaction_obj.transaction_amount
                                payments = Payment.objects.filter(salesTransaction=sales_transaction_obj)
                                for payment in payments:
                                    payment.invoice.invoice_due += payment.pay_amount
                                    payment.invoice.invoice_status = "Pending"
                                    payment.invoice.save()
                                sales_transaction_obj.save()

                            instance.retailer.amount_due = instance.retailer.amount_due - debit_amount + return_amount + paid_amount
                            instance.retailer.save()
                            instance.secondary_status = "cancel_approved"
                            instance.status = "cancelled"
                            invoice_obj.invoice_status = "Cancelled"
                            # invoice_obj.invoice_due = 0.000
                            invoice_obj.save()
                            instance.save()

                            # eggs_sort_date = instance.delivery_date
                            # orders_list_dict = {'Brown': 0, 'White': 0, 'Nutra': 0}
                            # order_lines = instance.lines.all()
                            # for order_line in order_lines:
                            #     # For Eggs Data
                            #     if order_line.product:
                            #         if orders_list_dict[str(order_line.product.name)] > 0:
                            #             orders_list_dict[str(order_line.product.name)] = orders_list_dict[
                            #                                                                  order_line.product.name] \
                            #                                                              + order_line.quantity * order_line.product.SKU_Count
                            #         else:
                            #             orders_list_dict[
                            #                 str(order_line.product.name)] = order_line.quantity * order_line.product.SKU_Count
                            # brown_eggs = orders_list_dict['Brown']
                            # white_eggs = orders_list_dict['White']
                            # nutra_eggs = orders_list_dict['Nutra']
                            # if instance.distributor:
                            #     distributionEggsdata = DistributionEggsdata.objects.filter(date=eggs_sort_date,
                            #                                                                distributionPerson=instance.distributor).first()
                            #     if distributionEggsdata:
                            #         distributionEggsdata.brown -= brown_eggs
                            #         distributionEggsdata.white -= white_eggs
                            #         distributionEggsdata.nutra -= nutra_eggs
                            #         distributionEggsdata.save()
                            # else:
                            #     salesEggdata = SalesEggsdata.objects.filter(date=eggs_sort_date,
                            #                                                 salesPerson=instance.salesPerson).first()
                            #     if salesEggdata:
                            #         salesEggdata.brown -= brown_eggs
                            #         salesEggdata.white -= white_eggs
                            #         salesEggdata.nutra -= nutra_eggs
                            #         salesEggdata.save()
                            #
                            # retailerEggdata = RetailerEggsdata.objects.filter(date=eggs_sort_date,
                            #                                                   retailer=instance.retailer).first()
                            # if retailerEggdata:
                            #     retailerEggdata.brown -= brown_eggs
                            #     retailerEggdata.white -= white_eggs
                            #     retailerEggdata.nutra -= nutra_eggs
                            #     retailerEggdata.save()


                    else:
                        return BadRequest({'error_type': "Validation Error",
                                           'errors': [{'message': "Can not be cancelled"}]})
                return Response({})
            else:
                return BadRequest({'error_type': "Validation Error",
                                   'errors': [{'message': "please provide id"}]})
        else:
            return BadRequest({'error_type': "Validation Error",
                               'errors': [{'message': "please provide ids"}]})

    @decorators.action(detail=False, methods=['post'], url_path="order_return")
    def order_return(self, request, *args, **kwargs):
        data = request.data
        print(data)
        if data.get('id'):
            orderResponse = {}
            instance = get_object_or_404(self.get_queryset(), pk=data.get('id'))
            order_return_serializer = OrderReturnReplacementSerializer(data=data)
            order_return_serializer.is_valid(raise_exception=True)
            order_return_serializer.order_return(instance, data)
            orderResponse["returns"] = OrderHistorySerializer(instance).data
            return Created(orderResponse)
        else:
            return BadRequest({'error_type': "Validation Error",
                               'errors': [{'message': "please provide id"}]})

    @decorators.action(detail=False, methods=['post'], url_path="return_order_picked")
    def order_return_picked(self, request, *args, **kwargs):
        data = request.data
        print(data)
        if data.get('id'):
            instance = get_object_or_404(self.get_queryset(), pk=data.get('id'))
            order_return_serializer = OrderReturnPickupSerializer(data=data)
            order_return_serializer.is_valid(raise_exception=True)
            order_return_serializer.order_pickup(instance, data)
            instance.return_picked_date = datetime.now(tz=CURRENT_ZONE)
            instance.save()
            return Created({})
        else:
            return BadRequest({'error_type': "Validation Error",
                               'errors': [{'message': "please provide id"}]})

    @decorators.action(detail=False, methods=['post'], url_path="return_order_replace")
    def order_return_replace(self, request, *args, **kwargs):
        data = request.data
        user = request.user
        print(data)
        if data.get('id'):
            instance = get_object_or_404(self.get_queryset(), pk=data.get('id'))
            order_return_serializer = OrderReturnSerializer(data=data)
            order_return_serializer.is_valid(raise_exception=True)
            order_return_serializer.order_return_replace(instance, data, user, False)
            instance.return_picked_date = datetime.now(tz=CURRENT_ZONE)
            instance.save()

            return Created({})
        else:
            return BadRequest({'error_type': "Validation Error",
                               'errors': [{'message': "please provide id"}]})

    @decorators.action(detail=False, methods=['post'], url_path="confirm_delivery")
    def confirm_delivery(self, request, *args, **kwargs):
        data = request.data
        print(data)

        orders = request.GET.get('orders', [])
        if orders and orders != "undefined":
            orders = json.loads(orders)
            orders = [int(c) for c in orders]
            if len(orders) > 0:
                for order in orders:
                    instance = get_object_or_404(Order, pk=order)
                    invoice_data = {"request": self.request, "order_ids": [instance.id]}
                    generate_invoice(invoice_data, 0.000)
                    # Make Debit Transaction
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
                                                                        transaction_amount=instance.order_price_amount)
                    sales_transaction.retailer.amount_due = decimal.Decimal(
                        sales_transaction.retailer.amount_due) + decimal.Decimal(sales_transaction.transaction_amount)
                    sales_transaction.retailer.save()
                    sales_transaction.current_balance = sales_transaction.retailer.amount_due
                    invoice_obj = Invoice.objects.filter(order=instance).first()
                    if invoice_obj:
                        sales_transaction.invoices.add(invoice_obj)
                    sales_transaction.save()
                    instance.status = "delivered"
                    instance.save()

                    # Update Inventory & EGGS DATA FOR SALES & RETAILER
                    orders_list_dict = {'Brown': 0, 'White': 0, 'Nutra': 0}
                    eggs_sort_date = datetime.now(tz=CURRENT_ZONE)
                    order_lines = instance.lines.all()
                    for order_line in order_lines:
                        # For Eggs Data

                        if order_line.product:
                            if orders_list_dict[str(order_line.product.name)] > 0:
                                orders_list_dict[str(order_line.product.name)] = orders_list_dict[
                                                                                     order_line.product.name] \
                                                                                 + order_line.quantity * order_line.product.SKU_Count
                            else:
                                orders_list_dict[
                                    str(order_line.product.name)] = order_line.quantity * order_line.product.SKU_Count

                        # For Inventory
                        product = order_line.product
                        baseProduct_slug = str(product.city.city_name) + "-Egg-" + product.name[:2]
                        baseProduct = BaseProduct.objects.filter(slug=baseProduct_slug).first()
                        if baseProduct:
                            inventory_statuses = ['in transit', 'delivered']
                            if instance.salesPerson:
                                warehouse = instance.salesPerson.warehouse
                            else:
                                warehouse = instance.warehouse
                            inventories = Inventory.objects.filter(warehouse=warehouse,
                                                                   baseProduct=baseProduct,
                                                                   inventory_status__in=inventory_statuses)
                            for inventory in inventories:
                                if inventory.inventory_status == 'in transit':
                                    inventory.quantity = inventory.quantity - (
                                            order_line.product.SKU_Count * order_line.quantity)
                                    inventory.branded_quantity = inventory.branded_quantity - (
                                            order_line.product.SKU_Count * order_line.quantity)
                                    inventory.save()
                                if inventory.inventory_status == 'delivered':
                                    inventory.quantity = inventory.quantity + (
                                            order_line.product.SKU_Count * order_line.quantity)
                                    inventory.branded_quantity = inventory.branded_quantity + (
                                            order_line.product.SKU_Count * order_line.quantity)
                                    inventory.save()

                    # salesEggdata = SalesEggsdata.objects.filter(date=eggs_sort_date,
                    #                                             salesPerson=instance.retailer.salesPersonProfile).first()
                    # if salesEggdata:
                    #     salesEggdata.brown = salesEggdata.brown + orders_list_dict['Brown']
                    #     salesEggdata.white = salesEggdata.white + orders_list_dict['White']
                    #     salesEggdata.nutra = salesEggdata.nutra + orders_list_dict['Nutra']
                    #     salesEggdata.save()
                    # else:
                    #     SalesEggsdata.objects.create(date=eggs_sort_date,
                    #                                  salesPerson=instance.retailer.salesPersonProfile,
                    #                                  brown=orders_list_dict['Brown'],
                    #                                  white=orders_list_dict['White'],
                    #                                  nutra=orders_list_dict['Nutra'])
                    #
                    # retailerEggdata = RetailerEggsdata.objects.filter(date=eggs_sort_date,
                    #                                                   retailer=instance.retailer).first()
                    # if retailerEggdata:
                    #     retailerEggdata.brown = retailerEggdata.brown + orders_list_dict[
                    #         'Brown']
                    #     retailerEggdata.white = retailerEggdata.white + orders_list_dict[
                    #         'White']
                    #     retailerEggdata.nutra = retailerEggdata.nutra + orders_list_dict[
                    #         'Nutra']
                    #     retailerEggdata.save()
                    # else:
                    #     RetailerEggsdata.objects.create(date=eggs_sort_date,
                    #                                     retailer=instance.retailer,
                    #                                     brown=orders_list_dict['Brown'],
                    #                                     white=orders_list_dict['White'],
                    #                                     nutra=orders_list_dict['Nutra'])

                return Created({})

            else:
                return BadRequest({'error_type': "Validation Error",
                                   'errors': [{'message': "please provide at least one order to delivery"}]})
        else:
            return BadRequest({'error_type': "Validation Error",
                               'errors': [{'message': "please provide at least one order to delivery"}]})

    def create(self, request, *args, **kwargs):
        data = request.data
        print(data)
        user_profile = UserProfile.objects.filter(user=request.user, department__name__in=['Sales']).first()
        if user_profile:
            print(user_profile)
            order_create_serializer = OrderCreateSerializer(data=data)
            order_create_serializer.is_valid(raise_exception=True)
            delivery_date = datetime.strptime(data.get('delivery_date'), "%d-%m-%Y")
            order_type = "Retailer"
            if data.get('order_type'):
                order_type = data.get('order_type')
            cart_products = data.get('cart_products', [])
            name = data.get('name', '')
            if cart_products:
                print(cart_products)
                cart_products = json.loads(cart_products)
                for cart_product in cart_products:
                    order_line_serializer = OrderLineSerializer(data=cart_product)
                    order_line_serializer.is_valid(raise_exception=True)
                salesPersonProfile = SalesPersonProfile.objects.filter(user=request.user).first()
                orders = Order.objects.all()
                # might be possible model has no records so make sure to handle None
                order_max_id = orders.aggregate(Max('id'))['id__max'] + 1 if orders else 1
                order_id = "OD-GGN-" + str(order_max_id)
                date = datetime.now(tz=CURRENT_ZONE)
                order_obj = order_create_serializer.save(orderId=order_id, name=name, order_type=order_type,
                                                         salesPerson=salesPersonProfile,
                                                         delivery_date=delivery_date, date=date)

                order_obj.delivery_date = order_obj.delivery_date
                order_obj.save()
                if order_obj.date:
                    order_obj.date = order_obj.date
                    order_obj.save()

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
                    order_obj.retailer.last_order_date = datetime.now(tz=pytz.timezone("Asia/Kolkata"))
                    order_obj.retailer.save()
                else:
                    pass

                # Update Inventory
                order_lines = order_obj.lines.all()
                for order_line in order_lines:
                    product = order_line.product
                    baseProduct_slug = str(product.city.city_name) + "-Egg-" + product.name[:2]
                    baseProduct = BaseProduct.objects.filter(slug=baseProduct_slug).first()
                    if baseProduct:
                        # TODO Filter according to warehouse
                        inventory_statuses = ['available', 'in packing']
                        if order_obj.salesPerson:
                            warehouse = order_obj.salesPerson.warehouse
                        else:
                            warehouse = order_obj.warehouse
                        inventories = Inventory.objects.filter(warehouse=warehouse,
                                                               baseProduct=baseProduct,
                                                               inventory_status__in=inventory_statuses)
                        for inventory in inventories:
                            if inventory.inventory_status == 'available':
                                inventory.quantity = inventory.quantity - (
                                        order_line.product.SKU_Count * order_line.quantity)
                                inventory.branded_quantity = inventory.branded_quantity - (
                                        order_line.product.SKU_Count * order_line.quantity)
                                if inventory.quantity < 0:
                                    inventory.quantity = 0
                                if inventory.branded_quantity < 0:
                                    inventory.branded_quantity = 0
                                inventory.save()
                            if inventory.inventory_status == 'in packing':
                                inventory.quantity = inventory.quantity + (
                                        order_line.product.SKU_Count * order_line.quantity)
                                inventory.branded_quantity = inventory.branded_quantity + (
                                        order_line.product.SKU_Count * order_line.quantity)
                                inventory.save()

                return Response({}, status=status.HTTP_201_CREATED)
            else:
                return BadRequest({'error_type': "Validation Error",
                                   'errors': [{'message': "Cart can not be empty"}]})

        else:
            return Forbidden({'error_type': "permission_denied",
                              'errors': [{'message': "You do not have permission to perform this action."}]})

    @decorators.action(detail=False, methods=['post'], url_path="backlog_order_create")
    def backlog_order_create(self, request, *args, **kwargs):
        data = request.data
        user = request.user
        print(data)

        if data.get('beat_assignment'):
            beat_assignment = BeatAssignment.objects.get(id=data.get('beat_assignment'))

        else:
            beat_assignment = None

        order_brand_type = data.get('order_brand_type', 'branded')
        # orderResponse = {"orders": {}, "returns":{}}
        orderResponse = {}
        # beat_assignment_id = data.get('beat_assignment', 2)
        sales_profile = UserProfile.objects.filter(user=request.user, department__name__in=['Sales']).first()
        distribution_profile = UserProfile.objects.filter(user=request.user,
                                                          department__name__in=['Distribution']).first()
        finance_profile = UserProfile.objects.filter(user=request.user,
                                                     department__name__in=['Finance']).first()

        if distribution_profile or sales_profile or finance_profile:

            if data.get('delivery_date') == 'Invalid date':
                delivery_date = datetime.now()
            else:
                delivery_date = datetime.strptime(data.get('delivery_date'), "%d-%m-%Y %H:%M:%S")
            if data.get('date') == 'Invalid date':
                date = datetime.now()
            else:
                date = datetime.strptime(data.get('date'), "%d-%m-%Y %H:%M:%S")
            delivery_date = CURRENT_ZONE.localize(delivery_date)
            print(delivery_date)
            date = CURRENT_ZONE.localize(date)
            print(delivery_date)
            print(date)

            order_return_data = request.data.get('orderReturnData')
            returned_amount = 0.000
            return_order_id = 0
            return_bill_data = {}
            return_bill_ids = []
            if order_return_data == "true":
                instance = get_object_or_404(self.get_queryset(), pk=data.get('id'))
                order_return_serializer = OrderReturnSerializer(data=data)
                order_return_serializer.is_valid(raise_exception=True)
                returnData = order_return_serializer.order_return_replace(instance, data, user, True)
                instance.return_picked_date = datetime.now(tz=CURRENT_ZONE)
                instance.save()
                orderResponse["returns"] = ReturnOrderHistorySerializer(instance).data
                returned_amount = decimal.Decimal(returnData['return_extra_amount'])
                return_order_id = orderResponse["returns"]['id']
                return_bill_data = returnData['bill_data']
                return_bill_ids = returnData['bill_data']['order_ids']

            # TODO Returns / Replacements Amount into current bill
            order_create_serializer = OrderCreateSerializer(data=data)
            order_create_serializer.is_valid(raise_exception=True)

            cart_products = data.get('cart_products', [])
            if cart_products:
                print(cart_products)
                cart_products = json.loads(cart_products)
                order_line_serializer = OrderLineSerializer(data=cart_products, many=True)
                order_line_serializer.is_valid(raise_exception=True)
                orderRetailer = Retailer.objects.get(id=int(data.get('retailer')))
                if beat_assignment and order_brand_type == "branded":
                    if int(data.get('retailer')) == 1386 or int(data.get('retailer')) == 1612:
                        pass
                    else:
                        for cart_product in cart_products:
                            salesDemand = SalesDemandSKU.objects.get(beatAssignment=beat_assignment,
                                                                     product=cart_product.get('product'))
                            salesDemand.product_sold_quantity += int(cart_product.get('quantity'))
                            salesDemand.save()
                        if RetailerDemand.objects.filter(beatAssignment=beat_assignment,
                                                         retailer=int(data.get('retailer'))):
                            retailerDemand = RetailerDemand.objects.get(beatAssignment=beat_assignment,
                                                                        retailer_id=int(data.get('retailer')))
                            retailerDemand.retailer_status = "Sales Booked"
                            retailerDemand.save()
                        else:
                            retailerDemand = RetailerDemand.objects.create(beatAssignment=beat_assignment,
                                                                           retailer_status="Sales Booked",
                                                                           date=datetime.now().date(),
                                                                           time=datetime.now().time(),
                                                                           retailer_id=int(data.get('retailer')))

                is_trial = False
                if orderRetailer.code == "T1001* Trial" or orderRetailer.code == "D2670* Paul Trial":
                    is_trial = True
                # Creating Order Obj
                orders = Order.objects.all()
                # might be possible model has no records so make sure to handle None
                order_max_id = orders.aggregate(Max('id'))['id__max'] + 1 if orders else 1
                retailer_order_max_id = Order.objects.filter(retailer=data.get('retailer')).count()
                max_retailer_id = retailer_order_max_id + 1
                code = data.get('retailerCode', "T1234*")
                bill_no = data.get('bill_no', "")
                max_retailer_str = str(max_retailer_id)
                if distribution_profile:
                    distributionPersonProfile = DistributionPersonProfile.objects.filter(user=request.user).first()

                    if '*' in str(code):
                        bill_name = code[:str(code).index('*')] + "-D" + str(distributionPersonProfile.id) + "-" + str(
                            order_max_id)
                        order_id = code[:str(code).index('*')] + "-" + max_retailer_str
                    else:
                        bill_name = code[:5] + "-D" + str(distributionPersonProfile.id) + "-" + str(order_max_id)
                        order_id = code[:5] + "-" + max_retailer_str
                    order_obj = order_create_serializer.save(orderId=order_id, name=bill_name, bill_no=bill_no,
                                                             delivery_date=delivery_date,
                                                             distributor=distributionPersonProfile,
                                                             is_trial=is_trial,
                                                             date=date)
                    order_obj.salesPerson = order_obj.retailer.salesPersonProfile
                    order_obj.save()
                else:
                    if sales_profile:
                        salesPersonProfile = SalesPersonProfile.objects.filter(user=request.user).first()
                    else:
                        salesPersonProfile = orderRetailer.salesPersonProfile

                    if '*' in str(code):
                        bill_name = code[:str(code).index('*')] + "-S" + str(salesPersonProfile.id) + "-" + str(
                            order_max_id)
                        order_id = code[:str(code).index('*')] + "-" + max_retailer_str
                    else:
                        bill_name = code[:5] + "-S" + str(salesPersonProfile.id) + "-" + str(order_max_id)
                        order_id = code[:5] + "-" + max_retailer_str

                    if sales_profile:
                        salesPersonProfile = SalesPersonProfile.objects.filter(user=request.user).first()
                        order_obj = order_create_serializer.save(orderId=order_id, name=bill_name, bill_no=bill_no,
                                                                 salesPerson=salesPersonProfile,
                                                                 delivery_date=delivery_date,
                                                                 is_trial=is_trial,
                                                                 date=date)
                    else:
                        salesPersonProfile = orderRetailer.salesPersonProfile
                        financeProfile = FinanceProfile.objects.filter(user=request.user).first()
                        order_obj = order_create_serializer.save(orderId=order_id, name=bill_name, bill_no=bill_no,
                                                                 salesPerson=salesPersonProfile,
                                                                 financePerson=financeProfile,
                                                                 delivery_date=delivery_date,
                                                                 is_trial=is_trial,
                                                                 date=date)

                if int(return_order_id) > 0:
                    order_obj.returned_bill_id = return_order_id
                    order_obj.save()

                # Saving Order Lines
                order_line_serializer.save(order=order_obj)
                print(order_obj)
                print(order_obj.retailer)
                print(order_obj.retailer.last_order_date)
                order_obj.retailer.last_order_date = date
                order_obj.retailer.save()
                # Update Inventory & EGGS DATA FOR SALES & RETAILER

                eggs_sort_date = delivery_date
                orders_list_dict = {'Brown': 0, 'White': 0, 'Nutra': 0}
                order_lines = order_obj.lines.all()
                # for order_line in order_lines:
                #     product = order_line.product
                #     baseProduct_slug = str(product.city.city_name) + "-Egg-" + product.name[:2]
                #     baseProduct = BaseProduct.objects.filter(slug=baseProduct_slug).first()
                #     if baseProduct:
                #         # TODO Filter according to warehouse
                #         inventory_statuses = ['available', 'delivered']
                #         if order_obj.salesPerson:
                #             warehouse = order_obj.salesPerson.warehouse
                #         else:
                #             warehouse = order_obj.warehouse
                #         inventories = Inventory.objects.filter(warehouse=warehouse,
                #                                                baseProduct=baseProduct,
                #                                                inventory_status__in=inventory_statuses)
                #         for inventory in inventories:
                #             if inventory.inventory_status == 'available':
                #                 inventory.quantity = inventory.quantity - (
                #                         order_line.product.SKU_Count * order_line.quantity)
                #                 inventory.branded_quantity = inventory.branded_quantity - (
                #                         order_line.product.SKU_Count * order_line.quantity)
                #                 if inventory.quantity < 0:
                #                     inventory.quantity = 0
                #                 if inventory.branded_quantity < 0:
                #                     inventory.branded_quantity = 0
                #                 inventory.save()
                #             if inventory.inventory_status == 'delivered':
                #                 inventory.quantity = inventory.quantity + (
                #                         order_line.product.SKU_Count * order_line.quantity)
                #                 inventory.branded_quantity = inventory.branded_quantity + (
                #                         order_line.product.SKU_Count * order_line.quantity)
                #                 inventory.save()

                # For Eggs Data
                #     if order_line.product:
                #         if order_line.product.name == "White Regular":
                #             name = "White"
                #         else:
                #             name = str(order_line.product.name)
                #
                #         if orders_list_dict[name] > 0:
                #             orders_list_dict[name] = orders_list_dict[name] \
                #                                                              + order_line.quantity * order_line.product.SKU_Count
                #         else:
                #             orders_list_dict[
                #                 name] = order_line.quantity * order_line.product.SKU_Count
                #
                # brown_eggs = orders_list_dict['Brown']
                # white_eggs = orders_list_dict['White']
                # nutra_eggs = orders_list_dict['Nutra']
                # salesEggdata = SalesEggsdata.objects.filter(date=eggs_sort_date,
                #                                             salesPerson=order_obj.salesPerson).first()
                # if salesEggdata:
                #     salesEggdata.brown += brown_eggs
                #     salesEggdata.white += white_eggs
                #     salesEggdata.nutra += nutra_eggs
                #     salesEggdata.save()
                # else:
                #     SalesEggsdata.objects.create(date=eggs_sort_date,
                #                                  salesPerson=order_obj.salesPerson,
                #                                  brown=brown_eggs,
                #                                  white=white_eggs,
                #                                  nutra=nutra_eggs)
                #
                # retailerEggdata = RetailerEggsdata.objects.filter(date=eggs_sort_date,
                #                                                   retailer=order_obj.retailer).first()
                # if retailerEggdata:
                #     retailerEggdata.brown += brown_eggs
                #     retailerEggdata.white += white_eggs
                #     retailerEggdata.nutra += nutra_eggs
                #     retailerEggdata.save()
                # else:
                #     RetailerEggsdata.objects.create(date=eggs_sort_date,
                #                                     retailer=order_obj.retailer,
                #                                     brown=brown_eggs,
                #                                     white=white_eggs,
                #                                     nutra=nutra_eggs)
                #
                # if distribution_profile:
                #     distributionEggdata = DistributionEggsdata.objects.filter(date=eggs_sort_date,
                #                                                 distributionPerson=order_obj.distributor).first()
                #     if distributionEggdata:
                #         distributionEggdata.brown += brown_eggs
                #         distributionEggdata.white += white_eggs
                #         distributionEggdata.nutra += nutra_eggs
                #         distributionEggdata.save()
                #     else:
                #         DistributionEggsdata.objects.create(date=eggs_sort_date,
                #                                      distributionPerson=order_obj.distributor,
                #                                      brown=brown_eggs,
                #                                      white=white_eggs,
                #                                      nutra=nutra_eggs)

                invoice_data = {"request": self.request, "order_ids": [order_obj.id]}
                # generate_invoice(invoice_data, returned_amount)

                debit_note_amount = decimal.Decimal(0.000)
                invoices = Invoice.objects.all()
                # might be possible model has no records so make sure to handle None
                invoice_max_id = invoices.aggregate(Max('id'))['id__max'] + 1 if invoices else 1
                invoice_id = "E" + str(invoice_max_id)
                # invoice_due = order.order_price_amount + order.retailer.amount_due
                if int(order_obj.order_price_amount) > int(decimal.Decimal(returned_amount)):
                    invoice_due = order_obj.order_price_amount - decimal.Decimal(returned_amount)
                    invoice_status = "Pending"
                else:
                    debit_note_amount = decimal.Decimal(returned_amount) - order_obj.order_price_amount
                    invoice_due = decimal.Decimal(0.000)
                    invoice_status = "Paid"

                # TODO Validte for negative due

                invoice = Invoice.objects.create(order=order_obj, invoice_id=invoice_id,
                                                 created_at=order_obj.delivery_date,
                                                 invoice_due=invoice_due, invoice_status=invoice_status)
                # create_invoice.delay(order_obj.id, request.build_absolute_uri())
                if int(returned_amount) > 0:
                    return_bill_ids.append(invoice.order.name)
                    return_bill_data["order_ids"] = return_bill_ids

                # Make Debit Transaction
                transactions = SalesTransaction.objects.all()
                # might be possible model has no records so make sure to handle None
                transaction_max_id = transactions.aggregate(Max('id'))['id__max'] + 1 if transactions else 1
                transaction_id = "TR" + str(transaction_max_id)
                transaction_date = delivery_date
                sales_transaction = SalesTransaction.objects.create(retailer=order_obj.retailer,
                                                                    transaction_id=transaction_id,
                                                                    transaction_type="Debit",
                                                                    salesPerson=order_obj.salesPerson if order_obj.salesPerson else None,
                                                                    distributor=order_obj.distributor if order_obj.distributor else None,
                                                                    financePerson=order_obj.financePerson if order_obj.financePerson else None,
                                                                    transaction_date=transaction_date,
                                                                    beat_assignment=beat_assignment,
                                                                    is_trial=is_trial,
                                                                    transaction_amount=order_obj.order_price_amount)
                sales_transaction.retailer.amount_due = decimal.Decimal(
                    sales_transaction.retailer.amount_due) + decimal.Decimal(sales_transaction.transaction_amount)
                sales_transaction.retailer.save()
                sales_transaction.current_balance = sales_transaction.retailer.amount_due

                sales_transaction.invoices.add(invoice)
                sales_transaction.save()
                if int(debit_note_amount) > 0:
                    return_bill_ids.append(invoice.order.orderId)
                    sales_debit_note_transaction = SalesTransaction.objects.create(retailer=order_obj.retailer,
                                                                                   transaction_id=transaction_id,
                                                                                   transaction_type="Debit Note",
                                                                                   salesPerson=order_obj.salesPerson if order_obj.salesPerson else None,
                                                                                   distributor=order_obj.distributor if order_obj.distributor else None,
                                                                                   beat_assignment=beat_assignment,
                                                                                   financePerson=order_obj.financePerson if order_obj.financePerson else None,
                                                                                   transaction_date=transaction_date,
                                                                                   is_trial=is_trial,
                                                                                   transaction_amount=debit_note_amount)
                order_obj.status = "delivered"
                order_obj.save()

                orderResponse["orders"] = OrderHistorySerializer(order_obj).data
                orderResponse["order_ids"] = return_bill_data

                return Response(orderResponse, status=status.HTTP_201_CREATED)
            else:
                return BadRequest({'error_type': "Validation Error",
                                   'errors': [{'message': "Cart can not be empty"}]})

        else:
            return Forbidden({'error_type': "permission_denied",
                              'errors': [{'message': "You do not have permission to perform this action."}]})

    @decorators.action(detail=False, methods=['post'], url_path="return_order")
    def return_order(self, request, *args, **kwargs):
        data = request.data
        user = request.user
        print(data)

        orderResponse = {}

        sales_profile = UserProfile.objects.filter(user=request.user, department__name__in=['Sales']).first()
        distribution_profile = UserProfile.objects.filter(user=request.user,
                                                          department__name__in=['Distribution']).first()

        finance_profile = UserProfile.objects.filter(user=request.user,
                                                     department__name__in=['Finance']).first()

        if distribution_profile or sales_profile or finance_profile:

            instance = get_object_or_404(self.get_queryset(), pk=data.get('id'))
            order_return_serializer = OrderReturnSerializer(data=data)
            order_return_serializer.is_valid(raise_exception=True)
            order_return_serializer.order_return_replace(instance, data, user, False)
            instance.return_picked_date = datetime.now(tz=CURRENT_ZONE)
            instance.save()
            orderResponse["returns"] = OrderHistorySerializer(instance).data

            return Response(orderResponse, status=status.HTTP_201_CREATED)

        else:
            return Forbidden({'error_type': "permission_denied",
                              'errors': [{'message': "You do not have permission to perform this action."}]})


class EcommerceOrderViewSet(viewsets.GenericViewSet, mixins.CreateModelMixin):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = EcommerceOrderHistorySerializer
    pagination_class = PaginationWithNoLimit
    queryset = EcommerceOrder.objects.all().order_by('delivery_date')
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = (
        'secondary_status', 'distributor', 'order_type', 'salesPerson', 'status', 'warehouse', 'delivery_date',
        'financePerson',
        'date', 'customer')

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        data_limit = request.GET.get('limit', 'false')
        if data_limit == 'true':
            queryset = queryset.filter(
                pk__in=list(queryset.values_list('id', flat=True)[:int(request.GET.get('limit_by', 100))]))

        no_retailer = self.request.GET.get('no_retailer', False)
        retailer_ledger = self.request.GET.get('retailer_ledger', False)
        if no_retailer == 'true':
            queryset = self.filter_queryset(self.get_queryset()).filter(Q(retailer=None))
        if retailer_ledger == 'true':
            queryset = self.filter_queryset(self.get_queryset()).filter(status__in=["delivered", "completed"])
        sales_order = self.request.GET.get('sales_order', False)
        if sales_order == 'true':
            order_days = self.request.GET.get('order_days', 90)
            time_difference = datetime.now(tz=CURRENT_ZONE) - timedelta(days=int(order_days))
            queryset = queryset.filter(delivery_date__gte=time_difference)
        clusters = request.GET.get('clusters', [])
        if clusters and clusters != "undefined":
            clusters = [int(c) for c in clusters.split(",")]
            if len(clusters) > 0:
                queryset = self.filter_queryset(self.get_queryset()).filter(retailer__cluster__in=clusters)

        from_date = None
        to_date = None
        statuses = request.GET.get('statuses', [])
        if statuses and statuses != "undefined":
            statuses = [str(c) for c in statuses.split(",")]
            queryset = queryset.filter(status__in=statuses)
        today_order = request.GET.get('today_order', 'false')
        if today_order == 'true':
            dt = datetime.now()
            start = dt.replace(hour=0, minute=0, second=0, microsecond=0)
            end = dt.replace(hour=23, minute=59, second=59, microsecond=999999)
            # queryset = queryset.filter(delivery_date__range=(start,end))
            queryset = queryset.filter(generation_date__range=(start, end))
        if queryset.first() and queryset.first().delivery_date:
            from_date = queryset.first().delivery_date
        if queryset.last() and queryset.last().delivery_date:
            to_date = queryset.last().delivery_date
        serializer = self.get_serializer(queryset, many=True)
        return Response({"from_date": from_date, "to_date": to_date, "results": serializer.data})

    def create(self, request, *args, **kwargs):
        data = request.data
        print(data)
        if request.user:
            user = request.user
            customer = Customer.objects.filter(user=user).first()
            ecomm_order_create_serializer = EcommerceOrderCreateSerializer(data=data)
            ecomm_order_create_serializer.is_valid(raise_exception=True)

            order_type = "Customer"
            cart_products = data.get('cart_products', [])
            if cart_products:
                print(cart_products)
                cart_products = json.loads(cart_products)
                for cart_product in cart_products:
                    order_line_serializer = OrderLineSerializer(data=cart_product)
                    order_line_serializer.is_valid(raise_exception=True)
                orders = Order.objects.all()
                # might be possible model has no records so make sure to handle None
                order_max_id = orders.aggregate(Max('id'))['id__max'] + 1 if orders else 1
                order_id = "CustomerOrder-" + str(order_max_id)
                date = datetime.now(tz=CURRENT_ZONE)
                is_promo = False
                if data.get("is_promo"):
                    if data.get('is_promo') == "true":
                        is_promo = True
                    else:
                        is_promo = False
                promo_amount = decimal.Decimal(data.get('promo_amount', 0.000))
                order_obj = ecomm_order_create_serializer.save(customer=customer, orderId=order_id, name=order_id,
                                                               order_type=order_type, date=date, generation_date=date,
                                                               delivery_date=date + timedelta(days=2),
                                                               warehouse_id=1,
                                                               is_promo=is_promo,
                                                               promo_amount=promo_amount,
                                                               status="draft", desc="description")
                # Handle Order Event
                OrderEvent.objects.create(order=order_obj, type="draft_created", user=order_obj.customer.user)
                for cart_product in cart_products:
                    order_line_serializer = OrderLineSerializer(data=cart_product)
                    order_line_serializer.is_valid(raise_exception=True)
                    order_line = order_line_serializer.save(order=order_obj)
                    if order_line.promo_quantity > 0:
                        OrderReturnLine.objects.create(orderLine=order_line, date=date, line_type="Promo",
                                                       quantity=order_line.promo_quantity,
                                                       amount=order_line.single_sku_mrp)
                customer_wallet = CustomerWallet.objects.filter(customer=customer).first()
                promoWallets = CustomerPromoWallet.objects.filter(wallet=customer_wallet, is_active=True,
                                                                  expired_at__gte=datetime.now(
                                                                      tz=CURRENT_ZONE)).order_by(
                    'expired_at')
                if order_obj.pay_by_wallet:
                    if customer_wallet.total_balance >= order_obj.order_price_amount:
                        # Remove balance from wallet
                        if order_obj.order_price_amount >= customer_wallet.recharge_balance:
                            customer_wallet.recharge_balance = 0.000
                            tempAmount = decimal.Decimal(order_obj.order_price_amount) - decimal.Decimal(
                                customer_wallet.recharge_balance)

                            for promoWallet in promoWallets:
                                if promoWallet.balance > tempAmount:
                                    promoWallet.balance -= tempAmount
                                    tempAmount = decimal.Decimal(0.000)
                                elif promoWallet.balance == tempAmount:
                                    promoWallet.balance = decimal.Decimal(0.000)
                                    promoWallet.is_active = False
                                    tempAmount = decimal.Decimal(0.000)
                                else:
                                    promoWallet.is_active = False
                                    tempAmount -= promoWallet.balance
                                    promoWallet.balance = decimal.Decimal(0.000)
                                promoWallet.save()
                                if tempAmount == decimal.Decimal(0.000):
                                    break
                            customer_wallet.total_balance -= order_obj.order_price_amount
                            customer_wallet.save()
                        else:
                            customer_wallet.recharge_balance -= order_obj.order_price_amount
                            customer_wallet.total_balance -= order_obj.order_price_amount
                            customer_wallet.save()
                        OrderEvent.objects.create(order=order_obj, type="order_marked_as_paid",
                                                  user=order_obj.customer.user)
                        order_obj.status = "created"
                        order_obj.order_payment_status = "Paid"
                        order_obj.save()

                        order_lines = order_obj.lines.all()
                        purchase_details = []
                        total_amount = 0
                        for order_line in order_lines:
                            product = order_line.product
                            print(product)

                            if product:
                                purchase_detail = {
                                    "item_description": "%s (%s SKU)" % (product.name, product.SKU_Count),
                                    "hsn_sac": product.productDivision.hsn,
                                    "sku_type": product.SKU_Count,
                                    "quantity": order_line.quantity,
                                    "sku_rate": round(product.current_price,
                                                      2)
                                }
                                purchase_detail['amount'] = round(
                                    purchase_detail['sku_rate'] * purchase_detail['quantity'], 2)
                                purchase_details.append(purchase_detail)
                                total_amount = round(total_amount + purchase_detail['amount'], 2)
                        address = {
                            "address_name": order_obj.shipping_address.address_name if order_obj.shipping_address.address_name else None,
                            "building_address": order_obj.shipping_address.building_address if order_obj.shipping_address.building_address else None,
                            "street_address": order_obj.shipping_address.street_address if order_obj.shipping_address.street_address else None,
                            "city_name": order_obj.shipping_address.city.city_name if order_obj.shipping_address.city else None,
                            "locality": order_obj.shipping_address.ecommerce_sector.sector_name if order_obj.shipping_address.ecommerce_sector else None,
                            "landmark": order_obj.shipping_address.landmark if order_obj.shipping_address.landmark else None,
                            "name": order_obj.shipping_address.name if order_obj.shipping_address.name else request.user.name,
                            "pinCode": order_obj.shipping_address.pinCode if order_obj.shipping_address.pinCode else None,
                            "phone_no": order_obj.shipping_address.phone_no if order_obj.shipping_address.phone_no else request.user.phone_no,
                        }
                        order_data = {"order_id": order_obj.orderId, "address": address,
                                      "order_total_amount": order_obj.order_price_amount,
                                      "order_total_in_words": num2words(order_obj.order_price_amount),
                                      "purchase_details": purchase_details}
                        print(order_data)
                        html_message = loader.render_to_string(
                            'invoice/order_email.html',
                            order_data
                        )
                        send_mail(subject="Order " + str(order_obj.orderId) + " has  been placed succesfully",
                                  message="Message", from_email=FROM_EMAIL,
                                  recipient_list=['po@eggoz.in', 'rohit.kumar@eggoz.in'], html_message=html_message)
                        OrderEvent.objects.create(order=order_obj, type="created", user=order_obj.customer.user)
                        # Handle Invoice
                        invoice = Invoice.objects.filter(order=order_obj).first()
                        if not invoice:
                            invoices = Invoice.objects.all()
                            # might be possible model has no records so make sure to handle None
                            invoice_max_id = invoices.aggregate(Max('id'))['id__max'] + 1 if invoices else 1
                            invoice_id = "E" + str(invoice_max_id)
                            invoice = Invoice.objects.create(invoice_id=invoice_id, order=order_obj,
                                                             invoice_status="Paid")
                        # Handle Sales Transactions
                        transactions = SalesTransaction.objects.all()
                        # might be possible model has no records so make sure to handle None
                        transaction_max_id = transactions.aggregate(Max('id'))['id__max'] + 1 if transactions else 1
                        transaction_id = "TR" + str(transaction_max_id)
                        st = SalesTransaction.objects.create(customer=order_obj.customer, transaction_id=transaction_id,
                                                             transaction_type="Debit", transaction_date=order_obj.date,
                                                             transaction_amount=order_obj.order_price_amount)
                        st.invoices.add(invoice)
                        st.save()

                        return Ok("order created successfully")
                    else:
                        orderAmount = order_obj.order_price_amount - customer_wallet.total_balance
                        # Handle in After Return

                        cash_free_all_obj = CashFreeTransaction.objects.all()
                        cft_maxcount = cash_free_all_obj.aggregate(Max('id'))['id__max'] + 1 if cash_free_all_obj else 1
                        cash_free_transaction = CashFreeTransaction.objects.create(
                            transaction_id="CustomerOrder-" + str(cft_maxcount),
                            note=order_obj.orderId,
                            order_id=order_obj.id,
                            wallet_id=int(customer_wallet.id))
                        # Handle Payment
                        domain = request.build_absolute_uri('/')[:-1]
                        if "https" in domain:
                            pass
                        else:
                            domain = domain.replace('http', 'https')
                        url = "%s/api/v1/order/create" % (CASHFREE_BASE_URL)
                        payload = {'appId': CASHFREE_APP_ID,
                                   'secretKey': CASHFREE_SECRET_KEY,
                                   'orderId': cash_free_transaction.transaction_id,
                                   'orderAmount': float("{:.2f}".format(orderAmount)),
                                   'orderCurrency': 'INR',
                                   'orderNote': cash_free_transaction.note,
                                   'customerEmail': str(customer.user.email),
                                   'customerName': customer.user.name,
                                   'customerPhone': str(customer.phone_no),
                                   'returnUrl': '%s/payment/return_payment/' % (domain),
                                   'notifyUrl': '%s/payment/notify_payment/' % (domain)}
                        files = [
                        ]

                        headers = {}
                        print(payload)
                        response = requests.request("POST", url, headers=headers, data=payload, files=files)
                        print(response.text)
                        gateway_response = json.loads(response.text)
                        return Ok(gateway_response)
                else:
                    orderAmount = order_obj.order_price_amount
                    # Handle in After Return

                    cash_free_all_obj = CashFreeTransaction.objects.all()
                    cft_maxcount = cash_free_all_obj.aggregate(Max('id'))['id__max'] + 1 if cash_free_all_obj else 1
                    cash_free_transaction = CashFreeTransaction.objects.create(
                        transaction_id="CustomerOrder" + str(cft_maxcount),
                        note=order_obj.orderId,
                        order_id=order_obj.id,
                        wallet_id=int(customer_wallet.id))
                    # Handle Payment
                    domain = request.build_absolute_uri('/')[:-1]
                    if "https" in domain:
                        pass
                    else:
                        domain = domain.replace('http', 'https')
                    url = "%s/api/v1/order/create" % (CASHFREE_BASE_URL)
                    payload = {'appId': CASHFREE_APP_ID,
                               'secretKey': CASHFREE_SECRET_KEY,
                               'orderId': cash_free_transaction.transaction_id,
                               'orderAmount': float("{:.2f}".format(orderAmount)),
                               'orderCurrency': 'INR',
                               'orderNote': cash_free_transaction.note,
                               'customerEmail': str(customer.user.email),
                               'customerName': customer.user.name,
                               'customerPhone': str(customer.phone_no),
                               'returnUrl': '%s/payment/return_payment/' % (domain),
                               'notifyUrl': '%s/payment/notify_payment/' % (domain)}
                    files = [
                    ]

                    headers = {}
                    print(payload)
                    response = requests.request("POST", url, headers=headers, data=payload, files=files)
                    print(response.text)
                    gateway_response = json.loads(response.text)
                    return Ok(gateway_response)
            else:
                return BadRequest({'error_type': "Validation Error",
                                   'errors': [{'message': "Cart can not be empty"}]})

        else:
            return Ok("Redirect to Login or SignUp Page")

    @decorators.action(detail=False, methods=['post'], url_path="change_status")
    def change_status(self, request, *args, **kwargs):
        data = request.data
        print(data)
        if request.user:
            user = request.user
            ops_profile = UserProfile.objects.filter(user=request.user, department__name__in=['Operations']).first()
            if ops_profile:
                opsProfile = OperationsPersonProfile.objects.filter(user=request.user).first()
                if opsProfile.management_status == "Worker":
                    return BadRequest({'error_type': "Not Authorized",
                                       'errors': [{'message': "please login with Admin Credentials"}]})
                else:
                    if data.get('id'):
                        order_id = int(data.get('id'))
                        ecomm_order = EcommerceOrder.objects.filter(id=order_id).first()
                        print(ecomm_order.status)
                        if ecomm_order.status == OrderStatus.CREATED:
                            ecomm_order.status = OrderStatus.CONFIRMED
                        elif ecomm_order.status == OrderStatus.CONFIRMED:
                            ecomm_order.status = OrderStatus.ONTHEWAY
                        elif ecomm_order.status == OrderStatus.ONTHEWAY:
                            ecomm_order.status = OrderStatus.DELIVERED
                        # elif ecomm_order.status == OrderStatus.DELIVERED:
                        #     ecomm_order.status = OrderStatus.REFUNDED
                        else:
                            return BadRequest({'error_type': "Validation Error",
                                               'errors': [{'message': "Status not in Created, Confirmed, ON THE WAY"}]})
                        ecomm_order.save()
                        OrderEvent.objects.create(order=ecomm_order, type=ecomm_order.status, user=request.user)

                        return Response({"results": "{} Successfully".format(ecomm_order.status)},
                                        status=status.HTTP_201_CREATED)

    @decorators.action(detail=False, methods=['post'], url_path="change_delivery_date")
    def change_delivery_date(self, request, *args, **kwargs):
        data = request.data
        print(data)
        if request.user:
            user = request.user
            ops_profile = UserProfile.objects.filter(user=request.user, department__name__in=['Operations']).first()
            if ops_profile:
                opsProfile = OperationsPersonProfile.objects.filter(user=request.user).first()
                if opsProfile.management_status == "Worker":
                    return BadRequest({'error_type': "Not Authorized",
                                       'errors': [{'message': "please login with Admin Credentials"}]})
                else:
                    if data.get('id'):
                        order_id = int(data.get('id'))
                        ecomm_order = EcommerceOrder.objects.filter(id=order_id).first()
                        delivery_date = datetime.strptime(data.get('delivery_date'), "%d-%m-%Y %H:%M:%S")
                        ecomm_order.delivery_date = delivery_date
                        ecomm_order.save()
                        OrderEvent.objects.create(order=ecomm_order, type="delivery_date_changed", user=request.user)

                        return Response({"results": "{} Successfully".format(ecomm_order.status)},
                                        status=status.HTTP_201_CREATED)

    def cart(self, request, *args, **kwargs):
        data = request.data
        print(data)
        if request.user:
            user = request.user
            customer = Customer.objects.filter(user=user).first()
            order_create_serializer = EcommerceOrderCreateSerializer(data=data)
            order_create_serializer.is_valid(raise_exception=True)
            # customer_wallet = customer.wallet
            order_type = "Customer"
            cart_products = data.get('cart_products', [])
            if cart_products:
                print(cart_products)
                cart_products = json.loads(cart_products)
                for cart_product in cart_products:
                    order_line_serializer = OrderLineSerializer(data=cart_product)
                    order_line_serializer.is_valid(raise_exception=True)

                if Order.objects.filter(status="draft", customer=customer):
                    order = Order.objects.filter(status="draft", customer=customer).first()
                    orderLines = order.lines.all()
                    if orderLines:
                        pass
                    else:
                        pass
                else:
                    # might be possible model has no records so make sure to handle None
                    orders = Order.objects.all()
                    order_max_id = orders.aggregate(Max('id'))['id__max'] + 1 if orders else 1
                    order_id = "Cart-" + str(customer.id) + "-GGN-" + str(order_max_id)
                    date = datetime.now(tz=CURRENT_ZONE)
                    order_obj = order_create_serializer.save(customer=customer, orderId=order_id, name=order_id,
                                                             order_type=order_type, date=date, generation_date=date,
                                                             delivery_date=date + timedelta(days=3),
                                                             warehouse_id=1,
                                                             status="draft")
                    # Handle Order Event
                    OrderEvent.objects.create(order=order_obj, type="draft_created", user=order_obj.customer.user)
                    for cart_product in cart_products:
                        order_line_serializer = OrderLineSerializer(data=cart_product)
                        order_line_serializer.is_valid(raise_exception=True)
                        order_line_serializer.save(order=order_obj)

                return Response({"cart": order_create_serializer.data})


def ecommerce_order_create(request):
    user = request.user
    data = request.data
    customer = Customer.objects.filter(user=user).first()
    ecomm_order_create_serializer = EcommerceOrderCreateSerializer(data=data)
    ecomm_order_create_serializer.is_valid(raise_exception=True)

    order_type = "Customer"
    cart_products = data.get('cart_products', [])
    if cart_products:
        print(cart_products)
        cart_products = json.loads(cart_products)
        for cart_product in cart_products:
            order_line_serializer = OrderLineSerializer(data=cart_product)
            order_line_serializer.is_valid(raise_exception=True)
        orders = Order.objects.all()
        # might be possible model has no records so make sure to handle None
        order_max_id = orders.aggregate(Max('id'))['id__max'] + 1 if orders else 1
        order_id = "CustomerOrder-" + str(order_max_id)
        date = datetime.now(tz=CURRENT_ZONE)
        is_promo = False
        if data.get("is_promo"):
            if data.get('is_promo') == "true":
                is_promo = True
            else:
                is_promo = False
        promo_amount = decimal.Decimal(data.get('promo_amount', 0.000))
        order_obj = ecomm_order_create_serializer.save(customer=customer, orderId=order_id, name=order_id,
                                                       order_type=order_type, date=date, generation_date=date,
                                                       delivery_date=date + timedelta(days=2),
                                                       warehouse_id=1,
                                                       is_promo=is_promo,
                                                       promo_amount=promo_amount,
                                                       status="draft", desc="description")
        # Handle Order Event
        OrderEvent.objects.create(order=order_obj, type="draft_created", user=order_obj.customer.user)
        for cart_product in cart_products:
            order_line_serializer = OrderLineSerializer(data=cart_product)
            order_line_serializer.is_valid(raise_exception=True)
            order_line = order_line_serializer.save(order=order_obj)
            if order_line.promo_quantity > 0:
                OrderReturnLine.objects.create(orderLine=order_line, date=date, line_type="Promo",
                                               quantity=order_line.promo_quantity,
                                               amount=order_line.single_sku_mrp)
        customer_wallet = CustomerWallet.objects.filter(customer=customer).first()
        promoWallets = CustomerPromoWallet.objects.filter(wallet=customer_wallet, is_active=True,
                                                          expired_at__gte=datetime.now(
                                                              tz=CURRENT_ZONE)).order_by(
            'expired_at')
        if order_obj.pay_by_wallet:
            if customer_wallet.total_balance >= order_obj.order_price_amount:
                # Remove balance from wallet
                if order_obj.order_price_amount >= customer_wallet.recharge_balance:
                    customer_wallet.recharge_balance = 0.000
                    tempAmount = decimal.Decimal(order_obj.order_price_amount) - decimal.Decimal(
                        customer_wallet.recharge_balance)

                    for promoWallet in promoWallets:
                        if promoWallet.balance > tempAmount:
                            promoWallet.balance -= tempAmount
                            tempAmount = decimal.Decimal(0.000)
                        elif promoWallet.balance == tempAmount:
                            promoWallet.balance = 0.000
                            promoWallet.is_active = False
                            tempAmount = decimal.Decimal(0.000)
                        else:
                            promoWallet.is_active = False
                            tempAmount -= promoWallet.balance
                            promoWallet.balance = decimal.Decimal(0.000)
                        promoWallet.save()
                        if tempAmount == decimal.Decimal(0.000):
                            break
                    customer_wallet.total_balance -= order_obj.order_price_amount
                    customer_wallet.save()
                else:
                    customer_wallet.recharge_balance -= order_obj.order_price_amount
                    customer_wallet.total_balance -= order_obj.order_price_amount
                    customer_wallet.save()
                OrderEvent.objects.create(order=order_obj, type="order_marked_as_paid",
                                          user=order_obj.customer.user)
                order_obj.status = "created"
                order_obj.order_payment_status = "Paid"
                order_obj.save()

                order_lines = order_obj.lines.all()
                purchase_details = []
                total_amount = 0
                for order_line in order_lines:
                    product = order_line.product
                    print(product)

                    if product:
                        purchase_detail = {
                            "item_description": "%s (%s SKU)" % (product.name, product.SKU_Count),
                            "hsn_sac": product.productDivision.hsn,
                            "sku_type": product.SKU_Count,
                            "quantity": order_line.quantity,
                            "sku_rate": round(product.current_price,
                                              2)
                        }
                        purchase_detail['amount'] = round(
                            purchase_detail['sku_rate'] * purchase_detail['quantity'], 2)
                        purchase_details.append(purchase_detail)
                        total_amount = round(total_amount + purchase_detail['amount'], 2)
                address = {
                    "address_name": order_obj.shipping_address.address_name if order_obj.shipping_address.address_name else None,
                    "building_address": order_obj.shipping_address.building_address if order_obj.shipping_address.building_address else None,
                    "street_address": order_obj.shipping_address.street_address if order_obj.shipping_address.street_address else None,
                    "city_name": order_obj.shipping_address.city.city_name if order_obj.shipping_address.city else None,
                    "locality": order_obj.shipping_address.ecommerce_sector.sector_name if order_obj.shipping_address.ecommerce_sector else None,
                    "landmark": order_obj.shipping_address.landmark if order_obj.shipping_address.landmark else None,
                    "name": order_obj.shipping_address.name if order_obj.shipping_address.name else request.user.name,
                    "pinCode": order_obj.shipping_address.pinCode if order_obj.shipping_address.pinCode else None,
                    "phone_no": order_obj.shipping_address.phone_no if order_obj.shipping_address.phone_no else request.user.phone_no,
                }
                order_data = {"order_id": order_obj.orderId, "address": address,
                              "order_total_amount": order_obj.order_price_amount,
                              "order_total_in_words": num2words(order_obj.order_price_amount),
                              "purchase_details": purchase_details}
                print(order_data)
                html_message = loader.render_to_string(
                    'invoice/order_email.html',
                    order_data
                )
                send_mail(subject="Order " + str(order_obj.orderId) + " has  been placed succesfully",
                          message="Message", from_email=FROM_EMAIL,
                          recipient_list=['po@eggoz.in', 'rohit.kumar@eggoz.in'], html_message=html_message)
                OrderEvent.objects.create(order=order_obj, type="created", user=order_obj.customer.user)
                # Handle Invoice
                invoice = Invoice.objects.filter(order=order_obj).first()
                if not invoice:
                    invoices = Invoice.objects.all()
                    # might be possible model has no records so make sure to handle None
                    invoice_max_id = invoices.aggregate(Max('id'))['id__max'] + 1 if invoices else 1
                    invoice_id = "E" + str(invoice_max_id)
                    invoice = Invoice.objects.create(invoice_id=invoice_id, order=order_obj,
                                                     invoice_status="Paid")
                # Handle Sales Transactions
                transactions = SalesTransaction.objects.all()
                # might be possible model has no records so make sure to handle None
                transaction_max_id = transactions.aggregate(Max('id'))['id__max'] + 1 if transactions else 1
                transaction_id = "TR" + str(transaction_max_id)
                st = SalesTransaction.objects.create(customer=order_obj.customer, transaction_id=transaction_id,
                                                     transaction_type="Debit", transaction_date=order_obj.date,
                                                     transaction_amount=order_obj.order_price_amount)
                st.invoices.add(invoice)
                st.save()

                return "order created successfully"
            else:
                orderAmount = order_obj.order_price_amount - customer_wallet.total_balance
                # Handle in After Return

                cash_free_all_obj = CashFreeTransaction.objects.all()
                cft_maxcount = cash_free_all_obj.aggregate(Max('id'))['id__max'] + 1 if cash_free_all_obj else 1
                cash_free_transaction = CashFreeTransaction.objects.create(
                    transaction_id="CustomerOrder-" + str(cft_maxcount),
                    note=order_obj.orderId,
                    order_id=order_obj.id,
                    wallet_amount=customer_wallet.total_balance,
                    wallet_id=int(customer_wallet.id))
                # Handle Payment
                domain = request.build_absolute_uri('/')[:-1]
                if "https" in domain:
                    pass
                else:
                    domain = domain.replace('http', 'https')
                url = "%s/api/v1/order/create" % (CASHFREE_BASE_URL)
                payload = {'appId': CASHFREE_APP_ID,
                           'secretKey': CASHFREE_SECRET_KEY,
                           'orderId': cash_free_transaction.transaction_id,
                           'orderAmount': float("{:.2f}".format(orderAmount)),
                           'orderCurrency': 'INR',
                           'orderNote': cash_free_transaction.note,
                           'customerEmail': str(customer.user.email),
                           'customerName': customer.user.name,
                           'customerPhone': str(customer.phone_no),
                           'returnUrl': '%s/payment/return_payment/' % (domain),
                           'notifyUrl': '%s/payment/notify_payment/' % (domain)}
                files = [
                ]

                headers = {}
                print(payload)
                response = requests.request("POST", url, headers=headers, data=payload, files=files)
                print(response.text)
                gateway_response = json.loads(response.text)
                return gateway_response
        else:
            orderAmount = order_obj.order_price_amount
            # Handle in After Return

            cash_free_all_obj = CashFreeTransaction.objects.all()
            cft_maxcount = cash_free_all_obj.aggregate(Max('id'))['id__max'] + 1 if cash_free_all_obj else 1
            cash_free_transaction = CashFreeTransaction.objects.create(
                transaction_id="CustomerOrder" + str(cft_maxcount),
                note=order_obj.orderId,
                order_id=order_obj.id,
                wallet_id=int(customer_wallet.id))
            # Handle Payment
            domain = request.build_absolute_uri('/')[:-1]
            if "https" in domain:
                pass
            else:
                domain = domain.replace('http', 'https')
            url = "%s/api/v1/order/create" % (CASHFREE_BASE_URL)
            payload = {'appId': CASHFREE_APP_ID,
                       'secretKey': CASHFREE_SECRET_KEY,
                       'orderId': cash_free_transaction.transaction_id,
                       'orderAmount': float("{:.2f}".format(orderAmount)),
                       'orderCurrency': 'INR',
                       'orderNote': cash_free_transaction.note,
                       'customerEmail': str(customer.user.email),
                       'customerName': customer.user.name,
                       'customerPhone': str(customer.phone_no),
                       'returnUrl': '%s/payment/return_payment/' % (domain),
                       'notifyUrl': '%s/payment/notify_payment/' % (domain)}
            files = [
            ]

            headers = {}
            print(payload)
            response = requests.request("POST", url, headers=headers, data=payload, files=files)
            print(response.text)
            gateway_response = json.loads(response.text)
            return gateway_response
    else:
        return BadRequest({'error_type': "Validation Error",
                           'errors': [{'message': "Cart can not be empty"}]})