from django.urls import path, include
from rest_framework import routers

from distributionchain.views.SerializedViews import DistributionProfileViewSet, \
    DistributionBeatViewSet, RetailerBeatWiseViewSet, RetailerBeatListViewSet, TripSKUTransferViewSet, SMRelativeViewSet

app_name = "distribution"

router = routers.DefaultRouter()
router.register(r'beat-wise-retailer', RetailerBeatWiseViewSet, basename='beat-wise-retailer')
router.register(r'retailer_list', RetailerBeatListViewSet, basename='retailer_list')
router.register(r'', DistributionProfileViewSet, basename='distribution')
router.register(r'get_transferskus', TripSKUTransferViewSet, basename='get_transferskus')
router.register(r'beat-assignment', DistributionBeatViewSet, basename='beat-assignment')
router.register(r'sm_relative_data', SMRelativeViewSet, basename='sm_relative_data')

urlpatterns = [
    path('', include(router.urls)),
]
