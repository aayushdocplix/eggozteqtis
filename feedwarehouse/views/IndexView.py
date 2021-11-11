from django.views.generic import TemplateView
from rest_framework import viewsets, permissions

from base.api.serializers import UploadDataSerializer
from feedwarehouse.scripts.upload_feed_products import upload_feed_product
from base.response import BadRequest, Created


class IndexView(TemplateView):
    template_name = 'custom_auth/home.html'


class UploadFeedProductViewSet(viewsets.ViewSet):
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
        file_response = upload_feed_product(csv_file)
        if file_response.get("status") == "success":
            return Created(file_response)
        else:
            return BadRequest(file_response)
