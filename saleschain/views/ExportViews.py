import json
from ast import literal_eval
from datetime import datetime, timedelta
from decimal import Decimal

import coreapi
import pytz
from celery import states
from django.http import JsonResponse
from django_filters import rest_framework as filters
from kombu.utils.encoding import safe_repr
from rest_framework import viewsets, mixins, permissions, status
from rest_framework.filters import BaseFilterBackend
from rest_framework.response import Response

from base.views import PaginationWithThousandLimit
from order.api.serializers import OrderHistorySerializer, OrderExportSerializer
from order.models.Order import Order
from payment.api.serializers import PaymentSerializer, PaymentHistorySerializer
from payment.models import Payment, Invoice
from retailer.models import RetailerEggsdata, Retailer
from saleschain.api.exportSerializers import SalesExportSerializer, SalesEggsDataExportSerializer, \
    RetailerEggsDataExportSerializer, InvoiceExportSerializer
from saleschain.models import SalesEggsdata
from django.db.models import Max, Q

from saleschain.tasks import sales_bills_list


class DateFilterBackend(BaseFilterBackend):
    def get_schema_fields(self, view):
        return [coreapi.Field(
            name='from_delivery_date',
            location='query',
            required=False,
            type='string'
        ),
            coreapi.Field(
                name='to_delivery_date',
                location='query',
                required=False,
                type='string'
            ),
        ]


class SalesFilteredExportViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = SalesExportSerializer
    queryset = Order.objects.all()
    pagination_class = PaginationWithThousandLimit
    filter_backends = (filters.DjangoFilterBackend, DateFilterBackend)
    filterset_fields = (
        'retailer', 'order_type', 'salesPerson', 'status', 'warehouse', 'date', 'distributor', 'delivery_date',
        'secondary_status')

    def list(self, request, *args, **kwargs):
        if request.GET.get('from_delivery_date') and request.GET.get('to_delivery_date'):

            from_delivery_date = datetime.strptime(request.GET.get('from_delivery_date'), '%d/%m/%Y')
            to_delivery_date = datetime.strptime(request.GET.get('to_delivery_date'), '%d/%m/%Y')

            from_delivery_date = from_delivery_date.replace(hour=0, minute=0, second=0)
            to_delivery_date = to_delivery_date.replace(hour=0, minute=0, second=0)

            delta = timedelta(hours=23, minutes=59, seconds=59)
            from_delivery_date = from_delivery_date
            to_delivery_date = to_delivery_date + delta
            print(from_delivery_date)
            print(to_delivery_date)
            orders = Order.objects.filter(delivery_date__gte=from_delivery_date, status__in=["delivered", "completed"],
                                          delivery_date__lte=to_delivery_date, is_trial=False,
                                          is_geb=False).select_related(
                'retailer', 'warehouse', 'salesPerson', 'distributor').order_by('id')

            # orders = orders.filter(~Q(distributor=None))
            # print(orders)
        else:
            orders = Order.objects.filter(status__in=["delivered", "completed"], is_trial=False,
                                          is_geb=False).select_related(
                'retailer', 'warehouse', 'salesPerson', 'distributor').order_by('id')
        page = self.paginate_queryset(orders)
        serializer = OrderExportSerializer(orders, many=True)
        if page is not None:
            serializer = OrderExportSerializer(page, many=True)
            print(serializer.data)
            return self.get_paginated_response(serializer.data)

        return Response({"results": serializer.data})


class SalesGEBExportViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = SalesExportSerializer
    queryset = Order.objects.all()
    pagination_class = PaginationWithThousandLimit
    filter_backends = (filters.DjangoFilterBackend, DateFilterBackend)
    filterset_fields = ('retailer', 'order_type', 'salesPerson', 'status', 'warehouse', 'date', 'distributor',
                        'delivery_date', 'secondary_status', 'is_geb', 'is_geb_verified')

    def list(self, request, *args, **kwargs):
        if request.GET.get('from_delivery_date') and request.GET.get('to_delivery_date'):
            from_delivery_date = datetime.strptime(request.GET.get('from_delivery_date'), '%d/%m/%Y')
            to_delivery_date = datetime.strptime(request.GET.get('to_delivery_date'), '%d/%m/%Y')

            from_delivery_date = from_delivery_date.replace(hour=0, minute=0, second=0)
            to_delivery_date = to_delivery_date.replace(hour=0, minute=0, second=0)

            delta = timedelta(hours=23, minutes=59, seconds=59)
            from_delivery_date = from_delivery_date
            to_delivery_date = to_delivery_date + delta
            print(from_delivery_date)
            print(to_delivery_date)
            orders = Order.objects.filter(delivery_date__gte=from_delivery_date, status__in=["delivered", "completed"],
                                          delivery_date__lte=to_delivery_date, is_trial=False,
                                          is_geb=True).select_related(
                'retailer', 'warehouse', 'salesPerson', 'distributor').order_by('id')

            # orders = orders.filter(~Q(distributor=None))
            # print(orders)
        else:
            orders = Order.objects.filter(status__in=["delivered", "completed"], is_trial=False,
                                          is_geb=True).select_related(
                'retailer', 'warehouse', 'salesPerson', 'distributor').order_by('id')
            # orders = orders.filter(~Q(distributor=None))
        page = self.paginate_queryset(orders)
        serializer = OrderExportSerializer(orders, many=True)
        if page is not None:
            serializer = OrderExportSerializer(page, many=True)
            print(serializer.data)
            return self.get_paginated_response(serializer.data)

        return Response({"results": serializer.data})


class SalesOrderExportViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = SalesExportSerializer
    queryset = Order.objects.all()
    pagination_class = PaginationWithThousandLimit
    filter_backends = (filters.DjangoFilterBackend, DateFilterBackend)
    filterset_fields = (
        'retailer', 'order_type', 'salesPerson', 'distributor', 'secondary_status', 'status', 'warehouse',
        'delivery_date',
        'date', 'is_geb', 'is_geb_verified')

    def list(self, request, *args, **kwargs):
        if request.GET.get('from_delivery_date') and request.GET.get('to_delivery_date'):
            from_delivery_date = datetime.strptime(request.GET.get('from_delivery_date'), '%d/%m/%Y')
            to_delivery_date = datetime.strptime(request.GET.get('to_delivery_date'), '%d/%m/%Y')

            from_delivery_date = from_delivery_date.replace(hour=0, minute=0, second=0)
            to_delivery_date = to_delivery_date.replace(hour=0, minute=0, second=0)

            delta = timedelta(hours=23, minutes=59, seconds=59)
            from_delivery_date = from_delivery_date
            to_delivery_date = to_delivery_date + delta
            print(from_delivery_date)
            print(to_delivery_date)
            orders = Order.objects.filter(delivery_date__gte=from_delivery_date,
                                          delivery_date__lte=to_delivery_date,
                                          is_trial=False).select_related(
                'retailer', 'warehouse', 'salesPerson', 'distributor').order_by('id')

        else:
            orders = Order.objects.filter(is_trial=False).select_related(
                'retailer', 'warehouse', 'salesPerson', 'distributor').order_by('id')

        page = self.paginate_queryset(orders)
        serializer = OrderExportSerializer(orders, many=True)
        if page is not None:
            serializer = OrderExportSerializer(page, many=True)
            print(serializer.data)
            return self.get_paginated_response(serializer.data)

        return Response({"results": serializer.data})


class FinancePaymentViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = PaymentSerializer
    queryset = Payment.objects.all()
    filter_backends = (filters.DjangoFilterBackend, DateFilterBackend)
    filterset_fields = ('payment_mode', 'pay_choice', 'pay_amount', 'invoice', 'salesTransaction', 'created_at')

    def list(self, request, *args, **kwargs):
        if request.GET.get('from_delivery_date') and request.GET.get('to_delivery_date'):
            from_delivery_date = datetime.strptime(request.GET.get('from_delivery_date'), '%d/%m/%Y')
            to_delivery_date = datetime.strptime(request.GET.get('to_delivery_date'), '%d/%m/%Y')

            from_delivery_date = from_delivery_date.replace(hour=0, minute=0, second=0)
            to_delivery_date = to_delivery_date.replace(hour=0, minute=0, second=0)

            delta = timedelta(hours=23, minutes=59, seconds=59)
            from_delivery_date = from_delivery_date
            to_delivery_date = to_delivery_date + delta
            print(from_delivery_date)
            print(to_delivery_date)
            payments = Payment.objects.filter(created_at__gte=from_delivery_date, created_at__lte=to_delivery_date,
                                              salesTransaction__is_trial=False, ).select_related(
                'invoice', 'salesTransaction').order_by('created_at')
            payments = payments.filter(~Q(salesTransaction__transaction_type="Cancelled"))
            payments = payments.filter(~Q(invoice__invoice_status="Cancelled"))
        else:
            payments = Payment.objects.filter(salesTransaction__is_trial=False).select_related(
                'invoice', 'salesTransaction').order_by('created_at')
            payments = payments.filter(
                ~Q(salesTransaction__transaction_type="Cancelled", invoice__invoice_status="Cancelled"))

        payment_results = []

        for payment in payments:
            payment_dict = {}
            payment_dict['bill'] = payment.invoice.order.name
            payment_dict['retailer'] = payment.invoice.order.retailer.code if payment.invoice.order.retailer else "Customer"
            payment_dict[
                'distributor'] = payment.salesTransaction.distributor.user.name if payment.salesTransaction.distributor else ""
            payment_dict[
                'salesPerson'] = payment.salesTransaction.salesPerson.user.name if payment.salesTransaction.salesPerson else ""
            payment_dict['type'] = payment.pay_choice
            payment_dict['amountPaid'] = payment.pay_amount
            payment_dict['mode'] = payment.payment_mode
            payment_dict['paid_at'] = payment.created_at
            payment_dict['cheque_number'] = payment.cheque_number if payment.cheque_number else ""
            payment_dict['upi_id'] = payment.upi_id if payment.upi_id else ""
            payment_dict['city'] = payment.invoice.order.retailer.city.city_name if payment.invoice.order.retailer else "Customer"
            payment_dict['id'] = str(payment.id)
            payment_dict['is_geb'] = payment.invoice.order.is_geb
            payment_dict['is_geb_verified'] = payment.invoice.order.is_geb_verified
            payment_results.append(payment_dict)

        # results = PaymentHistorySerializer(payments, many=True).data
        return Response({"payments": payment_results}, status=status.HTTP_201_CREATED)


class FinanceExportViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = SalesExportSerializer
    queryset = Order.objects.all()
    filter_backends = (filters.DjangoFilterBackend, DateFilterBackend)
    filterset_fields = ('retailer', 'order_type', 'salesPerson', 'status', 'warehouse', 'delivery_date')

    def list(self, request, *args, **kwargs):
        if request.GET.get('from_delivery_date') and request.GET.get('to_delivery_date'):
            from_delivery_date = datetime.strptime(request.GET.get('from_delivery_date'), '%d/%m/%Y')
            to_delivery_date = datetime.strptime(request.GET.get('to_delivery_date'), '%d/%m/%Y')

            from_delivery_date = from_delivery_date.replace(hour=0, minute=0, second=0)
            to_delivery_date = to_delivery_date.replace(hour=0, minute=0, second=0)

            delta = timedelta(hours=23, minutes=59, seconds=59)
            from_delivery_date = from_delivery_date
            to_delivery_date = to_delivery_date + delta
            print(from_delivery_date)
            print(to_delivery_date)
            orders = Order.objects.filter(delivery_date__gte=from_delivery_date, status__in=["delivered", "completed"],
                                          delivery_date__lte=to_delivery_date, is_trial=False).select_related(
                'retailer', 'warehouse', 'salesPerson', 'distributor').order_by('id')

            # orders = orders.filter(~Q(distributor=None))
            # print(orders)
        else:
            orders = Order.objects.filter(status__in=["delivered", "completed"], is_trial=False).select_related(
                'retailer', 'warehouse', 'salesPerson').order_by('id')
            # orders = orders.filter(~Q(distributor=None))

        invoice_results = []
        return_results = []
        payment_results = []
        for order in orders:
            city_id = order.retailer.city.id if order.retailer else \
                order.customer.shipping_address.city.id if order.customer.shipping_address.city else None
            invoice_dict = {}
            payment_dict = {}
            if order.invoice:
                payments = Payment.objects.filter(invoice=order.invoice, salesTransaction__is_trial=False)

                invoice_dict['bill_no'] = order.name
                invoice_dict['code'] = order.retailer.code if order.retailer else order.customer.name
                invoice_dict['bill_amount'] = order.order_price_amount
                invoice_dict['discount_amount'] = order.discount_amount
                invoice_dict['invoice_status'] = order.invoice.invoice_status
                invoice_dict['invoice_due'] = order.invoice.invoice_due
                invoice_dict['created_at'] = order.invoice.created_at
                invoice_dict['id'] = order.invoice.id
                invoice_dict['is_geb'] = order.is_geb
                invoice_dict['is_geb_verified'] = order.is_geb_verified

                if payments:
                    payment_dict['amount'] = Decimal(0.000)
                    payment_dict["pay_status"] = True
                    payment_dict['type'] = "&".join([payment.pay_choice for payment in payments])
                    payment_dict['amountString'] = "&".join([str(payment.pay_amount) for payment in payments])
                    payment_dict['mode'] = "&".join([payment.payment_mode for payment in payments])
                    payment_dict['paid_at'] = "&".join([str(payment.created_at) for payment in payments])
                    payment_dict['id'] = "&".join([str(payment.id) for payment in payments])
                    payment_dict['cheque_number'] = "&".join(
                        [payment.cheque_number if payment.cheque_number else "" for payment in payments])
                    payment_dict['upi_id'] = "&".join(
                        [payment.upi_id if payment.upi_id else "" for payment in payments])
                    payment_dict['city_id'] = city_id
                    payment_dict['is_geb'] = order.is_geb
                    payment_dict['is_geb_verified'] = order.is_geb_verified

                    for payment in payments:
                        # payment_dict["pay_status"] = True
                        # payment_dict['type'] = payment.pay_choice
                        payment_dict['amount'] += payment.pay_amount
                        # payment_dict['mode'] = payment.payment_mode
                        # payment_dict['paid_at'] = payment.created_at
                        # payment_dict['cheque_number'] = payment.cheque_number if payment.cheque_number else None
                        # payment_dict['upi_id'] = payment.upi_id if payment.upi_id else None
                        # payment_dict['id'] = payment.id
                        # payment_dict['city_id'] = city_id
                    invoice_dict.update(payment_dict)
                    payment_results.append(payment_dict)
                else:
                    payment_dict["pay_status"] = False
                    payment_dict['type'] = None
                    payment_dict['amount'] = None
                    payment_dict['amountString'] = None
                    payment_dict['mode'] = None
                    payment_dict['paid_at'] = None
                    payment_dict['cheque_number'] = None
                    payment_dict['upi_id'] = None
                    payment_dict['id'] = None
                    payment_dict['city_id'] = city_id
                    invoice_dict.update(payment_dict)
                    # continue

                invoice_results.append(invoice_dict)

                order_lines = order.lines.all()
                if order_lines:
                    for order_line in order_lines:
                        return_lines = order_line.lines.all()
                        if return_lines:
                            return_dict = {}
                            for return_line in return_lines:
                                print(return_line)
                                return_dict['bill_no'] = order.name
                                return_dict['code'] = order.retailer.code if order.retailer else order.customer.name
                                return_dict['product_name'] = str(
                                    order_line.product.SKU_Count) + order_line.product.name[:1]
                                return_dict['sku_count'] = order_line.product.SKU_Count
                                return_dict['type'] = return_line.line_type
                                return_dict['quantity'] = return_line.quantity
                                return_dict['amount'] = return_line.amount
                                return_dict['date'] = return_line.date
                                return_dict['id'] = return_line.id
                                return_dict['product_id'] = str(order_line.product.id)
                                return_dict['city_id'] = city_id
                                return_dict['city_id'] = order.is_geb
                                return_dict['city_id'] = order.is_geb_verified

                                return_results.append(return_dict)
                        else:
                            continue
                else:
                    continue
            else:
                continue

        return Response(
            {"results": {"invoices": invoice_results, "returns": return_results, "payments": payment_results}})


class ReturnExportViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = SalesExportSerializer
    queryset = Order.objects.all()
    filter_backends = (filters.DjangoFilterBackend, DateFilterBackend)
    filterset_fields = ('retailer', 'order_type', 'salesPerson', 'status', 'warehouse', 'delivery_date')

    def list(self, request, *args, **kwargs):
        if request.GET.get('from_delivery_date') and request.GET.get('to_delivery_date'):

            from_delivery_date = datetime.strptime(request.GET.get('from_delivery_date'), '%d/%m/%Y')
            to_delivery_date = datetime.strptime(request.GET.get('to_delivery_date'), '%d/%m/%Y')

            from_delivery_date = from_delivery_date.replace(hour=0, minute=0, second=0)
            to_delivery_date = to_delivery_date.replace(hour=0, minute=0, second=0)

            delta = timedelta(hours=23, minutes=59, seconds=59)
            from_delivery_date = from_delivery_date
            to_delivery_date = to_delivery_date + delta
            print(from_delivery_date)
            print(to_delivery_date)
            orders = Order.objects.filter(return_picked_date__gte=from_delivery_date,
                                          status__in=["delivered", "completed"],
                                          return_picked_date__lte=to_delivery_date, is_trial=False).select_related(
                'retailer', 'warehouse', 'salesPerson', 'distributor').order_by('id')

        else:
            orders = Order.objects.filter(status__in=["delivered", "completed"], is_trial=False).select_related(
                'retailer', 'warehouse', 'salesPerson').order_by('id')

        return_results = []
        for order in orders:
            city_id = order.retailer.city.id if order.retailer else \
                order.customer.shipping_address.city.id if order.customer.shipping_address.city else None

            if order.invoice:

                order_lines = order.lines.all()
                if order_lines:
                    return_orders = []
                    for order_line in order_lines:
                        return_lines = order_line.lines.all()
                        if return_lines:
                            return_dict = {}
                            for return_line in return_lines:
                                print(return_line)
                                return_dict['bill_no'] = order.name
                                return_dict[
                                    'Del Guy'] = return_line.distributor.user.name if return_line.distributor else ""
                                return_dict['code'] = order.retailer.code if order.retailer else order.customer.name
                                return_dict['product_name'] = str(
                                    order_line.product.SKU_Count) + order_line.product.name[:1]
                                return_dict['sku_count'] = order_line.product.SKU_Count
                                return_dict['type'] = return_line.line_type
                                return_dict['quantity'] = return_line.quantity
                                return_dict['amount'] = return_line.amount
                                return_dict['date'] = return_line.date
                                return_dict[
                                    'salesPerson'] = return_line.salesPerson.user.name if return_line.salesPerson else ""
                                return_dict['id'] = return_line.id
                                return_dict['product_id'] = str(order_line.product.id)
                                return_dict['city_id'] = city_id
                                return_dict['is_geb'] = order.is_geb
                                return_dict['is_geb_verified'] = order.is_geb_verified

                                return_results.append(return_dict)
                        else:
                            if int(order.deviated_amount) > 0:
                                return_orders.append(order)
                            continue
                    if len(return_orders) > 0:
                        for ret_order in return_orders:
                            ret_city_id = ret_order.retailer.city.id if ret_order.retailer else \
                                ret_order.customer.shipping_address.city.id if ret_order.customer.shipping_address.city else None
                            return_dict = {}
                            return_dict['bill_no'] = ret_order.name
                            return_dict['Del Guy'] = ""
                            return_dict[
                                'code'] = ret_order.retailer.code if ret_order.retailer else ret_order.customer.name
                            return_dict['product_name'] = ""
                            return_dict['sku_count'] = ""
                            return_dict['type'] = "Return"
                            return_dict['quantity'] = ""
                            return_dict['amount'] = ret_order.deviated_amount
                            return_dict['date'] = ret_order.return_picked_date
                            return_dict[
                                'salesPerson'] = ret_order.salesPerson.user.name if ret_order.salesPerson else ""
                            return_dict['id'] = 0
                            return_dict['product_id'] = ""
                            return_dict['city_id'] = ret_city_id
                            return_dict['is_geb'] = ret_order.is_geb
                            return_dict['is_geb_verified'] = ret_order.is_geb_verified

                            return_results.append(return_dict)
                else:

                    continue
            else:
                continue

        return Response({"results": {"returns": return_results}})


