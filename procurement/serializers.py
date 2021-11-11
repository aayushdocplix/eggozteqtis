from decimal import Decimal

from rest_framework import serializers
from procurement.models import *


class ProcurementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Procurement
        fields = '__all__'


class BatchSerializer(serializers.ModelSerializer):
    warehouse = serializers.SerializerMethodField()
    farmer_name = serializers.SerializerMethodField()
    egg_in_id = serializers.SerializerMethodField()
    egg_quality_id = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    procurement_bill_url = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()
    total_egg = serializers.SerializerMethodField()
    additional_charge = serializers.SerializerMethodField()

    def get_total_price(self, obj):
        return round(float(Decimal(obj.actual_egg_count) * Decimal(30) * Decimal(obj.actual_egg_price)), 2)

    def get_total_egg(self, obj):
        return obj.actual_egg_count * 30

    def get_warehouse(self, obj):
        try:
            procurement_mapping = BatchPerWarehouse.objects.get(batch=obj)
        except BatchPerWarehouse.DoesNotExist:
            return None
        return BatchPerWarehouseSerializer(procurement_mapping).data['id']

    def get_additional_charge(self, obj):
        if obj.procurement:
            return obj.procurement.additional_charge
        return None

    def get_farmer_name(self, obj):
        if obj.procurement:
            if obj.procurement.farmer:
                if obj.procurement.farmer.farmer:
                    return obj.procurement.farmer.farmer.name
        return None

    def get_egg_in_id(self, obj):
        try:
            egg_in = EggsIn.objects.get(batch_id=obj)
        except EggsIn.DoesNotExist:
            return None
        return EggsInSerializers(egg_in).data['id']

    def get_egg_quality_id(self, obj):
        try:
            egg_quality = EggQualityCheck.objects.get(batch=obj)
        except EggQualityCheck.DoesNotExist:
            return None
        return egg_quality.id

    def get_procurement_bill_url(self, obj):
        if obj.procurement:
            return obj.procurement.procurement_bill_url
        return None

    def get_status(self, obj):
        if self.get_warehouse(obj):
            if self.get_egg_in_id(obj):
                if EggCleaning.objects.filter(batch_id=obj).exists():
                    if self.get_egg_quality_id(obj):
                        return "QUALITY"
                    else:
                        return "CLEANING"
                return "EGG IN"
            else:
                return "WAREHOUSE"
        else:
            return "ON ROAD"

    class Meta:
        model = BatchModel
        fields = '__all__'


