# serializers.py
from datetime import datetime

from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers
from rest_framework_jwt.settings import api_settings

from base.api.serializers import CitySerializer, EcommerceSectorSerializer
from base.models import City, EcommerceSector
from custom_auth.models import User, UserProfile, Address, UserData, Department
from custom_auth.models.User import AdminProfile, FarmAdminProfile, FcmToken
from distributionchain.models import DistributionPersonProfile
from ecommerce.api import CustomerWalletSerializer, CustomerReferralSerializer, CustomerSubscriptionSerializer
from ecommerce.models import Customer, CustomerWallet, CustomerReferral, CustomerSubscription
from farmer.models import Farmer
from finance.models import FinanceProfile
from operationschain.models import OperationsPersonProfile
from saleschain.models import SalesPersonProfile
from supplychain.models import SupplyPersonProfile
from warehouse.models import WarehousePersonProfile


class GenerateOtpSerializer(serializers.Serializer):
    phone_no = PhoneNumberField(required=True)
    hash_code = serializers.CharField(required=False)
    otp_type = serializers.CharField(required=False)
    sender_type = serializers.CharField(required=False)
    sms_mode = serializers.CharField(required=False)


class ValidateOtpSerializer(serializers.Serializer):
    phone_no = PhoneNumberField(required=True)
    otp = serializers.IntegerField(required=True)
    name = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)


class CustomerCreationSerializer(serializers.Serializer):
    name = serializers.CharField(required=False, max_length=256)
    ecommerce_sector = serializers.PrimaryKeyRelatedField(required=True, queryset=EcommerceSector.objects.all())
    city = serializers.PrimaryKeyRelatedField(required=True, queryset=City.objects.all())


class CustomerWalletCreationSerializer(serializers.Serializer):
    customer = serializers.PrimaryKeyRelatedField(required=True, queryset=Customer.objects.all())


class AddressSerializer(serializers.HyperlinkedModelSerializer):
    date_added = serializers.ReadOnlyField()
    city = CitySerializer()
    ecommerce_sector = EcommerceSectorSerializer()
    default_address_user = serializers.PrimaryKeyRelatedField(many=True, queryset=User.objects.all())
    user_addresses_user = serializers.PrimaryKeyRelatedField(many=True, queryset=User.objects.all())

    def create(self, validated_data):
        print(self)
        address = Address.objects.create(
            address_name=validated_data['address_name'],
            building_address=validated_data['building_address'],
            ecommerce_sector=validated_data['ecommerce_sector'] if validated_data['ecommerce_sector'] else None,
            street_address=validated_data['building_address'],
            city=City.objects.get(pk=validated_data['city']),
            landmark=validated_data['landmark'],
            pinCode=validated_data['pinCode'],
        )

        # User.objects.create_or_update(pk=userId, default_address=address)

        address.save()
        return address

    class Meta:
        model = Address
        fields = (
            'id', 'default_address_user', 'user_addresses_user', 'address_name', 'building_address', 'street_address',
            'city', 'ecommerce_sector', 'name', 'phone_no',
            'landmark', 'pinCode', 'latitude', 'longitude', 'date_added', 'billing_city')

    def address_update(self, instance, validated_data):
        if validated_data.get('address_name'):
            instance.address_name = validated_data.get('address_name')
        if validated_data.get('building_address'):
            instance.building_address = validated_data.get('building_address')
        if validated_data.get('ecommerce_sector'):
            ecomm_scetor = EcommerceSector.objects.filter(id=validated_data.get('ecommerce_sector')).first()
            if ecomm_scetor:
                instance.ecommerce_sector = ecomm_scetor
            else:
                raise serializers.ValidationError("EcommerceSector with this id not exists")
        if validated_data.get('city'):
            city = City.objects.filter(id=validated_data.get('city')).first()
            if city:
                instance.city_id = validated_data.get('city')
            else:
                raise serializers.ValidationError("City with this id not exists")
        if validated_data.get('street_address'):
            instance.street_address = validated_data.get('street_address')
        if validated_data.get('billing_city'):
            instance.billing_city = validated_data.get('billing_city')
        if validated_data.get('landmark'):
            instance.landmark = validated_data.get('landmark')
        if validated_data.get('latitude'):
            instance.latitude = validated_data.get('latitude')
        if validated_data.get('longitude'):
            instance.longitude = validated_data.get('longitude')
        if validated_data.get('pinCode'):
            instance.pinCode = validated_data.get('pinCode')
        if validated_data.get('phone_no'):
            instance.phone_no = validated_data.get('phone_no')
        if validated_data.get('name'):
            instance.name = validated_data.get('name')
        instance.save()
        return instance


class UserDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserData
        fields = '__all__'


class UserShortSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'name', 'phone_no', 'image', 'is_profile_verified')


class UserTinySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'name', 'phone_no')

class UserSerializer(serializers.HyperlinkedModelSerializer):
    userProfile = serializers.SerializerMethodField()
    # default_address = serializers.PrimaryKeyRelatedField(queryset=Address.objects.all())
    default_address = AddressSerializer(read_only=True)
    # addresses = serializers.PrimaryKeyRelatedField(many=True, queryset=Address.objects.all())
    addresses = AddressSerializer(read_only=True, many=True)
    userCities = serializers.SerializerMethodField()
    userData = serializers.SerializerMethodField()
    userTokenData = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id',
                  'email', 'name', 'phone_no', 'default_address', 'addresses', 'userProfile', 'userData', 'userCities',
                  'userTokenData', 'date_joined', 'is_profile_verified')

    def get_userTokenData(self, obj):
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(obj)
        token = jwt_encode_handler(payload)
        print(payload)
        return {"token":token,"token_exp": datetime.fromtimestamp(int(payload.get('exp')))}

    def get_userData(self, obj):
        user_profile = UserProfile.objects.filter(user=obj).first()
        if user_profile:
            userData = UserData.objects.filter(userProfile=user_profile).first()
            if userData:
                return UserDataSerializer(userData).data
            else:
                return None
        else:
            return None

    def get_userProfile(self, obj):
        user_profile = UserProfile.objects.filter(user=obj).first()
        if user_profile:
            userProfileDict = {}
            userProfileDict['id'] = user_profile.id
            departments = user_profile.department.all()
            user_departments = []
            department_profiles = []
            customer_referral = []
            customer_subscriptions = []
            warehouse_ids = []
            if departments:
                for department in departments:
                    department_name = department.name
                    user_departments.append(department_name)
                    if department_name == "Sales":
                        salesPersonProfile = SalesPersonProfile.objects.filter(user=obj).first()
                        if salesPersonProfile:
                            department_profiles.append({"salesPersonProfile": salesPersonProfile.id,
                                                        "management_status": salesPersonProfile.management_status, "is_mt":salesPersonProfile.is_mt_profile})
                            if salesPersonProfile.warehouse:
                                warehouse_ids.append({"salesWarehouseId": salesPersonProfile.warehouse.id})
                    elif department_name == "Supply":
                        supplyPersonProfile = SupplyPersonProfile.objects.filter(user=obj).first()
                        if supplyPersonProfile:
                            department_profiles.append({"supplyPersonProfile": supplyPersonProfile.id,
                                                        "management_status": supplyPersonProfile.management_status})
                            if supplyPersonProfile.warehouse:
                                warehouse_ids.append({"supplyWarehouseId": supplyPersonProfile.warehouse.id})
                    elif department_name == "Warehouse":
                        warehousePersonProfile = WarehousePersonProfile.objects.filter(user=obj).first()
                        if warehousePersonProfile:
                            department_profiles.append({"warehousePersonProfile": warehousePersonProfile.id,
                                                        "management_status": warehousePersonProfile.management_status})
                            if warehousePersonProfile.warehouse:
                                warehouse_ids.append({"warehouseId": warehousePersonProfile.warehouse.id})
                    elif department_name == "Operations":
                        opsPersonProfile = OperationsPersonProfile.objects.filter(user=obj).first()
                        if opsPersonProfile:
                            department_profiles.append({"opsPersonProfile": opsPersonProfile.id,
                                                        "management_status": opsPersonProfile.management_status})
                            if opsPersonProfile.warehouse:
                                warehouse_ids.append({"opsWarehouseId": opsPersonProfile.warehouse.id})
                    elif department_name == "Admin":
                        adminProfile = AdminProfile.objects.filter(user=obj).first()
                        if adminProfile:
                            department_profiles.append(
                                {"adminProfile": adminProfile.id, "management_status": adminProfile.management_status})
                            if adminProfile.warehouses:
                                for warehouse in adminProfile.warehouses:
                                    warehouse_ids.append({"adminWarehouseid": warehouse.id})

                    elif department_name == "Farmer":
                        farmer = Farmer.objects.filter(farmer=obj).first()
                        if farmer:
                            department_profiles.append({"farmerProfile": farmer.id, "management_status": None})

                    elif department_name == "Customer":
                        user_departments.append(department_name)
                        customer = Customer.objects.filter(user=obj).first()
                        if customer:
                            if CustomerReferral.objects.filter(customer=customer):
                                customerReferral = CustomerReferral.objects.filter(customer=customer).first()
                                customer_referral.append(
                                    {"referral": CustomerReferralSerializer(customerReferral).data})
                            if CustomerWallet.objects.filter(customer=customer):
                                customerWallet = CustomerWallet.objects.filter(customer=customer).first()
                                department_profiles.append({"customerProfile": customer.id,
                                                            "wallet": CustomerWalletSerializer(customerWallet).data})
                            else:
                                department_profiles.append({"customerProfile": customer.id})

                            if CustomerSubscription.objects.filter(customer=customer,expiry_date__gt=datetime.now()):
                                subs = CustomerSubscription.objects.filter(customer=customer,expiry_date__gt=datetime.now())
                                customer_subscriptions.append({"subscriptions": CustomerSubscriptionSerializer(subs, many=True).data})
                    elif department_name == "Finance":
                        financeProfile = FinanceProfile.objects.filter(user=obj).first()
                        if financeProfile:
                            department_profiles.append({"financeProfile": financeProfile.id,
                                                        "management_status": financeProfile.management_status})
                            if financeProfile.warehouse:
                                warehouse_ids.append({"warehouseId": financeProfile.warehouse.id})

                    elif department_name == "Distribution":
                        distributionPersonProfile = DistributionPersonProfile.objects.filter(user=obj).first()
                        if distributionPersonProfile:
                            department_profiles.append({"distributionPersonProfile": distributionPersonProfile.id,
                                                        "management_status": distributionPersonProfile.management_status})
                            if distributionPersonProfile.warehouse:
                                warehouse_ids.append({"distributionWarehouseId": distributionPersonProfile.warehouse.id})

                    elif department_name == "FarmAdmin":
                        farmAdminProfile = FarmAdminProfile.objects.filter(user=obj).first()
                        if farmAdminProfile:
                            department_profiles.append({"farmAdminProfile": farmAdminProfile.id,
                                                        "management_status": farmAdminProfile.management_status})
                            # if farmAdminProfile.warehouse:
                            #     warehouse_ids.append({"farmAdminProfile": farmAdminProfile.warehouse.id})

            userProfileDict['departments'] = user_departments
            userProfileDict['department_profiles'] = department_profiles
            userProfileDict['warehouse_ids'] = warehouse_ids
            userProfileDict['customer_referral'] = customer_referral
            userProfileDict['customer_subscriptions'] = customer_subscriptions
            return userProfileDict
        else:
            return None

    def get_userCities(self, obj):
        user_cities = []
        user_addresses = obj.addresses.all()
        for user_address in user_addresses:
            city_dict = {}
            if user_address.city:
                city_dict['id'] = user_address.city.id
                city_dict['city_name'] = user_address.city.city_name
                user_cities.append(city_dict)
        user_cities = list({user_city['id']: user_city for user_city in user_cities}.values())
        return user_cities


