import decimal
import json
from ast import literal_eval
from datetime import datetime, timedelta
from decimal import Decimal

import coreapi
import pytz

from django.db.models import Max, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_filters import rest_framework as filters
from rest_framework import permissions, viewsets, status, decorators, mixins, pagination
from rest_framework.exceptions import NotFound
from rest_framework.filters import BaseFilterBackend
from rest_framework.response import Response

from Eggoz.settings import CURRENT_ZONE
from base.response import BadRequest, Forbidden, Created, Ok
from custom_auth.api.serializers import AddressCreationSerializer
from custom_auth.models import UserProfile, User
from distributionchain.models import DistributionProfile
from finance.models import FinanceProfile
from order.models import Order
from order.models.Order import PackingOrder
from payment.models import SalesTransaction
from payment.views.InvoiceView import generate_invoice
from product.models import BaseProduct
from saleschain.models import SalesPersonProfile
from supplychain.models import SupplyPersonProfile
from warehouse.api.serializers import VehicleSerializer, VehicleOnboardSerializer, DriverSerializer, \
    DriverOnboardSerializer, VehicleAssignmentSendDeliverySerializer, \
    StockPickUpValidationSerializer, StockInlineValidationSerializer, VehicleAssignmentSerializer, StockSerializer, \
    WarehouseSerializer, StockDuplicationSerializer, InventorySerializer, InventoryUpdateSerializer, \
    PackedInventoryUpdateSerializer, PackedInventorySerializer, DailyPaymentsSerializer, ExpenseRequestSerializer, \
    ExpenseSerializer, ExpenseCategorySerializer, BankDetailsSerializer, BankDepositSerializer, BeatInventorySerializer, \
    BeatInventoryLineSerializer, BeatInventoryHistorySerializer
from warehouse.models import Vehicle, Driver, VehicleAssignment, Stock, StockInline, \
    EggProductStockInline, Inventory, Warehouse, WarehousePersonProfile, StockSourceDestinationData, QCEntry, QCLine, \
    PackedInventory, DailyPayments, DailyPaymentLine, ExpenseRequest, Expense, ExpenseCategory, BankDetails, \
    BankTransaction, BeatInventory

from warehouse.models.Wastage import Wastage

from payment.api.serializers import SalesTransactionShortSerializer


class VehicleViewSet(viewsets.GenericViewSet, mixins.CreateModelMixin, mixins.ListModelMixin,
                               mixins.RetrieveModelMixin):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = VehicleSerializer
    queryset = Vehicle.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = {'vehicle_no': ['startswith']}

    def get_serializer_class(self):
        if self.action == 'driver_onboard':
            return VehicleOnboardSerializer
        return self.serializer_class

    @decorators.action(detail=False, methods=['post'], url_path="onboard")
    def onboard(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({}, status=status.HTTP_201_CREATED)


class DriverViewSet(viewsets.GenericViewSet, mixins.CreateModelMixin, mixins.ListModelMixin,
                               mixins.RetrieveModelMixin):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = DriverSerializer
    queryset = Driver.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = {'driver_name': ['startswith']}


class VehicleAssignmentViewSet(viewsets.GenericViewSet, mixins.CreateModelMixin, mixins.ListModelMixin,
                               mixins.RetrieveModelMixin):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = VehicleAssignmentSerializer
    queryset = VehicleAssignment.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ('status',)

    def get_serializer_class(self):
        if self.action == 'create':
            return VehicleAssignmentSendDeliverySerializer
        return self.serializer_class

    def list(self, request, *args, **kwargs):
        search_string = request.GET.get('search', None)
        queryset = self.get_queryset()
        if search_string:
            queryset = self.get_queryset().filter(
                Q(delivery_person__name=search_string) | Q(vehicle__vehicle_no=search_string))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        data = request.data
        user_profile = UserProfile.objects.filter(user=request.user, department__name__in=['Warehouse']).first()
        if user_profile:
            warehousePersonProfile = WarehousePersonProfile.objects.filter(user=request.user).first()
            if warehousePersonProfile:
                if data.get('operation_option') == "Delivery":
                    print(request.POST)
                    orders = request.GET.get('orders', [])
                    # invoice_data = {"request": self.request, "order_ids": orders}
                    # generate_invoice(invoice_data)

                    if orders and orders != "undefined":
                        orders = json.loads(orders)
                        orders = [int(c) for c in orders]
                        if len(orders) > 0:
                            for order in orders:
                                get_object_or_404(Order, pk=order)
                        else:
                            return BadRequest({'error_type': "Validation Error",
                                               'errors': [{'message': "please provide at least one order to assign"}]})
                    else:
                        return BadRequest({'error_type': "Validation Error",
                                           'errors': [{'message': "please provide at least one order to assign"}]})
                serializer = self.get_serializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                vehicle_assignment = serializer.save(date=datetime.now(tz=CURRENT_ZONE), warehouseEmployee=warehousePersonProfile)
                headers = self.get_success_headers(serializer.data)
                if data.get('operation_option') == "Delivery":

                    orders = request.GET.get('orders',[])
                    # invoice_data = {"request": self.request, "order_ids": orders}
                    # generate_invoice(invoice_data)
                    if orders and orders !="undefined":
                        orders = json.loads(orders)
                        if len(orders) > 0:
                            for order in orders:
                                order_obj = Order.objects.get(pk=order)
                                order_obj.vehicle_assignment = vehicle_assignment
                                order_obj.status = "on the way"
                                order_obj.save()
                                # Update Inventory
                                order_lines = order_obj.lines.all()
                                for order_line in order_lines:
                                    product = order_line.product
                                    baseProduct_slug = str(product.city.city_name) + "-Egg-" + product.name[:2]
                                    baseProduct = BaseProduct.objects.filter(slug=baseProduct_slug).first()
                                    if baseProduct:
                                        # TODO Filter according to warehouse
                                        inventory_statuses = ['packed', 'in transit']
                                        inventories = Inventory.objects.filter(warehouse=order_obj.salesPerson.warehouse,
                                                                               baseProduct=baseProduct,
                                                                               inventory_status__in=inventory_statuses)
                                        for inventory in inventories:
                                            if inventory.inventory_status == 'packed':
                                                inventory.quantity = inventory.quantity - (
                                                        order_line.product.SKU_Count * order_line.quantity)
                                                inventory.save()
                                            if inventory.inventory_status == 'in transit':
                                                inventory.quantity = inventory.quantity + (
                                                        order_line.product.SKU_Count * order_line.quantity)
                                                inventory.save()


                    packingOrders = request.GET.get('packingOrders', [])
                    if packingOrders and packingOrders != "undefined":
                        packingOrders = json.loads(packingOrders)
                        if len(packingOrders) > 0:
                            for packingOrder in packingOrders:
                                packingOrder_obj = PackingOrder.objects.get(pk=packingOrder)
                                packingOrder_obj.status = "on the way"
                                packingOrder_obj.save()

                return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
            else:
                return Forbidden({'error_type': "Internal Error",
                                  'errors': [{'message': "Warehouse Person profile not found"}]})
        else:
            return Forbidden({'error_type': "permission_denied",
                              'errors': [{'message': "You do not have permission to perform this action."}]})


class StockViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = StockSerializer
    queryset = Stock.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ('stock_status', 'is_forwarded')


class WarehouseViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.AllowAny,)
    serializer_class = WarehouseSerializer
    queryset = Warehouse.objects.all()

    def list(self, request, *args, **kwargs):
        name_filter = request.GET.get('name', None)
        slug_filter = request.GET.get('slug', None)
        warehouse_list = self.get_queryset()
        if name_filter is not None:
            warehouse_list = warehouse_list.filter(name__icontains=name_filter)
        if slug_filter is not None:
            warehouse_list = warehouse_list.filter(slug__icontains=slug_filter)
        page = self.paginate_queryset(warehouse_list)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(warehouse_list, many=True)
        return Response(serializer.data)



class InventoryViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = InventorySerializer
    queryset = Inventory.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ('inventory_status', 'warehouse', 'baseProduct')


class PackedInventoryViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = PackedInventorySerializer
    queryset = PackedInventory.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ('inventory_status', 'warehouse', 'product', 'category_type')


class StockPickupViewSet(viewsets.GenericViewSet, mixins.CreateModelMixin):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = StockPickUpValidationSerializer
    queryset = Stock.objects.all()

    def create(self, request, *args, **kwargs):
        data = request.data
        vehicle_assignment = None
        user_profile = UserProfile.objects.filter(user=request.user, department__name__in=['Supply']).first()
        if user_profile:
            supplyPersonProfile = SupplyPersonProfile.objects.filter(user=request.user).first()
            stock_pickup_serializer = self.get_serializer(data=request.data)
            stock_pickup_serializer.is_valid(raise_exception=True)
            # # Validate Stock In Line
            if data.get('stockInLines'):
                stockInLines = json.loads(data.get('stockInLines', []))
                if len(stockInLines) > 0:
                    stockInLineSerializer = StockInlineValidationSerializer(data=stockInLines, many=True,
                                                                            context={"stock_type": "pick_up"})
                    stockInLineSerializer.is_valid(raise_exception=True)
                    # Get warehouse Vehicle & Driver
                    if not data.get('vehicle_assignment_id'):
                        return BadRequest({'error_type': "Validation Error",
                                           'errors': [{'message': "vehicle_assignment_id required"}]})
                    else:
                        vehicle_assignment = VehicleAssignment.objects.filter(
                            id=data.get('vehicle_assignment_id')).first()
                        if vehicle_assignment:
                            driver = vehicle_assignment.driver
                            vehicle = vehicle_assignment.vehicle
                            warehouseEmployee = vehicle_assignment.warehouseEmployee
                            if vehicle and warehouseEmployee or driver:
                                if warehouseEmployee.warehouse:
                                    pass
                                else:
                                    return BadRequest({'error_type': "Validation Error", 'errors': [
                                        {'message': "No warehose assigned to this employee"}]})
                            else:
                                return BadRequest({'error_type': "Validation Error",
                                                   'errors': [
                                                       {'message': "vehicle_assignment has no valid information"}]})
                        else:
                            return BadRequest({'error_type': "Validation Error",
                                               'errors': [{
                                                   'message': "vehicle_assignment_id not valid or first assign vehicle to pickup"}]})

                    stockInLineSerializerData = stockInLineSerializer.validated_data
                    stocks = Stock.objects.all()
                    # might be possible model has no records so make sure to handle None
                    stock_max_id = stocks.aggregate(Max('id'))['id__max'] + 1 if stocks else 1
                    stock_batch_id = "SBI" + str(stock_max_id)

                    # From Source & Destination
                    source = StockSourceDestinationData.objects.filter(dataProfile='Farmer').first()
                    if source:
                        source_obj = source
                    else:
                        source_obj = StockSourceDestinationData.objects.create(dataProfile='Farmer')

                    destination = StockSourceDestinationData.objects.filter(dataProfile='Vehicle').first()
                    if source:
                        destination_obj = destination
                    else:
                        destination_obj = StockSourceDestinationData.objects.create(dataProfile='Vehicle')

                    stock_obj = stock_pickup_serializer.save(supplyPerson=supplyPersonProfile,
                                                             batch_id=stock_batch_id,
                                                             picked_at=datetime.now(tz=CURRENT_ZONE), from_source=source_obj,
                                                             to_destination=destination_obj,
                                                             vehicle=vehicle_assignment.vehicle,
                                                             driver=vehicle_assignment.driver,
                                                             warehousePerson=vehicle_assignment.warehouseEmployee,
                                                             warehouse=vehicle_assignment.warehouseEmployee.warehouse)

                    for stockInLine in stockInLineSerializerData:
                        stockInLineObj = StockInline(stock=stock_obj, baseProduct=stockInLine.get('baseProduct'),
                                                     stock_note=stockInLine.get('stock_note', 'remarks'))
                        stockInLineObj.save()
                        eggProductStockInlines = stockInLine.get("eggProductStockInLines")
                        for eggProductStockInline in eggProductStockInlines:
                            eggProductStockInline = EggProductStockInline(stock_inline=stockInLineObj,
                                                                          **eggProductStockInline)
                            eggProductStockInline.save()

                    # Update Inventory
                    # Increase pickup
                    pickup_stock_in_lines = stock_obj.stock_inline.all()

                    for pickup_stock_in_line in pickup_stock_in_lines:
                        base_product = pickup_stock_in_line.baseProduct
                        warehouse = pickup_stock_in_line.stock.warehouse
                        egg_update_dict = {"good": 0, "chatki": 0}
                        pickup_product_type_stock_inline_objs = pickup_stock_in_line.product_type_stock_inline.all()
                        for pickup_product_type_stock_inline_obj in pickup_product_type_stock_inline_objs:
                            if pickup_product_type_stock_inline_obj.sku_type == "Full":
                                egg_update_dict['good'] = egg_update_dict[
                                                              'good'] + pickup_product_type_stock_inline_obj.quantity * 30
                            elif pickup_product_type_stock_inline_obj.sku_type == "Single":
                                egg_update_dict['good'] = egg_update_dict[
                                                              'good'] + pickup_product_type_stock_inline_obj.quantity
                            else:
                                egg_update_dict['chatki'] = egg_update_dict[
                                                                'chatki'] + pickup_product_type_stock_inline_obj.quantity

                            inventory_obj = Inventory.objects.filter(warehouse=warehouse,
                                                                     baseProduct=base_product,
                                                                     inventory_status='picked up').first()
                            if not inventory_obj:
                                inventory_name = str(base_product.name)
                                Inventory.objects.create(warehouse=warehouse, baseProduct=base_product,
                                                         inventory_status='picked up',
                                                         quantity=egg_update_dict['good'] + egg_update_dict['chatki'],
                                                         name=inventory_name,
                                                         desc=inventory_name, branded_quantity=egg_update_dict['good'],
                                                         chatki_quantity=egg_update_dict['chatki'])
                            else:
                                inventory_obj.quantity = inventory_obj.quantity + egg_update_dict['good'] + \
                                                         egg_update_dict['chatki']
                                inventory_obj.branded_quantity = inventory_obj.branded_quantity + egg_update_dict[
                                    'good']
                                inventory_obj.chatki_quantity = inventory_obj.chatki_quantity + egg_update_dict[
                                    'chatki']
                                inventory_obj.save()

                    return Response({}, status=status.HTTP_201_CREATED)
                else:
                    return BadRequest({'error_type': "Validation Error",
                                       'errors': [{'message': "Stock In Lines can not be empty"}]})
            else:
                return BadRequest({'error_type': "Validation Error",
                                   'errors': [{'message': "Stock In Lines can not be empty"}]})

        else:
            return Forbidden({'error_type': "permission_denied",
                              'errors': [{'message': "You do not have permission to perform this action."}]})


