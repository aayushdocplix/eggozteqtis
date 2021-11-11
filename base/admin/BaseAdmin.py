from base.models import Sector, Cluster, City, Zone, EcommerceSector, UserRetailerFilters

from django.contrib import admin

from base.models.Video import Video, VideoCategory, VideoTag


class ZoneAdmin(admin.ModelAdmin):
    list_display = ('id', 'zone_name',)
    search_fields = ('id', 'zone_name')
    readonly_fields = ['id']

    def get_queryset(self, request):
        queryset = super(ZoneAdmin, self).get_queryset(request)
        queryset = queryset.order_by('id')
        return queryset


class CityAdmin(admin.ModelAdmin):
    list_display = ('id', 'city_name', 'zone')
    search_fields = ('id', 'city_name')
    readonly_fields = ['id']

    def get_queryset(self, request):
        queryset = super(CityAdmin, self).get_queryset(request)
        queryset = queryset.order_by('id')
        return queryset


class ClusterAdmin(admin.ModelAdmin):
    list_display = ('id', 'cluster_name', 'city')
    search_fields = ('id', 'cluster_name', 'city__city_name')
    readonly_fields = ['id']

    def get_queryset(self, request):
        queryset = super(ClusterAdmin, self).get_queryset(request)
        queryset = queryset.order_by('id')
        return queryset


class SectorAdmin(admin.ModelAdmin):
    list_display = ('id', 'sector_name', 'cluster')
    search_fields = ('id', 'sector_name', 'cluster__cluster_name')
    readonly_fields = ['id']

    def get_queryset(self, request):
        queryset = super(SectorAdmin, self).get_queryset(request)
        queryset = queryset.order_by('id')
        return queryset


class EcommerceSectorAdmin(admin.ModelAdmin):
    list_display = ('id', 'sector_name', 'city', 'cluster', 'pinCode')
    search_fields = ('id', 'sector_name', 'city__city_name', 'cluster__cluster_name')
    readonly_fields = ['id']

    def get_queryset(self, request):
        queryset = super(EcommerceSectorAdmin, self).get_queryset(request)
        queryset = queryset.order_by('id')
        return queryset


admin.site.register(Zone, ZoneAdmin)
admin.site.register(City, CityAdmin)
admin.site.register(Cluster, ClusterAdmin)
admin.site.register(Sector, SectorAdmin)
admin.site.register(EcommerceSector, EcommerceSectorAdmin)
admin.site.register(Video)
admin.site.register(VideoCategory)
admin.site.register(VideoTag)
admin.site.register(UserRetailerFilters)
