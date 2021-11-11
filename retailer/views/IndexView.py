from django.views.generic import TemplateView
from rest_framework import viewsets, permissions

from base.api.serializers import UploadDataSerializer, UploadCitiesSerializer
from base.response import BadRequest, Created
# from retailer.scripts.retailer_commission_slabs import retailer_commission_slabs
# from retailer.scripts.update_calc_amount import update_calc_amount
# from retailer.scripts.update_slabs import update_slabs
# from retailer.scripts.upload_retailer_data import upload_retailer_data, update_retailer_names
# from retailer.scripts.upload_retailer_dump import upload_retailer_dump
# from retailer.scripts.due_script import due_script
from retailer.scripts.onboard_retailer import onboard_ub_retailer
from retailer.scripts.update_beat import update_beat, update_oms_beat


class IndexView(TemplateView):
    template_name = 'custom_auth/home.html'


# class UploadRetailerDueViewSet(viewsets.ViewSet):
#     permission_classes = (permissions.IsAuthenticated,)
#
#     def create(self, request, *args, **kwargs):
#         data = request.data
#         serializer = UploadCitiesSerializer(data=data)
#         serializer.is_valid(raise_exception=True)
#         cities = serializer.validated_data.get('cities', [])
#         file_response = due_script(cities)
#         if file_response.get("status") == "success":
#             return Created(file_response)
#         else:
#             return BadRequest(file_response)
#
#
# class UploadRetailerSlabViewSet(viewsets.ViewSet):
#     permission_classes = (permissions.IsAuthenticated,)
#
#     def create(self, request, *args, **kwargs):
#         data = request.data
#         serializer = UploadDataSerializer(data=data)
#         serializer.is_valid(raise_exception=True)
#         csv_file = serializer.validated_data.get('csv_file')
#         # let's check if it is a csv file
#         csv_file_name = csv_file.name
#         if not csv_file_name.endswith('.csv'):
#             return BadRequest({"error": "File is not valid"})
#         file_response = update_slabs(csv_file)
#         if file_response.get("status") == "success":
#             return Created(file_response)
#         else:
#             return BadRequest(file_response)
#
#
# class UploadRetailerViewSet(viewsets.ViewSet):
#     permission_classes = (permissions.IsAuthenticated,)
#
#     def create(self, request, *args, **kwargs):
#         data = request.data
#         city_name = request.data.get('city_name', None)
#         if city_name:
#             serializer = UploadDataSerializer(data=data)
#             serializer.is_valid(raise_exception=True)
#             csv_file = serializer.validated_data.get('csv_file')
#             # let's check if it is a csv file
#             csv_file_name = csv_file.name
#             if not csv_file_name.endswith('.csv'):
#                 return BadRequest({"error": "File is not valid"})
#             file_response = upload_retailer_data(csv_file, city_name)
#             if file_response.get("status") == "success":
#                 return Created(file_response)
#             else:
#                 return BadRequest(file_response)
#         else:
#             return BadRequest({"city_name": "Required"})
#
#
# class UploadRetailerDumpViewSet(viewsets.ViewSet):
#     permission_classes = (permissions.IsAuthenticated,)
#
#     def create(self, request, *args, **kwargs):
#         data = request.data
#
#         serializer = UploadDataSerializer(data=data)
#         serializer.is_valid(raise_exception=True)
#         csv_file = serializer.validated_data.get('csv_file')
#         # let's check if it is a csv file
#         csv_file_name = csv_file.name
#         if not csv_file_name.endswith('.csv'):
#             return BadRequest({"error": "File is not valid"})
#         file_response = upload_retailer_dump(csv_file)
#         if file_response.get("status") == "success":
#             return Created(file_response)
#         else:
#             return BadRequest(file_response)
#
#
# class UpdateCalcAmountViewSet(viewsets.ViewSet):
#     permission_classes = (permissions.IsAuthenticated,)
#
#     def create(self, request, *args, **kwargs):
#         data = request.data
#         serializer = UploadCitiesSerializer(data=data)
#         serializer.is_valid(raise_exception=True)
#         cities = serializer.validated_data.get('cities')
#         file_response = update_calc_amount(cities)
#         if file_response.get("status") == "success":
#             return Created(file_response)
#         else:
#             return BadRequest(file_response)
#
#
# class UploadRetailerNamesViewSet(viewsets.ViewSet):
#     permission_classes = (permissions.IsAuthenticated,)
#
#     def create(self, request, *args, **kwargs):
#         data = request.data
#
#         serializer = UploadDataSerializer(data=data)
#         serializer.is_valid(raise_exception=True)
#         csv_file = serializer.validated_data.get('csv_file')
#         # let's check if it is a csv file
#         csv_file_name = csv_file.name
#         if not csv_file_name.endswith('.csv'):
#             return BadRequest({"error": "File is not valid"})
#         file_response = update_retailer_names(csv_file)
#         if file_response.get("status") == "success":
#             return Created(file_response)
#         else:
#             return BadRequest(file_response)
#
#
# class UploadCommissionSlabViewSet(viewsets.ViewSet):
#     permission_classes = (permissions.IsAuthenticated,)
#
#     def create(self, request, *args, **kwargs):
#         data = request.data
#         serializer = UploadDataSerializer(data=data)
#         serializer.is_valid(raise_exception=True)
#         csv_file = serializer.validated_data.get('csv_file')
#         # let's check if it is a csv file
#         csv_file_name = csv_file.name
#         if not csv_file_name.endswith('.csv'):
#             return BadRequest({"error": "File is not valid"})
#         file_response = retailer_commission_slabs(csv_file)
#         if file_response.get("status") == "success":
#             return Created(file_response)
#         else:
#             return BadRequest(file_response)


class UploadRetailerBeatViewSet(viewsets.ViewSet):
    permission_classes = (permissions.IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        data = request.data
        serializer = UploadDataSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        csv_file = serializer.validated_data.get('csv_file')
        # let's check if it is a csv file
        csv_file_name = csv_file.name
        if not csv_file_name.endswith('.csv'):
            return BadRequest({"error": "File is not valid"})
        file_response = update_beat(csv_file)
        if file_response.get("status") == "success":
            return Created(file_response)
        else:
            return BadRequest(file_response)


class UploadRetailerOmsBeatViewSet(viewsets.ViewSet):
    permission_classes = (permissions.IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        data = request.data
        serializer = UploadDataSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        csv_file = serializer.validated_data.get('csv_file')
        # let's check if it is a csv file
        csv_file_name = csv_file.name
        if not csv_file_name.endswith('.csv'):
            return BadRequest({"error": "File is not valid"})
        file_response = update_oms_beat(csv_file)
        if file_response.get("status") == "success":
            return Created(file_response)
        else:
            return BadRequest(file_response)


class UploadUBRetailerViewSet(viewsets.ViewSet):
    permission_classes = (permissions.IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        data = request.data
        serializer = UploadDataSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        csv_file = serializer.validated_data.get('csv_file')
        # let's check if it is a csv file
        csv_file_name = csv_file.name
        if not csv_file_name.endswith('.csv'):
            return BadRequest({"error": "File is not valid"})
        file_response = onboard_ub_retailer(csv_file)
        if file_response.get("status") == "success":
            return Created(file_response)
        else:
            return BadRequest(file_response)
