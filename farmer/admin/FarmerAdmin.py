from django.contrib import admin

from farmer.models import FarmerBankDetails, Farmer, Farm, Shed, Flock, FlockBreed, DailyInput, FeedMedicine, \
    MedicineInput, FarmerOrder, FarmerOrderInLine, Party, Expenses, Post, PostImage, PostLike, PostComment, \
    PostCommentLike, NECCCity, CityNECCRate, FarmerBanner, NECCZone, FarmerAlert, NECCPriceStamp, FeedIngredient, \
    FlockFeedFormulation, FeedFormulation, FeedIngredientFormulaData


class FarmerBankInline(admin.StackedInline):
    model = FarmerBankDetails
    can_delete = True
    show_change_link = True
    extra = 0


class FarmerAdmin(admin.ModelAdmin):
    list_display = ('id', 'farmer')
    search_fields = ('id', 'farmer__name')
    readonly_fields = ['id']
    inlines = [FarmerBankInline]

    def get_queryset(self, request):
        queryset = super(FarmerAdmin, self).get_queryset(request)
        queryset = queryset.order_by('id')
        return queryset

class FarmAdmin(admin.ModelAdmin):
    list_display = ('id', 'farm_name', 'farmer')
    search_fields = ('id', 'farm_name', 'farmer__farmer__name')
    readonly_fields = ['id']

    def get_queryset(self, request):
        queryset = super(FarmAdmin, self).get_queryset(request)
        queryset = queryset.order_by('id')
        return queryset


class FarmerBankAdmin(admin.ModelAdmin):
    list_display = ('id', 'farmer', 'benificiary_name')
    search_fields = ('id', 'farmer__name', 'benificiary_name')
    readonly_fields = ['id']

    def get_queryset(self, request):
        queryset = super(FarmerBankAdmin, self).get_queryset(request)
        queryset = queryset.order_by('id')
        return queryset

class FarmerOrderInLineShow(admin.StackedInline):
    model = FarmerOrderInLine
    can_delete = True
    show_change_link = True
    extra = 0

class FarmerOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'farm','date','status')
    search_fields = ('id', 'farm')
    readonly_fields = ['id']
    inlines = [FarmerOrderInLineShow]

    def get_queryset(self, request):
        queryset = super(FarmerOrderAdmin, self).get_queryset(request)
        queryset = queryset.order_by('id')
        return queryset

class NeccRateAdmin(admin.ModelAdmin):
    list_display = ('id', 'modified_at','necc_city')
    search_fields = ('id', 'necc_city__name')
    readonly_fields = ['id']


    def get_queryset(self, request):
        queryset = super(NeccRateAdmin, self).get_queryset(request)
        queryset = queryset.order_by('id')
        return queryset

class ShedAdmin(admin.ModelAdmin):
    list_display = ('id', 'farm', 'shed_name', 'shed_type', 'total_active_bird_capacity','farmer')
    search_fields = ('id', 'farm__farm_name', 'shed_name', 'shed_type', 'total_active_bird_capacity', 'farm__farmer__farmer__name')
    readonly_fields = ['id']

    def farmer(self, obj):
        return '%s' % obj.farm.farmer.farmer.name

    def get_queryset(self, request):
        queryset = super(ShedAdmin, self).get_queryset(request)
        queryset = queryset.order_by('id')
        return queryset


class FlockBreedAdmin(admin.ModelAdmin):
    list_display = ('id', 'breed_name',)
    search_fields = ('id', 'breed_name')
    readonly_fields = ['id']


    def get_queryset(self, request):
        queryset = super(FlockBreedAdmin, self).get_queryset(request)
        queryset = queryset.order_by('id')
        return queryset


class FlockAdmin(admin.ModelAdmin):
    list_display = ('id', 'flock_name', 'shed', 'breed', 'age', 'initial_capacity', 'current_capacity', 'last_daily_input_date', 'total_production', 'farmer')
    search_fields = ('id', 'flock_name', 'shed__shed_name', 'breed__breed_name', 'age', 'last_daily_input_date','shed__farm__farmer__farmer__name')
    readonly_fields = ['id']

    def farmer(self, obj):
        return '%s' % obj.shed.farm.farmer.farmer.name

    def get_queryset(self, request):
        queryset = super(FlockAdmin, self).get_queryset(request)
        queryset = queryset.order_by('id')
        return queryset


class DailyInputAdmin(admin.ModelAdmin):
    list_display = ('id', 'flock','date', 'egg_daily_production', 'culls', 'mortality', 'transferred_quantity', 'total_active_birds', 'farmer')
    search_fields = ('id', 'flock__flock_name', 'flock__shed__farm__farmer__farmer__name')
    readonly_fields = ['id']

    def farmer(self, obj):
        return '%s' % obj.flock.shed.farm.farmer.farmer.name

    def get_queryset(self, request):
        queryset = super(DailyInputAdmin, self).get_queryset(request)
        queryset = queryset.order_by('id')
        return queryset

admin.site.register(Farmer, FarmerAdmin)
admin.site.register(Farm, FarmAdmin)
admin.site.register(FarmerBankDetails,FarmerBankAdmin)
admin.site.register(Shed,ShedAdmin)
admin.site.register(FlockBreed, FlockBreedAdmin)
admin.site.register(Flock, FlockAdmin)
admin.site.register(DailyInput, DailyInputAdmin)
admin.site.register(FeedMedicine)
admin.site.register(MedicineInput)
admin.site.register(FarmerOrder,FarmerOrderAdmin)
admin.site.register(FarmerOrderInLine)
admin.site.register(Party)
admin.site.register(Expenses)
admin.site.register(Post)
admin.site.register(PostImage)
admin.site.register(PostLike)
admin.site.register(PostComment)
admin.site.register(PostCommentLike)
admin.site.register(NECCZone)
admin.site.register(NECCCity)
admin.site.register(CityNECCRate, NeccRateAdmin)
admin.site.register(NECCPriceStamp)
admin.site.register(FarmerBanner)
admin.site.register(FarmerAlert)
admin.site.register(FeedIngredient)
admin.site.register(FeedIngredientFormulaData)
admin.site.register(FeedFormulation)
admin.site.register(FlockFeedFormulation)

