from django.urls import path, include
from rest_framework import routers

from ecommerce.views import CustomerViewSet, EcommerceWordpressViewSet
from ecommerce.views.SerializedViews import RechargeVoucherViewSet, CustomerWalletViewSet, WalletRechargeViewSet, \
    MemberShipViewSet, CustomerSubscriptionViewSet, CustomerMemberShipViewSet, SubscriptionViewSet, \
    NotifyCustomerViewSet, CustomerCartCheckout

app_name = "ecommerce"
router = routers.DefaultRouter()
router.register('blogs', EcommerceWordpressViewSet, basename='blogs')
router.register('recharge_voucher', RechargeVoucherViewSet, basename='recharge_voucher')
router.register('customer_wallet', CustomerWalletViewSet, basename='customer_wallet')
router.register('membership', MemberShipViewSet, basename='membership')
router.register('subscription', SubscriptionViewSet, basename='subscription')
router.register('cart', CustomerCartCheckout, basename='cart')
router.register('notify', NotifyCustomerViewSet, basename='notify')
router.register('customer_subscriptions', CustomerSubscriptionViewSet, basename='customer_subscriptions')
router.register('customer_membership', CustomerMemberShipViewSet, basename='customer_membership')
router.register('wallet', WalletRechargeViewSet, basename='wallet')

router.register(r'', CustomerViewSet, basename='')


urlpatterns = [
    path('', include(router.urls)),

]