class UserCustomerSerializer(serializers.HyperlinkedModelSerializer):
    userProfile = serializers.SerializerMethodField()
    # default_address = serializers.PrimaryKeyRelatedField(queryset=Address.objects.all())
    default_address = AddressSerializer(read_only=True)
    # addresses = serializers.PrimaryKeyRelatedField(many=True, queryset=Address.objects.all())
    addresses = AddressSerializer(read_only=True, many=True)
    userCities = serializers.SerializerMethodField()
    userData = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id',
                  'email', 'name', 'phone_no', 'default_address', 'addresses', 'userProfile', 'userData', 'userCities',
                  'date_joined', 'is_profile_verified')

    def get_userData(self, obj):
        user_profile = UserProfile.objects.filter(user=obj).first()
        if user_profile:
            userData = UserData.objects.filter(userProfile=user_profile).first()
            if userData:
                return UserDataSerializer(userData).data
            else:
                return None
        else:
            return None

    def get_userProfile(self, obj):
        user_profile = UserProfile.objects.filter(user=obj).first()
        if user_profile:
            userProfileDict = {}
            userProfileDict['id'] = user_profile.id
            departments = user_profile.department.all()
            user_departments = []
            department_profiles = []
            warehouse_ids = []
            customer_referral = []
            customer_subscriptions = []
            if departments:
                for department in departments:
                    department_name = department.name

                    if department_name == "Farmer":
                        user_departments.append(department_name)
                        farmer = Farmer.objects.filter(farmer=obj).first()
                        if farmer:
                            department_profiles.append({"farmerProfile": farmer.id, "management_status": None})

                    elif department_name == "Customer":
                        user_departments.append(department_name)
                        customer = Customer.objects.filter(user=obj).first()
                        if customer:
                            if CustomerReferral.objects.filter(customer=customer):
                                customerReferral = CustomerReferral.objects.filter(customer=customer).first()
                                customer_referral.append({"referral": CustomerReferralSerializer(customerReferral).data})
                            if CustomerWallet.objects.filter(customer=customer):
                                customerWallet = CustomerWallet.objects.filter(customer=customer).first()
                                department_profiles.append({"customerProfile": customer.id,
                                                            "wallet": CustomerWalletSerializer(customerWallet).data})
                            else:
                                department_profiles.append({"customerProfile": customer.id})
                            if CustomerSubscription.objects.filter(customer=customer,expiry_date__gt=datetime.now()):
                                subs = CustomerSubscription.objects.filter(customer=customer,expiry_date__gt=datetime.now())
                                customer_subscriptions.append({"subscriptions": CustomerSubscriptionSerializer(subs, many=True).data})

            userProfileDict['departments'] = user_departments
            userProfileDict['department_profiles'] = department_profiles
            userProfileDict['warehouse_ids'] = warehouse_ids
            userProfileDict['customer_referral'] = customer_referral
            userProfileDict['customer_subscriptions'] = customer_subscriptions

            return userProfileDict
        else:
            return None

    def get_userCities(self, obj):
        user_cities = []
        user_addresses = obj.addresses.all()
        for user_address in user_addresses:
            city_dict = {}
            if user_address.city:
                city_dict['id'] = user_address.city.id
                city_dict['city_name'] = user_address.city.city_name
                user_cities.append(city_dict)
        user_cities = list({user_city['id']: user_city for user_city in user_cities}.values())
        return user_cities


