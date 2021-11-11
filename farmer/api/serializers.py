from django.db.models import Q
from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers
from datetime import datetime,timedelta

from Eggoz.settings import CURRENT_ZONE
from custom_auth.api.serializers import UserMediumSerializer, UserShortSerializer, AddressUpdateSerializer, \
    AddressCreationSerializer, AddressSerializer
from custom_auth.models import User, Address
from farmer.models import NECCCity, CityNECCRate, NECCZone
from farmer.models.Farmer import Farmer, Farm, Shed, FlockBreed, Flock, DailyInput, FeedMedicine, MedicineInput, \
    FarmerOrder, FarmerOrderInLine, Party, Expenses, Post, PostImage, PostLike, PostComment, PostCommentLike, \
    FarmerBanner, FarmerAlert, FeedIngredient, FeedFormulation, FeedIngredientFormulaData, FlockFeedFormulation


class FarmerSerializer(serializers.ModelSerializer):
    farmer = UserMediumSerializer()

    class Meta:
        model = Farmer
        fields = '__all__'


class FarmerCreateSerializer(serializers.Serializer):
    farmer = serializers.PrimaryKeyRelatedField(required=True, queryset=User.objects.all())
    farmer_name = serializers.CharField(required=True, max_length=100)
    phone_no = PhoneNumberField(required=False)
    pinCode = serializers.IntegerField(required=False)
    email = serializers.EmailField(required=False)
    necc_zone = serializers.PrimaryKeyRelatedField(required=False,queryset=NECCZone.objects.all())


class FarmSerializer(serializers.ModelSerializer):
    sheds = serializers.SerializerMethodField()
    farmer = FarmerSerializer()
    shipping_address = AddressSerializer(read_only=True)
    billing_address = AddressSerializer(read_only=True)

    class Meta:
        model = Farm
        fields = '__all__'

    def get_sheds(self, obj):
        shed_farms = obj.shed_farms.all()
        return ShedSerializer(shed_farms, many=True).data


class FarmCreateSerializer(serializers.ModelSerializer):
    farmer = serializers.PrimaryKeyRelatedField(required=True, queryset=Farmer.objects.all())

    class Meta:
        model = Farm
        fields = ('farm_name', 'farmer', 'number_of_layer_shed', 'number_of_grower_shed','number_of_broiler_shed','farm_layer_type')


class ShedCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shed
        fields = '__all__'


class ShedSerializer(serializers.ModelSerializer):
    flocks = serializers.SerializerMethodField()

    class Meta:
        model = Shed
        fields = '__all__'

    def get_flocks(self, obj):
        flock_sheds = obj.flock_sheds.all()
        return FlockSerializer(flock_sheds, many=True).data


class FlockBreedSerializer(serializers.ModelSerializer):
    class Meta:
        model = FlockBreed
        fields = '__all__'


class FlockCreateSerializer(serializers.ModelSerializer):
    shed = serializers.PrimaryKeyRelatedField(required=False, queryset=Shed.objects.all())

    class Meta:
        model = Flock
        fields = ('shed', 'flock_name', 'breed', 'age', 'initial_capacity', 'initial_production', 'egg_type')


class DailyInputSerializer(serializers.ModelSerializer):
    transferred_from_flock = serializers.IntegerField(required=False)
    class Meta:
        model = DailyInput
        fields = ('id','flock', 'date', 'egg_daily_production', 'mortality', 'feed', 'weight', 'culls',
                  'total_active_birds', 'transferred_quantity', 'transferred_from_flock',
                  'broken_egg_in_production', 'broken_egg_in_operation', 'remarks')
        read_only_fields = ('total_active_birds',)


class FlockSerializer(serializers.ModelSerializer):
    breed = FlockBreedSerializer()
    daily_inputs = serializers.SerializerMethodField()

    class Meta:
        model = Flock
        fields = '__all__'

    def get_daily_inputs(self, obj):
        # time_difference = datetime.now(tz=CURRENT_ZONE).date() - timedelta(days=6)
        daily_inputs = obj.dailyinputs.all()
        return DailyInputSerializer(daily_inputs, many=True).data


class FeedMedicineSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeedMedicine
        fields = '__all__'


class FeedIngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeedIngredient
        fields = '__all__'


class FeedFormulationSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeedFormulation
        fields = '__all__'


class FeedIngredientFormulaDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeedIngredientFormulaData
        fields = '__all__'


class FlockFeedFormulationSerializer(serializers.ModelSerializer):
    class Meta:
        model = FlockFeedFormulation
        fields = '__all__'


class MedicineInputCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicineInput
        fields = ('feedMedicine', 'quantity')


class FarmerOrderInLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = FarmerOrderInLine
        fields = '__all__'


class FarmerOrderSerializer(serializers.ModelSerializer):
    farmerOrderInLines = serializers.SerializerMethodField()

    class Meta:
        model = FarmerOrder
        fields = '__all__'

    def get_farmerOrderInLines(self, obj):
        farmerOrderInLines = obj.farmerOrderInlines.all()
        return FarmerOrderInLineSerializer(farmerOrderInLines, many=True).data


class FarmerOrderCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FarmerOrder
        fields = ('farm', 'date')


class FarmerOrderInLineCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FarmerOrderInLine
        fields = ('egg_type', 'quantity',)


class PartySerializer(serializers.ModelSerializer):
    class Meta:
        model = Party
        fields = '__all__'


class ExpensesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expenses
        fields = '__all__'


class InlinePostImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostImage
        fields = ('id', 'image', 'image_order')


