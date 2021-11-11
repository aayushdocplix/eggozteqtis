from django.urls import path, include
from rest_framework import routers

from feedwarehouse.views import UploadFeedProductViewSet
from feedwarehouse.views.SerializedViews import FeedWarehouseViewSet, FeedProductDivisionViewSet, \
    FeedProductSubDivisionViewSet, ProductVendorViewSet, FeedProductSpecificationViewSet, FeedProductViewSet, \
    FeedOrderViewSet

app_name = "feedwarehouse"
router = routers.DefaultRouter()
router.register(r'division', FeedProductDivisionViewSet, basename='division')
router.register(r'sub_division', FeedProductSubDivisionViewSet, basename='sub_division')
router.register(r'product_vendor', ProductVendorViewSet, basename='product_vendor')
router.register(r'product_specification', FeedProductSpecificationViewSet, basename='product_specification')
router.register(r'feed_product', FeedProductViewSet, basename='feed_product')
router.register(r'feed_order', FeedOrderViewSet, basename='feed_order')
router.register(r'upload_feed_product', UploadFeedProductViewSet, basename='upload_feed_product')
router.register(r'', FeedWarehouseViewSet, basename='')


urlpatterns = [
    path('', include(router.urls)),
]
