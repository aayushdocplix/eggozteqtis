from django.urls import path, include
from django.views.generic import TemplateView
from rest_framework import routers

import base.views as views
from base.views import ZoneViewSet, CityViewSet, ClusterViewSet, SectorViewSet, UploadClusterDataViewSet, \
    VideoCategoryViewSet, VideoViewSet, EcommerceSectorViewSet, EcommerceZoneViewSet, UserFilterViewSet

app_name = "base"
router = routers.DefaultRouter()
router.register(r'upload_cluster', UploadClusterDataViewSet, basename='upload_cluster')
router.register(r'zone', ZoneViewSet, basename='zone')
router.register(r'ecommerce_zone', EcommerceZoneViewSet, basename='ecommerce_zone')
router.register(r'city', CityViewSet, basename='city')
router.register(r'cluster', ClusterViewSet, basename='cluster')
router.register(r'sector', SectorViewSet, basename='sector')
router.register(r'locality', EcommerceSectorViewSet, basename='locality')
router.register(r'video_category', VideoCategoryViewSet, basename='video_category')
router.register(r'video', VideoViewSet, basename='video')
router.register(r'filters', UserFilterViewSet, basename='filters')

urlpatterns = [
    path('', include(router.urls)),
    path(r'', TemplateView.as_view(template_name="base.html", content_type='text/html'), name="home"),
    path('city-list/', views.CityListView.as_view(), name="cities"),
    path('cities/<int:pk>/', views.CityDetail.as_view(), name="city"),
]
