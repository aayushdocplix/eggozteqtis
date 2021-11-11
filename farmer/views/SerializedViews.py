import json
from datetime import datetime, timedelta
from decimal import Decimal

import coreapi
from django.db.models import Q, Sum
from django_filters import rest_framework as filters
from pyfcm import FCMNotification
from rest_framework import permissions, viewsets, mixins, decorators
from rest_framework.filters import BaseFilterBackend
from rest_framework.permissions import IsAuthenticated

from Eggoz.settings import CURRENT_ZONE, FCM_SERVER_KEY
from base.response import BadRequest, Created, Response, Unauthorized
from custom_auth.api.serializers import AddressCreationSerializer
from custom_auth.models import Address
from custom_auth.models.Department import Department
from custom_auth.models.User import FcmToken
from custom_auth.models.UserProfile import UserProfile
from farmer.api.serializers import FarmerSerializer, FarmSerializer, ShedSerializer, FlockSerializer, \
    FlockBreedSerializer, FarmerCreateSerializer, FarmCreateSerializer, FlockCreateSerializer, ShedCreateSerializer, \
    DailyInputSerializer, FeedMedicineSerializer, MedicineInputCreateSerializer, FarmerOrderCreateSerializer, \
    FarmerOrderInLineCreateSerializer, FarmerOrderSerializer, PartySerializer, ExpensesSerializer, PostCreateSerializer, \
    PostImageValidationSerializer, PostLikeSerializer, PostCommentSerializer, PostCommentLikeSerializer, PostSerializer, \
    PostCommentCreateSerializer, NECCCitySerializer, CityNECCRateSerializer, FarmUpdateSerializer, \
    FarmerBannerSerializer, NECCZoneSerializer, FarmerAlertSerializer, FeedIngredientSerializer, \
    FeedFormulationSerializer, FeedIngredientFormulaDataSerializer, FlockFeedFormulationSerializer
from farmer.models import Farmer, Farm, Shed, Flock, FlockBreed, DailyInput, FeedMedicine, MedicineInput, FarmerOrder, \
    Party, Expenses, Post, PostImage, PostLike, PostCommentLike, PostComment, NECCCity, CityNECCRate, FarmerBanner, \
    NECCZone, FarmerAlert, TransferredBirdInput, FeedIngredient, FeedFormulation, FeedIngredientFormulaData, \
    FlockFeedFormulation
from farmer.views import NotificationViewSet


class FarmerViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.AllowAny,)
    serializer_class = FarmerSerializer
    queryset = Farmer.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ('farmer',)

    def list(self, request, *args, **kwargs):
        farmer_filter = request.GET.get('farmer', None)
        farmer_name_filter = request.GET.get('farmer_name', None)
        farmers = self.get_queryset()
        if farmer_filter:
            farmers = farmers.filter(farmer__id=farmer_filter)
        if farmer_name_filter:
            farmers = farmers.filter(farmer__name__icontains=farmer_name_filter)
        page = self.paginate_queryset(farmers)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(farmers, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        data = request.data
        user = request.user
        print(request.data)
        serializer = FarmerCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if request.user.id == data.get('farmer'):
            if Farmer.objects.filter(farmer_id=data.get('farmer')):
                farmer = Farmer.objects.filter(farmer_id=data.get('farmer')).first()
                if data.get('necc_zone'):
                    farmer.necc_zone = NECCZone.objects.filter(id=data.get('necc_zone')).first()
                    farmer.save()
                else:
                    default_necc_zone = NECCZone.objects.filter(id=1).first()
                    if default_necc_zone:
                        farmer.necc_zone = default_necc_zone
                        farmer.save()
                user.name = data.get('farmer_name', user.name)
                user.email = data.get('email', user.email)
                user.phone_no = data.get('phone_no', user.phone_no)
                if user.default_address:
                    address = Address.objects.get(pk=user.default_address.id)
                    address.pinCode = data.get('pinCode', user.default_address.pinCode)
                    address.save()
                user.save()
                return Created(FarmerSerializer(farmer).data)
            else:
                farmer, farmer_created = Farmer.objects.get_or_create(farmer_id=data.get('farmer'))
                if farmer_created:
                    if data.get('necc_zone'):
                        farmer.necc_zone = NECCZone.objects.filter(id=data.get('necc_zone')).first()
                        farmer.save()
                    else:
                        default_necc_zone = NECCZone.objects.filter(id=1).first()
                        if default_necc_zone:
                            farmer.necc_zone = default_necc_zone
                            farmer.save()
                    department, department_created = Department.objects.get_or_create(name="Farmer")
                    farmer_user_profile, farmer_user_profile_created = UserProfile.objects.get_or_create(user=user)
                    farmer_user_profile.department.add(department)
                    farmer_user_profile.save()
                    user.name = data.get('farmer_name', user.name)
                    user.email = data.get('email', user.email)
                    user.phone_no = data.get('phone_no', user.phone_no)
                    if user.default_address:
                        address = Address.objects.get(pk=user.default_address.id)
                        address.pinCode = data.get('pinCode', user.default_address.pinCode)
                        address.save()
                    user.save()
                else:
                    return BadRequest({'error_type': "ValidationError",
                                       'errors': [{'message': "All ready Created farmer"}]})
                return Created(FarmerSerializer(farmer).data)
        else:
            return BadRequest({'error_type': "ValidationError",
                               'errors': [{'message': "user(farmer) id invalid"}]})


class FarmViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = FarmSerializer
    queryset = Farm.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ('farmer',)

    def create(self, request, *args, **kwargs):
        data = request.data
        if data.get('farm_address'):
            address_serializer = AddressCreationSerializer(data=data.get('farm_address'))
            address_serializer.is_valid(raise_exception=True)
            farm_serializer = FarmCreateSerializer(data=request.data)
            farm_serializer.is_valid(raise_exception=True)
            farm_obj = farm_serializer.save()
            address_obj = address_serializer.save()
            farm_obj.shipping_address = address_obj
            farm_obj.billing_address = address_obj
            farm_obj.billing_farm_address_same = True
            farm_obj.save()
            return Created({"success": "Farm Created Successfully"})
        else:
            return BadRequest({'error_type': "ValidationError",
                               'errors': [{'message': "farm_address required"}]})

    @decorators.action(detail=False, methods=['post'], url_path="farm_update")
    def farm_update(self, request, *args, **kwargs):
        data = request.data
        print(data)
        farm_id = data.get('id')

        if not farm_id:
            return BadRequest({'error_type': "ValidationError",
                               'errors': [{'message': "id required"}]})
        farm = Farm.objects.filter(id=farm_id).first()
        if not farm:
            return BadRequest({'error_type': "ValidationError",
                               'errors': [{'message': "farm id invalid"}]})
        farm_update_serializer = FarmUpdateSerializer(data=data)
        farm_update_serializer.is_valid(raise_exception=True)
        farm_update_serializer.farm_update(instance=farm, data=data)
        return Created({"success": "farm updated successfully"})


class ShedViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ShedSerializer
    queryset = Shed.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ('farm',)

    def create(self, request, *args, **kwargs):
        data = request.data
        if data.get('flocks'):
            flocks = data.get('flocks')
            if len(flocks) > 0:
                flocks_serializer = FlockCreateSerializer(data=flocks, many=True)
                flocks_serializer.is_valid(raise_exception=True)
                shed_serializer = ShedCreateSerializer(data=request.data)
                shed_serializer.is_valid(raise_exception=True)
                shed_obj = shed_serializer.save()
                for flock in flocks:
                    flock_serializer = FlockCreateSerializer(data=flock)
                    flock_serializer.is_valid(raise_exception=True)
                    flock_serializer.save(shed=shed_obj, flock_id=flock.get('flock_name') + "#" + str(
                        flocks.index(flock) + 1) + "#" + str(shed_obj.id),
                                          current_capacity=flock_serializer.validated_data.get('initial_capacity'))
                return Created({"success": "Shed Created Successfully"})
            else:
                return BadRequest({'error_type': "ValidationError",
                                   'errors': [{'message': " at least one flock required"}]})
        else:
            return BadRequest({'error_type': "ValidationError",
                               'errors': [{'message': "flocks required"}]})


class FlockViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = FlockSerializer
    queryset = Flock.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ('shed',)

    def get_serializer_class(self):
        if self.action == 'create':
            return FlockCreateSerializer
        return self.serializer_class

    def list(self, request, *args, **kwargs):
        user = request.user
        queryset = self.filter_queryset(self.get_queryset())
        if request.GET.get('farmer_flocks'):
            if request.GET.get('farmer_flocks') == 'true':
                queryset = queryset.filter(shed__farm__farmer__farmer__in=[user])
                if request.GET.get('input_remains'):
                    if request.GET.get('input_remains') == 'true':
                        today_date = datetime.now(tz=CURRENT_ZONE).date()
                        queryset = queryset.filter(
                            Q(last_daily_input_date=None) or Q(last_daily_input_date__lt=today_date))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        flock = Flock.objects.get(id=self.kwargs['pk'])
        data = request.data
        print(data)
        if data['initial_capacity']:
            request.data['current_capacity'] = flock.current_capacity + Decimal(
                data.get('initial_capacity')) - flock.initial_capacity
        serializer = self.get_serializer(flock, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        if getattr(flock, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            flock._prefetched_objects_cache = {}

        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        if request.data.get('shed'):
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data
            previous_flocks = validated_data.get('shed').flock_sheds.count()
            flock_id = validated_data.get('flock_name') + "#" + str(previous_flocks + 1) + "#" + str(
                validated_data.get('shed').id)
            serializer.save(flock_id=flock_id, current_capacity=validated_data.get('initial_capacity'))
            return Created(serializer.data)
        else:
            return BadRequest({'error_type': "ValidationError",
                               'errors': [{'message': "shed required"}]})


class FlockBreedViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = FlockBreedSerializer
    queryset = FlockBreed.objects.all()


class DailyInputViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                        mixins.UpdateModelMixin):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = DailyInputSerializer
    queryset = DailyInput.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ('flock',)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer_data = serializer.validated_data
        medicine_inputs = request.data.get('medicine_inputs', [])
        if medicine_inputs and len(medicine_inputs) > 0:
            medicine_inputs_serializer = MedicineInputCreateSerializer(data=medicine_inputs, many=True)
            medicine_inputs_serializer.is_valid()
        flock_obj = serializer_data.get('flock')
        if serializer_data.get('transferred_from_flock'):
            transfer_flock = Flock.objects.filter(id=serializer_data.get('transferred_from_flock'))
            current_flock = flock_obj
            transfer_quantity = serializer_data.get('transferred_quantity', 0)
            if transfer_quantity > 0:
                TransferredBirdInput.objects.create(transfer_from=transfer_flock, transfer_to=current_flock,
                                                    quantity=transfer_quantity)
            elif transfer_quantity < 0:
                TransferredBirdInput.objects.create(transfer_from=current_flock, transfer_to=transfer_flock,
                                                    quantity=transfer_quantity)
        current_active_birds = flock_obj.current_capacity - serializer_data.get('mortality', 0) - serializer_data.get(
            'culls', 0) + serializer_data.get('transferred_quantity', 0)
        if current_active_birds < 0:
            current_active_birds = 0
        daily_input_obj = serializer.save(total_active_birds=current_active_birds)
        flock_obj.current_capacity = current_active_birds
        flock_obj.last_daily_input_date = serializer_data.get('date')
        if serializer_data.get('egg_daily_production'):
            flock_obj.total_production = flock_obj.total_production + serializer_data.get('egg_daily_production')
        flock_obj.save()
        if medicine_inputs and len(medicine_inputs) > 0:
            for medicine_input in medicine_inputs:
                MedicineInput.objects.create(dailyInput=daily_input_obj,
                                             feedMedicine_id=medicine_input.get('feedMedicine'),
                                             quantity=medicine_input.get('quantity'))

        return Created(serializer.data)

    @decorators.action(detail=False, methods=['post'], url_path="semi_update")
    def semi_update(self, request, *args, **kwargs):
        data = request.data
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        old_mortality = instance.mortality
        old_culls = instance.culls
        old_transferred_quantity = instance.transferred_quantity
        old_total_active_birds = instance.total_active_birds
        old_egg_daily_production = instance.egg_daily_production
        flock_obj = instance.flock
        mortaility_diff = 0
        transferred_quantity_diff = 0
        if data.get('mortality') and int(data.get('mortality')) >= 0:
            mortaility_diff = old_mortality - int(data.get('mortality'))
        culls_diff = 0
        if data.get('culls') and int(data.get('culls')) >= 0:
            culls_diff = old_culls - int(data.get('culls'))
        if data.get('transferred_quantity') and int(data.get('transferred_quantity')):
            transferred_quantity_diff = old_transferred_quantity - int(data.get('transferred_quantity'))
        current_flock_active_birds = flock_obj.current_capacity + mortaility_diff + culls_diff - transferred_quantity_diff
        if data.get('egg_daily_production') and int(data.get('egg_daily_production')):
            instance.egg_daily_production = int(data.get('egg_daily_production'))
            flock_obj_total_production = flock_obj.total_production + data.get(
                'egg_daily_production') - old_egg_daily_production
            if flock_obj_total_production < 0:
                return BadRequest({'error_type': "ValidationError",
                                   'errors': [{'message': "Egg production Can never be zero is invalid"}]})
            flock_obj.total_production = flock_obj_total_production
        if current_flock_active_birds >= 0:
            dailyInputs = DailyInput.objects.filter(date__gte=instance.date, flock=flock_obj).order_by('date')
            if dailyInputs:
                for index, dailyInput in enumerate(dailyInputs[::1]):
                    if index >= 1:
                        old_active_birds = dailyInputs[index - 1].total_active_birds
                        diff = old_active_birds - dailyInputs[index].mortality - dailyInputs[index].culls \
                               + dailyInputs[index].transferred_quantity
                        dailyInput.total_active_birds = diff
                        dailyInput.save()
                        if index == len(dailyInputs) - 1:
                            flock_obj.current_capacity = dailyInput.total_active_birds
                    else:
                        if DailyInput.objects.filter(flock=flock_obj).order_by('date').first().id == dailyInput.id:
                            old_active_birds = flock_obj.initial_capacity
                            diff = old_active_birds - dailyInputs[index].mortality - dailyInputs[index].culls \
                                   + dailyInputs[index].transferred_quantity
                            dailyInput.total_active_birds = diff
                            dailyInput.save()
                            if index == len(dailyInputs) - 1:
                                flock_obj.current_capacity = dailyInput.total_active_birds
                        else:
                            pass

            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)

            return Response(serializer.data)
        else:
            return BadRequest({'error_type': "ValidationError",
                               'errors': [{'message': "data is invalid"}]})

    def update(self, request, *args, **kwargs):
        data = request.data
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        old_mortality = instance.mortality
        old_culls = instance.culls
        old_transferred_quantity = instance.transferred_quantity
        old_total_active_birds = instance.total_active_birds
        old_egg_daily_production = instance.egg_daily_production
        flock_obj = instance.flock
        mortaility_diff = 0
        transferred_quantity_diff = 0
        if data.get('mortality') and int(data.get('mortality')) > 0:
            mortaility_diff = old_mortality - int(data.get('mortality'))
        culls_diff = 0
        if data.get('culls') and int(data.get('culls')) > 0:
            culls_diff = old_culls - int(data.get('culls'))
        if data.get('transferred_quantity') and int(data.get('transferred_quantity')):
            transferred_quantity_diff = old_transferred_quantity - int(data.get('transferred_quantity'))
        current_flock_active_birds = flock_obj.current_capacity + mortaility_diff + culls_diff - transferred_quantity_diff
        if data.get('egg_daily_production') and int(data.get('egg_daily_production')):
            instance.egg_daily_production = int(data.get('egg_daily_production'))
            flock_obj_total_production = flock_obj.total_production + data.get(
                'egg_daily_production') - old_egg_daily_production
            if flock_obj_total_production < 0:
                return BadRequest({'error_type': "ValidationError",
                                   'errors': [{'message': "Egg production Can never be zero is invalid"}]})
            flock_obj.total_production = flock_obj_total_production
        if current_flock_active_birds >= 0:
            total_active_birds = old_total_active_birds + mortaility_diff + culls_diff - transferred_quantity_diff
            instance.total_active_birds = total_active_birds
            dailyInputs = DailyInput.objects.filter(date__gte=instance.date, flock=flock_obj).order_by('date')
            if dailyInputs:
                for dailyInput in dailyInputs:
                    diff = mortaility_diff + culls_diff - transferred_quantity_diff
                    dailyInput.total_active_birds += diff
                    dailyInput.save()
            instance.save()
            flock_obj.save()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)

            return Response(serializer.data)
        else:
            return BadRequest({'error_type': "ValidationError",
                               'errors': [{'message': "data is invalid"}]})