class PostSerializer(serializers.ModelSerializer):
    author = UserShortSerializer()
    images = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    stats = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = (
        'id', 'heading', 'description', 'author', 'publish_at', 'expire_at', 'is_pinned', 'images', 'is_liked', 'stats','created_at','modified_at')

    def get_images(self, obj):
        images = obj.post_images.all().order_by('image_order')
        return InlinePostImageSerializer(images, many=True, context=self.context).data

    def get_user(self):
        user = None
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user
        return user

    def get_is_liked(self, obj):
        user = self.get_user()
        if user is None or user.is_anonymous:
            return False
        post_like = PostLike.objects.filter(user=user, post=obj).first()
        if post_like:
            return post_like.is_liked
        return False

    def get_stats(self, obj):
        stats = {}
        stats['likes'] = obj.post_likes.all().count()
        stats['comments'] = obj.commented_posts.filter(Q(parent_comment__isnull=True)).count()
        return stats


class PostCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ('heading', 'description')


class PostImageValidationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostImage
        fields = ('image',)


class PostLikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostLike
        fields = ('post',)


class PostCommentSerializer(serializers.ModelSerializer):
    is_liked = serializers.SerializerMethodField()
    stats = serializers.SerializerMethodField()
    user = UserShortSerializer()

    class Meta:
        model = PostComment
        fields = '__all__'

    def get_user(self):
        user = None
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user
        return user

    def get_is_liked(self, obj):
        user = self.get_user()
        if user is None or user.is_anonymous:
            return False
        post_comment_like = PostCommentLike.objects.filter(user=user, post_comment=obj).first()
        if post_comment_like:
            return post_comment_like.is_liked
        return False

    def get_stats(self, obj):
        stats = {}
        stats['likes'] = obj.liked_post_comments.all().count()
        stats['comments'] = PostComment.objects.filter(parent_comment=obj).count()
        return stats


class PostCommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostComment
        fields = ('post', 'comment_text', 'is_pinned', 'parent_comment')


class PostCommentLikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostCommentLike
        fields = ('post_comment',)


class NECCCitySerializer(serializers.ModelSerializer):
    class Meta:
        model = NECCCity
        fields = '__all__'


class CityNECCRateSerializer(serializers.ModelSerializer):
    necc_city = NECCCitySerializer()

    class Meta:
        model = CityNECCRate
        fields = '__all__'


class FarmUpdateSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(required=True, queryset=Farm.objects.all())
    shipping_address = serializers.JSONField(required=False)
    billing_address = serializers.JSONField(required=False)
    farm_name = serializers.CharField(required=False)

    class Meta:
        model = Farm
        fields = ('id', 'farm_name', 'shipping_address', 'billing_address', 'billing_farm_address_same')

    def validate(self, data):
        print(data)
        farm_obj = data.get('id')
        shipping_address = data.get('shipping_address', None)
        if shipping_address:
            shipping_address_id = shipping_address.get('shipping_address_id', None)
            if farm_obj.shipping_address:
                if shipping_address_id is None:
                    raise serializers.ValidationError("shipping_address_id required")
                if not farm_obj.shipping_address.id == shipping_address_id:
                    raise serializers.ValidationError("shipping_address_id invalid")
            shipping_address_update_serializer = AddressUpdateSerializer(data=shipping_address)
            shipping_address_update_serializer.is_valid(raise_exception=True)

        billing_address = data.get('billing_address', None)
        if billing_address:
            billing_address_update_serializer = AddressUpdateSerializer(data=billing_address)
            billing_address_update_serializer.is_valid(raise_exception=True)
        return data

    def farm_update(self, instance, data):
        farm_name = data.get('farm_name', instance.farm_name)
        instance.farm_name = farm_name
        shipping_address_instance = instance.shipping_address
        shipping_address = data.get('shipping_address', None)
        if shipping_address:
            shipping_address_obj = Address.objects.filter(id=shipping_address.get('shipping_address_id')).first()
            shipping_address_update_serializer = AddressUpdateSerializer(data=shipping_address)
            shipping_address_update_serializer.is_valid(raise_exception=True)
            shipping_address_instance = shipping_address_update_serializer.update(shipping_address_obj,
                                                                                  shipping_address_update_serializer.validated_data)

        billing_shipping_address_same = data.get('billing_farm_address_same', None)
        if billing_shipping_address_same:
            instance.billing_address = shipping_address_instance
        else:
            billing_address = data.get('billing_address', None)
            if billing_address:
                if billing_address.get('billing_address_id'):
                    billing_address_obj = Address.objects.filter(id=billing_address.get('billing_address_id')).first()
                    billing_address_update_serializer = AddressUpdateSerializer(data=billing_address)
                    billing_address_update_serializer.is_valid(raise_exception=True)
                    billing_address_instance = billing_address_update_serializer.update(billing_address_obj, billing_address_update_serializer.validated_data)
                else:
                    billing_address_update_serializer = AddressCreationSerializer(data=billing_address)
                    billing_address_update_serializer.is_valid(raise_exception=True)
                    instance.billing_address = billing_address_update_serializer.save()
        instance.save()
        return instance


class FarmerBannerSerializer(serializers.ModelSerializer):

    class Meta:
        model = FarmerBanner
        fields = '__all__'


class FarmerAlertSerializer(serializers.ModelSerializer):

    class Meta:
        model = FarmerAlert
        fields = '__all__'


class NECCZoneSerializer(serializers.ModelSerializer):

    class Meta:
        model = NECCZone
        fields = '__all__'
