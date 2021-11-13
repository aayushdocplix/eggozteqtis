from django.urls import path, include
from rest_framework import routers
from procurement.views import ProcurementView, ProcurementPerWarehouseView, EggsInView, ImageUploadView, \
    EggCleaningView, EggQualityCheckView, PackageView, StockDetails, SendOtpView, VerifyOtpView, DriverSearchView, \
    BatchListView, MoveToUnbrandedView

app_name = "procurement"


router = routers.DefaultRouter()

router.register(r'warehouse', ProcurementPerWarehouseView, basename='warehouse')
router.register(r'egg-in', EggsInView, basename='egg-in')
router.register(r'image', ImageUploadView, basename='image')
router.register(r'cleaning', EggCleaningView, basename='cleaning')
router.register(r'quality', EggQualityCheckView, basename='quality')
router.register(r'packaging', PackageView, basename='packaging')
router.register(r'stock', StockDetails, basename='stock')
router.register(r'', ProcurementView, basename='procurement')

urlpatterns = [
    path('otp/verify', VerifyOtpView.as_view()),
    path('otp', SendOtpView.as_view()),
    path('', include(router.urls)),
    path('farmer/search',DriverSearchView.as_view() ),
    path('batch-list', BatchListView.as_view(), name='batch-list'),
    path('unbranded', MoveToUnbrandedView.as_view(), name='unbranded')
]
