from rest_framework import serializers

from custom_auth.api.serializers import UserSerializer, UserShortSerializer
from finance.models import FinanceProfile


class FinanceProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = FinanceProfile
        fields = '__all__'


class FinanceProfileShortSerializer(serializers.ModelSerializer):
    user = UserShortSerializer()

    class Meta:
        model = FinanceProfile
        fields = '__all__'


class FinancePersonHistorySerializer(serializers.ModelSerializer):

    class Meta:
        model = FinanceProfile
        fields = '__all__'