class FlockgraphFilterBackend(BaseFilterBackend):
    def get_schema_fields(self, view):
        return [coreapi.Field(
            name='flock_id',
            location='query',
            required=True,
            type='int'
        )]


class FarmerSummaryViewSet(viewsets.ViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = (FlockgraphFilterBackend,)

    def list(self, request, *args, **kwargs):
        farmer = Farmer.objects.filter(farmer=request.user).first()
        response_data = {}
        if farmer:
            flocks = Flock.objects.filter(shed__farm__farmer__in=[farmer])
            if flocks:
                response_data.update(flocks.aggregate(total_active_birds=Sum('current_capacity'),
                                                      total_production=Sum('total_production')))
                response_data.update(
                    flocks.filter(shed__shed_type="Layer").aggregate(total_layer_birds=Sum('current_capacity')))
                response_data.update(
                    flocks.filter(shed__shed_type="Grower").aggregate(total_grower_birds=Sum('current_capacity')))
                response_data.update(
                    DailyInput.objects.filter(flock__in=flocks).aggregate(total_mortality=Sum('mortality'),
                                                                          total_feed=Sum('feed')))
        return Response(response_data)


class FlockSummaryViewSet(viewsets.ViewSet):
    permission_classes = (permissions.IsAuthenticated,)

    def list(self, request, *args, **kwargs):
        response_data = {}
        if request.GET.get('flock_id'):
            flock_id = request.GET.get('flock_id')
            flock = Flock.objects.filter(id=flock_id).first()
            if flock:
                response_data['total_current_capacity'] = flock.current_capacity
                response_data['total_production'] = flock.current_capacity
                response_data.update(
                    DailyInput.objects.filter(flock__in=[flock]).aggregate(total_mortality=Sum('mortality'),
                                                                           total_feed=Sum('feed')))
                return Response(response_data)
            else:
                return Response({})
        else:
            return BadRequest({'error_type': "ValidationError",
                               'errors': [{'message': "flock_id required"}]})


class FlockGraphViewSet(viewsets.ViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = (FlockgraphFilterBackend,)

    def list(self, request, *args, **kwargs):
        if request.GET.get('flock_id'):
            flock_id = request.GET.get('flock_id')
            flock = Flock.objects.filter(id=flock_id).first()
            if flock:
                time_difference = datetime.now(tz=CURRENT_ZONE).date() - timedelta(days=int(request.GET.get('days', 7)))
                daily_inputs = flock.dailyinputs.filter(date__gte=time_difference)
                serializer = DailyInputSerializer(daily_inputs, many=True)
                return Response({"results": serializer.data})
            else:
                return Response({"results": []})
        else:
            return BadRequest({'error_type': "ValidationError",
                               'errors': [{'message': "flock_id required"}]})


class FeedMedicineViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = FeedMedicineSerializer
    queryset = FeedMedicine.objects.all()


class FeedFeedIngredientViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = FeedIngredientSerializer
    queryset = FeedIngredient.objects.all()


class FeedFormulationViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = FeedFormulationSerializer
    queryset = FeedFormulation.objects.all()


class FeedIngredientFormulaDataViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = FeedIngredientFormulaDataSerializer
    queryset = FeedIngredientFormulaData.objects.all()


class FlockFeedFormulationViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = FlockFeedFormulationSerializer
    queryset = FlockFeedFormulation.objects.all()


class FarmerOrderViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = FarmerOrderSerializer
    queryset = FarmerOrder.objects.all()

    def create(self, request, *args, **kwargs):
        farmer_order_serializer = FarmerOrderCreateSerializer(data=request.data)
        farmer_order_serializer.is_valid(raise_exception=True)
        order_in_lines = request.data.get('orderInlines', [])
        if order_in_lines and len(order_in_lines) > 0:
            farmer_order_inline_serializers = FarmerOrderInLineCreateSerializer(data=order_in_lines, many=True)
            farmer_order_inline_serializers.is_valid(raise_exception=True)
            farmer_order_obj = farmer_order_serializer.save()
            for order_in_line in order_in_lines:
                farmer_order_inline_serializer = FarmerOrderInLineCreateSerializer(data=order_in_line)
                farmer_order_inline_serializer.is_valid(raise_exception=True)
                farmer_order_inline_serializer.save(farmerOrder=farmer_order_obj)
            return Created({"success": "order created successfully"})
        else:
            return BadRequest({'error_type': "ValidationError",
                               'errors': [{'message': "orderInlines required and may not be empty"}]})


class PartyViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = PartySerializer
    queryset = Party.objects.all()


class ExpensesViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ExpensesSerializer
    queryset = Expenses.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ('farmer',)


class PostViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin):
    permission_classes = (permissions.AllowAny,)
    serializer_class = PostSerializer
    queryset = Post.objects.all()

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        user = self.request.user
        if user.is_anonymous:
            return Unauthorized({
                "errors": [
                    {
                        "message": "Authentication credentials were not provided."
                    }
                ],
                "error_type": "NotAuthenticated"
            })
        images = request.FILES.getlist('images')
        for image in images:
            postImageSerializer = PostImageValidationSerializer(data={"image": image})
            postImageSerializer.is_valid(raise_exception=True)
        post_serializer = PostCreateSerializer(data=request.data)
        post_serializer.is_valid(raise_exception=True)
        post_obj = post_serializer.save(author=user)
        for index, image in enumerate(images):
            post_image = PostImage(image=image, post=post_obj, image_order=index)
            post_image.save()
        return Created(post_serializer.data)


class PostLikeViewSet(viewsets.ViewSet):
    permission_classes = (IsAuthenticated,)

    def create(self, request):
        user = self.request.user
        data = request.data
        serializer = PostLikeSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        post_like, created = PostLike.objects.get_or_create(user=user, post_id=serializer.data.get('post'))
        if not created:
            if post_like.is_liked:
                post_like.is_liked = False
            else:
                post_like.is_liked = True
        post_like.save()
        return Created({"message": "post liked successfully"})


class PostCommentViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin):
    permission_classes = (IsAuthenticated,)
    serializer_class = PostCommentSerializer
    queryset = PostComment.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ('post', 'parent_comment')

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        if self.request.GET.get('super_comment'):
            if self.request.GET.get('super_comment') == 'true':
                queryset = queryset.filter(Q(parent_comment__isnull=True))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request):
        user = self.request.user
        data = request.data
        serializer = PostCommentCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=user)
        return Response(serializer.data)


