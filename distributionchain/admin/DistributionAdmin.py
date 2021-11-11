from django.contrib import admin

from distributionchain.models import DistributionPersonProfile, DistributionEggsdata, BeatAssignment, \
    BeatWarehouseSupply, BeatSMApproval, BeatRHApproval, TripSKUTransfer, TransferSKU, SMRelativeNumber


class DistributionEggsAdmin(admin.ModelAdmin):
    list_display = ('id', 'date', 'distributionPerson', 'brown', 'white', 'nutra')
    search_fields = ('id','date', 'distributionPerson__user__name')
    readonly_fields = ['id',]

    def get_queryset(self, request):
        queryset = super(DistributionEggsAdmin, self).get_queryset(request)
        queryset = queryset.order_by('id')
        return queryset


class DistributionPersonAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'warehouse', 'management_status'
                                               '')
    search_fields = ('id', 'user__name')
    readonly_fields = ['id',]

    def get_queryset(self, request):
        queryset = super(DistributionPersonAdmin, self).get_queryset(request)
        queryset = queryset.order_by('id')
        return queryset


class BeatAssignmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'beat_date', 'beat_number', 'distributor', 'demand_classification', 'warehouse')
    search_fields = ('id', 'distributor_user__name')
    readonly_fields = ['id',]

    def get_queryset(self, request):
        queryset = super(BeatAssignmentAdmin, self).get_queryset(request)
        queryset = queryset.order_by('id')
        return queryset


admin.site.register(DistributionPersonProfile, DistributionPersonAdmin)
admin.site.register(DistributionEggsdata, DistributionEggsAdmin)
admin.site.register(BeatAssignment, BeatAssignmentAdmin)
admin.site.register(BeatWarehouseSupply)
admin.site.register(BeatSMApproval)
admin.site.register(BeatRHApproval)
admin.site.register(TripSKUTransfer)
admin.site.register(TransferSKU)
admin.site.register(SMRelativeNumber)
