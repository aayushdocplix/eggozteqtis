from django.contrib import admin

from retailer.models import Retailer, Customer_Category, Customer_SubCategory, RetailOwner, IncomeSlab, CommissionSlab, \
    RetailerEggsdata, DiscountSlab, Classification, RetailerShorts, RetailerPaymentCycle, RetailerBeat, MarginRates


class RetailerAdmin(admin.ModelAdmin):
    list_display = ('id','beat_number','name_of_shop', 'billing_name_of_shop', 'code', 'code_int', 'code_string', 'commission_slab', 'onboarding_date', 'cluster', 'salesPersonProfile', 'phone_no',
                    'category', 'sub_category', 'shipping_address', 'amount_due', 'calc_amount_due')
    search_fields = ('id', 'name_of_shop', 'onboarding_date', 'salesPersonProfile__user__name', 'code')
    readonly_fields = ['id',]

    def get_queryset(self, request):
        queryset = super(RetailerAdmin, self).get_queryset(request)
        queryset = queryset.order_by('id')
        return queryset

class RetailerEggsAdmin(admin.ModelAdmin):
    list_display = ('id','date', 'retailer', 'brown', 'white', 'nutra')
    search_fields = ('id','date','retailer__name_of_shop',)
    readonly_fields = ['id',]

    def get_queryset(self, request):
        queryset = super(RetailerEggsAdmin, self).get_queryset(request)
        queryset = queryset.order_by('id')
        return queryset


class Customer_CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('id', 'name')
    readonly_fields = ['id',]

    def get_queryset(self, request):
        queryset = super(Customer_CategoryAdmin, self).get_queryset(request)
        queryset = queryset.order_by('id')
        return queryset

class Customer_SubCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('id', 'name')
    readonly_fields = ['id',]

    def get_queryset(self, request):
        queryset = super(Customer_SubCategoryAdmin, self).get_queryset(request)
        queryset = queryset.order_by('id')
        return queryset

class RetailOwnerAdmin(admin.ModelAdmin):
    list_display = ('id', 'owner_name', 'phone_no', 'retail_shop')
    search_fields = ('id', 'owner_name', 'phone_no', 'retail_shop__name_of_shop')
    readonly_fields = ['id',]

    def get_queryset(self, request):
        queryset = super(RetailOwnerAdmin, self).get_queryset(request)
        queryset = queryset.order_by('id')
        return queryset

class IncomeSlabAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('id', 'name')
    readonly_fields = ['id',]

    def get_queryset(self, request):
        queryset = super(IncomeSlabAdmin, self).get_queryset(request)
        queryset = queryset.order_by('id')
        return queryset


class CommissionSlabAdmin(admin.ModelAdmin):
    list_display = ('id', 'number', 'rates')
    search_fields = ('id', 'number')
    readonly_fields = ['id',]

    def rates(self, obj):
        if obj.margin.all():
            return "\n, ".join(["{}-{}".format(str(margin.product.SKU_Count)+str(margin.product.name[::1]),str(margin.margin_rate)) for margin in obj.margin.all()])
        else:
            return "-"
    def get_queryset(self, request):
        queryset = super(CommissionSlabAdmin, self).get_queryset(request)
        queryset = queryset.order_by('id')
        return queryset


class DiscountSlabAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'white_number', )
    search_fields = ('id', 'name')
    readonly_fields = ['id',]

    def get_queryset(self, request):
        queryset = super(DiscountSlabAdmin, self).get_queryset(request)
        queryset = queryset.order_by('id')
        return queryset


class ClassificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'name',)
    search_fields = ('id', 'name')
    readonly_fields = ['id',]

    def get_queryset(self, request):
        queryset = super(ClassificationAdmin, self).get_queryset(request)
        queryset = queryset.order_by('id')
        return queryset


admin.site.register(Retailer, RetailerAdmin)
admin.site.register(Customer_Category, Customer_CategoryAdmin)
admin.site.register(Customer_SubCategory, Customer_SubCategoryAdmin)
admin.site.register(RetailOwner, RetailOwnerAdmin)
admin.site.register(IncomeSlab, IncomeSlabAdmin)
admin.site.register(CommissionSlab, CommissionSlabAdmin)
admin.site.register(RetailerEggsdata, RetailerEggsAdmin)
admin.site.register(Classification, ClassificationAdmin)
admin.site.register(DiscountSlab, DiscountSlabAdmin)
admin.site.register(RetailerShorts)
admin.site.register(RetailerPaymentCycle)
admin.site.register(RetailerBeat)
admin.site.register(MarginRates)