class PostCommentLikeViewSet(viewsets.ViewSet):
    permission_classes = (IsAuthenticated,)

    def create(self, request):
        user = self.request.user
        data = request.data
        serializer = PostCommentLikeSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        post_comment_like, created = PostCommentLike.objects.get_or_create(user=user,
                                                                           post_comment_id=serializer.data.get(
                                                                               'post_comment'))
        if post_comment_like.is_liked:
            post_comment_like.is_liked = False
        else:
            post_comment_like.is_liked = True
        post_comment_like.save()
        return Created({"message": "post comment liked successfully"})


class NECCZoneViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = NECCZoneSerializer
    queryset = NECCZone.objects.all()


class NECCCityViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = NECCCitySerializer
    queryset = NECCCity.objects.all()


class CityNECCRateViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = CityNECCRateSerializer
    queryset = CityNECCRate.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ('necc_city',)

    @decorators.action(detail=False, methods=['put'], url_path="bulk_update")
    def bulk_update(self, request, *args, **kwargs):
        print(request.data)
        cityNeccRates = json.loads(request.data.get('cityNeccRates', []))
        print(cityNeccRates)
        cityDataList = []
        for cityNeccRate in cityNeccRates:
            neccRate = CityNECCRate.objects.filter(id=cityNeccRate['id']).first()
            neccRate.current_rate = cityNeccRate['current_rate']
            neccRate.save()
            cityData = {"city": neccRate.necc_city.name, "rate": cityNeccRate['current_rate']}
            cityDataList.append(cityData)
        message = ", ".join(cityDa['city'] for cityDa in cityDataList)
        title = "NECC Egg Rates Updated"
        data_body = {
            "title": title,
            "body": message,
            "image_url": "image_url",
            "activity_id": 1,
            "item_id": 1,
            "cityData": cityDataList
        }
        fcm_token = []
        tokens = FcmToken.objects.all()
        for token in tokens:
            fcm_token.append(token.token)
        push_service = FCMNotification(api_key=FCM_SERVER_KEY)
        result = push_service.notify_multiple_devices(
            registration_ids=fcm_token, data_message=data_body)
        return Response("Necc rates updates successfully")


class FarmerBannerViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = FarmerBannerSerializer
    queryset = FarmerBanner.objects.filter(is_shown=True)


class FarmerAlertViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = FarmerAlertSerializer
    print(datetime.now(tz=CURRENT_ZONE).time())
    queryset = FarmerAlert.objects.filter(is_shown=True, start_at__lte=datetime.now(tz=CURRENT_ZONE).time(),
                                          end_at__gte=datetime.now(tz=CURRENT_ZONE).time())
