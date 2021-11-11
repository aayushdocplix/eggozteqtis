from django.urls import path, include
from rest_framework import routers

# from order.views import UploadOrderViewSet, UploadDueDiffViewSet, UploadSampleOrderViewSet, UpdateOrderDateViewSet, \
#     UpdateOrderAmountViewSet, UpdateOrderBillViewSet, UpdateLedgersViewSet, UpdateEmptyOrderNameViewSet, \
#     CheckDuplicateOrdersViewSet, UpdateEggsDataViewSet
from order.views import UploadSampleOrderViewSet, UploadGEBMissingOrderViewSet, UploadGEBMissingPaymentViewSet, \
    UpdateEggsDataViewSet, UpdateLedgersViewSet, UpdateMTPaymentViewSet, InvoiceLedgersViewSet
from order.views.ExportViews import OrderExportViewSet
from order.views.SerializedViews import OrderViewSet, PackingViewSet, EcommerceOrderViewSet, PurchaseOrderViewSet

app_name = "order"

router = routers.DefaultRouter()
router.register(r'packing', PackingViewSet, basename='packing')
# router.register(r'upload_order', UploadOrderViewSet, basename='upload_order')
# router.register(r'update_order_date', UpdateOrderDateViewSet, basename='upload_order_date')
# router.register(r'update_order_amount', UpdateOrderAmountViewSet, basename='upload_order_amount')
# router.register(r'upload_due_diff', UploadDueDiffViewSet, basename='upload_due_diff')
router.register(r'update_ledgers', UpdateLedgersViewSet, basename='update_ledgers')
router.register(r'invoice_ledgers', InvoiceLedgersViewSet, basename='invoice_ledgers')
# router.register(r'update_empty_order', UpdateEmptyOrderNameViewSet, basename='update_empty_order')
# router.register(r'update_bill', UpdateOrderBillViewSet, basename='update_bill')
# router.register(r'find_duplicate_orders', CheckDuplicateOrdersViewSet, basename='find_duplicate_orders')
router.register(r'update_eggs_data', UpdateEggsDataViewSet, basename='update_eggs_data')
router.register(r'upload_order_dump', UploadSampleOrderViewSet, basename='upload_order_dump')
router.register(r'update_mt_payments', UpdateMTPaymentViewSet, basename='update_mt_payments')
router.register(r'upload_order_missing', UploadGEBMissingOrderViewSet, basename='upload_order_missing')
router.register(r'upload_payment_missing', UploadGEBMissingPaymentViewSet, basename='upload_payment_missing')
router.register(r'export', OrderExportViewSet, basename='export')
router.register(r'ecommerce_order', EcommerceOrderViewSet, basename='ecommerce_order')
router.register(r'po', PurchaseOrderViewSet, basename='po')
router.register(r'', OrderViewSet, basename='')

urlpatterns = [
    path('', include(router.urls)),
]
