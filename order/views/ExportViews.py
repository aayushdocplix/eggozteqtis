from django_filters import rest_framework as filters
from rest_framework import viewsets, mixins, permissions
from rest_framework.response import Response

from order.api.exportSerializers import OrderExportSerializer
from order.models.Order import Order


class OrderExportViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = OrderExportSerializer
    queryset = Order.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ('retailer', 'order_type', 'salesPerson', 'status', 'warehouse', 'delivery_date', 'date')

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset()).select_related('retailer','warehouse','salesPerson')
        serializer = self.get_serializer(queryset, many=True)
        return Response({"results": serializer.data})