class BatchStockDetailSerializer(serializers.ModelSerializer):
    egg_in_detail = None
    egg_quality_detail = None
    egg_cleaning_detail = None
    egg_packaging_detail = None
    warehouse_name = serializers.SerializerMethodField()
    farmer_name = serializers.SerializerMethodField()
    egg_in_loss = serializers.SerializerMethodField()
    egg_in_chatki = serializers.SerializerMethodField()
    egg_in_eggs = serializers.SerializerMethodField()
    egg_quality_loss = serializers.SerializerMethodField()
    egg_quality_chatki = serializers.SerializerMethodField()
    egg_quality_eggs = serializers.SerializerMethodField()
    egg_cleaning_loss = serializers.SerializerMethodField()
    egg_cleaning_chatki = serializers.SerializerMethodField()
    egg_cleaning_eggs = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()
    total_egg = serializers.SerializerMethodField()
    egg_tray = serializers.SerializerMethodField()

    def get_total_price(self, obj):
        return Decimal(obj.egg_count) * Decimal(30) * Decimal(obj.egg_price)

    def get_total_egg(self, obj):
        return obj.egg_count * 30

    def get_warehouse_name(self, obj):
        try:
            procurement_mapping = BatchPerWarehouse.objects.get(batch=obj)
        except BatchPerWarehouse.DoesNotExist:
            return None
        return BatchPerWarehouseSerializer(procurement_mapping).data['warehouse_name']

    def get_farmer_name(self, obj):
        if obj.procurement:
            if obj.procurement.farmer:
                if obj.procurement.farmer.farmer:
                    return obj.procurement.farmer.farmer.name
        return None

    def get_egg_in_loss(self, obj):
        if self.egg_in_detail is None:
            try:
                egg_in = EggsIn.objects.get(batch_id=obj)
                self.egg_in_detail = EggsInSerializers(egg_in).data
            except EggsIn.DoesNotExist:
                self.egg_in_detail = {}
                return None
        return self.egg_in_detail.get('egg_loss', None)

    def get_egg_in_chatki(self, obj):
        if self.egg_in_detail is None:
            try:
                egg_in = EggsIn.objects.get(batch_id=obj)
                self.egg_in_detail = EggsInSerializers(egg_in).data
            except EggsIn.DoesNotExist:
                self.egg_in_detail = {}
                return None
        return self.egg_in_detail.get('egg_chatki', None)

    def get_egg_in_eggs(self, obj):
        if self.egg_in_detail is None:
            try:
                egg_in = EggsIn.objects.get(batch_id=obj)
                self.egg_in_detail = EggsInSerializers(egg_in).data
            except EggsIn.DoesNotExist:
                self.egg_in_detail = {}
                return None
        return self.egg_in_detail.get('egg_in', None)

    def get_egg_quality_loss(self, obj):
        if self.egg_quality_detail is None:
            try:
                egg_quality = EggQualityCheck.objects.get(batch=obj)
                self.egg_quality_detail = EggQualityCheckSerializer(egg_quality).data
            except EggQualityCheck.DoesNotExist:
                self.egg_quality_detail = {}
                return None
        return self.egg_quality_detail.get('egg_loss', None)

    def get_egg_quality_chatki(self, obj):
        if self.egg_quality_detail is None:
            try:
                egg_quality = EggQualityCheck.objects.get(batch=obj)
                self.egg_quality_detail = EggQualityCheckSerializer(egg_quality).data
            except EggQualityCheck.DoesNotExist:
                self.egg_quality_detail = {}
                return None
        return self.egg_quality_detail.get('egg_chatki', None)

    def get_egg_quality_eggs(self, obj):
        if self.egg_quality_detail is None:
            try:
                egg_quality = EggQualityCheck.objects.get(batch=obj)
                self.egg_quality_detail = EggQualityCheckSerializer(egg_quality).data
            except EggQualityCheck.DoesNotExist:
                self.egg_quality_detail = {}
                return None
        return self.egg_quality_detail.get('egg_count', None)

    def get_egg_cleaning_loss(self, obj):
        if self.egg_cleaning_detail is None:
            egg_cleaning_list = EggCleaning.objects.filter(batch_id=obj)
            total_loss = 0
            total_chatki = 0
            total_eggs = 0
            for egg_cleaning in egg_cleaning_list:
                total_loss = total_loss + egg_cleaning.egg_loss
                total_chatki = total_chatki + egg_cleaning.egg_chatki
                total_eggs = total_eggs + egg_cleaning.egg_count
            self.egg_cleaning_detail = {
                'egg_loss': total_loss,
                'egg_chatki': total_chatki,
                'egg_count': total_eggs
            }
        return self.egg_cleaning_detail.get('egg_loss', None)

    def get_egg_cleaning_chatki(self, obj):
        if self.egg_cleaning_detail is None:
            egg_cleaning_list = EggCleaning.objects.filter(batch_id=obj)
            total_loss = 0
            total_chatki = 0
            total_eggs = 0
            for egg_cleaning in egg_cleaning_list:
                total_loss = total_loss + egg_cleaning.egg_loss
                total_chatki = total_chatki + egg_cleaning.egg_chatki
                total_eggs = total_eggs + egg_cleaning.egg_count
            self.egg_cleaning_detail = {
                'egg_loss': total_loss,
                'egg_chatki': total_chatki,
                'egg_count': total_eggs
            }
        return self.egg_cleaning_detail.get('egg_chatki', None)

    def get_egg_cleaning_eggs(self, obj):
        if self.egg_cleaning_detail is None:
            egg_cleaning_list = EggCleaning.objects.filter(batch_id=obj)
            total_loss = 0
            total_chatki = 0
            total_eggs = 0
            for egg_cleaning in egg_cleaning_list:
                total_loss = total_loss + egg_cleaning.egg_loss
                total_chatki = total_chatki + egg_cleaning.egg_chatki
                total_eggs = total_eggs + egg_cleaning.egg_count
            self.egg_cleaning_detail = {
                'egg_loss': total_loss,
                'egg_chatki': total_chatki,
                'egg_count': total_eggs
            }
        return self.egg_cleaning_detail.get('egg_count', None)

    def get_egg_tray(self, obj):
        return obj.egg_count

    class Meta:
        model = BatchModel
        exclude = ('quality_param1', 'quality_param2', 'quality_param3', 'updated_by', 'created_at',
                   'batch_egg_image_url')


