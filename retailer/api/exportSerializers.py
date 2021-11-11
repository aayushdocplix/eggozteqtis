from rest_framework import serializers

from order.models.Order import Order
from retailer.models import Retailer


class RetailerExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Retailer
        fields = ('id',)
