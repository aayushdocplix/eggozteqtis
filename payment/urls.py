from django.urls import path, include
from rest_framework import routers

from payment.views import SalesTransactionViewset, HandleReturnAfterPayment, HandleNotifyAfterPayment, \
    HandleReturnAfterWalletRecharge, SalesTransactionAmountViewset, SalesPaymentViewSet, \
    HandleReturnAfterMemberShipRecharge, HandleReturnAfterSubscriptionRecharge
from payment.views.ExportViews import SalesTransactionsExportViewSet
from payment.views.InvoiceView import InvoiceViewSet

app_name = "payment"
router = routers.DefaultRouter()
router.register(r'sales_transactions', SalesTransactionViewset, basename='sales_transactions')
router.register(r'sales_transactions_amount', SalesTransactionAmountViewset, basename='sales_transactions_amount')
router.register(r'invoice', InvoiceViewSet, basename='invoice')
router.register('return_payment', HandleReturnAfterPayment, basename='return_payment')
router.register('return_wallet_recharge', HandleReturnAfterWalletRecharge, basename='return_wallet_recharge')
router.register('return_membership_recharge', HandleReturnAfterMemberShipRecharge, basename='return_membership_recharge')
router.register('return_subscription_recharge', HandleReturnAfterSubscriptionRecharge, basename='return_subscription_recharge')
router.register('notify_payment', HandleNotifyAfterPayment, basename='notify_payment')
router.register('pending_collection', SalesPaymentViewSet, basename='pending_collection')
router.register(r'export', SalesTransactionsExportViewSet, basename='export')

urlpatterns = [
    path('', include(router.urls)),
]
