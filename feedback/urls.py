from django.urls import path, include
from rest_framework import routers

import feedback.views as views
from feedback.views import FarmerFeedbackViewSet, CustomerFeedbackViewSet

app_name = "feedback"

router = routers.DefaultRouter()
router.register('farmer', FarmerFeedbackViewSet, basename='farmer')
router.register('customer', CustomerFeedbackViewSet, basename='customer')
router.register(r'', views.FeedbackViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
