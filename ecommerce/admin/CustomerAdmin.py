from django.contrib import admin

from ecommerce.models import Customer, WalletRecharge, CashFreeTransaction, CustomerVoucherPromo, RechargeVoucher, \
    CustomerPromoWallet, CustomerWallet, CustomerReferral, EcommerceSlot, ReferralData
from ecommerce.models.Subscriptions import MemberShip, FrequencyDay, CustomerMemberShip, CustomerSubscription, \
    MemberShipData, MemberShipBenefits, MemberShipExtras, Subscription, SubscriptionExtras, SubscriptionBenefits


class CustomerAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'code' ,'phone_no', 'shipping_address')
    search_fields = ('id', 'user__name', 'code')
    readonly_fields = ['id']

    def get_queryset(self, request):
        queryset = super(CustomerAdmin, self).get_queryset(request)
        queryset = queryset.order_by('id')
        return queryset

admin.site.register(Customer, CustomerAdmin)
admin.site.register(CustomerWallet)
admin.site.register(CustomerPromoWallet)
admin.site.register(RechargeVoucher)
admin.site.register(CustomerVoucherPromo)
admin.site.register(CashFreeTransaction)
admin.site.register(WalletRecharge)
admin.site.register(CustomerReferral)
admin.site.register(CustomerSubscription)
admin.site.register(CustomerMemberShip)
admin.site.register(FrequencyDay)
admin.site.register(MemberShip)
admin.site.register(MemberShipData)
admin.site.register(MemberShipBenefits)
admin.site.register(MemberShipExtras)
admin.site.register(EcommerceSlot)
admin.site.register(ReferralData)
admin.site.register(Subscription)
admin.site.register(SubscriptionBenefits)
admin.site.register(SubscriptionExtras)
