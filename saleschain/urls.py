from django.urls import path, include
from rest_framework import routers

from saleschain.views.ExportViews import RetailerEggsDataExportViewSet, SalesEggsDataExportViewSet, \
    MonthlySalesExportViewSet, FinanceExportViewSet, SalesOrderExportViewSet, FinancePaymentViewSet, \
    SalesFilteredExportViewSet, SalesGEBExportViewSet, ReturnExportViewSet
from saleschain.views.SerializedViews import SalesDashboardViewSet, SalesPersonProfileViewSet, \
    SalesManagerProfileViewSet, SalesDemandViewSet

app_name = "saleschain"
router = routers.DefaultRouter()
router.register(r'dashboard', SalesDashboardViewSet, basename='dashboard')
router.register(r'export', SalesFilteredExportViewSet, basename='export')
router.register(r'geb_export', SalesGEBExportViewSet, basename='geb_export')
router.register(r'demand', SalesDemandViewSet, basename='demand')
router.register(r'order_export', SalesOrderExportViewSet, basename='order_export')
router.register(r'monthly_export', MonthlySalesExportViewSet, basename='monthly_export')
router.register(r'finance_export', FinanceExportViewSet, basename='finance_export')
router.register(r'return_export', ReturnExportViewSet, basename='return_export')
router.register(r'payment_export', FinancePaymentViewSet, basename='payment_export')
router.register(r'sales_eggs_export', SalesEggsDataExportViewSet, basename='sales_eggs_export')
router.register(r'retailer_eggs_export', RetailerEggsDataExportViewSet, basename='retailer_eggs_export')
router.register(r'', SalesPersonProfileViewSet, basename='')
router.register(r'manager', SalesManagerProfileViewSet, basename='manager')


urlpatterns = [
    path('', include(router.urls)),
]
