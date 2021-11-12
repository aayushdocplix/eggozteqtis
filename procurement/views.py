import base64
from datetime import datetime, timedelta

import pyotp
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.response import Response
from rest_framework import viewsets, pagination, permissions, status, mixins
from rest_framework.views import APIView

from Eggoz import settings
from Eggoz.settings import CURRENT_ZONE
from custom_auth.models import PhoneModel
from custom_auth.tasks import send_sms_message
from custom_auth.views import GenerateKey
from warehouse.models import Driver
from .models import BatchModel, BatchPerWarehouse, EggsIn, EggQualityCheck, EggCleaning, Package, \
    ReturnedPackage, Procurement, ImageUpload
from .serializers import BatchSerializer, BatchPerWarehouseSerializer, EggsInSerializers, \
    EggCleaningSerializer, EggQualityCheckSerializer, PackageSerializer, ReturnedPackageSerializer, \
    BatchCreateRequestSerializer, ImageUploadSerializer, ProcurementSerializer, BatchStockDetailSerializer, \
    BatchUpdateRequestSerializer, BatchListSerializer, MoveToUnbrandedSerializer


class Pagination(pagination.PageNumberPagination):
    page_size = 7


class ProcurementView(viewsets.ModelViewSet):
    queryset = BatchModel.objects.all().order_by('-id')
    permission_classes = (permissions.AllowAny,)
    pagination_class = Pagination
    serializer_class = BatchSerializer

    def create(self, request, *args, **kwargs):
        batch_serializer = BatchCreateRequestSerializer(data=request.data.get('procurements', None), many=True)
        if not batch_serializer.is_valid():
            return Response(data=batch_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        procurement_serializer = ProcurementSerializer(data={'farmer': request.data.get('farmer')})
        if procurement_serializer.is_valid():
            procurement_serializer.save()
        else:
            return Response(data=procurement_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        procurement = procurement_serializer.data
        batches_list = []
        data = batch_serializer.data
        for batch in data:
            batch_model = BatchModel.objects.create(egg_type=batch['egg_type'],
                                                    procurement=Procurement.objects.get(id=procurement['id']),
                                                    date=batch.get('date'),
                                                    expected_egg_count=batch['expected_egg_count'],
                                                    expected_egg_price=batch['expected_egg_price'])
            batches_list.append(batch_model)
        batch_serializer = BatchSerializer(batches_list, many=True)
        return Response(data=batch_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        batch_serializer = BatchUpdateRequestSerializer(data=request.data.get('procurements', None), many=True)
        if not batch_serializer.is_valid():
            return Response(data=batch_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        procurement_serializer = ProcurementSerializer(
            data={'procurement_bill_url': request.data.get('procurement_bill_url', ''),
                  'additional_charge': request.data.get('additional_charge', 0)}
        )
        try:
            batch_model = self.get_queryset().get(id=kwargs['pk'])
        except ObjectDoesNotExist:
            return Response(data={'message': 'batch not found'}, status=status.HTTP_400_BAD_REQUEST)
        if procurement_serializer.is_valid():
            serializer_data = procurement_serializer.data
            procurement_model = batch_model.procurement
            procurement_model.procurement_bill_url = serializer_data['procurement_bill_url']
            procurement_model.additional_charge = serializer_data['additional_charge']
            procurement_model.save()
        serializer_data = batch_serializer.data[0]
        batch_model.egg_ph = serializer_data['egg_ph']
        batch_model.actual_egg_price = serializer_data['actual_egg_price']
        batch_model.actual_egg_count = serializer_data['actual_egg_count']
        batch_model.batch_egg_image_url = serializer_data['batch_egg_image_url']
        batch_model.save()
        return Response(data=self.get_serializer(batch_model).data, status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        batch_id_filter = request.GET.get('batch_id', None)
        egg_type_filter = request.GET.get('egg_type', None)
        farmer_name_filter = request.GET.get('farmer_name', None)
        procurement_list = self.get_queryset()
        if batch_id_filter is not None:
            procurement_list = procurement_list.filter(batch_id__icontains=batch_id_filter)
        if egg_type_filter is not None:
            procurement_list = procurement_list.filter(egg_type__icontains=egg_type_filter)
        if farmer_name_filter is not None:
            procurement_list = procurement_list.filter(procurement__farmer__farmer__name__icontains=farmer_name_filter)
        page = self.paginate_queryset(procurement_list)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(procurement_list, many=True)
        return Response(serializer.data)


class ProcurementPerWarehouseView(viewsets.ModelViewSet):
    permission_classes = (permissions.AllowAny,)
    pagination_class = Pagination
    serializer_class = BatchPerWarehouseSerializer
    queryset = BatchPerWarehouse.objects.all().order_by('-id')


class EggsInView(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    queryset = EggsIn.objects.all().order_by('-id')
    pagination_class = Pagination
    serializer_class = EggsInSerializers


class EggQualityCheckView(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    queryset = EggQualityCheck.objects.all().order_by('-id')
    pagination_class = Pagination
    serializer_class = EggQualityCheckSerializer

    def list(self, request, *args, **kwargs):
        return Response(status=status.HTTP_404_NOT_FOUND)


class EggCleaningView(viewsets.ModelViewSet):
    permission_classes = (permissions.AllowAny,)
    queryset = EggCleaning.objects.all().order_by('-id')
    pagination_class = Pagination
    serializer_class = EggCleaningSerializer

    def list(self, request, *args, **kwargs):
        batch_id_filter = request.GET.get('batch', None)
        egg_cleaning_list = self.get_queryset().filter(batch_id__id=batch_id_filter)
        serializer = self.get_serializer(egg_cleaning_list, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)


class PackageView(viewsets.ModelViewSet):
    permission_classes = (permissions.AllowAny,)
    queryset = Package.objects.all().order_by('-id')
    pagination_class = Pagination
    serializer_class = PackageSerializer

    def list(self, request, *args, **kwargs):
        batch_id_filter = request.GET.get('batch_id', None)
        package_list = self.get_queryset()
        if batch_id_filter:
            package_list = package_list.filter(batch_id__id=batch_id_filter)
        page = self.paginate_queryset(package_list)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(package_list, many=True)
        return Response(serializer.data)


class ReturnedPackageView(viewsets.ModelViewSet):
    permission_classes = (permissions.AllowAny,)
    queryset = ReturnedPackage.objects.all().order_by('-id')
    pagination_class = Pagination
    serializer_class = ReturnedPackageSerializer


class ImageUploadView(viewsets.ModelViewSet):
    permission_classes = (permissions.AllowAny,)
    queryset = ImageUpload.objects.all().order_by('-id')
    pagination_class = Pagination
    serializer_class = ImageUploadSerializer

    def list(self, request, *args, **kwargs):
        return Response(status=status.HTTP_404_NOT_FOUND);

    def create(self, request, *args, **kwargs):
        image = request.FILES.get('image')
        serializer = ImageUploadSerializer(data={"image": image})
        if serializer.is_valid():
            serializer.save()
        else:
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response(data=serializer.data, status=status.HTTP_200_OK)


class StockDetails(viewsets.GenericViewSet):
    permission_classes = (permissions.AllowAny,)
    serializer_class = BatchStockDetailSerializer
    pagination_class = Pagination

    def list(self, request, *args, **kwargs):
        procurement_filter = request.GET.get('procurement_id', None)
        batch_id_filter = request.GET.get('batch_id', None)
        batch_list = BatchModel.objects.all().order_by('-id')
        if procurement_filter is not None:
            batch_list = batch_list.filter(procurement__id=procurement_filter)
        if batch_id_filter is not None:
            batch_list = batch_list.filter(batch_id__icontains=batch_list)
        page = self.paginate_queryset(batch_list)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(batch_list, many=True)
        return Response(serializer.data)


class SendOtpView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        phone_no = request.data.get('phone_no')
        if phone_no is None:
            return Response(data={'message': 'no phone number is found'}, status=status.HTTP_400_BAD_REQUEST)
        sender_type = "Implicit"
        sms_mode = True
        hash_code = request.data.get('hash_code', "")
        otp_type = "farmer_verification"
        phone_model, created = PhoneModel.objects.get_or_create(
            phone_no=phone_no)  # if Mobile already exists the take this else create New One
        phone_model.counter += 1  # Update Counter At every Call
        phone_model.isVerified = False
        phone_model.save()
        keygen = GenerateKey()
        key = base64.b32encode(keygen.return_value(phone_no).encode())  # Key is generated
        OTP = pyotp.HOTP(key)  # HOTP Model for OTP is created
        if settings.PHONE_SMS_ON and sms_mode:
            try:
                send_sms_message(msg_str=(str(OTP.at(phone_model.counter))), hash_code=hash_code,
                                 phone_number=str(phone_no), sms_type="otp", otp_type=otp_type, sender_type=sender_type)
                return Response(data={"Result": "Otp sent successfully"}, status=status.HTTP_200_OK)
            except Exception as e:
                print(e)
                return Response(data={'error_type': "Internal Error", 'errors': [{'message': e.args[1]}]})
        else:
            return Response(
                data={"Result": "Otp sent successfully", "otp": OTP.at(phone_model.counter),
                      "message": "To sent actual otp set phone_sms_on true"})


class VerifyOtpView(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        phone_no = request.data.get('phone_no')
        otp = request.data.get('otp')
        if phone_no is None or otp is None:
            return Response(data={
                'message': 'phone number or otp is missing'
            })
        try:
            phone_model = PhoneModel.objects.get(phone_no=phone_no)
        except ObjectDoesNotExist:
            return Response(data={'error_type': "Validation Error",
                                  'errors': [{'message': "Phone number does not exist"}]})  # False Call
        time_difference = datetime.now(tz=CURRENT_ZONE) - timedelta(minutes=5)
        phone_expiry = PhoneModel.objects.filter(phone_no=phone_no, updated_at__gte=time_difference, isVerified=False)
        if len(phone_expiry) > 0:
            keygen = GenerateKey()
            key = base64.b32encode(keygen.return_value(phone_no).encode())  # Generating Key
            OTP = pyotp.HOTP(key)  # HOTP Model
            if OTP.verify(request.data["otp"], phone_model.counter):  # Verifying the OTP
                phone_model.isVerified = True
                phone_model.login_count += 1
                phone_model.save()
                return Response(data={"message": "Successfully Verified"}, status=status.HTTP_200_OK)
            return Response(data={'error_type': "Validation Error",
                                  'errors': [{'message': "OTP is wrong"}]})
        else:
            return Response(data={'error_type': "Validation Error",
                                  'errors': [{
                                      'message': "Otp has been expired or already verified, "
                                                 "please request for new otp"}]})  # Otp Expire

class DriverSearchView(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        try:
            data_list = list()
            farmer_name = self.request.query_params.get('search')
            user_obj = Driver.objects.filter(driver_name__icontains=farmer_name)
            for user in user_obj:
                data_list.append({'id': user.id, 'name': user.driver_name})
            return Response({'success': True, 'error': None, 'data': data_list}, status=status.HTTP_200_OK)
        except Exception as error:
            return Response({'success': False, 'error': error.args[0], 'data': None},
                            status=status.HTTP_400_BAD_REQUEST)


class BatchListView(APIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = BatchListSerializer

    @staticmethod
    def get_model_data(_type):
        try:
            mapping_dict = {
                'quality_check': EggsIn.objects.all().values_list('batch',flat=True),
                'cleaning': EggQualityCheck.objects.all().values_list('batch',flat=True),
                'package': EggCleaning.objects.all().values_list('batch_id',flat=True),
            }

            return mapping_dict.get(_type)
        except Exception as e:
            return None

    @staticmethod
    def get_category_model_data(_status, _type):
        import pdb
        pdb.set_trace()
        try:
            _status_dict = {
                'chatki': {
                    'fresh': EggsIn.objects.all().values_list('batch', flat=True),
                    'cleaning': EggCleaning.objects.all().values_list('batch_id', flat=True),
                },
                'unbranded': None
            }
            return _status_dict.get(_status).get(_type)
        except Exception as e:
            return None

    def get(self, request, *args, **kwargs):
        try:
            _type = self.request.query_params.get('type', None)
            category = self.request.query_params.get('category', None)
            if category:
                result = self.get_category_model_data(category, _type)
            else:
                result = self.get_model_data(_type)
            if result:
                batch_obj = BatchModel.objects.filter(id__in=result)
                serializer_data = self.serializer_class(batch_obj, many=True).data
                return Response({'success': True, 'error': None, 'data': serializer_data}, status=status.HTTP_200_OK)
            return Response({'success': False, 'error': 'type is mandatory', 'data': None},
                            status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'success': False, 'error': e.args[0], 'data': None},
                            status=status.HTTP_400_BAD_REQUEST)


# class MoveToUnbrandedView(APIView):
#     permission_classes = (permissions.AllowAny,)
#
#     def post(self, request, *args, **kwargs):
#         try:
#             data = request.data
#             serializer_data = MoveToUnbrandedSerializer(data=data, many=True)
#             if serializer_data.is_valid(raise_exception=True):
#                 serializer_data.save()
#                 return Response({'success': True, 'error': None, 'data': serializer_data}, status=status.HTTP_200_OK)
#
#         except Exception as e:
#             return Response({'success': False, 'error': e.args[0], 'data': None},
#                             status=status.HTTP_400_BAD_REQUEST)
