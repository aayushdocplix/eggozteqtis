from django.urls import path, include
from rest_framework import routers

from finance.views import FinanceProfileViewSet

app_name = "finance"

router = routers.DefaultRouter()
router.register('finance', FinanceProfileViewSet, basename='finance')

urlpatterns = [
    path('', include(router.urls)),
]
