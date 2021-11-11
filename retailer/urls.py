from django.urls import path, include
from rest_framework import routers

# from retailer.views import UploadRetailerViewSet, UploadRetailerDumpViewSet, UploadRetailerDueViewSet, \
#     UpdateCalcAmountViewSet, UploadRetailerSlabViewSet, UploadRetailerNamesViewSet, UploadCommissionSlabViewSet
from retailer.views import UploadRetailerBeatViewSet, UploadRetailerOmsBeatViewSet, UploadUBRetailerViewSet
from retailer.views.ExportViews import RetailerExportViewSet
from retailer.views.SerializedViews import CustomerCategoryViewSet, CustomerSubCategoryViewSet, RetailerViewSet, \
    CustomerCommissionSlabViewSet, CustomerDiscountSlabViewSet, CustomerClassificationViewSet, CustomerShortNameViewSet, \
    CustomerPaymentCycleViewSet, RetailerBeatViewSet, MarginRatesViewSet

app_name = "retailer"
router = routers.DefaultRouter()
# router.register(r'upload_retailer', UploadRetailerViewSet, basename='upload_retailer')
# router.register(r'upload_due', UploadRetailerDueViewSet, basename='upload_due')
# router.register(r'upload_slabs', UploadRetailerSlabViewSet, basename='upload_slabs')
# router.register(r'update_calc_amount', UpdateCalcAmountViewSet, basename='update_calc_amount')
# router.register(r'upload_retailer_dump', UploadRetailerDumpViewSet, basename='upload_retailer_dump')
# router.register(r'upload_retailer_names', UploadRetailerNamesViewSet, basename='upload_retailer_names')
# router.register(r'update_margins', UploadCommissionSlabViewSet, basename='update_margins')
router.register(r'update_beats', UploadRetailerBeatViewSet, basename='update_beats')
router.register(r'update_oms_beats', UploadRetailerOmsBeatViewSet, basename='update_oms_beats')
router.register(r'customer_category', CustomerCategoryViewSet, basename='customer_category')
router.register(r'margin_rates', MarginRatesViewSet, basename='margin_rates')
router.register(r'retailer_beat_list', RetailerBeatViewSet, basename='retailer_beat_list')
router.register(r'customer_short', CustomerShortNameViewSet, basename='customer_short')
router.register(r'customer_payment_cycle', CustomerPaymentCycleViewSet, basename='customer_payment_cycle')
router.register(r'customer_subcategory', CustomerSubCategoryViewSet, basename='customer_subcategory')
router.register(r'customer_commissionSlab', CustomerCommissionSlabViewSet, basename='customer_commissionSlab')
router.register(r'customer_classification', CustomerClassificationViewSet, basename='customer_classification')
router.register(r'customer_discount_slab', CustomerDiscountSlabViewSet, basename='customer_discount_slab')
router.register(r'export', RetailerExportViewSet, basename='export')
router.register(r'onboard_ub_retailer', UploadUBRetailerViewSet, basename='onboard_ub_retailer')
router.register(r'', RetailerViewSet, basename='')

urlpatterns = [
    path('', include(router.urls)),
]
