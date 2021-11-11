from django.urls import path, include
from rest_framework import routers

from product.views.SerializedViews import UploadProductDataViewSet, ProductViewSet, ProductDivisionViewSet, \
    BaseProductViewSet, ProductSubDivisionViewSet, UploadProductDescriptionsViewSet, UploadProductBenefitsViewSet, \
    EcommerceProductViewSet, ProductUpdateViewSet, ProductShortViewSet

app_name = "product"
router = routers.DefaultRouter()
router.register(r'upload_product', UploadProductDataViewSet, basename='upload_product')
router.register(r'upload_product_descriptions', UploadProductDescriptionsViewSet, basename='upload_product_descriptions')
router.register(r'upload_product_benefits', UploadProductBenefitsViewSet, basename='upload_product_benefits')
router.register(r'division', ProductDivisionViewSet, basename='division')
router.register(r'sub_division', ProductSubDivisionViewSet, basename='sub_division')
router.register('base_product', BaseProductViewSet, basename='base_product')
router.register(r'ecommerce', EcommerceProductViewSet, basename='ecommerce')
router.register(r'ecomm', ProductUpdateViewSet, basename='ecomm')
router.register(r'unit_list', ProductShortViewSet, basename='unit_list')
router.register(r'', ProductViewSet, basename='')


urlpatterns = [
    path('', include(router.urls)),
]