class UserCitiesSerializer(serializers.HyperlinkedModelSerializer):
    userCities = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'userCities')

    def get_userCities(self, obj):
        user_cities = []
        user_addresses = obj.addresses.all()
        default_address = obj.default_address
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
        return {"results": {"cities": user_cities, "city": city_dict}}


class UserDepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'


class UserSerializerWithToken(serializers.ModelSerializer):
    date_joined = serializers.ReadOnlyField()
    token = serializers.SerializerMethodField()
    userTokenData = serializers.SerializerMethodField()

    def get_token(self, obj):
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

        payload = jwt_payload_handler(obj)
        token = jwt_encode_handler(payload)
        return token

    def get_userTokenData(self, obj):
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(obj)
        token = jwt_encode_handler(payload)
        print(payload)
        return {"token":token,"token_exp": datetime.fromtimestamp(int(payload.get('exp')))}

    def create(self, validated_data):
        user = User.objects.create(
            name=validated_data['name'],
            email=validated_data['email'],
            phone_no=validated_data['phone_no'],
        )

        password = validated_data.pop('password', None)
        if password is not None:
            user.set_password(password)
        user.save()
        return user

    class Meta(object):
        model = User
        fields = ('id', 'email', 'phone_no', 'token', 'name', 'userTokenData'
                                                      'date_joined')
        extra_kwargs = {'password': {'write_only': True}}


class UserSmallSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'name', 'is_profile_verified')


class UserMediumSerializer(serializers.ModelSerializer):
    default_address = AddressSerializer()
    addresses = AddressSerializer(many=True)

    class Meta:
        model = User
        fields = ('id', 'name', 'email', 'phone_no', 'default_address', 'addresses', 'image', 'is_profile_verified')


class AddressCreationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = '__all__'

    def create(self, validated_data):
        address = Address(**validated_data)
        address.save()
        return address


class AddressUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = (
            'id', 'address_name', 'building_address', 'street_address', 'city', 'billing_city', 'landmark', 'latitude',
            'longitude', 'pinCode', 'ecommerce_sector', 'phone_no', 'name')


class UserLoginSerializer(serializers.Serializer):
    password = serializers.CharField(required=True)
    phone_no = PhoneNumberField(required=True)


class UserRegistrationSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(max_length=None, use_url=True, required=False)

    class Meta:
        model = User
        fields = ('email', 'password', 'name', 'phone_no', 'image')

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        if validated_data.get('name'):
            user.name = validated_data.get('name')
        user.email = validated_data.get('email')
        user.set_password(password)
        user.save()
        return user


class DummyUserRegistrationSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(max_length=None, use_url=True, required=False)
    email = serializers.EmailField(required=False)
    password = serializers.CharField(required=False)

    class Meta:
        model = User
        fields = ('email', 'name', 'phone_no', 'image', 'password')

    def validate(self, data):
        email = data.get('email', None)
        if email:
            user = User.objects.filter(email=email).first()
            if user:
                raise serializers.ValidationError("Email already exist")
        return data

    def create(self, validated_data):
        print(validated_data)
        email = validated_data.get('email')
        name = validated_data.get('name')
        random_email = str(validated_data.get('phone_no'))[-10::]
        if email is None:
            email = '%s@gmail.com' % (random_email)
            validated_data['email'] = email
        if name is None:
            name = random_email
            validated_data['name'] = name
        user = User(**validated_data)
        if validated_data.get('password'):
            user.set_password(validated_data.get('password'))
        else:
            user.set_unusable_password()
        user.save()
        return user

    def update(self, instance, validated_data):
        email = validated_data.get('email', instance.email)
        name = validated_data.get('name', instance.name)
        if email is not None:
            instance.email = email
        instance.name = name
        instance.save()
        return instance


class UserAddressAddSerializer(serializers.Serializer):
    address = serializers.JSONField(required=True)


class UserAddressDeleteSerializer(serializers.Serializer):
    address = serializers.PrimaryKeyRelatedField(required=True, queryset=Address.objects.all())


class UserUpdateSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(max_length=None, use_url=True, required=False)
    email = serializers.EmailField(required=False)
    name = serializers.CharField(required=False)
    phone_no = PhoneNumberField(required=False)

    class Meta:
        model = User
        fields = ('email', 'name', 'phone_no', 'image', 'default_address')

    def user_update(self, instance, validated_data):
        if validated_data.get('email'):
            instance.email = validated_data.get('email')
        if validated_data.get('name'):
            instance.name = validated_data.get('name')
            customer = Customer.objects.filter(user=instance).first()
            if customer:
                customer.name = validated_data.get('name')
                customer.save()
        if validated_data.get('phone_no'):
            instance.phone_no = validated_data.get('phone_no')
            instance.is_phone_verified = False
        if validated_data.get('default_address'):
            instance.default_address = validated_data.get('default_address')
        if validated_data.get('image'):
            instance.image = validated_data.get('image')
        instance.is_profile_verified = True

        instance.save()
        return instance


class FcmTokenSerializer(serializers.ModelSerializer):

    class Meta:
        model = FcmToken
        fields = '__all__'
