import decimal
import json
from ast import literal_eval
from datetime import datetime

import coreapi
import pytz
from django.db.models import Q, Max
from future.backports.datetime import timedelta
from rest_framework import permissions, viewsets, decorators, mixins, pagination
from rest_framework.filters import BaseFilterBackend
from rest_framework.response import Response

from Eggoz.settings import CURRENT_ZONE
from base.response import NotFound, Forbidden, BadRequest
from base.views import PaginationWithNoLimit
from custom_auth.models import UserProfile
from distributionchain.api import BeatAssignmentSerializer, BeatAssignmentDetailSerializer, \
    BeatWarehouseSupplySerializer, BeatSMApprovalSerializer, BeatRHApprovalSerializer
from distributionchain.models import BeatAssignment, DistributionPersonProfile
from order.api.serializers import OrderHistorySerializer, OrderExportSerializer
from order.models import Order
from payment.api.serializers import SalesTransactionSerializer, SalesTransactionShortSerializer
from payment.models import SalesTransaction, Payment
from retailer.api.serializers import RetailerDashboardSerializer, ShortRetailerSerializer, \
    RetailerDashboardShortSerializer, ShortBeatRetailerSerializer, RetailerDashboardManagerSerializer, \
    RetailerMarginSerializer, RetailerDashboardManagerShortSerializer, RetailerSalesSerializer
from retailer.models.Retailer import Retailer, CommissionSlab
from saleschain.api.serializers import SalesPersonProfileSerializer, \
    SalesPersonHistorySerializer, SalesRetailerLedgerSerializer, RetailerDemandSerializer, \
    RetailerDemandCreateSerializer, RetailerDemandSKUCreateSerializer, SalesDemandSKUCreateSerializer, \
    SalesSupplySkuSerializer, SalesSMApprovalSerializer, SalesRHApprovalSerializer, SalesSupplyPackedSkuSerializer
from saleschain.models import SalesPersonProfile, RetailerDemand, RetailerDemandSKU, SalesDemandSKU, SalesSupplySKU, \
    SalesSMApprovalSKU
from django_filters import rest_framework as filters

from warehouse.models import WarehousePersonProfile


class PaginationWithLimit(pagination.PageNumberPagination):
    page_size = 5000


class SimpleFilterBackend(BaseFilterBackend):
    def get_schema_fields(self, view):
        return [coreapi.Field(
            name='from_felivery_date',
            location='query',
            required=False,
            type='string'
        ),
            coreapi.Field(
                name='to_delivery_date',
                location='query',
                required=False,
                type='string'
            )
        ]


class SalesPersonProfileViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin):
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = PaginationWithNoLimit
    serializer_class = SalesPersonProfileSerializer
    queryset = SalesPersonProfile.objects.all()
    filter_backends = (filters.DjangoFilterBackend, SimpleFilterBackend)
    filterset_fields = ('user',)

    def list(self, request, *args, **kwargs):
        user = request.user
        user_profile = UserProfile.objects.filter(user=user, department__name__in=['Sales']).first()
        if user_profile:
            salesPersonProfile = SalesPersonProfile.objects.filter(user=user).first()
            if salesPersonProfile.management_status == "Worker":
                return BadRequest({'error_type': "Not Authorized",
                                   'errors': [{'message': "please login with Admin Credentials"}]})
            else:
                cities = request.GET.get('cities', [])
                if cities and cities != "undefined":
                    cities = json.loads(cities)
                    cities = [int(c) for c in cities]
                    if len(cities) > 0:
                        queryset = SalesPersonProfile.objects.filter(user__addresses__city__in=cities).exclude(
                            user=user).distinct()
                    else:
                        return BadRequest({'error_type': "Validation Error",
                                           'errors': [{'message': "please provide at least one city to filter"}]})
                else:
                    queryset = SalesPersonProfile.objects.none()
        else:
            return BadRequest({'error_type': "Not Authorized",
                               'errors': [{'message': "No User Profile"}]})
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @decorators.action(detail=False, methods=['get'], url_path="orders")
    def orders(self, request, *args, **kwargs):
        user = request.user
        user_profile = UserProfile.objects.filter(user=user, department__name__in=['Sales']).first()
        if user_profile:
            salesPersonProfile = SalesPersonProfile.objects.filter(user=user).first()
            if request.GET.get("from_delivery_date") and request.GET.get("to_delivery_date"):

                from_delivery_date = datetime.strptime(request.GET.get('from_delivery_date'),
                                                       '%d/%m/%Y')

                to_delivery_date = datetime.strptime(request.GET.get('to_delivery_date'), '%d/%m/%Y')

                from_delivery_date = from_delivery_date.replace(hour=0, minute=0, second=0)
                to_delivery_date = to_delivery_date.replace(hour=0, minute=0, second=0)

                delta = timedelta(hours=23, minutes=59, seconds=59)
                from_delivery_date = from_delivery_date
                to_delivery_date = to_delivery_date + delta

                queryset = Order.objects.filter(salesPerson=salesPersonProfile,
                                                delivery_date__gte=from_delivery_date,
                                                delivery_date__lte=to_delivery_date)
            else:
                queryset = Order.objects.filter(salesPerson=salesPersonProfile,
                                                delivery_date__gte=datetime.now(
                                                    tz=CURRENT_ZONE) - timedelta(days=15))
        else:
            return BadRequest({'error_type': "Not Authorized",
                               'errors': [{'message': "No User Profile"}]})

        page = self.paginate_queryset(queryset)
        serializer = OrderExportSerializer(queryset, many=True)
        if page is not None:
            serializer = OrderExportSerializer(page, many=True)
            print(serializer.data)
            return self.get_paginated_response(serializer.data)

        return Response({"results": serializer.data})

        # sales_results = []
        # for order in queryset:
        #     city_id = order.retailer.city.id if order.retailer else \
        #         order.customer.shipping_address.city.id if order.customer.shipping_address.city else None
        #     city_name = order.retailer.city.city_name if order.retailer else \
        #         order.customer.shipping_address.city.city_name if order.customer.shipping_address.city else None
        #     sales_dict = {}
        #
        #     instant_amount = 0
        #     instant_mode = ""
        #     later_mode = ""
        #     later_amount = 0
        #     later_mode_date = None
        #     if order.invoice:
        #         payments = Payment.objects.filter(invoice=order.invoice, salesTransaction__is_trial=False)
        #         if payments:
        #             for payment in payments:
        #                 # print(payment.payment_mode)
        #                 # print(payment.payment_type)
        #                 if payment.pay_choice == "InstantPay":
        #                     instant_amount += payment.pay_amount
        #                     instant_mode += payment.payment_mode
        #                 else:
        #                     later_amount += payment.pay_amount
        #                     later_mode += payment.payment_mode
        #                     later_mode_date = payment.created_at + timedelta(hours=5, minutes=30, seconds=0)
        #     order_date = order.date + timedelta(hours=5, minutes=30, seconds=0)
        #     order_delivery_date = order.delivery_date + timedelta(hours=5, minutes=30, seconds=0)
        #     sales_dict['Beat no.'] = order.retailer.beat_number if order.retailer else 0
        #     sales_dict['Del. Guy'] = order.distributor.user.name if order.distributor else None
        #     sales_dict[
        #         'Operator'] = order.distributor.user.name if order.distributor else order.salesPerson.user.name if order.salesPerson else ""
        #     IST = pytz.timezone('Asia/Kolkata')
        #     sales_dict['Date'] = order_delivery_date.replace(tzinfo=IST).strftime(
        #         '%d/%m/%Y %H:%M:%S') if order.delivery_date else None
        #     sales_dict['Party Name'] = str(order.retailer.code) if order.retailer else None
        #     sales_dict['Sales Person'] = order.salesPerson.user.name if order.salesPerson else None
        #     sales_dict['emp1'] = ""
        #     sales_dict['bill no'] = order.name
        #     sales_dict['PENDING'] = int(order.invoice.invoice_due) if order.invoice else None
        #     sales_dict.update(get_order_line_dict(order)["Qty"])
        #     sales_dict['Instant Pay'] = instant_amount
        #     sales_dict['Mode'] = instant_mode
        #     sales_dict['C.D'] = ""
        #     sales_dict.update(get_order_line_dict(order)["Rate"])
        #
        #     sales_dict['amount'] = order.order_price_amount if order.order_price_amount else 0
        #     sales_dict['Acc pay'] = None
        #     sales_dict['Later pay'] = later_amount
        #     sales_dict['Later pay date'] = later_mode_date.replace(tzinfo=IST).strftime(
        #         '%d/%m/%Y %H:%M:%S') if later_mode_date != None else None
        #     sales_dict['pending'] = order.invoice.invoice_due if order.invoice else None
        #     sales_dict['paid status'] = order.invoice.invoice_status if order.invoice else None
        #     sales_dict['RETURN VALUE ADJUSTMENT'] = int(order.deviated_amount) if order.deviated_amount else 0
        #     sales_dict['order_date'] = order_date
        #     sales_dict['status'] = order.status
        #     sales_dict['secondary_status'] = order.secondary_status
        #     sales_dict['city_name'] = city_name
        #     sales_dict['city_id'] = city_id
        #     sales_dict['is_geb'] = order.is_geb
        #     sales_dict['is_geb_verified'] = order.is_geb_verified
        #
        #     sales_results.append(sales_dict)
        # return Response({"results": sales_results})

    @decorators.action(detail=False, methods=['get'], url_path="history")
    def history(self, request, *args, **kwargs):
        user = request.user
        user_profile = UserProfile.objects.filter(user=user, department__name__in=['Sales']).first()
        if user_profile:
            salesPersonProfile = SalesPersonProfile.objects.filter(user=user).first()
            if salesPersonProfile:
                serializer = SalesPersonHistorySerializer(salesPersonProfile, context={"request": request})
                return Response(serializer.data)
            else:
                return NotFound({'error_type': "ValidationError",
                                 'errors': [{'message': "Sales Person Profile Not found"}]})
        else:
            return NotFound({'error_type': "ValidationError",
                             'errors': [{'message': "User Profile Not found"}]})

    @decorators.action(detail=False, methods=['get'], url_path="profile")
    def profile(self, request, *args, **kwargs):
        user = request.user
        user_profile = UserProfile.objects.filter(user=user, department__name__in=['Sales']).first()
        if user_profile:
            salesPersonProfile = SalesPersonProfile.objects.filter(user=user).first()
            if salesPersonProfile:
                user_cities = []
                user_addresses = user.addresses.all()
                default_address = user.default_address
                city_dict = {}
                if default_address:
                    city_dict['id'] = default_address.city.id
                    city_dict['city_name'] = default_address.city.city_name
                if user_addresses:
                    for user_address in user_addresses:
                        cities_dict = {}
                        cities_dict['id'] = user_address.city.id if user_address.city.id else 1
                        cities_dict[
                            'city_name'] = user_address.city.city_name if user_address.city.city_name else "No City"
                        user_cities.append(cities_dict)
                user_cities = list({user_city['id']: user_city for user_city in user_cities}.values())
                # serializer = SalesPersonHistorySerializer(salesPersonProfile, context={"request": request})
                return Response({"results": {"cities": user_cities, "city": city_dict}})
            else:
                return NotFound({'error_type': "ValidationError",
                                 'errors': [{'message': "Sales Person Profile Not found"}]})
        else:
            return NotFound({'error_type': "ValidationError",
                             'errors': [{'message': "User Profile Not found"}]})


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


class SalesManagerProfileViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin):
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = PaginationWithNoLimit
    serializer_class = SalesPersonProfileSerializer
    queryset = SalesPersonProfile.objects.all()
    filter_backends = (filters.DjangoFilterBackend, SimpleFilterBackend)
    filterset_fields = ('user',)

    def list(self, request, *args, **kwargs):
        user = request.user
        user_profile = UserProfile.objects.filter(user=user, department__name__in=['Sales']).first()
        if user_profile:
            salesPersonProfile = SalesPersonProfile.objects.filter(user=user).first()
            if salesPersonProfile.management_status == "Worker":
                return BadRequest({'error_type': "Not Authorized",
                                   'errors': [{'message': "please login with Admin Credentials"}]})
            else:
                queryset = SalesPersonProfile.objects.filter(management_choice="Regional Manager")
        else:
            return BadRequest({'error_type': "Not Authorized",
                               'errors': [{'message': "No User Profile"}]})
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @decorators.action(detail=False, methods=['get'], url_path="sales_retailers")
    def sales_retailers(self, request, *args, **kwargs):
        user = request.user
        user_profile = UserProfile.objects.filter(user=user, department__name__in=['Sales']).first()
        if user_profile:
            salesPersonProfile = SalesPersonProfile.objects.filter(user=user).first()
            if salesPersonProfile.management_status == "Worker":
                return BadRequest({'error_type': "Not Authorized",
                                   'errors': [{'message': "please login with Admin Credentials"}]})
            else:
                salesPersonProfile = literal_eval(request.GET.get('salesPersonProfile'))
                if salesPersonProfile:
                    queryset = Retailer.objects.filter(salesPersonProfile=salesPersonProfile).order_by('id')
                    print(queryset)
                else:
                    queryset = Retailer.objects.none()
        else:
            return BadRequest({'error_type': "Not Authorized",
                               'errors': [{'message': "No User Profile"}]})

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = RetailerDashboardManagerSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @decorators.action(detail=False, methods=['get'], url_path="retailers")
    def retailers(self, request, *args, **kwargs):
        user = request.user
        user_profile = UserProfile.objects.filter(user=user, department__name__in=['Sales']).first()
        if user_profile:
            salesPersonProfile = SalesPersonProfile.objects.filter(user=user).first()
            if salesPersonProfile.management_status == "Worker":
                return BadRequest({'error_type': "Not Authorized",
                                   'errors': [{'message': "please login with Admin Credentials"}]})
            else:

                cities = request.GET.get('cities', [])
                if cities and cities != "undefined":
                    cities = json.loads(cities)
                    cities = [int(c) for c in cities]
                    if len(cities) > 0:
                        queryset = Retailer.objects.filter(city__in=cities)
                        # print(queryset)
                    else:
                        return BadRequest({'error_type': "Validation Error",
                                           'errors': [{'message': "please provide at least one city to filter"}]})
                else:
                    queryset = Retailer.objects.none()
        else:
            return BadRequest({'error_type': "Not Authorized",
                               'errors': [{'message': "No User Profile"}]})

        page = self.paginate_queryset(queryset)
        if page is not None:
            # serializer = RetailerDashboardManagerSerializer(page, many=True)
            serializer = RetailerDashboardManagerShortSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = RetailerDashboardManagerShortSerializer(queryset, many=True)
        # serializer = RetailerDashboardManagerSerializer(queryset, many=True)
        return Response(serializer.data)

    @decorators.action(detail=False, methods=['get'], url_path="retailers_margin")
    def retailers_margin(self, request, *args, **kwargs):
        user = request.user
        user_profile = UserProfile.objects.filter(user=user, department__name__in=['Sales']).first()
        if user_profile:
            salesPersonProfile = SalesPersonProfile.objects.filter(user=user).first()
            if salesPersonProfile.management_status == "Worker":
                return BadRequest({'error_type': "Not Authorized",
                                   'errors': [{'message': "please login with Admin Credentials"}]})
            else:
                cities = request.GET.get('cities', [])
                if cities and cities != "undefined":
                    cities = json.loads(cities)
                    cities = [int(c) for c in cities]
                    if len(cities) > 0:
                        queryset = Retailer.objects.filter(city__in=cities)
                        print(queryset)
                    else:
                        return BadRequest({'error_type': "Validation Error",
                                           'errors': [{'message': "please provide at least one city to filter"}]})
                else:
                    queryset = Retailer.objects.none()
        else:
            return BadRequest({'error_type': "Not Authorized",
                               'errors': [{'message': "No User Profile"}]})

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = RetailerMarginSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = RetailerMarginSerializer(queryset, many=True)

        return Response(serializer.data)

    @decorators.action(detail=False, methods=['post'], url_path="retailers_edit")
    def retailers_edit(self, request, *args, **kwargs):
        user = request.user
        user_profile = UserProfile.objects.filter(user=user, department__name__in=['Sales']).first()
        if user_profile:
            salesPersonProfile = SalesPersonProfile.objects.filter(user=user).first()

            retailer_id = request.data.get('retailer_id')
            if retailer_id:
                retailer = Retailer.objects.get(id=retailer_id)
                if request.data.get('commission_slab_id'):
                    commission_slab_id = request.data.get('commission_slab_id')
                    cs = CommissionSlab.objects.get(id=commission_slab_id)
                    retailer.commission_slab = cs
                if request.data.get('onboarding_status'):
                    onboarding_status = request.data.get('onboarding_status')
                    retailer.onboarding_status = onboarding_status
                if request.data.get('beat_number'):
                    retailer = Retailer.objects.get(id=retailer_id)
                    retailer.beat_number = request.data.get('beat_number')
                retailer.save()
                return Response({})
            else:
                return BadRequest({'error_type': "Not Valid Retailer",
                                   'errors': [{'message': "Retailer Id is invalid"}]})
        else:
            return BadRequest({'error_type': "Not Authorized",
                               'errors': [{'message': "please login with Sales Credentials"}]})

    @decorators.action(detail=False, methods=['get'], url_path="orders")
    def orders(self, request, *args, **kwargs):
        user = request.user
        user_profile = UserProfile.objects.filter(user=user, department__name__in=['Sales']).first()
        if user_profile:
            salesPersonProfile = SalesPersonProfile.objects.filter(user=user).first()
            if salesPersonProfile.management_status == "Worker":
                return BadRequest({'error_type': "Not Authorized",
                                   'errors': [{'message': "please login with Admin Credentials"}]})
            else:

                cities = request.GET.get('cities', [])
                if cities and cities != "undefined":
                    cities = json.loads(cities)
                    cities = [int(c) for c in cities]
                    if len(cities) > 0:
                        # salesProfiles = SalesPersonProfile.objects.filter(user__addresses__city__in=cities).exclude(
                        #     user=user).distinct()
                        if request.GET.get("from_delivery_date") and request.GET.get("to_delivery_date"):

                            from_delivery_date = datetime.strptime(request.GET.get('from_delivery_date'),
                                                                   '%d/%m/%Y')

                            to_delivery_date = datetime.strptime(request.GET.get('to_delivery_date'), '%d/%m/%Y')

                            from_delivery_date = from_delivery_date.replace(hour=0, minute=0, second=0)
                            to_delivery_date = to_delivery_date.replace(hour=0, minute=0, second=0)

                            delta = timedelta(hours=23, minutes=59, seconds=59)
                            from_delivery_date = from_delivery_date
                            to_delivery_date = to_delivery_date + delta
                            queryset = Order.objects.filter(delivery_date__gte=from_delivery_date,
                                                            status__in=["delivered", "completed"],
                                                            retailer__city__in=cities,
                                                            delivery_date__lte=to_delivery_date,
                                                            is_trial=False).select_related(
                                'retailer', 'warehouse', 'salesPerson', 'distributor').order_by('id')
                        else:
                            queryset = Order.objects.filter(status__in=["delivered", "completed"],
                                                            is_trial=False,
                                                            delivery_date__gte=datetime.now(
                                                                tz=CURRENT_ZONE) - timedelta(days=15)).select_related(
                                'retailer', 'warehouse', 'salesPerson', 'distributor').order_by('id')
                    else:
                        return BadRequest({'error_type': "Validation Error",
                                           'errors': [{'message': "please provide at least one city to filter"}]})
                else:
                    queryset = None
                # TODO COmment

        else:
            return BadRequest({'error_type': "Not Authorized",
                               'errors': [{'message': "No User Profile"}]})

        page = self.paginate_queryset(queryset)
        serializer = OrderExportSerializer(queryset, many=True)
        if page is not None:
            serializer = OrderExportSerializer(page, many=True)
            print(serializer.data)
            return self.get_paginated_response(serializer.data)

        return Response({"results": serializer.data})
        # sales_results = []
        # for order in queryset:
        #     city_id = order.retailer.city.id if order.retailer else \
        #         order.customer.shipping_address.city.id if order.customer.shipping_address.city else None
        #     city_name = order.retailer.city.city_name if order.retailer else \
        #         order.customer.shipping_address.city.city_name if order.customer.shipping_address.city else None
        #     sales_dict = {}
        #
        #     instant_amount = 0
        #     instant_mode = ""
        #     later_mode = ""
        #     later_amount = 0
        #     later_mode_date = None
        #     if order.invoice:
        #         payments = Payment.objects.filter(invoice=order.invoice, salesTransaction__is_trial=False)
        #         if payments:
        #             for payment in payments:
        #                 # print(payment.payment_mode)
        #                 # print(payment.payment_type)
        #                 if payment.pay_choice == "InstantPay":
        #                     instant_amount += payment.pay_amount
        #                     instant_mode += payment.payment_mode
        #                 else:
        #                     later_amount += payment.pay_amount
        #                     later_mode += payment.payment_mode
        #                     later_mode_date = payment.created_at + timedelta(hours=5, minutes=30, seconds=0)
        #     order_date = order.date + timedelta(hours=5, minutes=30, seconds=0)
        #     order_delivery_date = order.delivery_date + timedelta(hours=5, minutes=30, seconds=0)
        #     sales_dict['Beat no.'] = order.retailer.beat_number if order.retailer else 0
        #     sales_dict['Del. Guy'] = order.distributor.user.name if order.distributor else None
        #     sales_dict[
        #         'Operator'] = order.distributor.user.name if order.distributor else order.salesPerson.user.name if order.salesPerson else ""
        #     IST = pytz.timezone('Asia/Kolkata')
        #     sales_dict['Date'] = order_delivery_date.replace(tzinfo=IST).strftime(
        #         '%d/%m/%Y %H:%M:%S') if order.delivery_date else None
        #     sales_dict['Party Name'] = str(order.retailer.code) if order.retailer else None
        #     sales_dict['Sales Person'] = order.salesPerson.user.name if order.salesPerson else None
        #     sales_dict['emp1'] = ""
        #     sales_dict['bill no'] = order.name
        #     sales_dict['Manual bill no'] = order.bill_no if order.bill_no else ""
        #     sales_dict['PENDING'] = int(order.invoice.invoice_due) if order.invoice else None
        #     sales_dict.update(get_order_line_dict(order)["Qty"])
        #     sales_dict['Instant Pay'] = instant_amount
        #     sales_dict['Mode'] = instant_mode
        #     sales_dict['C.D'] = ""
        #     sales_dict.update(get_order_line_dict(order)["Rate"])
        #     # sales_dict['Year'] = order_delivery_date.replace(tzinfo=IST).strftime('%Y') if order.delivery_date else None
        #     # sales_dict['Month'] = order_delivery_date.replace(tzinfo=IST).strftime(
        #     #     '%m') if order.delivery_date else None
        #     # sales_dict['Day'] = str(
        #     #     int(order_delivery_date.replace(tzinfo=IST).strftime('%d'))) if order.delivery_date else None
        #     sales_dict['amount'] = order.order_price_amount if order.order_price_amount else 0
        #     sales_dict['Acc pay'] = None
        #     sales_dict['Later pay'] = later_amount
        #     sales_dict['Later pay date'] = later_mode_date.replace(tzinfo=IST).strftime(
        #         '%d/%m/%Y %H:%M:%S') if later_mode_date != None else None
        #     sales_dict['pending'] = order.invoice.invoice_due if order.invoice else None
        #     sales_dict['paid status'] = order.invoice.invoice_status if order.invoice else None
        #     sales_dict['RETURN VALUE ADJUSTMENT'] = int(order.deviated_amount) if order.deviated_amount else 0
        #     sales_dict['order_date'] = order_date
        #     sales_dict['status'] = order.status
        #     sales_dict['secondary_status'] = order.secondary_status
        #     sales_dict['city_name'] = city_name
        #     sales_dict['city_id'] = city_id
        #     sales_dict['is_geb'] = order.is_geb
        #     sales_dict['is_geb_verified'] = order.is_geb_verified
        #
        #     sales_results.append(sales_dict)
        # return Response({"results": sales_results})

    @decorators.action(detail=False, methods=['get'], url_path="transactions")
    def transactions(self, request, *args, **kwargs):
        user = request.user
        user_profile = UserProfile.objects.filter(user=user, department__name__in=['Sales']).first()
        if user_profile:
            salesPersonProfile = SalesPersonProfile.objects.filter(user=user).first()

            if salesPersonProfile.management_status == "Worker":
                return BadRequest({'error_type': "Not Authorized",
                                   'errors': [{'message': "please login with Admin Credentials"}]})
            else:
                cities = request.GET.get('cities', [])
                total = 0.000
                transaction_date = datetime.today()
                if request.GET.get('date'):
                    transaction_date = datetime.strptime(request.GET.get('date'), '%d/%m/%Y')
                print(cities)
                if cities and cities != "undefined":
                    cities = json.loads(cities)
                    cities = [int(c) for c in cities]
                    if len(cities) > 0:
                        salesProfiles = SalesPersonProfile.objects.filter(user__addresses__city__in=cities).exclude(
                            user=user).distinct()

                        queryset = SalesTransaction.objects.filter(transaction_date=transaction_date,
                                                                   transaction_type="Credit",
                                                                   is_trial=False,
                                                                   salesPerson__in=salesProfiles)
                        for item in queryset:
                            total = total + float(item.transaction_amount)
                    else:
                        return BadRequest({'error_type': "Validation Error",
                                           'errors': [{'message': "please provide at least one city to filter"}]})
                else:
                    queryset = SalesTransaction.objects.none()
        else:
            return BadRequest({'error_type': "Not Authorized",
                               'errors': [{'message': "No User Profile"}]})
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = SalesTransactionShortSerializer(page, many=True)
            return self.get_paginated_response({"data": serializer.data, "total": total})

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @decorators.action(detail=False, methods=['get'], url_path="profile")
    def profile(self, request, *args, **kwargs):
        user = request.user
        user_profile = UserProfile.objects.filter(user=user, department__name__in=['Sales']).first()
        if user_profile:
            salesPersonProfile = SalesPersonProfile.objects.filter(user=user).first()
            if salesPersonProfile:
                user_cities = []
                user_addresses = user.addresses.all()
                default_address = user.default_address
                city_dict = {}
                if default_address:
                    city_dict['id'] = default_address.city.id
                    city_dict['city_name'] = default_address.city.city_name
                if user_addresses:
                    for user_address in user_addresses:
                        cities_dict = {}
                        cities_dict['id'] = user_address.city.id
                        cities_dict['city_name'] = user_address.city.city_name
                        user_cities.append(cities_dict)
                user_cities = list({user_city['id']: user_city for user_city in user_cities}.values())
                return Response({"results": {"cities": user_cities, "city": city_dict}})
            else:
                return NotFound({'error_type': "ValidationError",
                                 'errors': [{'message': "Sales Person Profile Not found"}]})
        else:
            return NotFound({'error_type': "ValidationError",
                             'errors': [{'message': "User Profile Not found"}]})


class SalesDashboardViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = RetailerDashboardSerializer
    pagination_class = PaginationWithLimit
    queryset = Retailer.objects.all()

    # filter_backends = (filters.DjangoFilterBackend,)
    # filterset_fields = {'name_of_shop': ['startswith']}

    def get_serializer_class(self):
        short = self.request.GET.get('short', False)
        beat_short = self.request.GET.get('beat_short', False)

        if beat_short == "true":

            return ShortBeatRetailerSerializer
        elif short == "true":

            return ShortRetailerSerializer
        return self.serializer_class

    def get_serializer_context(self):
        context = super(SalesDashboardViewSet, self).get_serializer_context()
        if self.request:
            context.update({'request': self.request, 'days': self.request.GET.get('days', 7)})
        return context

    @decorators.action(detail=False, methods=['get'], url_path="retailer_list")
    def retailer_list(self, request, *args, **kwargs):
        user = request.user
        user_profile = UserProfile.objects.filter(user=user, department__name__in=['Sales']).first()
        if user_profile:
            salesPersonProfile = SalesPersonProfile.objects.filter(user=user).first()
            if salesPersonProfile:
                sales = self.request.GET.get('sales', False)
                unbranded = self.request.GET.get('unbranded', False)
                if unbranded == "true":
                    queryset = self.get_queryset().filter(rate_type="unbranded")
                else:
                    if salesPersonProfile.is_adhoc_profile == True and sales == "true":
                        queryset = self.get_queryset().filter()
                    else:
                        queryset = self.get_queryset().filter(salesPersonProfile=salesPersonProfile)

            else:
                return Forbidden({'error_type': "permission_denied",
                                  'errors': [{'message': "You do not have permission to perform this action."}]})
        else:
            return Forbidden({'error_type': "permission_denied",
                              'errors': [{'message': "You do not have permission to perform this action."}]})
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        # print(queryset)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @decorators.action(detail=False, methods=['get'], url_path="retailer_detail")
    def retailer_detail(self, request, *args, **kwargs):
        retailer_id = request.GET.get('retailer_id')
        try:
            instance = Retailer.objects.get(id=retailer_id)
            serializer = self.get_serializer(instance,
                                             context={"request": request, 'days': self.request.GET.get('days', 7)})
            return Response(serializer.data)
        except Retailer.DoesNotExist:
            return NotFound({'error_type': "ValidationError",
                             'errors': [{'message': " Retailer Not found"}]})

    @decorators.action(detail=False, methods=['get'], url_path="retailer_ledger")
    def retailer_ledger(self, request, *args, **kwargs):
        retailer_id = request.GET.get('retailer_id')
        try:
            retailer = Retailer.objects.get(id=retailer_id)
            orderbyList = ['-transaction_date', '-id']  # default order
            salesTransactions = SalesTransaction.objects.filter(retailer=retailer, ).order_by(*orderbyList)
            salesTransactions = salesTransactions.filter(~Q(transaction_type="Cancelled"))
            print(salesTransactions)
            page = self.paginate_queryset(salesTransactions)
            if page is not None:
                serializer = SalesRetailerLedgerSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            serializer = SalesRetailerLedgerSerializer(salesTransactions, many=True)
            return Response(serializer.data)
        except Retailer.DoesNotExist:
            return NotFound({'error_type': "ValidationError",
                             'errors': [{'message': " Retailer Not found"}]})


class SalesDemandViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = RetailerDemandSerializer
    queryset = RetailerDemand.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ('retailer', 'date')

    def list(self, request, *args, **kwargs):
        user = request.user
        queryset = RetailerDemand.objects.all()

        serializer = RetailerDemandSerializer(queryset, many=True)
        return Response(serializer.data)

    @decorators.action(detail=False, methods=['post'], url_path="demand_create")
    def demand_create(self, request, *args, **kwargs):
        user = request.user
        data = request.data
        user_profile = UserProfile.objects.filter(user=user, department__name__in=['Sales']).first()
        if user_profile:
            salesPersonProfile = SalesPersonProfile.objects.filter(user=user).first()
            if salesPersonProfile:
                beat_create_serializer = BeatAssignmentSerializer(data=data)
                beat_create_serializer.is_valid(raise_exception=True)
                beatDate = datetime.strptime(data.get('beat_date'),
                                             '%Y-%m-%d').date()
                assignments = BeatAssignment.objects.filter(beat_type="Adhoc", beat_date=beatDate)
                # might be possible model has no records so make sure to handle None
                assignment_max_number = assignments.aggregate(Max('beat_type_number'))[
                                            'beat_type_number__max'] + 1 if assignments else 1
                beatAssignment = beat_create_serializer.save(beat_demand_by=salesPersonProfile,
                                                             beat_material_status="Demand",
                                                             beat_type_number=assignment_max_number)
                demands = data.get('demands', [])
                salesDemands = data.get('salesDemands', [])
                if salesDemands:
                    salesDemands = json.loads(salesDemands)
                    sales_demand_serializer = SalesDemandSKUCreateSerializer(data=salesDemands, many=True)
                    sales_demand_serializer.is_valid(raise_exception=True)
                    salesDemand = sales_demand_serializer.save(beatAssignment=beatAssignment)

                if demands:
                    demands = json.loads(demands)
                    for demand in demands:
                        retailer_demand_serializer = RetailerDemandCreateSerializer(data=demand)
                        retailer_demand_serializer.is_valid(raise_exception=True)
                        retailerDemand = retailer_demand_serializer.save(beatAssignment=beatAssignment)
                        # print(demand)
                        # demand_skus = demand['demand_skus']
                        # if demand_skus:
                        #     retailer_demand_sku_serializer = RetailerDemandSKUCreateSerializer(data=demand_skus, many=True)
                        #     retailer_demand_sku_serializer.is_valid(raise_exception=True)
                        #     retailer_demand_sku_serializer.save(retailerDemand=retailerDemand)
                        # else:
                        #     return BadRequest({'error_type': "Validation Error",
                        #                    'errors': [{'message': "Demand skus can not be empty"}]})

                return Response({"results": BeatAssignmentDetailSerializer(beatAssignment).data})
            else:
                return BadRequest({'error_type': "Validation Error",
                                   'errors': [{'message': "Permission Denied for user"}]})

    @decorators.action(detail=False, methods=['post'], url_path="update_status")
    def update_status(self, request, *args, **kwargs):
        user = request.user
        data = request.data
        user_profile = UserProfile.objects.filter(user=user, department__name__in=['Distribution', 'Sales']).first()
        if user_profile:
            distributionPersonProfile = DistributionPersonProfile.objects.filter(user=user).first()

            salesPersonProfile = SalesPersonProfile.objects.filter(user=user).first()
            if distributionPersonProfile:
                retailerDemand = RetailerDemand.objects.get(id=int(data.get('id')))
                if not data.get('retailer_status') == "No Action":
                    retailerDemand.retailer_status = data.get('retailer_status')
                    retailerDemand.save()
            else:
                return BadRequest({'error_type': "Validation Error",
                                   'errors': [{'message': "Permission Denied for user"}]})
                # retailerDemand = RetailerDemand.objects.get(id=int(data.get('id')))
                # if not request.data.retailer_status == "No Action":
                #     retailerDemand.retailer_status = data.get('retailer_status')
                #     retailerDemand.save()
            return Response({"results": "Updated status successfully"})
        else:
            return BadRequest({'error_type': "Validation Error",
                               'errors': [{'message': "Permission Denied for user"}]})

    @decorators.action(detail=False, methods=['post'], url_path="supply_adjust")
    def supply_adjust(self, request, *args, **kwargs):
        user = request.user
        data = request.data
        user_profile = UserProfile.objects.filter(user=user, department__name__in=['Warehouse']).first()
        if user_profile:
            warehousePersonProfile = WarehousePersonProfile.objects.filter(user=user).first()
            if warehousePersonProfile:
                beat_warehouse_supply_serializer = BeatWarehouseSupplySerializer(data=data)
                beat_warehouse_supply_serializer.is_valid(raise_exception=True)
                beatWarehouseSupply = beat_warehouse_supply_serializer.save(beat_supply_by=warehousePersonProfile)
                beat_date = datetime.strptime(request.data.get('beat_date'),
                                              '%Y-%m-%d')
                beatAssignments = BeatAssignment.objects.filter(beat_date=beat_date, beat_material_status="Demand")
                for beatAssignment in beatAssignments:
                    beatAssignment.beat_material_status = "Supply"
                    beatAssignment.save()

                # TODO product_id and quantity
                skusPacked = data.get('skusPacked', [])
                if skusPacked:
                    skusPacked = json.loads(skusPacked)
                    print(skusPacked)
                    for demand_sku in skusPacked:
                        sales_supply_packed_serialzer = SalesSupplyPackedSkuSerializer(data=demand_sku)
                        sales_supply_packed_serialzer.is_valid(raise_exception=True)
                        sales_supply_packed_serialzer.save(beatWarehouseSupply=beatWarehouseSupply)
                salesDemand = data.get('salesDemand', [])
                if salesDemand:
                    salesDemand = json.loads(salesDemand)
                    print(salesDemand)
                    for demand_sku in salesDemand:
                        sales_supply_serializer = SalesSupplySkuSerializer(data=demand_sku)
                        sales_supply_serializer.is_valid(raise_exception=True)
                        sales_supply_serializer.save(beatWarehouseSupply=beatWarehouseSupply)

                return Response({"results": "Supply Updated Successfully"})
            else:
                return BadRequest({'error_type': "Validation Error",
                                   'errors': [{'message': "Permission Denied for user"}]})

    @decorators.action(detail=False, methods=['post'], url_path="supply_sm_adjust")
    def supply_sm_adjust(self, request, *args, **kwargs):
        user = request.user
        data = request.data
        user_profile = UserProfile.objects.filter(user=user, department__name__in=['Sales']).first()
        if user_profile:
            salesPersonProfile = SalesPersonProfile.objects.filter(user=user).first()
            if salesPersonProfile:
                if salesPersonProfile.management_status == "Manager":
                    sm_data = data.get('sm_data', [])
                    beat_warehouse_supply = int(data.get('beat_warehouse_supply'))
                    if sm_data:
                        sm_data = json.loads(sm_data)
                        print(sm_data)
                        for sm_mini_data in sm_data:
                            beat_sm_supply_serializer = BeatSMApprovalSerializer(data=sm_mini_data)
                            beat_sm_supply_serializer.is_valid(raise_exception=True)
                            beatSMApproval = beat_sm_supply_serializer.save(
                                beat_warehouse_supply_id=beat_warehouse_supply,
                                beat_supply_approved_by=salesPersonProfile)
                            beat_date = datetime.strptime(sm_mini_data.get('beat_date'),
                                                          '%Y-%m-%d')
                            beatAssignments = BeatAssignment.objects.filter(beat_date=beat_date,
                                                                            beat_material_status="Supply")
                            for beatAssignment in beatAssignments:
                                beatAssignment.beat_material_status = "SMApproved"
                                beatAssignment.save()

                            # TODO product_id and qunatity and demand_classification
                            salesDemand = sm_mini_data.get('salesDemand', [])
                            if salesDemand:
                                # salesDemand = json.loads(salesDemand)
                                print(salesDemand)
                                for demand_sku in salesDemand:
                                    sales_sm_supply_serializer = SalesSMApprovalSerializer(data=demand_sku)
                                    sales_sm_supply_serializer.is_valid(raise_exception=True)
                                    sales_sm_supply_serializer.save(beatSMApproval=beatSMApproval)

                        return Response({"results": "Supply Approved Successfully"})
                    else:
                        return BadRequest({'error_type': "Validation Error",
                                           'errors': [{'message': "Data should not be empty"}]})

                else:
                    return BadRequest({'error_type': "Validation Error",
                                       'errors': [{'message': "Not a Sales Admin Manager"}]})

            else:
                return BadRequest({'error_type': "Validation Error",
                                   'errors': [{'message': "Permission Denied for user"}]})

    @decorators.action(detail=False, methods=['post'], url_path="supply_rh_adjust")
    def supply_rh_adjust(self, request, *args, **kwargs):
        user = request.user
        data = request.data
        user_profile = UserProfile.objects.filter(user=user, department__name__in=['Sales']).first()
        if user_profile:
            salesPersonProfile = SalesPersonProfile.objects.filter(user=user).first()
            if salesPersonProfile:
                sm_data = data.get('sm_data', [])
                if sm_data:
                    sm_data = json.loads(sm_data)
                    for sm_mini_data in sm_data:
                        beat_rh_supply_serializer = BeatRHApprovalSerializer(data=sm_mini_data)
                        beat_rh_supply_serializer.is_valid(raise_exception=True)
                        beatSMApproval = int(data.get('beatSMApproval'))
                        beatRHApproval = beat_rh_supply_serializer.save(beatSMApproval_id=beatSMApproval,
                                                                        beat_supply_approved_by=salesPersonProfile)
                        beatAssignment = BeatAssignment.objects.get(id=sm_mini_data.get('beat_assignment_id'))
                        beatAssignment.beat_material_status = "RHApproved"

                        # TODO Material Status to supply
                        salesDemand = sm_mini_data.get('salesDemand', [])
                        if salesDemand:
                            # salesDemand = json.loads(salesDemand)
                            print(salesDemand)
                            for demand_sku in salesDemand:
                                print(demand_sku)
                                sales_rh_supply_serializer = SalesRHApprovalSerializer(data=demand_sku)
                                sales_rh_supply_serializer.is_valid(raise_exception=True)
                                sales_rh_supply_serializer.save(beatRHApproval=beatRHApproval)

                                sales_demand_sku = SalesDemandSKU.objects.get(id=demand_sku['id'])
                                sales_demand_sku.product_supply_quantity = demand_sku['product_quantity']
                                sales_demand_sku.save()
                        beatAssignment.save()
                    return Response({"results": "Supply Assigned to beats"})
                else:
                    return BadRequest({'error_type': "Validation Error",
                                       'errors': [{'message': "Data cannot be empty"}]})
                # if demands:
                #     demands = json.loads(demands)
                # for demand in demands:
                #     retailerDemand = RetailerDemand.objects.get(id=data.get('retailerDemand'))
                #     demand_skus = demand['demand_skus']
                #     if demand_skus:
                #         for demand_sku in demand_skus:
                #             retailer_demand_sku = RetailerDemandSKU.objects.get(id=demand_sku.id)
                #             retailer_demand_sku.product_supply_quantity = demand_sku.product_supply_quantity
                #             retailer_demand_sku.save()
                #     else:
                #         return BadRequest({'error_type': "Validation Error",
                #                            'errors': [{'message': "Demand skus can not be empty"}]})

            else:
                return BadRequest({'error_type': "Validation Error",
                                   'errors': [{'message': "Permission Denied for user"}]})
