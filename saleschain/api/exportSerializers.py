from rest_framework import serializers

from order.models.Order import Order
from payment.models import Invoice, SalesTransaction
from retailer.models import RetailerEggsdata
from saleschain.models import SalesEggsdata


class SalesExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ('id',)


class InvoiceExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = ('id',)


class SalesTransactionExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesTransaction
        fields = ('id',)


class SalesEggsDataExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesEggsdata
        fields = ('id',)


class RetailerEggsDataExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = RetailerEggsdata
        fields = ('id',)
