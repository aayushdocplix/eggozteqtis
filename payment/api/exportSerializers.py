from rest_framework import serializers

from payment.models import SalesTransaction


class SalesTransactionExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesTransaction
        fields = ('id',)