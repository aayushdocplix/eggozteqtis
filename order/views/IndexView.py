from django.views.generic import TemplateView
from rest_framework import viewsets, permissions

from base.api.serializers import UploadDataSerializer, UploadDueDataSerializer, UploadCitiesSerializer, \
    UploadAmountsSerializer
from base.response import BadRequest, Created
# from order.scripts.update_bill_no import update_bill_no, find_duplicate_orders
# from order.scripts.update_empty_order_name import update_empty_order_name
# from order.scripts.update_order_amount import update_order_amount
# from order.scripts.update_order_date import update_order_date, update_eggs_data
#
# from order.scripts.upload_order_22_march import upload_order_22_march
# from order.scripts.upload_order_data import upload_order_data
# from order.scripts.upload_sales_due import upload_sales_due
from order.scripts.UpdateSalesTransactions import sales_transactions_balance, sales_pending_invoices
from order.scripts.update_eggs_data import update_eggs_data
from order.scripts.update_mt_payments import update_mt_payments

from order.scripts.upload_order_14_June import upload_order_14_June
from order.scripts.upload_missing_sales import upload_missing_sales, upload_missing_payments


class IndexView(TemplateView):
    template_name = 'custom_auth/home.html'


class UploadSampleOrderViewSet(viewsets.ViewSet):
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
        file_response = upload_order_14_June(csv_file)
        if file_response.get("status") == "success":
            return Created(file_response)
        else:
            return BadRequest(file_response)

class UpdateMTPaymentViewSet(viewsets.ViewSet):
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
        file_response = update_mt_payments(csv_file)
        if file_response.get("status") == "success":
            return Created(file_response)
        else:
            return BadRequest(file_response)


class UploadGEBMissingOrderViewSet(viewsets.ViewSet):
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
        file_response = upload_missing_sales(csv_file)
        if file_response.get("status") == "success":
            return Created(file_response)
        else:
            return BadRequest(file_response)


class UploadGEBMissingPaymentViewSet(viewsets.ViewSet):
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
        file_response = upload_missing_payments(csv_file)
        if file_response.get("status") == "success":
            return Created(file_response)
        else:
            return BadRequest(file_response)


# class UploadOrderViewSet(viewsets.ViewSet):
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
#         file_response = upload_order_data(csv_file)
#         if file_response.get("status") == "success":
#             return Created(file_response)
#         else:
#             return BadRequest(file_response)
#
#
# class UploadDueDiffViewSet(viewsets.ViewSet):
#     permission_classes = (permissions.IsAuthenticated,)
#
#     def create(self, request, *args, **kwargs):
#         data = request.data
#         serializer = UploadDueDataSerializer(data=data)
#         serializer.is_valid(raise_exception=True)
#         cities = serializer.validated_data.get('cities')
#         date = serializer.validated_data.get('date')
#         file_response = upload_sales_due(cities, date)
#         if file_response.get("status") == "success":
#             return Created(file_response)
#         else:
#             return BadRequest(file_response)
#
#
class UpdateLedgersViewSet(viewsets.ViewSet):
    permission_classes = (permissions.IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        data = request.data
        serializer = UploadCitiesSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        cities = serializer.validated_data.get('cities')
        file_response = sales_transactions_balance(cities)
        if file_response.get("status") == "success":
            return Created(file_response)
        else:
            return BadRequest(file_response)

class InvoiceLedgersViewSet(viewsets.ViewSet):
    permission_classes = (permissions.IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        data = request.data
        serializer = UploadCitiesSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        cities = serializer.validated_data.get('cities')
        file_response = sales_pending_invoices(cities)
        if file_response.get("status") == "success":
            return Created(file_response)
        else:
            return BadRequest(file_response)



#
# class UpdateEmptyOrderNameViewSet(viewsets.ViewSet):
#     permission_classes = (permissions.IsAuthenticated,)
#
#     def create(self, request, *args, **kwargs):
#         data = request.data
#         serializer = UploadCitiesSerializer(data=data)
#         serializer.is_valid(raise_exception=True)
#         cities = serializer.validated_data.get('cities')
#         file_response = update_empty_order_name(cities)
#         if file_response.get("status") == "success":
#             return Created(file_response)
#         else:
#             return BadRequest(file_response)
#
#
# class UpdateOrderDateViewSet(viewsets.ViewSet):
#     permission_classes = (permissions.IsAuthenticated,)
#
#     def create(self, request, *args, **kwargs):
#         data = request.data
#         serializer = UploadCitiesSerializer(data=data)
#         serializer.is_valid(raise_exception=True)
#         cities = serializer.validated_data.get('cities')
#         file_response = update_order_date(cities)
#         if file_response.get("status") == "success":
#             return Created(file_response)
#         else:
#             return BadRequest(file_response)
#
#
# class UpdateOrderAmountViewSet(viewsets.ViewSet):
#     permission_classes = (permissions.IsAuthenticated,)
#
#     def create(self, request, *args, **kwargs):
#         data = request.data
#         serializer = UploadAmountsSerializer(data=data)
#         serializer.is_valid(raise_exception=True)
#         salesPersonId = serializer.validated_data.get('salesPersonId')
#         minOrderId = serializer.validated_data.get('minOrderId')
#         file_response = update_order_amount(salesPersonId, minOrderId)
#         if file_response.get("status") == "success":
#             return Created(file_response)
#         else:
#             return BadRequest(file_response)
#
#
# class UpdateOrderBillViewSet(viewsets.ViewSet):
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
#         file_response = update_bill_no(csv_file)
#         if file_response.get("status") == "success":
#             return Created(file_response)
#         else:
#             return BadRequest(file_response)
#
#
# class CheckDuplicateOrdersViewSet(viewsets.ViewSet):
#     permission_classes = (permissions.IsAuthenticated,)
#
#     def create(self, request, *args, **kwargs):
#         data = request.data
#         file_response = find_duplicate_orders()
#         if file_response.get("status") == "success":
#             return Created(file_response)
#         else:
#             return BadRequest(file_response)
#
#

class UpdateEggsDataViewSet(viewsets.ViewSet):
    permission_classes = (permissions.IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        data = request.data
        file_response = update_eggs_data()
        if file_response.get("status") == "success":
            return Created(file_response)
        else:
            return BadRequest(file_response)