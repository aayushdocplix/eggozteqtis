from rest_framework import viewsets, permissions, mixins
from django_filters import rest_framework as filters

from base.response import Created, BadRequest
from feedwarehouse.api.serializers import FeedWarehouseSerializer, FeedProductDivisionSerializer, \
    FeedProductSubDivisionSerializer, ProductVendorSerializer, FeedProductSpecificationSerializer, \
    FeedProductSerializer, FeedOrderCreateSerializer, FeedOrderLineCreateSerializer, FeedOrderSerializer
from feedwarehouse.models import FeedWarehouse, FeedProductDivision, FeedProductSubDivision, ProductVendor, \
    FeedProductSpecification, FeedProduct, FeedOrder


class FeedWarehouseViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = FeedWarehouseSerializer
    queryset = FeedWarehouse.objects.all()


class FeedProductDivisionViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = FeedProductDivisionSerializer
    queryset = FeedProductDivision.objects.all()


class FeedProductSubDivisionViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = FeedProductSubDivisionSerializer
    queryset = FeedProductSubDivision.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ('feedProductDivision',)


class ProductVendorViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ProductVendorSerializer
    queryset = ProductVendor.objects.all()


class FeedProductSpecificationViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = FeedProductSpecificationSerializer
    queryset = FeedProductSpecification.objects.all()


class FeedProductViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = FeedProductSerializer
    queryset = FeedProduct.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ('feedProductDivision', 'vendor', 'feedProductSubDivision','is_popular')


class FeedOrderViewSet(viewsets.GenericViewSet, mixins.CreateModelMixin,mixins.ListModelMixin,mixins.RetrieveModelMixin):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = FeedOrderSerializer
    queryset = FeedOrder.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ('farmer', 'status')

    def create(self, request, *args, **kwargs):
        feed_order_serializer = FeedOrderCreateSerializer(data=request.data)
        feed_order_serializer.is_valid(raise_exception=True)
        order_in_lines = request.data.get('feed_order_lines', [])
        if order_in_lines and len(order_in_lines) > 0:
            feed_order_line_serializers = FeedOrderLineCreateSerializer(data=order_in_lines, many=True)
            feed_order_line_serializers.is_valid(raise_exception=True)
            feed_order_obj = feed_order_serializer.save()
            for order_in_line in order_in_lines:
                feed_order_line_serializer = FeedOrderLineCreateSerializer(data=order_in_line)
                feed_order_line_serializer.is_valid(raise_exception=True)
                print(feed_order_line_serializer)
                feed_order_line_serializer.save(feed_order=feed_order_obj)

            feed_order_lines = feed_order_obj.feed_order_lines.all()
            order_lines = None
            for feed_order_line in feed_order_lines:
                if order_lines is None:
                    order_lines = feed_order_line.feed_product.name + "X" + str(feed_order_line.quantity)
                else:
                    order_lines = order_lines + "&" + feed_order_line.feed_product.name + "X" + str(
                        feed_order_line.quantity)
                email_message = "Farmer Name: " + feed_order_obj.farmer.farmer.name + "\nFeedOrder Id: " + str(feed_order_obj.id) + "\n" + "Order Price: " + str(
                    feed_order_obj.order_price_amount) + "\nOrdered Products: " + order_lines
                print(email_message)
                # send_mail("Feed Order Received", email_message, FROM_EMAIL,
                #           ['paul.manohar@eggoz.in', 'jkguptaer@gmail.com'])
            return Created({"success": "feed order created successfully"})
        else:
            return BadRequest({'error_type': "ValidationError",
                               'errors': [{'message': "feed_order_lines required and may not be empty"}]})
