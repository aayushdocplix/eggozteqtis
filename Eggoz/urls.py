"""Eggoz URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from drf_yasg import openapi
from rest_framework import permissions
from rest_framework.documentation import include_docs_urls
from rest_framework.schemas import get_schema_view
from rest_framework_jwt.views import obtain_jwt_token, refresh_jwt_token, verify_jwt_token

from Eggoz import settings

schema_view = get_schema_view(
    openapi.Info(
        title="Eggoz API",
        default_version='v1',
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('openapi', schema_view, name='openapi-schema'),
    url(r'^swagger/', include_docs_urls(title='Eggoz API docs', permission_classes=(permissions.AllowAny,)),
        name='swagger'),
    path(r'base/', include('base.urls')),
    path(r'retailer/', include('retailer.urls')),
    path(r'farmer/', include('farmer.urls')),
    path(r'warehouse/', include('warehouse.urls')),
    path(r'sales/', include('saleschain.urls')),
    path(r'', include('custom_auth.urls')),
    path(r'order/', include('order.urls')),
    path(r'product/', include('product.urls')),
    path(r'feed/', include('feedwarehouse.urls')),
    path(r'payment/', include('payment.urls')),
    path(r'api/feedback/', include('feedback.urls')),
    path(r'api-auth/', include('rest_framework.urls')),
    path('token-auth/', obtain_jwt_token),
    path('api-token-refresh/', refresh_jwt_token),
    path('api-token-verify/', verify_jwt_token),
    path(r'ecommerce/', include('ecommerce.urls')),
    path(r'distribution/', include('distributionchain.urls')),
    path(r'finance/', include('finance.urls')),
    path(r'procurement/', include('procurement.urls'))
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
