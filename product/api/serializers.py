from rest_framework import serializers

from product.models import Product, ProductDivision, BaseProduct, ProductInline, ProductSubDivision, ProductBenefit, \
    ProductDescription, ProductLongDescription, ProductSpecification, ProductInformationLine, ProductInformation


class ProductDivisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductDivision
        fields = '__all__'


class ProductSubDivisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSubDivision
        fields = '__all__'


class ProductBenefitSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductBenefit
        fields = '__all__'


class ProductDescriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductDescription
        fields = '__all__'


class ProductLongDescriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductLongDescription
        fields = '__all__'


class ProductSpecificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSpecification
        fields = '__all__'


class ProductInformationLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductInformationLine
        fields = '__all__'


class ProductInformationSerializer(serializers.ModelSerializer):
    productInformationLine = serializers.SerializerMethodField()

    class Meta:
        model = ProductInformation
        fields = '__all__'

    def get_productInformationLine(self,obj):
        informationLines = obj.inlineInformationProduct.all()
        return ProductInformationLineSerializer(informationLines, many=True).data


class ProductInlineSerializer(serializers.ModelSerializer):
    baseProduct_name = serializers.SerializerMethodField()
    class Meta:
        model = ProductInline
        fields = ('name', 'baseProduct', 'baseProduct_name', 'quantity')

    def get_baseProduct_name(self, obj):
        return obj.baseProduct.name


class ProductSerializer(serializers.ModelSerializer):
    productInlines = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = '__all__'

    def get_productInlines(self, obj):
        productInlines = obj.inlineProduct.all()
        return ProductInlineSerializer(productInlines, many=True).data


class ProductShortSerializer(serializers.ModelSerializer):

    class Meta:
        model = Product
        fields = ('id', 'SKU_Count', 'name', 'description','brand_type', 'productSubDivision', 'current_price')


class ProductMarginSerializer(serializers.ModelSerializer):

    class Meta:
        model = Product
        fields = ('id', 'SKU_Count', 'name')


class EcommerceProductSerializer(serializers.ModelSerializer):
    productDescriptions = serializers.SerializerMethodField()
    productBenefits = serializers.SerializerMethodField()
    productInlines = serializers.SerializerMethodField()
    productLongDescriptions = serializers.SerializerMethodField()
    productSpecifications = serializers.SerializerMethodField()
    productInformations = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = '__all__'

    def get_productDescriptions(self, obj):
        productDescriptions = obj.descriptionProduct.all()
        return ProductDescriptionSerializer(productDescriptions, many=True).data

    def get_productBenefits(self, obj):
        productBenefits = obj.benefitProduct.all()
        return ProductBenefitSerializer(productBenefits, many=True).data

    def get_productInlines(self, obj):
        productInlines = obj.inlineProduct.all()
        return ProductInlineSerializer(productInlines, many=True).data

    def get_productLongDescriptions(self, obj):
        productLongDescriptions = obj.longDescriptionProduct.all()
        return ProductLongDescriptionSerializer(productLongDescriptions, many=True).data

    def get_productSpecifications(self, obj):
        productSpecifications = obj.specificationProduct.all()
        return ProductSpecificationSerializer(productSpecifications, many=True).data

    def get_productInformations(self, obj):
        productInformations = obj.informationProduct.all()
        return ProductInformationSerializer(productInformations, many=True).data

class BaseProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = BaseProduct
        fields = '__all__'



