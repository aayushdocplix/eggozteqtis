from django.urls import path, include
from rest_framework import routers

import custom_auth.views as views
from custom_auth.views import GenerateOtpViewset, ValidateOtpViewset, \
    LoginGenerateOtpViewset, LoginValidateOtpViewset, EcommerceLoginGenerateOtpViewset, EcommerceLoginValidateOtpViewset

app_name = "custom_auth"

# Routers provide an easy way of automatically determining the URL conf.
router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'beat-users', views.BeatUserViewSet)
router.register(r'user', views.UserOnboardViewSet)
router.register(r'addresses', views.AddressViewSet)
router.register(r'fcm_token', views.FcmTokenViewSet)

router.register(r'departments', views.DepartmentViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path("otp/generate/", GenerateOtpViewset.as_view(), name="generate_otp"),
    path("otp/validate/", ValidateOtpViewset.as_view(), name="validate_otp"),
    path("login_otp/generate/", LoginGenerateOtpViewset.as_view(), name="generate_login_otp"),
    path("login_otp/validate/", LoginValidateOtpViewset.as_view(), name="validate_login_otp"),
    path("ecomm_login_otp/generate/", EcommerceLoginGenerateOtpViewset.as_view(), name="ecomm_generate_login_otp"),
    path("ecomm_login_otp/validate/", EcommerceLoginValidateOtpViewset.as_view(), name="ecomm_validate_login_otp"),
    path('signup/', views.SignupView.as_view(), name="home"),
    path('current_user/', views.current_user),
    path('current_user_cities/', views.current_user_cities),
    path('user/confirm_email/', views.registration_confirm, name="confirm_email"),
]