class StockReceiveViewSet(viewsets.ViewSet):
    permission_classes = (permissions.IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        data = request.data
        user_profile = UserProfile.objects.filter(user=request.user, department__name__in=['Warehouse']).first()
        if user_profile:
            warehousePersonProfile = WarehousePersonProfile.objects.filter(user=request.user).first()
            if warehousePersonProfile:
                if data.get('batch_id'):
                    picked_up_stock = Stock.objects.filter(batch_id=data.get('batch_id'),
                                                           stock_status="Picked up").first()
                    if picked_up_stock:
                        received_stock = Stock.objects.filter(batch_id=data.get('batch_id'),
                                                              stock_status="Received").first()
                        if received_stock:
                            return BadRequest({'error_type': "Validation Error",
                                               'errors': [{'message': "Stock already received"}]})
                        else:
                            if data.get('stockInLines'):
                                stockInLines = json.loads(data.get('stockInLines', []))
                                if len(stockInLines) > 0:
                                    stockInLineSerializer = StockInlineValidationSerializer(data=stockInLines,
                                                                                            many=True, context={
                                            "stock_type": "receive"})
                                    stockInLineSerializer.is_valid(raise_exception=True)
                                    stockInLineSerializerData = stockInLineSerializer.validated_data

                                    pick_up_stock_serializer = StockDuplicationSerializer(instance=picked_up_stock)
                                    stock_pickup_data = pick_up_stock_serializer.data
                                    receive_stock = Stock(batch_id=stock_pickup_data.get('batch_id'),
                                                          warehouse_id=stock_pickup_data.get('warehouse'),
                                                          farm_id=stock_pickup_data.get('farm'),
                                                          supplyPerson_id=stock_pickup_data.get('supplyPerson'),
                                                          warehousePerson_id=stock_pickup_data.get('warehousePerson'),
                                                          driver_id=stock_pickup_data.get('driver'),
                                                          productDivision_id=stock_pickup_data.get('productDivision'),
                                                          stock_status="Received")

                                    # From Source & Destination
                                    source = StockSourceDestinationData.objects.filter(dataProfile='Vehicle').first()
                                    if source:
                                        source_obj = source
                                    else:
                                        source_obj = StockSourceDestinationData.objects.create(dataProfile='Vehicle')

                                    destination = StockSourceDestinationData.objects.filter(
                                        dataProfile='Warehouse').first()
                                    if source:
                                        destination_obj = destination
                                    else:
                                        destination_obj = StockSourceDestinationData.objects.create(
                                            dataProfile='Warehouse')

                                    receive_stock.from_source = source_obj
                                    receive_stock.to_destination = destination_obj
                                    receive_stock.received_at = datetime.now(tz=CURRENT_ZONE)
                                    receive_stock.save()
                                    for stockInLine in stockInLineSerializerData:
                                        stockInLineObj = StockInline(stock=receive_stock,
                                                                     baseProduct=stockInLine.get('baseProduct'),
                                                                     stock_note=stockInLine.get('stock_note',
                                                                                                'remarks'))
                                        stockInLineObj.save()
                                        eggProductStockInlines = stockInLine.get("eggProductStockInLines")
                                        for eggProductStockInline in eggProductStockInlines:
                                            eggProductStockInline = EggProductStockInline(stock_inline=stockInLineObj,
                                                                                          **eggProductStockInline)
                                            eggProductStockInline.save()

                                        wastageInLines = stockInLine.get("wastageInLines")
                                        for wastageInLine in wastageInLines:
                                            wastageInline = Wastage(stock_inline=stockInLineObj, **wastageInLine)
                                            wastageInline.save()

                                    # Update Inventory
                                    # Decrease Pickup
                                    picked_up_stock_in_lines = picked_up_stock.stock_inline.all()
                                    for picked_up_stock_in_line in picked_up_stock_in_lines:
                                        base_product = picked_up_stock_in_line.baseProduct
                                        warehouse = picked_up_stock_in_line.stock.warehouse
                                        egg_update_dict = {"good": 0, "chatki": 0}
                                        pick_up_product_type_stock_inline_objs = picked_up_stock_in_line.product_type_stock_inline.all()
                                        for pick_up_product_type_stock_inline_obj in pick_up_product_type_stock_inline_objs:
                                            if pick_up_product_type_stock_inline_obj.sku_type == "Full":
                                                egg_update_dict['good'] = egg_update_dict[
                                                                              'good'] + pick_up_product_type_stock_inline_obj.quantity * 30
                                            elif pick_up_product_type_stock_inline_obj.sku_type == "Single":
                                                egg_update_dict['good'] = egg_update_dict[
                                                                              'good'] + pick_up_product_type_stock_inline_obj.quantity
                                            else:
                                                egg_update_dict['chatki'] = egg_update_dict[
                                                                                'chatki'] + pick_up_product_type_stock_inline_obj.quantity

                                        inventory_pickup_obj = Inventory.objects.filter(warehouse=warehouse,
                                                                                        baseProduct=base_product,
                                                                                        inventory_status='picked up').first()
                                        inventory_pickup_obj.quantity = inventory_pickup_obj.quantity - egg_update_dict[
                                            'good'] - \
                                                                        egg_update_dict['chatki']
                                        inventory_pickup_obj.branded_quantity = inventory_pickup_obj.branded_quantity - \
                                                                                egg_update_dict['good']
                                        inventory_pickup_obj.chatki_quantity = inventory_pickup_obj.chatki_quantity - \
                                                                               egg_update_dict[
                                                                                   'chatki']
                                        inventory_pickup_obj.save()

                                    # Increase Receive
                                    receive_stock_in_lines = receive_stock.stock_inline.all()

                                    for receive_stock_in_line in receive_stock_in_lines:
                                        base_product = receive_stock_in_line.baseProduct
                                        warehouse = receive_stock_in_line.stock.warehouse
                                        egg_update_dict = {"good": 0, "chatki": 0}
                                        receive_product_type_stock_inline_objs = receive_stock_in_line.product_type_stock_inline.all()
                                        for receive_product_type_stock_inline_obj in receive_product_type_stock_inline_objs:
                                            if receive_product_type_stock_inline_obj.sku_type == "Full":
                                                egg_update_dict['good'] = egg_update_dict[
                                                                              'good'] + receive_product_type_stock_inline_obj.quantity * 30
                                            elif receive_product_type_stock_inline_obj.sku_type == "Single":
                                                egg_update_dict['good'] = egg_update_dict[
                                                                              'good'] + receive_product_type_stock_inline_obj.quantity
                                            else:
                                                egg_update_dict['chatki'] = egg_update_dict[
                                                                                'chatki'] + receive_product_type_stock_inline_obj.quantity

                                        inventory_obj = Inventory.objects.filter(warehouse=warehouse,
                                                                                 baseProduct=base_product,
                                                                                 inventory_status='received').first()
                                        if not inventory_obj:
                                            inventory_name = str(base_product.name)
                                            Inventory.objects.create(warehouse=warehouse, baseProduct=base_product,
                                                                     inventory_status='received',
                                                                     quantity=egg_update_dict['good'] + egg_update_dict[
                                                                         'chatki'],
                                                                     name=inventory_name,
                                                                     desc=inventory_name,
                                                                     branded_quantity=egg_update_dict['good'],
                                                                     chatki_quantity=egg_update_dict['chatki'])
                                        else:
                                            inventory_obj.quantity = inventory_obj.quantity + egg_update_dict['good'] + \
                                                                     egg_update_dict['chatki']
                                            inventory_obj.branded_quantity = inventory_obj.branded_quantity + \
                                                                             egg_update_dict['good']
                                            inventory_obj.chatki_quantity = inventory_obj.chatki_quantity + \
                                                                            egg_update_dict['chatki']
                                            inventory_obj.save()
                                    picked_up_stock.is_forwarded = True
                                    picked_up_stock.save()
                                    return Response({}, status=status.HTTP_201_CREATED)



                                else:
                                    return BadRequest({'error_type': "Validation Error",
                                                       'errors': [{'message': "Stock In Lines can not be empty"}]})

                            else:
                                return BadRequest({'error_type': "Validation Error",
                                                   'errors': [{'message': "Stock In Lines can not be empty"}]})

                    else:
                        return BadRequest({'error_type': "Validation Error",
                                           'errors': [{'message': "Stock not picked yet"}]})

                else:
                    return BadRequest({'error_type': "Validation Error",
                                       'errors': [{'message': "Stock required"}]})

            else:
                return Forbidden({'error_type': "permission_denied",
                                  'errors': [{'message': "Supply person profile not found"}]})

        else:
            return Forbidden({'error_type': "permission_denied",
                              'errors': [{'message': "You do not have permission to perform this action."}]})


class StockQCViewSet(viewsets.ViewSet):
    permission_classes = (permissions.IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        data = request.data
        user_profile = UserProfile.objects.filter(user=request.user, department__name__in=['Warehouse']).first()
        if user_profile:
            warehousePersonProfile = WarehousePersonProfile.objects.filter(user=request.user).first()
            if warehousePersonProfile:
                if data.get('batch_id'):
                    receive_stock = Stock.objects.filter(batch_id=data.get('batch_id'),
                                                         stock_status="Received").first()
                    if receive_stock:
                        qc_done_stock = Stock.objects.filter(batch_id=data.get('batch_id'),
                                                             stock_status="Qc Done").first()
                        if qc_done_stock:
                            return BadRequest({'error_type': "Validation Error",
                                               'errors': [{'message': "Stock already done it's qc"}]})
                        else:
                            if data.get('stockInLines'):
                                stockInLines = json.loads(data.get('stockInLines', []))
                                if len(stockInLines) > 0:
                                    stockInLineSerializer = StockInlineValidationSerializer(data=stockInLines,
                                                                                            many=True, context={
                                            "stock_type": "qc_done"})
                                    stockInLineSerializer.is_valid(raise_exception=True)
                                    stockInLineSerializerData = stockInLineSerializer.validated_data

                                    # Make New Instance of stock For QC DONE
                                    receive_stock_serializer = StockDuplicationSerializer(instance=receive_stock)
                                    stock_receive_data = receive_stock_serializer.data
                                    qc_done_stock = Stock(batch_id=stock_receive_data.get('batch_id'),
                                                          warehouse_id=stock_receive_data.get('warehouse'),
                                                          farm_id=stock_receive_data.get('farm'),
                                                          supplyPerson_id=stock_receive_data.get('supplyPerson'),
                                                          warehousePerson_id=stock_receive_data.get('warehousePerson'),
                                                          driver_id=stock_receive_data.get('driver'),
                                                          productDivision_id=stock_receive_data.get('productDivision'),
                                                          stock_status="Qc Done")

                                    # From Source & Destination
                                    source = StockSourceDestinationData.objects.filter(dataProfile='Warehouse').first()
                                    if source:
                                        source_obj = source
                                    else:
                                        source_obj = StockSourceDestinationData.objects.create(dataProfile='Warehouse')

                                    destination = StockSourceDestinationData.objects.filter(
                                        dataProfile='Qc').first()
                                    if source:
                                        destination_obj = destination
                                    else:
                                        destination_obj = StockSourceDestinationData.objects.create(
                                            dataProfile='Qc')

                                    qc_done_stock.from_source = source_obj
                                    qc_done_stock.to_destination = destination_obj
                                    qc_done_stock.qc_done_at = datetime.now(tz=CURRENT_ZONE)
                                    qc_done_stock.save()

                                    # Make New Instance of stock For Inventory Available
                                    available_stock = Stock(batch_id=stock_receive_data.get('batch_id'),
                                                            warehouse_id=stock_receive_data.get('warehouse'),
                                                            farm_id=stock_receive_data.get('farm'),
                                                            supplyPerson_id=stock_receive_data.get('supplyPerson'),
                                                            warehousePerson_id=stock_receive_data.get(
                                                                'warehousePerson'),
                                                            driver_id=stock_receive_data.get('driver'),
                                                            productDivision_id=stock_receive_data.get(
                                                                'productDivision'),
                                                            stock_status="Inventory")

                                    # From Source & Destination
                                    source = StockSourceDestinationData.objects.filter(dataProfile='Qc').first()
                                    if source:
                                        source_obj = source
                                    else:
                                        source_obj = StockSourceDestinationData.objects.create(dataProfile='Qc')

                                    destination = StockSourceDestinationData.objects.filter(
                                        dataProfile='Operations').first()
                                    if source:
                                        destination_obj = destination
                                    else:
                                        destination_obj = StockSourceDestinationData.objects.create(
                                            dataProfile='Operations')

                                    available_stock.from_source = source_obj
                                    available_stock.to_destination = destination_obj
                                    available_stock.save()

                                    # Update Inlines For QC
                                    for stockInLine in stockInLineSerializerData:
                                        stockInLineObj = StockInline(stock=qc_done_stock,
                                                                     baseProduct=stockInLine.get('baseProduct'),
                                                                     stock_note=stockInLine.get('stock_note',
                                                                                                'remarks'))
                                        stockInLineObj.save()
                                        eggProductStockInlines = stockInLine.get("eggProductStockInLines")
                                        for eggProductStockInline in eggProductStockInlines:
                                            eggProductStockInline = EggProductStockInline(stock_inline=stockInLineObj,
                                                                                          **eggProductStockInline)
                                            eggProductStockInline.save()

                                        wastageInLines = stockInLine.get("wastageInLines")
                                        for wastageInLine in wastageInLines:
                                            wastageInline = Wastage(stock_inline=stockInLineObj, **wastageInLine)
                                            wastageInline.save()

                                        qc_entry = stockInLine.get("qc_entry")
                                        qc_lines = qc_entry.get("qc_lines")
                                        total_ph_value = decimal.Decimal(0.0)
                                        for qc_line in qc_lines:
                                            total_ph_value = total_ph_value + decimal.Decimal(qc_line.get('ph_value'))
                                        mean_ph_value = total_ph_value / decimal.Decimal(len(qc_lines))
                                        qc_entry_obj = QCEntry(batch_id=data.get('batch_id'),
                                                               stock_inline=stockInLineObj, ph_value=mean_ph_value,
                                                               desc=qc_entry.get('desc'))
                                        qc_entry_obj.save()
                                        for qc_line in qc_lines:
                                            qc_line_obj = QCLine(qcEntry=qc_entry_obj, **qc_line)
                                            qc_line_obj.save()

                                    # Update Inlines For Available
                                    for stockInLine in stockInLineSerializerData:
                                        stockInLineObj = StockInline(stock=available_stock,
                                                                     baseProduct=stockInLine.get('baseProduct'),
                                                                     stock_note=stockInLine.get('stock_note',
                                                                                                'remarks'))
                                        stockInLineObj.save()
                                        eggProductStockInlines = stockInLine.get("eggProductStockInLines")
                                        for eggProductStockInline in eggProductStockInlines:
                                            eggProductStockInline = EggProductStockInline(
                                                stock_inline=stockInLineObj,
                                                **eggProductStockInline)
                                            eggProductStockInline.save()

                                        wastageInLines = stockInLine.get("wastageInLines")
                                        for wastageInLine in wastageInLines:
                                            wastageInline = Wastage(stock_inline=stockInLineObj,
                                                                    **wastageInLine)
                                            wastageInline.save()

                                    # Update Inventory For Available
                                    # Decrease Receive
                                    receive_stock_in_lines = receive_stock.stock_inline.all()
                                    for receive_stock_in_line in receive_stock_in_lines:
                                        base_product = receive_stock_in_line.baseProduct
                                        warehouse = receive_stock_in_line.stock.warehouse
                                        egg_update_dict = {"good": 0, "chatki": 0}
                                        receive_product_type_stock_inline_objs = receive_stock_in_line.product_type_stock_inline.all()
                                        for receive_product_type_stock_inline_obj in receive_product_type_stock_inline_objs:
                                            if receive_product_type_stock_inline_obj.sku_type == "Full":
                                                egg_update_dict['good'] = egg_update_dict[
                                                                              'good'] + receive_product_type_stock_inline_obj.quantity * 30
                                            elif receive_product_type_stock_inline_obj.sku_type == "Single":
                                                egg_update_dict['good'] = egg_update_dict[
                                                                              'good'] + receive_product_type_stock_inline_obj.quantity
                                            else:
                                                egg_update_dict['chatki'] = egg_update_dict[
                                                                                'chatki'] + receive_product_type_stock_inline_obj.quantity

                                        inventory_receive_obj = Inventory.objects.filter(warehouse=warehouse,
                                                                                         baseProduct=base_product,
                                                                                         inventory_status='received').first()
                                        inventory_receive_obj.quantity = inventory_receive_obj.quantity - \
                                                                         egg_update_dict[
                                                                             'good'] - \
                                                                         egg_update_dict['chatki']
                                        inventory_receive_obj.branded_quantity = inventory_receive_obj.branded_quantity - \
                                                                                 egg_update_dict['good']
                                        inventory_receive_obj.chatki_quantity = inventory_receive_obj.chatki_quantity - \
                                                                                egg_update_dict[
                                                                                    'chatki']
                                        inventory_receive_obj.save()

                                    # Increase Available
                                    available_stock_in_lines = available_stock.stock_inline.all()

                                    for available_stock_in_line in available_stock_in_lines:
                                        base_product = available_stock_in_line.baseProduct
                                        warehouse = available_stock_in_line.stock.warehouse
                                        egg_update_dict = {"good": 0, "chatki": 0}
                                        available_product_type_stock_inline_objs = available_stock_in_line.product_type_stock_inline.all()
                                        for available_product_type_stock_inline_obj in available_product_type_stock_inline_objs:
                                            if available_product_type_stock_inline_obj.sku_type == "Full":
                                                egg_update_dict['good'] = egg_update_dict[
                                                                              'good'] + available_product_type_stock_inline_obj.quantity * 30
                                            elif available_product_type_stock_inline_obj.sku_type == "Single":
                                                egg_update_dict['good'] = egg_update_dict[
                                                                              'good'] + available_product_type_stock_inline_obj.quantity
                                            else:
                                                egg_update_dict['chatki'] = egg_update_dict[
                                                                                'chatki'] + available_product_type_stock_inline_obj.quantity

                                        inventory_obj = Inventory.objects.filter(warehouse=warehouse,
                                                                                 baseProduct=base_product,
                                                                                 inventory_status='available').first()
                                        if not inventory_obj:
                                            inventory_name = str(base_product.name)
                                            Inventory.objects.create(warehouse=warehouse, baseProduct=base_product,
                                                                     inventory_status='available',
                                                                     quantity=egg_update_dict['good'] + egg_update_dict[
                                                                         'chatki'],
                                                                     name=inventory_name,
                                                                     desc=inventory_name,
                                                                     branded_quantity=egg_update_dict['good'],
                                                                     chatki_quantity=egg_update_dict['chatki'])
                                        else:
                                            inventory_obj.quantity = inventory_obj.quantity + egg_update_dict['good'] + \
                                                                     egg_update_dict['chatki']
                                            inventory_obj.branded_quantity = inventory_obj.branded_quantity + \
                                                                             egg_update_dict['good']
                                            inventory_obj.chatki_quantity = inventory_obj.chatki_quantity + \
                                                                            egg_update_dict['chatki']
                                            inventory_obj.save()
                                    receive_stock.is_forwarded = True
                                    receive_stock.save()
                                    qc_done_stock.is_forwarded = True
                                    qc_done_stock.save()
                                    return Response({}, status=status.HTTP_201_CREATED)



                                else:
                                    return BadRequest({'error_type': "Validation Error",
                                                       'errors': [{'message': "Stock In Lines can not be empty"}]})

                            else:
                                return BadRequest({'error_type': "Validation Error",
                                                   'errors': [{'message': "Stock In Lines can not be empty"}]})
                    else:
                        return BadRequest({'error_type': "Validation Error",
                                           'errors': [{'message': "Stock not received yet"}]})
                else:
                    return BadRequest({'error_type': "Validation Error",
                                       'errors': [{'message': "Stock required"}]})

            else:
                return Forbidden({'error_type': "permission_denied",
                                  'errors': [{'message': "Warehouse person profile not found"}]})

        else:
            return Forbidden({'error_type': "permission_denied",
                              'errors': [{'message': "You do not have permission to perform this action."}]})


class InventoryUpdateViewSet(viewsets.ViewSet):
    permission_classes = (permissions.IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        data = request.data
        print(data)
        inventory_serializer = InventoryUpdateSerializer(data=data)
        inventory_serializer.is_valid(raise_exception=True)
        validated_data = inventory_serializer.validated_data
        warehouse_obj = validated_data.get('warehouse')
        inventory_name = validated_data.get('name')
        branded_quantity = int(validated_data.get('branded_quantity'))
        unbranded_quantity = int(validated_data.get('unbranded_quantity'))
        chatki_quantity = int(validated_data.get('chatki_quantity'))
        inventory = Inventory.objects.filter(warehouse=warehouse_obj, name=inventory_name,
                                             inventory_status='available').first()
        if inventory:
            inventory.quantity = inventory.quantity + branded_quantity + chatki_quantity + unbranded_quantity
            inventory.unbranded_quantity = inventory.unbranded_quantity + unbranded_quantity
            inventory.branded_quantity = inventory.branded_quantity + branded_quantity
            inventory.chatki_quantity = inventory.chatki_quantity + chatki_quantity
            inventory.save()
            return Created({})
        else:
            raise NotFound("Inventory Not found to update")


class PackedInventoryUpdateViewSet(viewsets.ViewSet):
    permission_classes = (permissions.IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        data = request.data
        print(data)
        inventory_serializer = PackedInventoryUpdateSerializer(data=data)
        inventory_serializer.is_valid(raise_exception=True)
        validated_data = inventory_serializer.validated_data
        warehouse_obj = validated_data.get('warehouse')

        inventory_name = validated_data.get('name')
        packed_inventory = PackedInventory.objects.filter(warehouse=warehouse_obj, name=inventory_name,
                                                          inventory_status='available').first()
        if packed_inventory:
            packed_inventory.quantity = packed_inventory.quantity + data.get('quantity')
            packed_inventory.save()
            return Created({})
        else:
            raise NotFound("Packed Inventory Not found to update")


class DailyPaymentViewSet(viewsets.GenericViewSet, mixins.CreateModelMixin, mixins.ListModelMixin,
                          mixins.RetrieveModelMixin):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = DailyPaymentsSerializer
    queryset = DailyPayments.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ('warehouse', 'date', 'salesPerson', 'distributor', 'entered_by')

    def list(self, request, *args, **kwargs):
        search_string = request.GET.get('search', None)
        salesPersonId = request.GET.get('salesPersonId')
        queryset = self.get_queryset().filter(salesPerson_id=salesPersonId)

        if search_string:
            queryset = self.get_queryset().filter(
                Q(salesPerson_user__name=search_string))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @decorators.action(detail=False, methods=['get'], url_path="payment_list")
    def payment_list(self, request, *args, **kwargs):
        # salesPersonId = request.GET.get('salesPersonId')
        userId = request.GET.get('userId')
        # profile = request.GET.get('profile')
        temp_user =User.objects.filter(pk=userId).first()

        sales_profile = UserProfile.objects.filter(user=temp_user, department__name__in=['Sales']).first()
        distribution_profile = UserProfile.objects.filter(user=temp_user, department__name__in=['Distribution']).first()
        if sales_profile:
            # salesPerson = SalesPersonProfile.objects.filter(user=temp_user).first()
            salesPerson = temp_user.sales
            querysetCredit = SalesTransaction.objects.filter(salesPerson=salesPerson, transaction_type="Credit",is_trial=False,
                                                             is_verified=False, transaction_date__gte=datetime.now(tz=CURRENT_ZONE) - timedelta(days=25))
            querysetPayments = DailyPayments.objects.filter(salesPerson_id=salesPerson.id)
        elif distribution_profile:
            # distributor = DistributionProfile.objects.filter(user=temp_user).first()
            distributor = temp_user.distribution
            querysetCredit = SalesTransaction.objects.filter(distributor=distributor, transaction_type="Credit",is_trial=False,
                                                             is_verified=False,transaction_date__gte=datetime.now(tz=CURRENT_ZONE) - timedelta(days=25))
            querysetPayments = DailyPayments.objects.filter(distributor_id=distributor.id)
        else:
            querysetCredit = SalesTransaction.objects.none()
            querysetPayments = DailyPayments.objects.none()

        # if profile == "Sales":
        #     querysetCredit = SalesTransaction.objects.filter(salesPerson_id=salesPersonId, transaction_type="credit",
        #                                                      is_verified=False)
        #     querysetPayments = DailyPayments.objects.filter(salesPerson_id=salesPersonId)
        # else:
        #     querysetCredit = SalesTransaction.objects.filter(distributor_id=salesPersonId, transaction_type="credit",
        #                                                      is_verified=False)
        #     querysetPayments = DailyPayments.objects.filter(distributor_id=salesPersonId)



        serializerCredits = SalesTransactionShortSerializer(querysetCredit, many=True)
        serializerPayments = self.get_serializer(querysetPayments, many=True)
        # print(serializerCredits.data)
        # print(serializerPayments.data)
        return Response({"resultsCredit": serializerCredits.data, "resultsPayment": serializerPayments.data})

    def create(self, request, *args, **kwargs):
        data = request.data
        print(data)
        user = request.user
        # daily_payment_serializer = DailyPaymentsSerializer(data=data)
        # daily_payment_serializer.is_valid(raise_exception=True)
        # validated_data = daily_payment_serializer.validated_data
        # remark = validated_data.get('remark', '')
        if data.get('warehouse'):
            warehouse_obj = data.get('warehouse', 1)
        else:
            warehouse_obj = 1
        financeProfile = FinanceProfile.objects.filter(user=user).first()
        if financeProfile:
            # salesPerson_obj = validated_data.get('salesPerson')

            date_time = datetime.strptime(str(data.get('date')) + " " + str(data.get('time')),
                                          "%Y-%m-%d %H:%M:%S")
            # current_amount = Decimal(data.get('total_amount'))
            if data.get('paymentInfo'):
                paymentLines = data.get('paymentInfo')
                paymentLines = json.loads(paymentLines)
                for payment in paymentLines:
                    # print(payment)
                    amount = Decimal(payment['total_amount'])
                    salesPersonId = int(payment['salesPerson'])
                    profile = payment['profile']

                    remark = payment["remark"]
                    if profile == "Sales":
                        daily_payment = DailyPayments.objects.filter(warehouse_id=int(warehouse_obj), date=date_time,
                                                                     salesPerson_id=salesPersonId).first()
                    else:
                        daily_payment = DailyPayments.objects.filter(warehouse_id=int(warehouse_obj), date=date_time,
                                                                     distributor_id=salesPersonId).first()
                    if daily_payment:
                        daily_payment.total_amount += amount
                        daily_payment.save()
                        DailyPaymentLine.objects.create(dailyPayment=daily_payment, amount=amount, remark=remark,
                                                        date_time=date_time)

                    else:
                        if profile == "Sales":
                            daily_payment_new, created = DailyPayments.objects.update_or_create(warehouse_id=int(warehouse_obj),
                                                                                                date=date_time,
                                                                                                total_amount=amount,
                                                                                                salesPerson_id=salesPersonId)
                        else:
                            daily_payment_new, created = DailyPayments.objects.update_or_create(
                                warehouse_id=int(warehouse_obj),
                                date=date_time,
                                total_amount=amount,
                                remark=remark,
                                entered_by=financeProfile,
                                distributor_id=salesPersonId)
                        DailyPaymentLine.objects.update_or_create(dailyPayment=daily_payment_new, amount=amount,
                                                                  remark=remark, date_time=date_time)

                return Created({})

        else:
            return BadRequest({'error_type': "Validation Error",
                               'errors': [{'message': "Not a Valid Profile"}]})


class PaginationWithNoLimit(pagination.PageNumberPagination):
    page_size = 5000


class ExpenseRequestViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = PaginationWithNoLimit
    serializer_class = ExpenseRequestSerializer
    queryset = ExpenseRequest.objects.all().order_by('-date_time')


class ExpenseCategoryViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = PaginationWithNoLimit
    serializer_class = ExpenseCategorySerializer
    queryset = ExpenseCategory.objects.all().order_by('-id')


class SimpleFilterBackend(BaseFilterBackend):
    def get_schema_fields(self, view):
        return [coreapi.Field(
            name='from_date',
            location='query',
            required=False,
            type='string'
        ),
            coreapi.Field(
                name='to_date',
                location='query',
                required=False,
                type='string'
            )
        ]

class ExpenseViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = PaginationWithNoLimit
    serializer_class = ExpenseSerializer
    queryset = Expense.objects.all().order_by('-id')
    filter_backends = (filters.DjangoFilterBackend, SimpleFilterBackend)
    filterset_fields = ('entered_date',)

    def list(self, request, *args, **kwargs):
        if request.GET.get('from_date') and request.GET.get('to_date'):
            from_date = datetime.strptime(request.GET.get('from_date'), '%d/%m/%Y')
            to_date = datetime.strptime(request.GET.get('to_date'), '%d/%m/%Y')
            # If date is added automatically
            from_date = from_date.replace(hour=0, minute=0, second=0)
            to_date = to_date.replace(hour=0, minute=0, second=0)

            from_date = from_date
            delta = timedelta(hours=23, minutes=59, seconds=59)
            to_date = to_date + delta
            # print(from_date)
            # print(to_date)
            queryset = Expense.objects.filter(entered_date__gte=from_date,
                                                                           entered_date__lte=to_date).order_by('-id')
        else:
            queryset = Expense.objects.all().order_by('-id')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class BankDetailsViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = PaginationWithNoLimit
    serializer_class = BankDetailsSerializer
    queryset = BankDetails.objects.all().order_by('-id')


class BankTransactionViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = PaginationWithNoLimit
    serializer_class = BankDepositSerializer
    queryset = BankTransaction.objects.all().order_by('-date_time')
    filter_backends = (filters.DjangoFilterBackend,SimpleFilterBackend)
    filterset_fields = ('entered_date',)

    def list(self, request, *args, **kwargs):
        if request.GET.get('from_date') and request.GET.get('to_date'):
            from_date = datetime.strptime(request.GET.get('from_date'), '%d/%m/%Y')
            to_date = datetime.strptime(request.GET.get('to_date'), '%d/%m/%Y')
            # If date is added automatically
            from_date = from_date.replace(hour=0, minute=0, second=0)
            to_date = to_date.replace(hour=0, minute=0, second=0)

            from_date = from_date
            delta = timedelta(hours=23, minutes=59, seconds=59)
            to_date = to_date + delta
            # print(from_date)
            # print(to_date)
            queryset = BankTransaction.objects.filter(entered_date__gte=from_date,
                                                                           entered_date__lte=to_date).order_by('-id')
        else:
            queryset = BankTransaction.objects.all().order_by('-id')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class BeatInventoryViewSet(viewsets.GenericViewSet, mixins.CreateModelMixin, mixins.ListModelMixin,
                          mixins.RetrieveModelMixin):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = BeatInventorySerializer
    queryset = BeatInventory.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ('warehouse', 'date', 'inventory_status','entered_by')


    def list(self, request, *args, **kwargs):
        queryset = self.queryset
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = BeatInventoryHistorySerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = BeatInventoryHistorySerializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        data = request.data
        user = request.user
        print(data)
        warehouse_profile = UserProfile.objects.filter(user=request.user, department__name__in=['Warehouse']).first()
        if warehouse_profile:
            cart_products = data.get('inlines', [])
            if cart_products:
                print(cart_products)
                cart_products = json.loads(cart_products)
                for cart_product in cart_products:
                    beat_inventory_line_serializer = BeatInventoryLineSerializer(data=cart_product)
                    beat_inventory_line_serializer.is_valid(raise_exception=True)

                beat_inventory_create_serializer = BeatInventorySerializer(data=data)
                beat_inventory_create_serializer.is_valid(raise_exception=True)
                beat_inventory_obj = beat_inventory_create_serializer.save(desc="")

                beat_inventory_line_serializer = BeatInventoryLineSerializer(data=cart_products, many=True)
                beat_inventory_line_serializer.is_valid(raise_exception=True)
                beat_inventory_line_serializer.save(beat_inventory=beat_inventory_obj)


                results = BeatInventoryHistorySerializer(beat_inventory_obj).data

                return Response({"results":results}, status=status.HTTP_201_CREATED)
            else:
                return BadRequest({'error_type': "Validation Error",
                                   'errors': [{'message': "Cart can not be empty"}]})
        else:
            return Forbidden({'error_type': "permission_denied",
                              'errors': [{'message': "You do not have permission to perform this action."}]})
