from django.contrib import admin

# Register your models here.
from procurement.models import BatchModel, BatchPerWarehouse, EggsIn, ImageUpload, EggCleaning, EggQualityCheck, \
    Procurement, Package


class ProcurementAdmin(admin.ModelAdmin):
    list_display = ('id', 'batch_id', 'egg_type', 'date', 'created_at', 'updated_by')
    search_fields = ('batch_id', 'egg_type',)
    list_filter = ('egg_type',)
    ordering = ('-created_at',)


class BatchModelPerWarehouseAdmin(admin.ModelAdmin):
    list_display = ('id', 'batch', 'warehouse')
    search_fields = ('batch',)
    list_filter = ('warehouse',)
    ordering = ('-id',)
    autocomplete_fields = ['batch']


class EggsInAdmin(admin.ModelAdmin):
    list_display = ('id', 'batch_id', 'date', 'egg_loss')
    search_fields = ('batch_id',)
    ordering = ('-id',)


class ImageUploadAdmin(admin.ModelAdmin):
    list_display = ('id', 'image', 'created_at')
    search_fields = ('image',)
    ordering = ('-id',)


class EggCleaningAdmin(admin.ModelAdmin):
    list_display = ('id', 'batch_id', 'egg_chatki', 'egg_loss', 'egg_count', 'start_time', 'end_time')
    search_fields = ('batch_id',)
    ordering = ('-id',)


class EggQualityCheckAdmin(admin.ModelAdmin):
    list_display = ('id', 'batch_id', 'egg_chatki', 'egg_loss', 'egg_count', 'start_time', 'end_time')
    search_fields = ('batch_id',)
    ordering = ('-id',)


class ProcurementBatchAdmin(admin.ModelAdmin):
    list_display = ('id', 'farmer', 'procurement_bill_url')
    search_fields = ('farmer',)
    ordering = ('-id',)


class PackageAdmin(admin.ModelAdmin):
    list_display = ('id', 'batch_id', 'start_time', 'egg_chatki', 'egg_loss', 'package_count')
    search_fields = ('batch_id',)
    ordering = ('-id',)


admin.site.register(BatchModel, ProcurementAdmin)
admin.site.register(BatchPerWarehouse, BatchModelPerWarehouseAdmin)
admin.site.register(EggsIn, EggsInAdmin)
admin.site.register(ImageUpload, ImageUploadAdmin)
admin.site.register(EggCleaning, EggCleaningAdmin)
admin.site.register(EggQualityCheck, EggQualityCheckAdmin)
admin.site.register(Procurement, ProcurementBatchAdmin)
admin.site.register(Package, PackageAdmin)
