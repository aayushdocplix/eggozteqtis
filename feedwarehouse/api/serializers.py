from rest_framework import serializers

from custom_auth.api.serializers import AddressSerializer
from custom_auth.models import Address
from farmer.api.serializers import FarmerSerializer
from feedwarehouse.models import FeedWarehouse, FeedProductSpecification, FeedProduct, ProductVendor, \
    FeedProductSubDivision, FeedProductDivision, FeedOrder, FeedOrderLine


class FeedWarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeedWarehouse
        fields = '__all__'


class FeedProductDivisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeedProductDivision
        fields = '__all__'


class FeedProductSubDivisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeedProductSubDivision
        fields = '__all__'


class ProductVendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVendor
        fields = '__all__'


class FeedProductSpecificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeedProductSpecification
        fields = '__all__'


class FeedProductSerializer(serializers.ModelSerializer):
    feedProductDivision = FeedProductDivisionSerializer()
    feedProductSubDivision = FeedProductSubDivisionSerializer()
    vendor = ProductVendorSerializer()
    feedProductSpecifications = serializers.SerializerMethodField()

    class Meta:
        model = FeedProduct
        fields = '__all__'

    def get_feedProductSpecifications(self, obj):
        feedProductSpecifications = obj.feedSpecificationProduct.all()
        return FeedProductSpecificationSerializer(feedProductSpecifications, many=True).data


class FeedProductOrderSerializer(serializers.ModelSerializer):
    feedProductDivision = FeedProductDivisionSerializer()
    feedProductSubDivision = FeedProductSubDivisionSerializer()
    vendor = ProductVendorSerializer()

    class Meta:
        model = FeedProduct
        fields = '__all__'


class FeedOrderLineSerializer(serializers.ModelSerializer):
    # feed_product = FeedProductSerializer()
    feed_product = FeedProductOrderSerializer()

    class Meta:
        model = FeedOrderLine
        fields = '__all__'



class FeedOrderSerializer(serializers.ModelSerializer):
    farmer = FarmerSerializer()
    shipping_address = AddressSerializer()
    feedOrderLines = serializers.SerializerMethodField()

    class Meta:
        model = FeedOrder
        fields = '__all__'

    def get_feedOrderLines(self, obj):
        feedOrderLines = obj.feed_order_lines.all()
        return FeedOrderLineSerializer(feedOrderLines, many=True).data


class FeedOrderCreateSerializer(serializers.ModelSerializer):
    shipping_address = serializers.PrimaryKeyRelatedField(queryset=Address.objects.all(),required=True)
    class Meta:
        model = FeedOrder
        fields = ('farm','farmer', 'order_price_amount','shipping_address')


class FeedOrderLineCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeedOrderLine
        fields = ('feed_product', 'quantity',)
