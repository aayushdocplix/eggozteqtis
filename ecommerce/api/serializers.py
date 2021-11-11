from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers

from custom_auth.models import User
from ecommerce.models.Customer import Customer, RechargeVoucher, CustomerWallet, ReferralData, CustomerReferral, \
    SubscriptionRequest, NotifyCustomer
from ecommerce.models.Subscriptions import CustomerSubscription, CustomerMemberShip, MemberShip, MemberShipData, \
    MemberShipBenefits, SubscriptionBenefits, Subscription, SubscriptionExtras


class CustomerSerializer(serializers.ModelSerializer):

    class Meta:
        model = Customer
        fields = '__all__'


class CustomerWalletSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer()

    class Meta:
        model = CustomerWallet
        fields = '__all__'


class ReferralDataSerializer(serializers.ModelSerializer):

    class Meta:
        model = ReferralData
        fields = '__all__'

class CustomerReferralSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer()
    referral_data = ReferralDataSerializer(many=True)

    class Meta:
        model = CustomerReferral
        fields = '__all__'

class MemberShipDataSerializer(serializers.ModelSerializer):

    class Meta:
        model = MemberShipData
        fields = ('id', 'months', 'rate')


class MemberShipBenefitsSerializer(serializers.ModelSerializer):

    class Meta:
        model = MemberShipBenefits
        fields = ('benefit',)


class MemberShipSerializer(serializers.ModelSerializer):
    data_membership = MemberShipDataSerializer(many=True)
    benefit_membership = MemberShipBenefitsSerializer(many=True)

    class Meta:
        model = MemberShip
        fields = ('name', 'margin', 'data_membership', 'benefit_membership')


class SubscriptionBenefitsSerializer(serializers.ModelSerializer):

    class Meta:
        model = SubscriptionBenefits
        fields = ('benefit', 'is_visible')


class SubscriptionExtrasSerializer(serializers.ModelSerializer):

    class Meta:
        model = SubscriptionExtras
        fields = ('extra', 'is_visible')


class SubscriptionSerializer(serializers.ModelSerializer):
    # benefit_subscription = SubscriptionBenefitsSerializer(many=True)
    # extra_subscription = SubscriptionExtrasSerializer(many=True)

    benefit_subscription = serializers.SerializerMethodField()
    extra_subscription = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = '__all__'

    def get_benefit_subscription(self, obj):
        return SubscriptionBenefitsSerializer(obj.benefit_subscription.filter(is_visible=True), many=True).data

    def get_extra_subscription(self, obj):
        return SubscriptionExtrasSerializer(obj.extra_subscription.filter(is_visible=True), many=True).data


class CustomerSubscriptionSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomerSubscription
        fields = '__all__'


class CustomerSubscriptionCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomerSubscription
        exclude = ('days',)

class CustomerSubscriptionRequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionRequest
        exclude = ('days',)



class CustomerMemberShipSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomerMemberShip
        fields = '__all__'


class NotifyCustomerSerializer(serializers.ModelSerializer):

    class Meta:
        model = NotifyCustomer
        fields = '__all__'


class CustomerCreateSerializer(serializers.Serializer):
    user = serializers.PrimaryKeyRelatedField(required=True, queryset=User.objects.all())
    name = serializers.CharField(required=True, max_length=100)
    phone_no = PhoneNumberField(required=False)
    pinCode = serializers.IntegerField(required=False)
    email = serializers.EmailField(required=False)


class RechargeVoucherSerializer(serializers.ModelSerializer):
    class Meta:
        model = RechargeVoucher
        fields = '__all__'
