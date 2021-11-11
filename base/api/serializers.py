from rest_framework import serializers

from base.models import City, Zone, Cluster, Sector, EcommerceSector, UserRetailerFilters
from base.models.Video import VideoCategory, VideoTag, Video


class ZoneSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Zone
        fields = ('id', 'zone_name')


class EcommerceZoneSerializer(serializers.ModelSerializer):
    cities = serializers.SerializerMethodField()

    class Meta:
        model = Zone
        fields = ('id', 'zone_name','cities')

    def get_cities(self,obj):
        cities = obj.cities.filter(is_ecommerce=True)
        return EcommerceCitySerializer(cities,many=True).data

class EcommerceCitySerializer(serializers.ModelSerializer):
    ecommerceSectors = serializers.SerializerMethodField()

    class Meta:
        model = City
        fields = ('id', 'city_name', 'state', 'country','ecommerceSectors')

    def get_ecommerceSectors(self,obj):
        ecommerceSectors = obj.ecommerceSectors.filter(is_ecommerce=True)
        return EcommerceSectorSerializer(ecommerceSectors,many=True).data

class EcommerceSectorSerializer(serializers.ModelSerializer):

    class Meta:
        model = EcommerceSector
        fields = ('id', 'sector_name', 'city', 'cluster')


class CitySerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = City
        fields = ('id', 'city_name', 'state', 'country')


class ClusterSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Cluster
        fields = ('id', 'cluster_name')


class SectorSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Sector
        fields = ('id', 'sector_name')


class UploadDataSerializer(serializers.Serializer):
    csv_file = serializers.FileField(required=True)


class UploadDueDataSerializer(serializers.Serializer):
    cities = serializers.ListField(required=True)
    date = serializers.CharField(required=True)

class UploadCitiesSerializer(serializers.Serializer):
    cities = serializers.ListField(required=True)


class UploadAmountsSerializer(serializers.Serializer):
    salesPersonId = serializers.ListField(required=True)
    minOrderId = serializers.IntegerField(required=True)


class VideoCategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = VideoCategory
        fields = '__all__'

class VideoTagSerializer(serializers.ModelSerializer):

    class Meta:
        model = VideoTag
        fields = '__all__'

class VideoSerializer(serializers.ModelSerializer):
    video_tags = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = '__all__'

    def get_video_tags(self,obj):
        video_tags = obj.video_tags.all()
        return VideoTagSerializer(video_tags,many=True).data


class UserRetailerFilterSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserRetailerFilters
        fields = '__all__'