class BatchCreateRequestSerializer(serializers.Serializer):
    egg_type = serializers.ChoiceField(choices=EGG_TYPES)
    date = serializers.DateField(default=timezone.now().date())
    expected_egg_count = serializers.IntegerField(required=True)
    expected_egg_price = serializers.FloatField(required=True)


class BatchUpdateRequestSerializer(serializers.Serializer):
    egg_ph = serializers.FloatField(default=0)
    actual_egg_count = serializers.IntegerField(required=True)
    actual_egg_price = serializers.FloatField(required=True)
    batch_egg_image_url = serializers.CharField(required=True, max_length=200)

class BatchPerWarehouseSerializer(serializers.ModelSerializer):
    batch_id = serializers.SerializerMethodField()
    warehouse_name = serializers.SerializerMethodField()

    def get_batch_id(self, obj):
        return obj.batch.batch_id

    def get_warehouse_name(self, obj):
        return obj.warehouse.name

    class Meta:
        model = BatchPerWarehouse
        fields = '__all__'


class EggsInSerializers(serializers.ModelSerializer):
    procurement_id = serializers.SerializerMethodField()
    egg_type = serializers.SerializerMethodField

    def get_procurement_id(self, obj):
        if obj.batch:
            return obj.batch.procurement.id
        return None

    def get_egg_type(self, obj):
        if obj.batch:
            return obj.batch.egg_type

    class Meta:
        model = EggsIn
        fields = '__all__'


class EggQualityCheckSerializer(serializers.ModelSerializer):
    egg_type = serializers.SerializerMethodField()

    def get_egg_type(self, obj):
        return obj.batch.egg_type

    class Meta:
        model = EggQualityCheck
        fields = '__all__'


class EggCleaningSerializer(serializers.ModelSerializer):
    egg_type = serializers.SerializerMethodField()

    def get_egg_type(self, obj):
        return obj.batch_id.egg_type

    class Meta:
        model = EggCleaning
        fields = '__all__'


class PackageSerializer(serializers.ModelSerializer):
    egg_type = serializers.SerializerMethodField()
    sku_count = serializers.SerializerMethodField()

    def get_egg_type(self, obj):
        return obj.batch_id.egg_type

    def get_sku_count(self, obj):
        if obj.product:
            return obj.product.SKU_Count
        return None

    class Meta:
        model = Package
        fields = '__all__'


class ReturnedPackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReturnedPackage
        fields = '__all__'


class ImageUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImageUpload
        fields = '__all__'


class BatchListSerializer(serializers.ModelSerializer):
    class Meta:
        model = BatchModel
        fields = ('id', 'actual_egg_count', 'batch_egg_image_url', 'batch_id', 'egg_type')


class MoveToUnbrandedSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovetoUnbranded
        fields = '__all__'