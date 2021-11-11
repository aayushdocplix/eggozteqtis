import json
from datetime import datetime

from django.db.models import Max
from django.utils import timezone
from django_filters import rest_framework as filters
from rest_framework import permissions, viewsets, decorators, mixins

from Eggoz.settings import CURRENT_ZONE
from base.models import City
from base.response import Forbidden, BadRequest, Created, Ok
from base.views import PaginationWithNoLimit
from custom_auth.api.serializers import DummyUserRegistrationSerializer, AddressCreationSerializer
from custom_auth.models import UserProfile, Department
from retailer.api.serializers import CustomerCategorySerializer, CustomerSubCategorySerializer, \
    RetailerOnboardSerializer, RetailerSerializer, RetailOwnerCreateSerializer, RetailerUpdateSerializer, \
    CommissionSlabSerializer, DiscountSlabSerializer, ClassificationSerializer, RetailerPaymentCycleSerializer, \
    RetailerShortsSerializer, RetailerBeatSerializer, MarginRateSerializer
from retailer.models.Retailer import Customer_Category, Customer_SubCategory, Retailer, CommissionSlab, Classification, \
    DiscountSlab, RetailerShorts, RetailerPaymentCycle, RetailerBeat, MarginRates
from saleschain.models import SalesPersonProfile


class CustomerCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.AllowAny,)
    pagination_class = PaginationWithNoLimit
    serializer_class = CustomerCategorySerializer
    queryset = Customer_Category.objects.all().order_by('name')


class MarginRatesViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.AllowAny,)
    pagination_class = PaginationWithNoLimit
    serializer_class = MarginRateSerializer
    queryset = MarginRates.objects.all().order_by('id')
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ('margin',)



class RetailerBeatViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin):
    permission_classes = (permissions.AllowAny,)
    pagination_class = PaginationWithNoLimit
    serializer_class = RetailerBeatSerializer
    queryset = RetailerBeat.objects.all().order_by('beat_number')
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ('beat_number',)

class CustomerShortNameViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.AllowAny,)
    pagination_class = PaginationWithNoLimit
    serializer_class = RetailerShortsSerializer
    queryset = RetailerShorts.objects.all().order_by('id')


class CustomerPaymentCycleViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.AllowAny,)
    pagination_class = PaginationWithNoLimit
    serializer_class = RetailerPaymentCycleSerializer
    queryset = RetailerPaymentCycle.objects.all().order_by('id')


class CustomerCommissionSlabViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.AllowAny,)
    pagination_class = PaginationWithNoLimit
    serializer_class = CommissionSlabSerializer
    queryset = CommissionSlab.objects.all().order_by('id')
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ('is_visible', 'is_available')


class CustomerDiscountSlabViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.AllowAny,)
    pagination_class = PaginationWithNoLimit
    serializer_class = DiscountSlabSerializer
    queryset = DiscountSlab.objects.all().order_by('id')


class CustomerClassificationViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.AllowAny,)
    pagination_class = PaginationWithNoLimit
    serializer_class = ClassificationSerializer
    queryset = Classification.objects.all().order_by('id')


class CustomerSubCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.AllowAny,)
    pagination_class = PaginationWithNoLimit
    serializer_class = CustomerSubCategorySerializer
    queryset = Customer_SubCategory.objects.all().order_by('name')
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ('category',)


class RetailerViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = RetailerSerializer
    queryset = Retailer.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = {'code': ['startswith']}

    def get_serializer_context(self):
        context = super(RetailerViewSet, self).get_serializer_context()
        if self.request:
            context.update({'request': self.request, 'days': self.request.GET.get('days', 7)})
        return context

    @decorators.action(detail=False, methods=['post'], url_path="onboard")
    def onboard(self, request, *args, **kwargs):
        data = request.data
        print(data)
        # Check Loggedin User is Sales Person or not
        user_profile = UserProfile.objects.filter(user=request.user, department__name__in=['Sales']).first()
        if user_profile:
            salesPersonProfile = SalesPersonProfile.objects.filter(user=request.user).first()
            if salesPersonProfile:
                dummy_user_register_serializer = DummyUserRegistrationSerializer(data=data)
                dummy_user_register_serializer.is_valid(raise_exception=True)
                if not data.get('shipping_address'):
                    return BadRequest({'error_type': "ValidationError",
                                       'errors': [{'message': "Shipping Address required"}]})
                shipping_address = data.get('shipping_address')
                shipping_address = json.loads(shipping_address)
                shipping_address_creation_serializer = AddressCreationSerializer(data=shipping_address)
                shipping_address_creation_serializer.is_valid(raise_exception=True)
                if not data.get('billing_shipping_address_same'):
                    billing_address = data.get('billing_address', None)
                    if billing_address:
                        billing_address = json.loads(billing_address)
                        billing_address_creation_serializer = AddressCreationSerializer(data=billing_address)
                        billing_address_creation_serializer.is_valid(raise_exception=True)
                    else:
                        return BadRequest({'error_type': "ValidationError",
                                           'errors': [{'message': "Billing Address required"}]})
                retailer_onboard_serializer = RetailerOnboardSerializer(data=data)
                retailer_onboard_serializer.is_valid(raise_exception=True)
                if not data.get('retail_owners'):
                    return BadRequest({'error_type': "ValidationError",
                                       'errors': [{'message': "Owner required"}]})
                retail_owners = data.get('retail_owners', [])
                if retail_owners:
                    retail_owners = json.loads(retail_owners)
                    if len(retail_owners) > 0:
                        for retail_owner in retail_owners:
                            retail_owner_serializer = RetailOwnerCreateSerializer(data=retail_owner)
                            retail_owner_serializer.is_valid(raise_exception=True)
                    else:
                        return BadRequest({'error_type': "ValidationError",
                                           'errors': [{'message': " At least one Retail owner required"}]})
                try:
                    retailer = dummy_user_register_serializer.save()
                    retailer_user_profile, created = UserProfile.objects.get_or_create(user=retailer)
                    retailer_department, created = Department.objects.get_or_create(name="Retailer")
                    retailer_user_profile.department.add(retailer_department)
                    try:
                        retailer_shipping_address = shipping_address_creation_serializer.save()
                        retailer.addresses.add(retailer_shipping_address)
                        if retailer.default_address is None:
                            retailer.default_address = retailer_shipping_address
                        retailer.save()
                        if data.get('billing_shipping_address_same'):
                            retailer_billing_address = retailer_shipping_address
                        else:
                            billing_address = json.loads(data.get('billing_address'))
                            billing_address_creation_serializer = AddressCreationSerializer(data=billing_address)
                            billing_address_creation_serializer.is_valid(raise_exception=True)
                            retailer_billing_address = billing_address_creation_serializer.save()
                        try:
                            beat_number = data.get("beat_number", 0)
                            classification, created = Classification.objects.get_or_create(name="C")
                            if data.get('classification'):
                                classification = Classification.objects.get(
                                    pk=int(data.get('classification', classification.id)))

                            short_name, created = RetailerShorts.objects.get_or_create(name="GT")
                            if data.get('short_name'):
                                short_name = RetailerShorts.objects.get(
                                    pk=int(data.get('short_name', short_name.id)))

                            payment_cycle, created = RetailerPaymentCycle.objects.get_or_create(number=1,
                                                                                                type="Bill Pending")
                            if data.get('payment_cycle'):
                                payment_cycle = RetailerPaymentCycle.objects.get(
                                    pk=int(data.get('payment_cycle', payment_cycle.id)))

                            commission_slab = CommissionSlab.objects.get(id=1)
                            if data.get('commission_slab'):
                                commission_slab = CommissionSlab.objects.get(
                                    id=int(data.get('commission_slab', commission_slab.id)))
                            discount_slab, created = DiscountSlab.objects.get_or_create(name="0 %")
                            if data.get('discount_slab'):
                                discount_slab = DiscountSlab.objects.get(
                                    pk=int(data.get('discount_slab', discount_slab.id)))
                            data_city = City.objects.get(id=data.get('city'))
                            name = str(data.get("name_of_shop"))
                            billing_name_of_shop = str(data.get("billing_name_of_shop"))
                            code_string = data_city.city_string
                            retailers = Retailer.objects.filter(code_string=code_string)
                            retailer_max_code_id = retailers.aggregate(Max('code_int'))[
                                                       'code_int__max'] + 1 if retailers else 0

                            code_int = str(retailer_max_code_id)
                            print(name)
                            onboarded_retailer = retailer_onboard_serializer.save(
                                salesPersonProfile=salesPersonProfile,
                                retailer=retailer,
                                code=str(code_string) + str(code_int) + "* " + name,
                                billing_name_of_shop=billing_name_of_shop,
                                code_int=code_int,
                                code_string=code_string,
                                onboarding_date=datetime.now(tz=CURRENT_ZONE),
                                beat_number=beat_number,
                                commission_slab=commission_slab,
                                classification=classification,
                                discount_slab=discount_slab,
                                short_name=short_name,
                                payment_cycle=payment_cycle,
                                shipping_address=retailer_shipping_address,
                                billing_address=retailer_billing_address)
                            if retail_owners:
                                for retail_owner in retail_owners:
                                    retail_owner_serializer = RetailOwnerCreateSerializer(data=retail_owner)
                                    retail_owner_serializer.is_valid(raise_exception=True)
                                    retail_owner_serializer.save(retail_shop=onboarded_retailer)

                            return Created({"code":onboarded_retailer.code})
                        except Exception as e:
                            print(e.args[1])
                            print(e)
                            retailer.delete()
                            retailer_shipping_address.delete()
                            if data.get('billing_address'):
                                retailer_billing_address.delete()
                            return BadRequest({'error_type': "Internal Error", 'errors': [{'message': "Beat and slab Error"}]})
                    except Exception as e:
                        print(e.args[1])
                        print(e)
                        retailer.delete()
                        return BadRequest({'error_type': "Internal Error", 'errors': [{'message': "Retailer Data Error"}]})
                except Exception as e:
                    print(e.args[1])
                    print(e)

                    # return BadRequest({'error_type': "Internal Error", 'errors': [{'message': e.args[1]}]})
                    return BadRequest({'error_type': "Internal Error", 'errors': [{'message': "Retailer Reg Error"}]})
            else:
                return Forbidden({'error_type': "ValidationError",
                                  'errors': [{'message': "No Sales Person profile found"}]})
        else:
            return Forbidden({'error_type': "permission_denied",
                              'errors': [{'message': "You do not have permission to perform this action."}]})

    @decorators.action(detail=False, methods=['post'], url_path="profile_update")
    def profile_update(self, request, *args, **kwargs):
        data = request.data
        print(data)
        # Check Loggedin User is Sales Person or not
        user_profile = UserProfile.objects.filter(user=request.user, department__name__in=['Sales']).first()
        if user_profile:
            salesPersonProfile = SalesPersonProfile.objects.filter(user=request.user).first()
            if salesPersonProfile:
                retailer_id = data.get('id')
                if not retailer_id:
                    return BadRequest({'error_type': "ValidationError",
                                       'errors': [{'message': "id required"}]})
                retailer = Retailer.objects.filter(id=retailer_id).first()
                if not retailer:
                    return BadRequest({'error_type': "ValidationError",
                                       'errors': [{'message': "retailer id invalid"}]})
                retailer_update_serializer = RetailerUpdateSerializer(data=data)
                retailer_update_serializer.is_valid(raise_exception=True)
                # Update Retailer
                retailer_update_serializer.retailer_update(instance=retailer, data=data)
                return Created()
                # if retailer.salesPersonProfile == salesPersonProfile:
                #     retailer_update_serializer = RetailerUpdateSerializer(data=data)
                #     retailer_update_serializer.is_valid(raise_exception=True)
                #     # Update Retailer
                #     retailer_update_serializer.retailer_update(instance=retailer, data=data)
                #     return Created()
                # else:
                #     return BadRequest({'error_type': "ValidationError",
                #                        'errors': [{'message': "Sales Person invalid to update"}]})

            else:
                return Forbidden({'error_type': "ValidationError",
                                  'errors': [{'message': "No Sales Person profile found"}]})
        else:
            return Forbidden({'error_type': "permission_denied",
                              'errors': [{'message': "You do not have permission to perform this action."}]})

    @decorators.action(detail=False, methods=['get'], url_path="beat_list")
    def beat_list(self, request, *args, **kwargs):
        # Check Loggedin User is Sales Person or not
        beat_number_list = list(set(self.get_queryset().values_list('beat_number',flat=True)))
        return Ok({"beat_numbers":beat_number_list})