def get_order_line_dict(order_obj):
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
            if str(order_line.product.SKU_Count) + order_line.product.name[:1] in mapped_dict.keys():
                mapped_dict[str(order_line.product.SKU_Count) + order_line.product.name[:1]] = order_line.quantity
                mapped_rate_dict[
                    str(order_line.product.SKU_Count) + order_line.product.name[:1] + " R"] = order_line.single_sku_rate

    return {"Qty": mapped_dict, "Rate": mapped_rate_dict}


class SalesEggsDataExportViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = SalesEggsDataExportSerializer
    queryset = SalesEggsdata.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ('salesPerson', 'date')

    def list(self, request, *args, **kwargs):

        if request.GET.get('from_delivery_date') and request.GET.get('to_delivery_date'):
            from_delivery_date = datetime.strptime(request.GET.get('from_delivery_date'), '%d/%m/%Y')
            to_delivery_date = datetime.strptime(request.GET.get('to_delivery_date'), '%d/%m/%Y')

            from_delivery_date = from_delivery_date.replace(hour=0, minute=0, second=0)
            to_delivery_date = to_delivery_date.replace(hour=0, minute=0, second=0)

            delta = timedelta(hours=23, minutes=59, seconds=59)
            from_delivery_date = from_delivery_date
            to_delivery_date = to_delivery_date + delta
            salesEggsDataList = self.filter_queryset(self.get_queryset().filter(date__gte=from_delivery_date,
                                                                                date__lte=to_delivery_date)). \
                select_related('salesPerson')
        else:
            salesEggsDataList = self.filter_queryset(self.get_queryset()). \
                select_related('salesPerson')
        eggs_results = []
        for eggsData in salesEggsDataList:
            eggs_dict = {}
            eggs_dict['date'] = eggsData.date if eggsData.date else "No Date"
            eggs_dict['salesPerson'] = eggsData.salesPerson.user.name if eggsData.salesPerson else "No Sales Person"
            eggs_dict['brown'] = eggsData.brown if eggsData.brown else 0
            eggs_dict['white'] = eggsData.white if eggsData.white else 0
            eggs_dict['nutra'] = eggsData.nutra if eggsData.nutra else 0

            eggs_results.append(eggs_dict)
        return Response({"results": eggs_results})


class RetailerEggsDataExportViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = RetailerEggsDataExportSerializer
    queryset = RetailerEggsdata.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ('retailer', 'date')

    def list(self, request, *args, **kwargs):

        if request.GET.get('from_delivery_date') and request.GET.get('to_delivery_date'):
            from_delivery_date = datetime.strptime(request.GET.get('from_delivery_date'), '%d/%m/%Y')
            to_delivery_date = datetime.strptime(request.GET.get('to_delivery_date'), '%d/%m/%Y')
            from_delivery_date = from_delivery_date.replace(hour=0, minute=0, second=0)
            to_delivery_date = to_delivery_date.replace(hour=0, minute=0, second=0)

            delta = timedelta(hours=23, minutes=59, seconds=59)
            from_delivery_date = from_delivery_date
            to_delivery_date = to_delivery_date + delta

            retailersEggsDataList = self.filter_queryset(self.get_queryset().filter(date__gte=from_delivery_date,
                                                                                    date__lte=to_delivery_date)). \
                select_related('retailer')
        else:
            retailersEggsDataList = self.filter_queryset(self.get_queryset()). \
                select_related('retailer')
        eggs_results = []
        for eggsData in retailersEggsDataList:
            eggs_dict = {}
            eggs_dict['date'] = eggsData.date if eggsData.date else "No Date"
            eggs_dict['retailer'] = eggsData.retailer.retailer.name if eggsData.retailer else "No Retailer"
            eggs_dict['brown'] = eggsData.brown if eggsData.brown else 0
            eggs_dict['white'] = eggsData.white if eggsData.white else 0
            eggs_dict['nutra'] = eggsData.nutra if eggsData.nutra else 0

            eggs_results.append(eggs_dict)
        return Response({"results": eggs_results})


class MonthlySalesExportViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = SalesExportSerializer
    queryset = Order.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ('retailer', 'order_type', 'salesPerson', 'status', 'warehouse', 'date')

    def list(self, request, *args, **kwargs):
        if request.GET.get('from_delivery_date') and request.GET.get('to_delivery_date'):
            from_delivery_date = datetime.strptime(request.GET.get('from_delivery_date'), '%d/%m/%Y')
            to_delivery_date = datetime.strptime(request.GET.get('to_delivery_date'), '%d/%m/%Y')

            from_delivery_date = from_delivery_date.replace(hour=0, minute=0, second=0)
            to_delivery_date = to_delivery_date.replace(hour=0, minute=0, second=0)

            delta = timedelta(hours=23, minutes=59, seconds=59)
            from_delivery_date = from_delivery_date
            to_delivery_date = to_delivery_date + delta
            print(from_delivery_date)
            print(to_delivery_date)
            cities = request.GET.get('cities', [])
            # TODO Comment
            if cities and cities != "undefined":
                cities = json.loads(cities)
                cities = [int(c) for c in cities]
                if len(cities) > 0:
                    orders = self.filter_queryset(self.get_queryset().filter(delivery_date__gte=from_delivery_date,
                                                                             status__in=["delivered", "completed"],
                                                                             retailer__city__in=cities,
                                                                             delivery_date__lte=to_delivery_date,
                                                                             is_trial=False)).select_related(
                        'retailer', 'warehouse', 'salesPerson', 'distributor').order_by('id')
                else:
                    orders = self.filter_queryset(self.get_queryset().filter(delivery_date__gte=from_delivery_date,
                                                                             status__in=["delivered", "completed"],
                                                                             delivery_date__lte=to_delivery_date,
                                                                             is_trial=False)).select_related(
                        'retailer', 'warehouse', 'salesPerson', 'distributor').order_by('id')

            # orders = orders.filter(~Q(distributor=None))
            # print(orders)
        else:
            orders = self.filter_queryset(
                self.get_queryset().filter(status__in=["delivered", "completed"], is_trial=False)).select_related(
                'retailer', 'warehouse', 'salesPerson').order_by('id')
            # orders = orders.filter(~Q(distributor=None))
        sales_results = []
        unique_retailers = orders.values_list('retailer', flat=True)
        unique_retailers = list(set(unique_retailers))
        # print(unique_retailers)

        for retailer in unique_retailers:
            same_retailer_orders = list(filter(lambda x: x.retailer_id == retailer, orders))
            # print(same_retailer_orders)
            orders_list_dict = {'Brown': 0, 'White': 0, 'Nutra': 0}
            replaced_list_dict = {'Brown': 0, 'White': 0, 'Nutra': 0}
            returned_list_dict = {'Brown': 0, 'White': 0, 'Nutra': 0}
            ord_retailer = same_retailer_orders[0].retailer
            ord_salesPerson = same_retailer_orders[0].salesPerson
            order_amount = Decimal(0.000)
            return_amount = Decimal(0.000)
            replacement_amount = Decimal(0.000)
            order_delivery_date = None
            bill_no = None
            retailer_obj = Retailer.objects.filter(id=retailer).first()
            city_id = retailer_obj.city.id if retailer else None
            city_name = retailer_obj.city.city_name if retailer else None
            for retailer_order in same_retailer_orders:
                order_delivery_date = retailer_order.delivery_date + timedelta(hours=5, minutes=30, seconds=0)
                bill_no = retailer_order.name
                order_lines = retailer_order.lines.all()
                for order_line in order_lines:
                    # For Eggs Data
                    if order_line.product:
                        if order_line.product.name == "White Regular":
                            name = "White"
                        else:
                            name = order_line.product.name
                        order_amount += order_line.quantity * order_line.single_sku_rate
                        if orders_list_dict[name] > 0:
                            orders_list_dict[name] = orders_list_dict[
                                                         name] + order_line.quantity * order_line.product.SKU_Count
                        else:
                            orders_list_dict[name] = order_line.quantity * order_line.product.SKU_Count
                        return_replace_lines = order_line.lines.all()
                        if return_replace_lines:
                            for return_replace_line in return_replace_lines:
                                if return_replace_line.line_type == "Replacement":
                                    replacement_amount += Decimal(0.000)
                                    if replaced_list_dict[name] > 0:
                                        replaced_list_dict[name] = replaced_list_dict[name] \
                                                                   + order_line.deviated_quantity * order_line.product.SKU_Count
                                    else:
                                        replaced_list_dict[
                                            name] = order_line.deviated_quantity * order_line.product.SKU_Count
                                else:
                                    return_amount += order_line.deviated_quantity * order_line.single_sku_rate
                                    if returned_list_dict[name] > 0:
                                        returned_list_dict[name] = returned_list_dict[name] \
                                                                   + order_line.deviated_quantity * order_line.product.SKU_Count
                                    else:
                                        returned_list_dict[
                                            name] = order_line.deviated_quantity * order_line.product.SKU_Count

            sales_dict = {}
            sales_dict['code'] = ord_retailer.code
            sales_dict['salesPerson'] = ord_salesPerson.user.name
            sales_dict['salesPersonId'] = ord_salesPerson.id
            sales_dict['category'] = ord_retailer.category.name

            sales_dict["Sold White"] = orders_list_dict['White']
            sales_dict["Sold Brown"] = orders_list_dict['Brown']
            sales_dict["Sold Nutra"] = orders_list_dict['Nutra']

            sales_dict["Replaced White"] = replaced_list_dict['White']
            sales_dict["Replaced Brown"] = replaced_list_dict['Brown']
            sales_dict["Replaced Nutra"] = replaced_list_dict['Nutra']

            sales_dict["Returned White"] = returned_list_dict['White']
            sales_dict["Returned Brown"] = returned_list_dict['Brown']
            sales_dict["Returned Nutra"] = returned_list_dict['Nutra']

            sales_dict["Net White"] = orders_list_dict['White'] - replaced_list_dict['White'] - returned_list_dict[
                'White']
            sales_dict["Net Brown"] = orders_list_dict['Brown'] - replaced_list_dict['Brown'] - returned_list_dict[
                'Brown']
            sales_dict["Net Nutra"] = orders_list_dict['Nutra'] - replaced_list_dict['Nutra'] - returned_list_dict[
                'Nutra']
            sales_dict["Date"] = order_delivery_date
            sales_dict["Bill No"] = bill_no
            sales_dict["Bill Amount"] = order_amount
            sales_dict["Net Amount"] = order_amount - replacement_amount - return_amount
            sales_dict["city_id"] = city_id
            sales_dict["city_name"] = city_name

            sales_results.append(sales_dict)
        return Response({"results": sales_results})
