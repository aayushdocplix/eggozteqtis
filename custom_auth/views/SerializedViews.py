from datetime import timedelta, datetime

from django.http import HttpResponse

from django.utils.encoding import force_text
from django.utils.http import urlsafe_base64_decode
from rest_framework import permissions, viewsets, decorators, mixins, pagination
from rest_framework.decorators import api_view
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework_jwt.settings import api_settings

from django_filters import rest_framework as filters

from Eggoz.settings import CURRENT_ZONE
from base.response import Created, BadRequest, Ok
from custom_auth.api.serializers import UserSerializer, AddressSerializer, \
    UserRegistrationSerializer, AddressCreationSerializer, UserLoginSerializer, UserSerializerWithToken, \
    DummyUserRegistrationSerializer, AddressUpdateSerializer, \
    UserAddressAddSerializer, UserAddressDeleteSerializer, UserUpdateSerializer, UserDepartmentSerializer, \
    UserShortSerializer, FcmTokenSerializer
from custom_auth.models import User, Address, Department, PhoneModel, DeleteAddresses, UserProfile, UserData
from custom_auth.models.User import FarmAdminProfile, AdminProfile, FcmToken
from distributionchain.models import DistributionPersonProfile
from finance.models import FinanceProfile
from operationschain.models import OperationsPersonProfile
from saleschain.models import SalesPersonProfile
from supplychain.models import SupplyPersonProfile
from warehouse.models import WarehousePersonProfile, Warehouse


class PaginationWithLimit(pagination.PageNumberPagination):
    page_size = 1000


@api_view(['GET'])
def current_user(request):
    """
    Determine the current user by their token, and return their data
    """

    serializer = UserSerializer(request.user)
    content = JSONRenderer().render(serializer.data)

    # return Response(serializer.data)
    return Response(content)


@api_view(['GET'])
def current_user_cities(request):
    """
    Determine the current user by their token, and return their data
    """
    user = request.user
    user_cities = []
    user_addresses = user.addresses.all()
    default_address = user.default_address
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
    return Response({"results": {"cities": user_cities, "city": city_dict}})


class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.filter(is_visible=True)
    serializer_class = UserDepartmentSerializer
    pagination_class = PaginationWithLimit
    permission_classes = [permissions.AllowAny]


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    pagination_class = PaginationWithLimit
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        return self.serializer_class

    def list(self, request, *args, **kwargs):
        queryset = None
        department_users = request.GET.get('department_users', False)
        sales_users = request.GET.get('sales_users', False)
        warehouse = 1
        if request.GET.get('warehouse'):
            warehouse = int(request.GET.get('warehouse', 1))
        department_user_ids = []
        if department_users or sales_users:
            if warehouse > 0:
                sales_user_ids = SalesPersonProfile.objects.filter(warehouse=warehouse,is_visible=True, working_status="Onboarded").values_list('user_id',
                                                                                                    flat=True)

                supply_user_ids = SupplyPersonProfile.objects.filter(warehouse=warehouse).values_list('user_id',
                                                                                                      flat=True)
                operations_user_ids = OperationsPersonProfile.objects.filter(warehouse=warehouse).values_list('user_id',
                                                                                                              flat=True)
                warehouse_user_ids = WarehousePersonProfile.objects.filter(warehouse=warehouse).values_list('user_id',
                                                                                                            flat=True)
                distribution_user_ids = DistributionPersonProfile.objects.filter(warehouse=warehouse).values_list('user_id',
                                                                                                            flat=True)
                department_user_ids.extend(list(sales_user_ids))
                department_user_ids.extend(list(supply_user_ids))
                department_user_ids.extend(list(operations_user_ids))
                department_user_ids.extend(list(warehouse_user_ids))
                department_user_ids.extend(list(distribution_user_ids))
            else:
                pass
            queryset = self.filter_queryset(self.get_queryset()).filter(id__in=list(set(department_user_ids)))

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @decorators.action(detail=False, methods=['post'], url_path="add_address")
    def add_address(self, request, *args, **kwargs):
        user = request.user
        data = request.data
        user_serializer = UserAddressAddSerializer(data=data)
        user_serializer.is_valid(raise_exception=True)
        serializer_data = user_serializer.data
        if serializer_data.get('address'):
            address_serializer = AddressUpdateSerializer(data=serializer_data.get('address'))
            address_serializer.is_valid(raise_exception=True)
            new_address = address_serializer.save()
            if not user.default_address:
                user.default_address = new_address
            user.addresses.add(new_address)
            user.save()
        return Created({"success": "user address added successfully"})

    @decorators.action(detail=False, methods=['delete'], url_path="delete_address")
    def delete_address(self, request, *args, **kwargs):
        user = request.user
        data = request.data
        user_address_delete_serializer = UserAddressDeleteSerializer(data=data)
        user_address_delete_serializer.is_valid(raise_exception=True)
        address = user_address_delete_serializer.data.get('address')
        address = Address.objects.get(id=address)
        print(address)
        if user.default_address == address:
            print("in default")
            user.default_address = None
            deleteAddresses, created = DeleteAddresses.objects.get_or_create(user=user, address=address)
            user.save()
        if address in user.addresses.all():
            user.addresses.remove(address)
            deleteAddresses, created = DeleteAddresses.objects.get_or_create(user=user, address=address)
            user.save()

        return Created({"success": "user address removed successfully"})

    @decorators.action(detail=False, methods=['put'], url_path="update_user")
    def update_user(self, request, *args, **kwargs):
        user = request.user
        data = request.data
        user_update_serializer = UserUpdateSerializer(data=data)
        user_update_serializer.is_valid(raise_exception=True)
        serializer_data = user_update_serializer.validated_data
        print(serializer_data)
        user=user_update_serializer.user_update(instance=user, validated_data=serializer_data)
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)
        return Created({"success": "user updated successfully","token": token})


class BeatUserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserShortSerializer
    pagination_class = PaginationWithLimit
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        return self.serializer_class

    def list(self, request, *args, **kwargs):
        queryset = None

        beat_users = request.GET.get('beat_users', False)
        warehouse = int(request.GET.get('warehouse', 1))
        department_user_ids = []

        if beat_users:
            if warehouse > 0:
                sales_user_ids = SalesPersonProfile.objects.filter(warehouse=warehouse,is_visible=True, working_status="Onboarded").values_list('user_id',
                                                                                                    flat=True)
                distribution_user_ids = DistributionPersonProfile.objects.filter(warehouse=warehouse).values_list('user_id',
                                                                                                      flat=True)
                department_user_ids.extend(list(sales_user_ids))
                department_user_ids.extend(list(distribution_user_ids))
            else:
                pass
            queryset = self.filter_queryset(self.get_queryset()).filter(id__in=list(set(department_user_ids)))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class UserOnboardViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def get_serializer_class(self):
        if self.action in ['login']:
            return UserLoginSerializer
        return self.serializer_class

    @decorators.action(detail=False, methods=['post'], url_path="login")
    def login(self, request, *args, **kwargs):
        data = request.data
        userLoginSerializer = UserLoginSerializer(data=data)
        userLoginSerializer.is_valid(raise_exception=True)
        validated_data = userLoginSerializer.data
        user = User.objects.filter(phone_no=validated_data.get('phone_no')).first()

        if user:
            if user.check_password(validated_data.get('password')):
                if user.is_phone_verified:
                    user_serializer = UserSerializerWithToken(user)
                    return Ok(user_serializer.data)
                else:
                    time_difference = datetime.now(tz=CURRENT_ZONE) - timedelta(minutes=5)
                    phone_expiry = PhoneModel.objects.filter(phone_no=validated_data.get('phone_no'),
                                                             updated_at__gte=time_difference, isVerified=True)
                    if len(phone_expiry) > 0:
                        user.is_phone_verified = True
                        user.save()
                        user_serializer = UserSerializerWithToken(user)
                        return Ok(user_serializer.data)
                    else:
                        return BadRequest({'error_type': "Validation Error",
                                           'errors': [{'message': "This Phone No is Not Verified, Please Verify"}]})
            else:
                return BadRequest({'error_type': "Validation Error",
                                   'errors': [{'message': "Password Not Match"}]})
        return BadRequest({'error_type': "Validation Error",
                           'errors': [{'message': "User With This phone Number Does Not Exist"}]})

    @decorators.action(detail=False, methods=['post'], url_path="submit_password")
    def submit_password(self, request, *args, **kwargs):
        data = request.data
        userLoginSerializer = UserLoginSerializer(data=data)
        userLoginSerializer.is_valid(raise_exception=True)
        validated_data = userLoginSerializer.data
        time_difference = datetime.now(tz=CURRENT_ZONE) - timedelta(minutes=5)
        phone_expiry = PhoneModel.objects.filter(phone_no=validated_data.get('phone_no'),
                                                 updated_at__gte=time_difference, isVerified=True)
        if len(phone_expiry) > 0:
            user = User.objects.filter(phone_no=validated_data.get('phone_no')).first()
            if user:
                user.set_password(validated_data.get('password'))
                user.is_phone_verified = True
                user.save()
                user_serializer = UserSerializerWithToken(user)
                return Ok(user_serializer.data)
            else:
                dummy_user_serialiizer = DummyUserRegistrationSerializer(data=validated_data)
                dummy_user_serialiizer.is_valid(raise_exception=True)
                user = dummy_user_serialiizer.save(is_phone_verified=True)
                user_serializer = UserSerializerWithToken(user)
                return Ok(user_serializer.data)
        else:
            return BadRequest({'error_type': "Validation Error", 'errors': [
                {'message': "Otp has been expired or already verified, please request for new otp"}]})

    @decorators.action(detail=False, methods=['post'], url_path="sign-up")
    def registration(self, request, *args, **kwargs):
        department = request.data.get('department_name')
        phone_no = request.data.get('phone_no')
        print("department" + department)
        department_obj = Department.objects.filter(name=department).first()
        if department_obj:
            print(department_obj)
            if User.objects.filter(phone_no=phone_no):

                # warehouse = Warehouse.objects.filter(city=instance.default_address.city).first()
                # if warehouse:
                #     pass
                # else:
                #     warehouse = Warehouse.objects.filter(city_id=1).first()
                warehouse = Warehouse.objects.filter(city_id=1).first()
                user = User.objects.filter(phone_no=phone_no).first()
                if UserProfile.objects.filter(user=user, department=department_obj):

                    return BadRequest({'error_type': "Validation Error", 'errors': [
                        {'message': "Department With Phone no already Exists"}]})
                else:
                    user_profile = UserProfile.objects.filter(user=user).first()
                    email = request.data.get('email', None)
                    if email:
                        if User.objects.filter(email=email):
                            pass
                        else:
                            user.email = email
                            user.set_password(request.data.get('password', "eggoz@#user"))
                            user.save()
                    user_profile.department.add(department_obj)
                    user_profile.save()
                    user_data = UserData.objects.filter(userProfile=user_profile).first()
                    if not user_data:
                        UserData.objects.create(userProfile=user_profile, rating=5.0)
                    if department == "Admin":
                        admin_profile, created = AdminProfile.objects.get_or_create(user=user)
                        admin_profile.save()
                        admin_profile.warehouse_admin.add(warehouse)
                    elif department == "Sales":
                        sales_profile, created = SalesPersonProfile.objects.get_or_create(user=user,
                                                                                          warehouse=warehouse)
                        sales_profile.save()
                    elif department == "Supply":
                        supply_profile, created = SupplyPersonProfile.objects.get_or_create(user=user,
                                                                                            warehouse=warehouse)
                        supply_profile.save()
                    elif department == "Operations":
                        operation_profile, created = OperationsPersonProfile.objects.get_or_create(user=user,
                                                                                                   warehouse=warehouse)
                        operation_profile.save()
                    elif department == "Warehouse":
                        warehouse_profile, created = WarehousePersonProfile.objects.get_or_create(user=user,
                                                                                                  warehouse=warehouse)
                        warehouse_profile.save()

                    elif department == "Finance":
                        print(user)
                        finance_profile, created = FinanceProfile.objects.get_or_create(user=user)
                        finance_profile.save()

                    elif department == "Distribution":
                        distribution_profile, created = DistributionPersonProfile.objects.get_or_create(user=user,
                                                                                                        warehouse=warehouse)
                        distribution_profile.save()

                    elif department == "FarmAdmin":
                        farm_admin_profile, created = FarmAdminProfile.objects.get_or_create(user=user)
                        farm_admin_profile.save()
                    return Created({})

            else:
                data = request.data
                address_creation_serializer = AddressCreationSerializer(data=data)
                address_creation_serializer.is_valid(raise_exception=True)
                serializer = DummyUserRegistrationSerializer(data=data)
                serializer.is_valid(raise_exception=True)
                user = serializer.save()
                user_address = address_creation_serializer.save()
                user.addresses.add(user_address)
                if user.default_address is None:
                    user.default_address = user_address
                user.department = department_obj.name
                user.save()
                # TODO Turning off for now (WE can use email_confirm/otp validation or Nothing)
                # Send Confirmation Email

                # domain = 'http://' + request.get_host() + '/'
                # url_path = 'user/confirm_email/?'
                # message_data = {'domain': domain, 'uid': urlsafe_base64_encode(force_bytes(user.id))}
                # email_message = message_data.get('domain') + url_path + "uid=" + message_data.get('uid')
                # email_message_dict = {
                #     "email_message_key": email_message, "username": user.username}
                # email_subject = "Email Confirmation"
                # ema = EmailMultiAlternatives(subject=email_subject, body=email_message, from_email=FROM_EMAIL,
                #                              to=[str(user.email)])
                # html_template = get_template(
                #     settings.BASE_DIR + "/custom_auth/templates/onboard/email_confirm.html").render(
                #     context=email_message_dict)
                # ema.attach_alternative(html_template, "text/html")
                # ema.send()
                return Created({})
        else:
            return BadRequest({'error_type': "Validation Error", 'errors': [
                {'message': "Invalid department"}]})


def registration_confirm(request):
    uid64 = request.GET.get('uid')
    uid = force_text(urlsafe_base64_decode(uid64))
    try:
        user = User.objects.get(id=uid)
        user.is_active = True
        user.save()
        # TODO return to login screen
        return HttpResponse("Email Confirmed")
    except User.DoesNotExist:
        # TODO return to registration screen
        return HttpResponse("User does not exist")


class AddressViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = Address.objects.all().order_by('-id')
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def update(self, request, *args, **kwargs):
        print(request.data)
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.address_update(instance, request.data)
        return Response(serializer.data)


class FcmTokenViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = FcmToken.objects.all().order_by('-id')
    serializer_class = FcmTokenSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ('user',)

    def create(self, request, *args, **kwargs):
        data = request.data
        fcm_token, created = FcmToken.objects.update_or_create(
            user_id=data.get('user'),
            defaults={'token': data.get('token')})

        return Response(FcmTokenSerializer(fcm_token).data)

    def update(self, request, *args, **kwargs):
        print(request.data)
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.address_update(instance, request.data)
        return Response(serializer.data)