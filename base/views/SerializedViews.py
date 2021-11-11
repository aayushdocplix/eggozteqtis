from django.http import Http404
from django_filters import rest_framework as filters
from rest_framework import status, permissions, viewsets, pagination, mixins, decorators
from rest_framework.response import Response
from rest_framework.views import APIView

from base import models
from base.api import serializers
from base.api.serializers import CitySerializer, UploadDataSerializer
from base.models import City, UserRetailerFilters
from base.models.Video import VideoCategory, Video
from base.response import BadRequest, Created
from base.scripts.upload_cluster_data import upload_cluster_data
from custom_auth.models import UserProfile
from saleschain.models import SalesPersonProfile


class PaginationWithNoLimit(pagination.PageNumberPagination):
    page_size = 5000


class PaginationWithLimit(pagination.PageNumberPagination):
    page_size = 100


class PaginationWithThousandLimit(pagination.PageNumberPagination):
    page_size = 5000


class CityListView(APIView):
    # Allow any user (authenticated or not) to access this url
    permission_classes = (permissions.AllowAny,)

    def get(self, request, format=None):
        queryset = City.objects.all().order_by('city_name')
        serializer = CitySerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = CitySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CityDetail(APIView):
    """
    Retrieve, update or delete a snippet instance.
    """
    def get_object(self, pk):
        try:
            return City.objects.get(pk=pk)
        except City.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        city = self.get_object(pk)
        serializer = CitySerializer(city)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        city = self.get_object(pk)
        serializer = CitySerializer(city, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        city = self.get_object(pk)
        city.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CityListView(APIView):
    # Allow any user (authenticated or not) to access this url
    permission_classes = (permissions.AllowAny,)

    def get(self, request, format=None):
        queryset = City.objects.all().order_by('city_name')
        serializer = CitySerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = CitySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UploadClusterDataViewSet(viewsets.ViewSet):
    permission_classes = (permissions.AllowAny,)

    def create(self, request, *args, **kwargs):
        data = request.data
        serializer = UploadDataSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        csv_file = serializer.validated_data.get('csv_file')
        # let's check if it is a csv file
        csv_file_name = csv_file.name
        if not csv_file_name.endswith('.csv'):
            return BadRequest({"error": "File is not valid"})
        file_response = upload_cluster_data(csv_file)
        if file_response.get("status") == "success":
            return Created(file_response)
        else:
            return BadRequest(file_response)


class ZoneViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list:
    Get paginated list of zones

    retrieve:
    Get single zone by id
    """
    permission_classes = (permissions.AllowAny,)
    pagination_class = PaginationWithNoLimit
    serializer_class = serializers.ZoneSerializer
    queryset = models.Zone.objects.all().order_by('zone_name')


class CityViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list:
    Get paginated list of city(should filter by zone)

    retrieve:
    Get single city by id
    """
    permission_classes = (permissions.AllowAny,)
    pagination_class = PaginationWithNoLimit
    serializer_class = serializers.CitySerializer
    queryset = models.City.objects.all().order_by('city_name')
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ('zone', 'is_ecommerce')


class ClusterViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list:
    Get paginated list of cluster(should filter by city)

    retrieve:
    Get single cluster by id
    """
    permission_classes = (permissions.AllowAny,)
    pagination_class = PaginationWithNoLimit
    serializer_class = serializers.ClusterSerializer
    queryset = models.Cluster.objects.all().order_by('cluster_name')
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ('city', 'is_ecommerce')


class SectorViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list:
    Get paginated list of sector(should filter by cluster)

    retrieve:
    Get single sector by id
    """
    permission_classes = (permissions.AllowAny,)
    pagination_class = PaginationWithNoLimit
    serializer_class = serializers.SectorSerializer
    queryset = models.Sector.objects.all().order_by('sector_name')
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ('cluster', 'is_ecommerce')


class EcommerceSectorViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list:
    Get paginated list of ecommerce sector(should filter by city)

    retrieve:
    Get single sector by id
    """
    permission_classes = (permissions.AllowAny,)
    pagination_class = PaginationWithNoLimit
    serializer_class = serializers.SectorSerializer
    queryset = models.EcommerceSector.objects.all().order_by('sector_name')
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ('cluster', 'city', 'is_ecommerce')


class VideoCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = serializers.VideoCategorySerializer
    queryset = VideoCategory.objects.all()

class VideoViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = serializers.VideoSerializer
    queryset = Video.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ('videoCategory',)


class EcommerceZoneViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list:
    Get paginated list of zones

    retrieve:
    Get single zone by id
    """
    permission_classes = (permissions.AllowAny,)
    pagination_class = PaginationWithNoLimit
    serializer_class = serializers.EcommerceZoneSerializer
    queryset = models.Zone.objects.filter(is_ecommerce=True).order_by('zone_name')


class UserFilterViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin):
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = PaginationWithNoLimit
    serializer_class = serializers.UserRetailerFilterSerializer
    queryset = UserRetailerFilters.objects.all().order_by('id')
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ('beat', 'salesPerson')

    def list(self, request, *args, **kwargs):
        user = request.user
        queryset =UserRetailerFilters.objects.all().order_by('id')
        print(queryset)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


    @decorators.action(detail=False, methods=['post'], url_path="save_filter")
    def save_filter(self, request, *args, **kwargs):
        user = request.user
        data = request.data
        print(user)
        print(data)
        admin = UserProfile.objects.filter(user=user, department__name__in=['Admin']).first()
        sales_profile = UserProfile.objects.filter(user=user, department__name__in=['Sales']).first()

        if sales_profile or admin:
            if admin:
                pass
            else:
                print(data)
                salesPersonProfile = SalesPersonProfile.objects.filter(user=user).first()
                user_filter_serializer = self.get_serializer(data=data)
                user_filter_serializer.is_valid(raise_exception=True)

                urf=UserRetailerFilters.objects.filter(salesPerson=salesPersonProfile.id).first()
                if urf:
                    urf.beat=data.get('beat',urf.beat)
                    urf.commission=int(data.get('commission',urf.commission))
                    urf.retailer_status=data.get('retailer_status',urf.retailer_status)
                    urf.save()
                else:
                    user_filter_serializer.save(salesPerson=salesPersonProfile.id)

                return Created({"success": "Beat Assigned Created Successfully"})
