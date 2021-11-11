import json
from datetime import timedelta, datetime

import coreapi
from django.db.models import Q
from django_filters import rest_framework as filters
from rest_framework import viewsets, mixins, permissions, decorators
from rest_framework.filters import BaseFilterBackend

from base.response import Response, BadRequest, Created, NotFound
from base.views import PaginationWithNoLimit
from custom_auth.models import UserProfile
from distributionchain.api import BeatAssignmentSerializer, \
    DistributionPersonShortSerializer, BeatAssignmentDummySerializer, RetailerBeatWiseSerializer, \
    RetailerBeatUpdateSerializer, BeatAssignmentDetailSerializer, BeatWiseRetailerSerializer, BeatUpdateSerializer, \
    BeatWarehouseSupplyDetailSerializer, TransferSKUSerializer, BeatSMApprovalDetailSerializer, \
    BeatRHApprovalDetailSerializer, SMRelativeNumberSerializer
from distributionchain.models import DistributionPersonProfile, BeatAssignment, BeatWarehouseSupply, BeatSMApproval, \
    TripSKUTransfer, TransferSKU, BeatRHApproval, SMRelativeNumber
from finance.models import FinanceProfile
from order.api.serializers import OrderHistorySerializer, OrderReturnLineSerializer
from order.models import Order
from order.models.Order import OrderReturnLine
from payment.api.serializers import SalesTransactionSerializer, PaymentSerializer
from payment.models import SalesTransaction, Payment
from retailer.api.serializers import RetailerDashboardShortSerializer, ShortBeatRetailerSerializer, \
    ShortRetailerSerializer, RetailerSalesSerializer
from retailer.models import Retailer
from saleschain.models import SalesPersonProfile, SalesDemandSKU
from warehouse.api.serializers import AdhocVehicleSerializer
from warehouse.models import WarehousePersonProfile, Vehicle


class SimpleFilterBackend(BaseFilterBackend):
    def get_schema_fields(self, view):
        return [coreapi.Field(
            name='beat_number',
            location='query',
            required=True,
            type='int'
        )]


class TripSKUTransferViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin):
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = PaginationWithNoLimit
    serializer_class = TransferSKUSerializer
    queryset = TripSKUTransfer.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ('beat_date', 'transfer_type', 'from_warehouse', 'to_warehouse', 'from_distributor',
                        'to_distributor', 'from_beat', 'to_beat', 'transfer_status')

    @decorators.action(detail=False, methods=['get'], url_path="get_transfer_list")
    def get_transfer_list(self, request, *args, **kwargs):
        user = request.user
        user_profile = UserProfile.objects.filter(user=user,
                                                  department__name__in=['Distribution', 'Warehouse', 'Sales']).first()
        if user_profile:
            queryset = TripSKUTransfer.objects.all()
        else:
            return BadRequest({'error_type': "Not Authorized",
                               'errors': [{'message': "No User Profile"}]})
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = TransferSKUSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = TransferSKUSerializer(queryset, many=True)
        return Response(serializer.data)


class DistributionProfileViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin):
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = PaginationWithNoLimit
    serializer_class = DistributionPersonShortSerializer
    queryset = DistributionPersonProfile.objects.all()
    filter_backends = (SimpleFilterBackend,)

    def list(self, request, *args, **kwargs):
        user = request.user
        user_profile = UserProfile.objects.filter(user=user, department__name__in=['Distribution', 'Sales']).first()
        if user_profile:
            queryset = DistributionPersonProfile.objects.all()
            # distributionPersonProfile = DistributionPersonProfile.objects.filter(user=user).first()
            # warehouse = request.data.get("warehouse_id", 1)
            # if distributionPersonProfile.management_status == "Worker":
            #     return BadRequest({'error_type': "Not Authorized",
            #     return BadRequest({'error_type': "Not Authorized",
            #                        'errors': [{'message': "please login with Admin Credentials"}]})
            # else:
            #     queryset = DistributionPersonProfile.objects.filter(warehouse=warehouse)
        else:
            return BadRequest({'error_type': "Not Authorized",
                               'errors': [{'message': "No User Profile"}]})
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @decorators.action(detail=False, methods=['get'], url_path="distributor_retailers")
    def distributor_retailers(self, request, *args, **kwargs):
        print(request.GET)
        user = request.user
        user_profile = UserProfile.objects.filter(user=user,
                                                  department__name__in=['Distribution', 'Sales', 'Finance']).first()
        short_data = request.GET.get('short', False)
        if short_data == "true":
            # retailerSerializer = ShortBeatRetailerSerializer
            retailerSerializer = RetailerSalesSerializer
        else:
            retailerSerializer = ShortRetailerSerializer
        if user_profile:
            distributionPersonProfile = DistributionPersonProfile.objects.filter(user=user).first()
            financeProfile = FinanceProfile.objects.filter(user=user).first()
            salesPersonProfile = SalesPersonProfile.objects.filter(user=user).first()
            unbranded = self.request.GET.get('unbranded', False)
            if distributionPersonProfile or financeProfile:

                if unbranded == "true":
                    queryset = Retailer.objects.filter(rate_type="unbranded")
                else:
                    if request.GET.get('beat_number'):
                        beat_number = request.GET.get('beat_number')
                        queryset = Retailer.objects.filter(beat_number=int(beat_number)).order_by('beat_order_number')
                    else:
                        queryset = Retailer.objects.filter().order_by('beat_order_number')

                print(queryset)
            elif salesPersonProfile:
                if unbranded == "true":
                    queryset = Retailer.objects.filter(rate_type="unbranded")
                else:
                    if request.GET.get('beat_number'):
                        beat_number = request.GET.get('beat_number')
                        queryset = Retailer.objects.filter(beat_number=int(beat_number),
                                                           salesPersonProfile=salesPersonProfile).order_by(
                            'beat_order_number')
                    else:
                        queryset = Retailer.objects.filter(salesPersonProfile=salesPersonProfile).order_by(
                            'beat_order_number')
                print(queryset)
            else:
                queryset = Retailer.objects.none()
        else:
            return BadRequest({'error_type': "Not Authorized",
                               'errors': [{'message': "No User Profile"}]})

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = retailerSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = retailerSerializer(queryset, many=True)
        return Response(serializer.data)

    @decorators.action(detail=False, methods=['get'], url_path="distributor_nonbeat_retailers")
    def distributor_nonbeat_retailers(self, request, *args, **kwargs):
        print(request.GET)
        user = request.user
        user_profile = UserProfile.objects.filter(user=user,
                                                  department__name__in=['Distribution', 'Sales', 'Finance'])
        if user_profile:
            if request.GET.get('beat_number'):
                beat_number = request.GET.get('beat_number')
                retailers = Retailer.objects.all().order_by(
                    'beat_order_number')
                retailers = retailers.filter(~Q(beat_number=int(beat_number)))

            else:
                retailers = Retailer.objects.all().order_by(
                    'beat_order_number')
        else:
            return BadRequest({'error_type': "Not Authorized",
                               'errors': [{'message': "No User Profile"}]})

        page = self.paginate_queryset(retailers)
        if page is not None:
            serializer = ShortBeatRetailerSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ShortBeatRetailerSerializer(retailers, many=True)
        return Response(serializer.data)

    @decorators.action(detail=False, methods=['get'], url_path="profile")
    def profile(self, request, *args, **kwargs):
        user = request.user
        user_profile = UserProfile.objects.filter(user=user, department__name__in=['Distribution']).first()
        if user_profile:
            distributionPersonProfile = DistributionPersonProfile.objects.filter(user=user).first()
            if distributionPersonProfile:
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
                                 'errors': [{'message': "Distribution Person Profile Not found"}]})
        else:
            return NotFound({'error_type': "ValidationError",
                             'errors': [{'message': "User Profile Not found"}]})


class DistributionBeatViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin):
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = PaginationWithNoLimit
    # serializer_class = BeatAssignmentDetailSerializer
    serializer_class = BeatAssignmentSerializer
    queryset = BeatAssignment.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ('beat_status', 'beat_number', 'distributor', 'beat_person', 'beat_date',
                        'beat_material_status', 'demand_classification', 'beat_type')

    def get_serializer_class(self):
        if self.action == "print_beat":
            return BeatAssignmentDummySerializer
        else:
            return BeatAssignmentDetailSerializer

    @decorators.action(detail=False, methods=['get'], url_path="current_beat_list")
    def current_beat_list(self, request, *args, **kwargs):
        queryset = BeatAssignment.objects.all()
        serializer = BeatAssignmentDetailSerializer(queryset, many=True)
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        user = request.user
        queryset = self.filter_queryset(self.get_queryset())
        admin = UserProfile.objects.filter(user=user, department__name__in=['Admin']).first()
        user_profile = UserProfile.objects.filter(user=user,
                                                  department__name__in=['Distribution', 'Sales', 'Warehouse']).first()
        if user_profile or admin:
            if admin:
                queryset = self.filter_queryset(self.get_queryset())
            else:
                distributionPersonProfile = DistributionPersonProfile.objects.filter(user=user).first()
                salesPersonProfile = SalesPersonProfile.objects.filter(user=user).first()
                warehouseProfile = WarehousePersonProfile.objects.filter(user=user).first()
                if distributionPersonProfile:
                    if distributionPersonProfile.management_status == "Worker":
                        queryset = self.filter_queryset(self.get_queryset()).filter(
                            distributor=distributionPersonProfile, )
                    else:
                        queryset = self.filter_queryset(self.get_queryset())
                elif salesPersonProfile:
                    queryset = self.filter_queryset(self.get_queryset())
                else:
                    queryset = self.filter_queryset(
                        self.get_queryset().filter(warehouse_id=warehouseProfile.warehouse.id))
        else:
            return BadRequest({'error_type': "Not Authorized",
                               'errors': [{'message': "No User Profile"}]})
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @decorators.action(detail=False, methods=['get'], url_path="current_beat")
    def current_beat(self, request, *args, **kwargs):
        user = request.user
        data = request.data
        print(user)
        print(request)

        user_profile = UserProfile.objects.filter(user=user,
                                                  department__name__in=['Distribution', 'Sales', 'Warehouse']).first()
        if user_profile:
            distributionPersonProfile = DistributionPersonProfile.objects.filter(user=user).first()
            salesPersonProfile = SalesPersonProfile.objects.filter(user=user).first()
            warehousePersonProfile = WarehousePersonProfile.objects.filter(user=user).first()
            if distributionPersonProfile:
                queryset = BeatAssignment.objects.filter(distributor=distributionPersonProfile)
                if request.GET.get('beat_date'):
                    beat_date = datetime.strptime(request.GET.get('beat_date'), '%d-%m-%Y')
                    queryset = queryset.filter(beat_date=beat_date)
                    print(queryset)
                serializer = self.get_serializer(queryset, many=True)
                return Response(serializer.data)

            if salesPersonProfile:
                queryset = BeatAssignment.objects.filter(beat_demand_by=salesPersonProfile)
                if request.GET.get('beat_date'):
                    beat_date = datetime.strptime(request.GET.get('beat_date'), '%d-%m-%Y')
                    queryset = queryset.filter(beat_date=beat_date)

                serializer = self.get_serializer(queryset, many=True)
                return Response(serializer.data)
            else:
                queryset = BeatAssignment.objects.filter(warehouse=warehousePersonProfile.warehouse)
                if request.GET.get('beat_date'):
                    beat_date = datetime.strptime(request.GET.get('beat_date'), '%d-%m-%Y')
                    queryset = queryset.filter(beat_date=beat_date)
                print(queryset)
                serializer = self.get_serializer(queryset, many=True)
                return Response(serializer.data)

    @decorators.action(detail=False, methods=['post'], url_path="vehicle_assign")
    def vehicle_assign(self, request, *args, **kwargs):
        user = request.user
        data = request.data
        print(user)
        print(data)
        admin = UserProfile.objects.filter(user=user, department__name__in=['Admin']).first()
        user_profile = UserProfile.objects.filter(user=user, department__name__in=['Distribution']).first()
        print(admin)
        print(user_profile)
        if user_profile or admin:
            if admin:
                pass
            else:
                distributionPersonProfile = DistributionPersonProfile.objects.filter(user=user).first()
                if distributionPersonProfile:
                    if distributionPersonProfile.management_status == "Worker":
                        return BadRequest({'error_type': "Not Authorized",
                                           'errors': [{'message': "please login with Admin Credentials"}]})
                    else:
                        trip_id = request.data.get('beatAssignment_id')

                        beatAssignemnt = BeatAssignment.objects.get(id=trip_id)
                        if request.data.get('vehicle_id'):
                            vehicle_id = request.data.get('vehicle_id')
                            if request.data.get('sc_in_time'):
                                sc_in_time = datetime.strptime(request.data.get('sc_in_time'), '%H:%M:%S').time()
                            else:
                                sc_in_time = beatAssignemnt.time
                            vehicle = Vehicle.objects.get(id=vehicle_id)
                            beatAssignemnt.vehicle = vehicle
                            beatAssignemnt.sc_in_time = sc_in_time
                            if request.data.get('driver_id'):
                                driver_id = request.data.get('driver_id')
                                beatAssignemnt.driver_id = driver_id
                            else:
                                beatAssignemnt.driver = vehicle.default_driver
                        else:
                            adhoc_vehicle_serializer = AdhocVehicleSerializer(data=data)
                            adhoc_vehicle_serializer.is_valid(raise_exception=True)
                            adhoc_vehicle = adhoc_vehicle_serializer.save()
                            beatAssignemnt.adhoc_vehicle = adhoc_vehicle
                        beatAssignemnt.beat_status = "Assigned"
                        beatAssignemnt.save()
                        return Created({"success": "Beat Assignment Created Successfully"})
        else:
            return BadRequest({'error_type': "Not Authorized",
                               'errors': [{'message': "No User Profile"}]})

    @decorators.action(detail=False, methods=['post'], url_path="update_beat")
    def update_beat(self, request, *args, **kwargs):
        user = request.user
        data = request.data
        print(user)
        print(data)
        user_profile = UserProfile.objects.filter(user=user,
                                                  department__name__in=['Sales', 'Distribution', 'Warehouse']).first()
        print(user_profile)
        if user_profile:
            distributionPersonProfile = DistributionPersonProfile.objects.filter(user=user).first()
            warehousePersonProfile = WarehousePersonProfile.objects.filter(user=user).first()
            salesPersonProfile = SalesPersonProfile.objects.filter(user=user).first()
            if distributionPersonProfile and distributionPersonProfile.management_status == "Worker":
                return BadRequest({'error_type': "Not Authorized",
                                   'errors': [{'message': "No Permission"}]})
            else:
                beatAssignment = BeatAssignment.objects.get(id=int(data.get('id')))
                beatAssignment.distributor_id = int(data.get('distributor'))
                beatAssignment.save()
                return Response(BeatAssignmentDetailSerializer(beatAssignment).data)

    @decorators.action(detail=False, methods=['post'], url_path="update_trip_status")
    def update_trip_status(self, request, *args, **kwargs):
        user = request.user
        data = request.data
        print(user)
        print(data)
        user_profile = UserProfile.objects.filter(user=user,
                                                  department__name__in=['Sales', 'Distribution', 'Warehouse',
                                                                        'Finance']).first()
        print(user_profile)
        if user_profile:
            distributionPersonProfile = DistributionPersonProfile.objects.filter(user=user).first()
            warehousePersonProfile = WarehousePersonProfile.objects.filter(user=user).first()
            salesPersonProfile = SalesPersonProfile.objects.filter(user=user).first()
            financeProfile = FinanceProfile.objects.filter(user=user).first()
            if distributionPersonProfile and distributionPersonProfile.management_status == "Worker":
                beatAssignment = BeatAssignment.objects.get(id=int(data.get('id')))
                if data.get('distributor_trip_status'):
                    beatAssignment.distributor_trip_status = data.get('distributor_trip_status')
                    beatAssignment.save()
                    return Response(BeatAssignmentDetailSerializer(beatAssignment).data)
            else:
                beatAssignment = BeatAssignment.objects.get(id=int(data.get('id')))
                if data.get('warehouse_trip_status'):
                    beatAssignment.distributor_trip_status = data.get('warehouse_trip_status')
                    beatAssignment.save()
                    return Response(BeatAssignmentDetailSerializer(beatAssignment).data)
                elif data.get('finance_trip_status'):
                    beatAssignment.distributor_trip_status = data.get('finance_trip_status')
                    beatAssignment.save()
                    return Response(BeatAssignmentDetailSerializer(beatAssignment).data)

    @decorators.action(detail=False, methods=['post'], url_path="vehicle_report")
    def vehicle_report(self, request, *args, **kwargs):
        user = request.user
        data = request.data
        print(user)
        print(data)
        admin = UserProfile.objects.filter(user=user, department__name__in=['Admin']).first()
        user_profile = UserProfile.objects.filter(user=user, department__name__in=['Warehouse']).first()
        print(admin)
        print(user_profile)
        if user_profile or admin:
            if admin:
                trip_id = request.data.get('beatAssignment_id')
                beatAssignemnt = BeatAssignment.objects.get(id=trip_id)
                if beatAssignemnt.beat_material_status == "Demand" or beatAssignemnt.beat_material_status == "Supply" or beatAssignemnt.beat_material_status == "SMApproved" or beatAssignemnt.beat_material_status == "RHApproved":
                    if beatAssignemnt.beat_status == "Assigned":
                        beatAssignemnt.ODO_in = request.data.get('ODO_in')
                        in_time = datetime.strptime(request.data.get('in_time'), '%H:%M:%S').time()
                        beatAssignemnt.in_time = in_time
                        beatAssignemnt.beat_status = "Scheduled"
                        beatAssignemnt.beat_material_status = "Reported"
                        beatAssignemnt.save()
                        return Created({"success": "Beat Assignment Reported Successfully"})
                    else:
                        return BadRequest({'error_type': "Not Authorized",
                                           'errors': [{'message': "Vehicle Not Assigned yet"}]})
                elif beatAssignemnt.beat_material_status == "Reported":
                    out_time = datetime.strptime(request.data.get('out_time'), '%H:%M:%S').time()
                    beatAssignemnt.out_time = out_time
                    beatAssignemnt.beat_status = "Ongoing"
                    beatAssignemnt.beat_material_status = "Loaded"
                    cart_products = data.get('cart_products', [])
                    if cart_products:
                        cart_products = json.loads(cart_products)
                        for cart_product in cart_products:
                            # salesDemand = SalesDemandSKU.objects.get(beatAssignment=beatAssignemnt,
                            #                                          product=cart_product.get('product'))
                            salesDemand = SalesDemandSKU.objects.get(id=cart_product.get('id'))
                            salesDemand.product_out_quantity = int(cart_product.get('quantity'))
                            salesDemand.save()

                    beatAssignemnt.save()
                    return Created({"success": "Beat Assignment Scheduled Successfully"})
                elif beatAssignemnt.beat_material_status == "Loaded":
                    beatAssignemnt.ODO_return = request.data.get('ODO_return')
                    return_time = datetime.strptime(request.data.get('return_time'), '%H:%M:%S').time()
                    beatAssignemnt.return_time = return_time
                    beatAssignemnt.beat_status = "Completed"
                    beatAssignemnt.beat_material_status = "Closed"
                    cart_products = data.get('cart_products', [])
                    if cart_products:
                        cart_products = json.loads(cart_products)
                        for cart_product in cart_products:
                            salesDemand = SalesDemandSKU.objects.get(id=cart_product.get('id'))
                            salesDemand.product_in_quantity = int(cart_product.get('quantity'))
                            salesDemand.product_fresh_in_quantity = int(cart_product.get('quantity'))
                            salesDemand.product_return_repalce_in_quantity = int(cart_product.get('old_quantity'))
                            salesDemand.product_fresh_stock_validated = cart_product.get('fresh_validated')
                            salesDemand.product_old_stock_validated = cart_product.get('old_validated')

                            salesDemand.save()
                    beatAssignemnt.save()
                    return Created({"success": "Beat Assignment Completed Successfully"})
                else:
                    return BadRequest({'error_type': "Not Authorized",
                                       'errors': [{'message': "No Proper Status"}]})
            else:
                warehousePersonProfile = WarehousePersonProfile.objects.filter(user=user).first()
                if warehousePersonProfile:
                    # if warehousePersonProfile.management_status == "Worker":
                    #     return BadRequest({'error_type': "Not Authorized",
                    #                        'errors': [{'message': "please login with Admin Credentials"}]})
                    # else:
                    trip_id = request.data.get('beatAssignment_id')
                    beatAssignemnt = BeatAssignment.objects.get(id=trip_id)
                    if beatAssignemnt.beat_material_status == "Demand" or beatAssignemnt.beat_material_status == "Supply" or beatAssignemnt.beat_material_status == "SMApproved" or beatAssignemnt.beat_material_status == "RHApproved":
                        if beatAssignemnt.beat_status == "Assigned":
                            beatAssignemnt.ODO_in = request.data.get('ODO_in')
                            in_time = datetime.strptime(request.data.get('in_time'), '%H:%M:%S').time()
                            beatAssignemnt.in_time = in_time
                            beatAssignemnt.beat_status = "Scheduled"
                            beatAssignemnt.beat_material_status = "Reported"
                            beatAssignemnt.save()
                            return Created({"success": "Beat Assignment Reported Successfully"})
                        else:
                            return BadRequest({'error_type': "Not Authorized",
                                               'errors': [{'message': "Vehicle Not Assigned yet"}]})
                    elif beatAssignemnt.beat_material_status == "Reported":
                        out_time = datetime.strptime(request.data.get('out_time'), '%H:%M:%S').time()
                        beatAssignemnt.out_time = out_time
                        beatAssignemnt.beat_status = "Ongoing"
                        beatAssignemnt.beat_material_status = "Loaded"
                        cart_products = data.get('cart_products', [])
                        if cart_products:
                            cart_products = json.loads(cart_products)
                            for cart_product in cart_products:
                                salesDemand = SalesDemandSKU.objects.get(id=cart_product.get('id'))
                                salesDemand.product_out_quantity = int(cart_product.get('quantity'))
                                salesDemand.save()
                        beatAssignemnt.save()
                        return Created({"success": "Beat Assignment Scheduled Successfully"})
                    elif beatAssignemnt.beat_material_status == "Loaded":
                        beatAssignemnt.ODO_return = request.data.get('ODO_return')
                        return_time = datetime.strptime(request.data.get('return_time'), '%H:%M:%S').time()
                        beatAssignemnt.return_time = return_time
                        beatAssignemnt.beat_status = "Completed"
                        beatAssignemnt.beat_material_status = "Closed"
                        cart_products = data.get('cart_products', [])
                        if cart_products:
                            cart_products = json.loads(cart_products)
                            for cart_product in cart_products:
                                salesDemand = SalesDemandSKU.objects.get(id=cart_product.get('id'))
                                salesDemand.product_in_quantity = int(cart_product.get('quantity'))
                                salesDemand.product_fresh_in_quantity = int(cart_product.get('quantity'))
                                salesDemand.product_return_repalce_in_quantity = int(cart_product.get('old_quantity'))
                                salesDemand.product_fresh_stock_validated = cart_product.get('fresh_validated')
                                salesDemand.product_old_stock_validated = cart_product.get('old_validated')

                                salesDemand.save()
                        beatAssignemnt.save()
                        return Created({"success": "Beat Assignment Completed Successfully"})
                    else:
                        return BadRequest({'error_type': "Not Authorized",
                                           'errors': [{'message': "No Proper Status"}]})
        else:
            return BadRequest({'error_type': "Not Authorized",
                               'errors': [{'message': "No User Profile"}]})

    @decorators.action(detail=False, methods=['post'], url_path="assign")
    def assign(self, request, *args, **kwargs):
        user = request.user
        data = request.data
        print(user)
        print(data)
        admin = UserProfile.objects.filter(user=user, department__name__in=['Admin']).first()
        user_profile = UserProfile.objects.filter(user=user, department__name__in=['Distribution']).first()
        print(admin)
        print(user_profile)
        if user_profile or admin:
            if admin:
                beat_assignment_serializer = BeatAssignmentSerializer(data=data)
                beat_assignment_serializer.is_valid(raise_exception=True)
                beat_assignment_serializer.save()
                return Created({"success": "Beat Assignment Created Successfully"})
            else:
                distributionPersonProfile = DistributionPersonProfile.objects.filter(user=user).first()
                if distributionPersonProfile:
                    if distributionPersonProfile.management_status == "Worker":
                        return BadRequest({'error_type': "Not Authorized",
                                           'errors': [{'message': "please login with Admin Credentials"}]})
                    else:
                        beat_assignment_serializer = BeatAssignmentSerializer(data=data)
                        print(data)
                        beat_assignment_serializer.is_valid(raise_exception=True)
                        # distributor = DistributionPersonProfile.objects.filter(id=int(data['distributor'])).first()
                        beat_assignment_serializer.save(assigned_by=distributionPersonProfile,
                                                        beat_name=(data['beat_date']) + "-Beat-" + str(
                                                            data['beat_number']))

                        return Created({"success": "Beat Assignment Created Successfully"})
        else:
            return BadRequest({'error_type': "Not Authorized",
                               'errors': [{'message': "No User Profile"}]})

    @decorators.action(detail=False, methods=['get'], url_path="other_beat_list")
    def other_beat_list(self, request, *args, **kwargs):
        user = request.user
        data = request.data
        print(user)
        print(data)
        if request.GET.get('beat_assignment_id'):
            beat_date = datetime.strptime(request.GET.get('beat_date'), '%d-%m-%Y')
            beat_id = request.GET.get('beat_assignment_id')
            queryset = BeatAssignment.objects.filter(beat_date=beat_date).order_by('-beat_date')
            queryset = queryset.filter(~Q(id=beat_id))
            serializer = BeatAssignmentDetailSerializer(queryset, many=True)
            return Response(serializer.data)
        else:
            return BadRequest({'error_type': "Invalid Request",
                               'errors': [{'message': "Send current Beat Id"}]})

    @decorators.action(detail=False, methods=['post'], url_path="transfer_beat_skus")
    def transfer_beat_skus(self, request, *args, **kwargs):
        user = request.user
        data = request.data
        print(user)
        print(data)
        from_warehouse = None
        from_beat = None
        to_beat = None
        to_warehouse = None
        from_warehouse_person = None
        if request.data.get('beat_assignment_id') or request.data.get('from_warehouse'):
            beat_date = datetime.strptime(request.data.get('beat_date'), '%d-%m-%Y')
            transfer_type = request.data.get('transfer_type')
            if request.data.get('beat_assignment_id'):
                beat_id = request.data.get('beat_assignment_id')
                from_beat = BeatAssignment.objects.filter(id=int(beat_id)).first()
                if request.data.get('transfer_type') == "beat":
                    to_beat_id = request.data.get('to_beat_assignment_id')
                    to_beat = BeatAssignment.objects.filter(id=to_beat_id).first()
                # TODO to Warehouse id
                else:
                    to_warehouse = request.data.get('to_warehouse')
            else:
                from_warehouse = request.data.get('from_warehouse')
                from_warehouse_person = request.data.get('from_warehouse_person')
                if request.data.get('transfer_type') == "satellite":
                    to_warehouse = request.data.get('to_warehouse')
                else:
                    to_beat_id = request.data.get('to_beat_assignment_id')
                    to_beat = BeatAssignment.objects.filter(id=to_beat_id).first()

            tripSKUTransfer = TripSKUTransfer.objects.create(
                from_distributor=from_beat.distributor if from_beat else None,
                to_distributor=to_beat.distributor if to_beat else None,
                from_warehouse_person_id=from_warehouse_person if from_warehouse_person else None,
                transfer_type=transfer_type,
                from_warehouse_id=from_warehouse if from_warehouse else None,
                to_warehouse_id=to_warehouse if to_warehouse else None,
                from_beat=from_beat if from_beat else None,
                to_beat=to_beat if to_beat else None,
                beat_date=beat_date)

            cart_products = data.get('cart_products', [])
            if cart_products:
                cart_products = json.loads(cart_products)
                for cart_product in cart_products:
                    TransferSKU.objects.create(tripSKUTransfer=tripSKUTransfer, product_id=cart_product.get('product'),
                                               quantity=int(cart_product.get('quantity')))
            return Response({})
        else:
            return BadRequest({'error_type': "Invalid Request",
                               'errors': [{'message': "Send current Beat Id"}]})

    @decorators.action(detail=False, methods=['post'], url_path="approve_transfer_beat_skus")
    def approve_transfer_beat_skus(self, request, *args, **kwargs):
        user = request.user
        data = request.data
        print(user)
        print(data)
        if request.data.get('beat_transfer_sku'):
            tripSKUTransfer = TripSKUTransfer.objects.filter(id=request.data.get('beat_transfer_sku')).first()
            skus = tripSKUTransfer.tripTransferSKU.all()
            if skus:
                if tripSKUTransfer.transfer_type == "beat" or tripSKUTransfer.transfer_type == "warehouse":
                    if tripSKUTransfer.transfer_type == "beat":
                        for sku in skus:
                            salesDemand = SalesDemandSKU.objects.get(beatAssignment=tripSKUTransfer.from_beat,
                                                                     product=sku.product)
                            salesDemand.product_transfer_quantity -= sku.quantity
                            salesDemand.save()

                            to_salesDemand = SalesDemandSKU.objects.get(beatAssignment=tripSKUTransfer.to_beat,
                                                                        product=sku.product)
                            to_salesDemand.product_transfer_quantity += sku.quantity
                            to_salesDemand.save()
                    else:
                        for sku in skus:
                            salesDemand = SalesDemandSKU.objects.get(beatAssignment=tripSKUTransfer.from_beat,
                                                                     product=sku.product)
                            salesDemand.product_transfer_quantity -= sku.quantity
                            salesDemand.save()

                            # TODO From Warehouse Approval

                else:
                    if tripSKUTransfer.transfer_type == "satellite" or tripSKUTransfer.transfer_type == "w-beat":
                        if tripSKUTransfer.transfer_type == "satellite":
                            # for sku in skus:
                            # TODO from and to warehouse
                            pass
                        else:
                            for sku in skus:
                                # TODO from warehouse
                                to_salesDemand = SalesDemandSKU.objects.get(beatAssignment=tripSKUTransfer.to_beat,
                                                                            product=sku.product)
                                to_salesDemand.product_transfer_quantity += sku.quantity
                                to_salesDemand.save()
                tripSKUTransfer.transfer_status = "Confirmed"
                tripSKUTransfer.save()
            return Response({})
        else:
            return BadRequest({'error_type': "Invalid Request",
                               'errors': [{'message': "Send current Beat Id"}]})

    @decorators.action(detail=False, methods=['get'], url_path="current_rh_trip")
    def current_rh_trip(self, request, *args, **kwargs):
        user = request.user
        data = request.data
        print(user)
        print(data)
        beat_date = datetime.strptime(request.GET.get('beat_date'), '%d-%m-%Y')
        beat_material_status = request.GET.get('beat_material_status', None)
        beat_status = request.GET.get('beat_status', None)
        if beat_material_status and beat_material_status != "undefined":
            beat_material_status = json.loads(beat_material_status)
            beat_material_status = [c for c in beat_material_status]
        if beat_status and beat_status != "undefined":
            beat_status = json.loads(beat_status)
            beat_status = [c for c in beat_status]
        user_profile = UserProfile.objects.filter(user=user,
                                                  department__name__in=['Sales']).first()

        if user_profile:
            salesPersonProfile = SalesPersonProfile.objects.filter(user=user).first()
            if BeatSMApproval.objects.filter(beat_date=beat_date,
                                             demand_classification=salesPersonProfile.demand_classification):
                beatQuerySet = BeatSMApproval.objects.filter(beat_date=beat_date,
                                                             demand_classification=salesPersonProfile.demand_classification)
            else:
                beatQuerySet = None

            if BeatRHApproval.objects.filter(beat_date=beat_date,
                                             beat_supply_approved_by=salesPersonProfile):
                beatRHQuerySet = BeatRHApproval.objects.filter(beat_date=beat_date,
                                                               beat_supply_approved_by=salesPersonProfile)
            else:
                beatRHQuerySet = None

            print(beatQuerySet)

            queryset = BeatAssignment.objects.filter(demand_classification=salesPersonProfile.demand_classification,
                                                     beat_date=beat_date).order_by('-beat_date')
            if beat_material_status:
                queryset = queryset.filter(beat_material_status__in=beat_material_status)
            if beat_status:
                queryset = queryset.filter(beat_status__in=beat_status)

            serializer = BeatAssignmentDetailSerializer(queryset, many=True)
            beatSMSupplySerializer = BeatSMApprovalDetailSerializer(beatQuerySet, many=True)
            beatRHSupplySerializer = BeatRHApprovalDetailSerializer(beatRHQuerySet, many=True)

            return Response({"results": serializer.data, "beat_sm_supply": beatSMSupplySerializer.data,
                             "rh_supply": beatRHSupplySerializer.data})

        else:
            return BadRequest({'error_type': "Not Authorized",
                               'errors': [{'message': "No User Profile"}]})

    @decorators.action(detail=False, methods=['get'], url_path="current_trip")
    def current_trip(self, request, *args, **kwargs):
        user = request.user
        data = request.data
        print(user)
        print(data)
        beat_date = datetime.strptime(request.GET.get('beat_date'), '%d-%m-%Y')
        beat_material_status = request.GET.get('beat_material_status', None)
        beat_status = request.GET.get('beat_status', None)

        if beat_material_status and beat_material_status != "undefined":
            beat_material_status = json.loads(beat_material_status)
            beat_material_status = [c for c in beat_material_status]

        if beat_status and beat_status != "undefined":
            beat_status = json.loads(beat_status)
            beat_status = [c for c in beat_status]

        admin = UserProfile.objects.filter(user=user, department__name__in=['Admin']).first()
        user_profile = UserProfile.objects.filter(user=user,
                                                  department__name__in=['Distribution', 'Warehouse', 'Sales']).first()
        if user_profile or admin:
            if admin:
                queryset = BeatAssignment.objects.filter(beat_date=beat_date).order_by('-beat_date')
                serializer = BeatAssignmentDetailSerializer(queryset, many=True)
                return Response(serializer.data)
            else:
                distributionPersonProfile = DistributionPersonProfile.objects.filter(user=user).first()
                warehousePersonProfile = WarehousePersonProfile.objects.filter(user=user).first()
                salesPersonProfile = SalesPersonProfile.objects.filter(user=user).first()
                if distributionPersonProfile:
                    if distributionPersonProfile.management_status == "Worker":
                        queryset = BeatAssignment.objects.filter(distributor=distributionPersonProfile,
                                                                 beat_date=beat_date).order_by(
                            '-beat_date')
                    elif distributionPersonProfile.management_status == "Manager":
                        queryset = BeatAssignment.objects.filter(beat_date=beat_date).order_by(
                            '-beat_date')
                    else:
                        queryset = BeatAssignment.objects.filter(warehouse=distributionPersonProfile.warehouse,
                                                                 beat_date=beat_date).order_by(
                            '-beat_date')

                    if beat_material_status:
                        queryset = queryset.filter(beat_material_status__in=beat_material_status)
                    if beat_status:
                        queryset = queryset.filter(beat_status__in=beat_status)

                    serializer = BeatAssignmentDetailSerializer(queryset, many=True)
                    return Response(serializer.data)
                elif warehousePersonProfile:
                    beatQuerySet = None
                    if warehousePersonProfile.management_status == "Worker":
                        queryset = BeatAssignment.objects.filter(beat_date=beat_date,
                                                                 warehouse=warehousePersonProfile.warehouse).order_by(
                            '-beat_date')
                        if beat_material_status:
                            queryset = queryset.filter(beat_material_status__in=beat_material_status)
                        if beat_status:
                            queryset = queryset.filter(beat_status__in=beat_status)
                    elif warehousePersonProfile.management_status == "Manager":
                        queryset = BeatAssignment.objects.filter(beat_date=beat_date).order_by(
                            '-beat_date')
                        if BeatWarehouseSupply.objects.filter(beat_date=beat_date):
                            beatQuerySet = BeatWarehouseSupply.objects.filter(beat_date=beat_date)
                        else:
                            beatQuerySet = None
                    else:
                        queryset = BeatAssignment.objects.filter(beat_date=beat_date).order_by(
                            '-beat_date')
                    if beat_material_status:
                        queryset = queryset.filter(beat_material_status__in=beat_material_status)
                    if beat_status:
                        queryset = queryset.filter(beat_status__in=beat_status)
                    serializer = BeatAssignmentDetailSerializer(queryset, many=True)
                    beatSupplySerializer = BeatWarehouseSupplyDetailSerializer(beatQuerySet, many=True)
                    return Response({"results": serializer.data, "beat_supply": beatSupplySerializer.data})
                elif salesPersonProfile:
                    if salesPersonProfile.management_status == "Worker":
                        queryset = BeatAssignment.objects.filter(beat_date=beat_date,
                                                                 beat_demand_by=salesPersonProfile).order_by(
                            '-beat_date')
                        serializer = BeatAssignmentDetailSerializer(queryset, many=True)
                        return Response(serializer.data)
                    elif salesPersonProfile.management_status == "Regional Manager":
                        if BeatSMApproval.objects.filter(beat_date=beat_date,
                                                         demand_classification=salesPersonProfile.demand_classification):
                            beatQuerySet = BeatSMApproval.objects.filter(beat_date=beat_date,
                                                                         demand_classification=salesPersonProfile.demand_classification)
                        else:
                            beatQuerySet = None

                        queryset = BeatAssignment.objects.filter(
                            demand_classification=salesPersonProfile.demand_classification,
                            beat_date=beat_date).order_by('-beat_date')
                        if beat_material_status:
                            queryset = queryset.filter(beat_material_status__in=beat_material_status)
                        if beat_status:
                            queryset = queryset.filter(beat_status__in=beat_status)
                        serializer = BeatAssignmentDetailSerializer(queryset, many=True)
                        beatSMSupplySerializer = BeatSMApprovalDetailSerializer(beatQuerySet, many=True)
                        return Response({"results": serializer.data, "beat_sm_supply": beatSMSupplySerializer.data})
                    elif salesPersonProfile.management_status == "Manager":
                        if BeatWarehouseSupply.objects.filter(beat_date=beat_date):
                            beatQuerySet = BeatWarehouseSupply.objects.filter(beat_date=beat_date)
                        else:
                            beatQuerySet = None
                        if BeatSMApproval.objects.filter(beat_date=beat_date,
                                                         beat_supply_approved_by=salesPersonProfile):
                            beatSMQuerySet = BeatSMApproval.objects.filter(beat_date=beat_date,
                                                                           beat_supply_approved_by=salesPersonProfile)
                        else:
                            beatSMQuerySet = None
                        queryset = BeatAssignment.objects.filter(
                            beat_date=beat_date).order_by(
                            '-beat_date')
                        if beat_material_status:
                            queryset = queryset.filter(beat_material_status__in=beat_material_status)
                        if beat_status:
                            queryset = queryset.filter(beat_status__in=beat_status)
                        serializer = BeatAssignmentDetailSerializer(queryset, many=True)
                        beatSupplySerializer = BeatWarehouseSupplyDetailSerializer(beatQuerySet, many=True)
                        beatSMSupplySerializer = BeatSMApprovalDetailSerializer(beatSMQuerySet, many=True)

                        return Response({"results": serializer.data, "beat_supply": beatSupplySerializer.data,
                                         "sm_supply": beatSMSupplySerializer.data})

                    else:
                        return BadRequest({'error_type': "Not Authorized",
                                           'errors': [{'message': "No Sales manager User Profile"}]})
                else:
                    return BadRequest({'error_type': "Not Authorized",
                                       'errors': [{'message': "No Such User Profile"}]})

        else:
            return BadRequest({'error_type': "Not Authorized",
                               'errors': [{'message': "No User Profile"}]})

    @decorators.action(detail=False, methods=['get'], url_path="trip_list")
    def trip_list(self, request, *args, **kwargs):
        user = request.user
        data = request.data
        print(user)
        print(data)
        beat_date = datetime.strptime(request.GET.get('beat_date'), '%d-%m-%Y')
        admin = UserProfile.objects.filter(user=user, department__name__in=['Admin']).first()
        user_profile = UserProfile.objects.filter(user=user,
                                                  department__name__in=['Distribution', 'Warehouse', 'Sales']).first()
        if user_profile or admin:
            if admin:
                queryset = BeatAssignment.objects.filter(beat_date=beat_date).order_by('-beat_date')
            else:
                distributionPersonProfile = DistributionPersonProfile.objects.filter(user=user).first()
                warehousePersonProfile = WarehousePersonProfile.objects.filter(user=user).first()
                salesPersonProfile = SalesPersonProfile.objects.filter(user=user).first()
                if distributionPersonProfile:
                    if distributionPersonProfile.management_status == "Worker":
                        queryset = BeatAssignment.objects.filter(distributor=distributionPersonProfile,
                                                                 beat_date__gte=beat_date - timedelta(
                                                                     days=30)).order_by(
                            '-beat_date')
                    elif distributionPersonProfile.management_status == "Manager":
                        queryset = BeatAssignment.objects.filter(warehouse=distributionPersonProfile.warehouse,
                                                                 beat_date__gte=beat_date - timedelta(
                                                                     days=30)).order_by(
                            '-beat_date')
                    else:
                        queryset = BeatAssignment.objects.filter(warehouse=distributionPersonProfile.warehouse,
                                                                 beat_date__gte=beat_date - timedelta(
                                                                     days=30)).order_by(
                            '-beat_date')

                elif warehousePersonProfile:
                    queryset = BeatAssignment.objects.filter(beat_date=beat_date,
                                                             warehouse=warehousePersonProfile.warehouse).order_by(
                        '-beat_date')
                else:
                    if salesPersonProfile.management_status == "Worker":
                        queryset = BeatAssignment.objects.filter(beat_date__gte=beat_date - timedelta(days=30),
                                                                 beat_demand_by=salesPersonProfile).order_by(
                            '-beat_date')
                    elif salesPersonProfile.management_status == "Manager":
                        queryset = BeatAssignment.objects.filter(
                            beat_date__gte=beat_date - timedelta(days=30)).order_by(
                            '-beat_date')
                    else:
                        queryset = BeatAssignment.objects.filter(warehouse=salesPersonProfile.warehouse,
                                                                 beat_date__gte=beat_date - timedelta(
                                                                     days=30)).order_by(
                            '-beat_date')

            serializer = BeatAssignmentDetailSerializer(queryset, many=True)
            return Response(serializer.data)
        else:
            return BadRequest({'error_type': "Not Authorized",
                               'errors': [{'message': "No User Profile"}]})

    @decorators.action(detail=False, methods=['get'], url_path="print_beat")
    def print_beat(self, request, *args, **kwargs):

        user = request.user
        if request.GET.get("beat_assignment"):
            beat_assignment = BeatAssignment.objects.filter(id=request.GET.get("beat_assignment", 2)).first()
        else:
            beat_assignment = BeatAssignment.objects.filter(id=7).first()

        # print(beat_assignment)
        print("beat time")
        print(beat_assignment.beat_date)

        beat_time = beat_assignment.beat_date.replace(hour=0, minute=0, second=0)
        # print("time")
        # print(Order.objects.get(pk=8111).delivery_date )
        # print(beat_time)
        delta = timedelta(hours=23, minutes=59, seconds=59)
        start_time = beat_time
        end_time = beat_time + delta
        # print(beat_assignment)
        # print("start time")
        # print(start_time)
        # print("end time")
        # print(end_time)
        admin = UserProfile.objects.filter(user=user, department__name__in=['Admin']).first()
        distribution_profile = UserProfile.objects.filter(user=user, department__name__in=['Distribution']).first()
        if distribution_profile or admin:
            if admin:
                order_queryset = Order.objects.filter(delivery_date__gte=start_time,
                                                      delivery_date__lte=end_time,
                                                      distributor=beat_assignment.distributor, )
                sales_queryset = SalesTransaction.objects.filter(transaction_date__gte=start_time,
                                                                 transaction_date__lte=end_time,
                                                                 transaction_type="Credit",
                                                                 distributor=beat_assignment.distributor, )
                salesIds = sales_queryset.values_list('id', flat=True)
                payment_queryset = Payment.objects.filter(salesTransaction_id__in=salesIds)
                return_queryset = OrderReturnLine.objects.filter(date__gte=start_time, date__lte=end_time,
                                                                 distributor=beat_assignment.distributor)
            else:
                distributionPersonProfile = DistributionPersonProfile.objects.filter(user=user).first()
                order_queryset = Order.objects.none()
                sales_queryset = SalesTransaction.objects.none()
                return_queryset = OrderReturnLine.objects.none()
                payment_queryset = Payment.objects.none()
                if distributionPersonProfile:
                    if distributionPersonProfile.management_status == "Worker":
                        return BadRequest({'error_type': "Not Authorized",
                                           'errors': [{'message': "please login with Admin Credentials"}]})
                    else:
                        order_queryset = Order.objects.filter(delivery_date__gte=start_time,
                                                              delivery_date__lte=end_time,
                                                              distributor=beat_assignment.distributor, )
                        # retailer__beat_number=beat_assignment.beat_number)
                        sales_queryset = SalesTransaction.objects.filter(transaction_date__gte=start_time,
                                                                         transaction_date__lte=end_time,
                                                                         transaction_type="Credit",
                                                                         distributor=beat_assignment.distributor, )
                        salesIds = sales_queryset.values_list('id', flat=True)
                        payment_queryset = Payment.objects.filter(salesTransaction_id__in=salesIds)
                        return_queryset = OrderReturnLine.objects.filter(date__gte=start_time, date__lte=end_time,
                                                                         distributor=beat_assignment.distributor)

            order_history_serializer = OrderHistorySerializer(order_queryset, many=True)
            print(order_history_serializer.data)

            sales_history_serializer = SalesTransactionSerializer(sales_queryset, many=True)
            print(sales_history_serializer.data)

            payment_serializer = PaymentSerializer(payment_queryset, many=True)
            print(payment_serializer.data)

            return_history_serializer = OrderReturnLineSerializer(return_queryset, many=True)
            print(return_history_serializer.data)

            return Response({"orders": order_history_serializer.data, "payments": sales_history_serializer.data,
                             "returns": return_history_serializer.data, "sales_payments": payment_serializer.data})

        else:
            return BadRequest({'error_type': "Not Authorized",
                               'errors': [{'message': "No User Profile"}]})


class RetailerBeatListViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin):
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = PaginationWithNoLimit
    serializer_class = BeatWiseRetailerSerializer
    queryset = Retailer.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ('beat_number', 'code', 'onboarding_status')


class RetailerBeatWiseViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin):
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = PaginationWithNoLimit
    serializer_class = RetailerBeatWiseSerializer
    queryset = Retailer.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ('beat_number', 'code', 'onboarding_status')

    @decorators.action(detail=False, methods=['post'], url_path="beat_update")
    def beat_update(self, request, *args, **kwargs):
        retailer_beat_update_serializer = RetailerBeatUpdateSerializer(data=request.data)
        retailer_beat_update_serializer.is_valid(raise_exception=True)
        retailer_beat_update_serializer.beat_update(retailer_beat_update_serializer.validated_data)
        return Created()


class SMRelativeViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin):
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = PaginationWithNoLimit
    serializer_class = SMRelativeNumberSerializer
    queryset = SMRelativeNumber.objects.all()
    filter_backends = (SimpleFilterBackend,)
    filterset_fields = ('demand_classification', 'egg_type', 'date')

    @decorators.action(detail=False, methods=['get'], url_path="current_data")
    def current_data(self, request, *args, **kwargs):
        queryset = SMRelativeNumber.objects.filter(date='2021-09-07')
        # page = self.paginate_queryset(queryset)
        # if page is not None:
        #     serializer = SMRelativeNumberSerializer(page, many=True)
        #     return self.get_paginated_response(serializer.data)

        serializer = SMRelativeNumberSerializer(queryset, many=True)
        return Response(serializer.data)
