from rest_framework import serializers

from farmer.api.serializers import FarmerSerializer
from feedback.models import Feedback, FarmerFeedback, CustomerFeedback


class FeedbackSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Feedback
        fields = ('email', 'first_name', 'last_name', 'phone', 'query_type',
                  'message', 'feedback_date', 'is_resolved')


class FarmerFeedbackSerializer(serializers.ModelSerializer):
    farmer = FarmerSerializer()

    class Meta:
        model = FarmerFeedback
        fields = '__all__'


class FarmerFeedbackCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FarmerFeedback
        fields = ('title', 'query_type', 'message', 'file')


class CustomerFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerFeedback
        fields = '__all__'
