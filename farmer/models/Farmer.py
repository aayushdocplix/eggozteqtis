from django.db import models

from Eggoz import settings
from base.models.Cluster import TimeStampedModel

from order.statuses import OrderStatus
from supplychain.models import SupplyPersonProfile
from product.models import ProductDivision, ProductSubDivision
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from uuid_upload_path import upload_to


class Farmer(models.Model):
    farmer = models.OneToOneField('custom_auth.User', on_delete=models.DO_NOTHING, related_name="farmer")
    necc_zone = models.ForeignKey('farmer.NECCZone', on_delete=models.DO_NOTHING, related_name="necczonefarmer",
                                  null=True,
                                  blank=True, default=1)
    farmer_iot_id = models.CharField(max_length=150, default="non-iot")
    is_test_profile = models.BooleanField(default=False)

    def __str__(self):
        return self.farmer.name


class Farm(models.Model):
    farm_name = models.CharField(max_length=200)
    farmer = models.ForeignKey(Farmer, on_delete=models.DO_NOTHING, blank=True, null=True, related_name="farmer_farm")
    necc_zone = models.ForeignKey('farmer.NECCZone', on_delete=models.DO_NOTHING, related_name="necczonefarm",
                                  null=True,
                                  blank=True, default=1)
    shipping_address = models.ForeignKey('custom_auth.Address', null=True, blank=True, on_delete=models.DO_NOTHING,
                                         related_name='shipping_address')
    billing_address = models.ForeignKey('custom_auth.Address', null=True, blank=True, on_delete=models.DO_NOTHING,
                                        related_name='billing_address')
    billing_farm_address_same = models.BooleanField(default=False)
    supplyPerson = models.ForeignKey(SupplyPersonProfile, on_delete=models.CASCADE, null=True, blank=True,
                                     related_name="supply_manager")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    number_of_layer_shed = models.IntegerField(default=0)
    number_of_grower_shed = models.IntegerField(default=0)
    number_of_broiler_shed = models.IntegerField(default=0)
    FARM_TYPES = (('Automatic', 'Automatic'), ('Manual', 'Manual'))
    farm_type = models.CharField(max_length=100, choices=FARM_TYPES, default="Automatic")
    farm_iot_id = models.CharField(max_length=150, default="non-iot")
    FARM_LAYER_TYPES = (('Layer', 'Layer'), ('Broiler', 'Broiler'))
    farm_layer_type = models.CharField(max_length=100, choices=FARM_LAYER_TYPES, default="Layer")

    is_feed_mixed = models.BooleanField(default=False)
    feed_mix_photo_url = models.CharField(max_length=200, default="feed url", null=True)
    feed_mix_remarks = models.CharField(max_length=200, default="feed")

    is_fssai_license_present = models.BooleanField(default=False)
    fssai_license_photo_url = models.CharField(max_length=200, default="license url", null=True)
    fssai_license_no = models.CharField(max_length=200, default="fssai license")
    is_fssai_verified = models.BooleanField(default=False)

    is_vehicle_available = models.BooleanField(default=False)
    vehicle_photo_url = models.CharField(max_length=200, default="vehicle url", null=True)
    vehicle_no = models.CharField(max_length=200, null=True, blank=True)

    GSTIN = models.CharField(max_length=200, default="GSTIN")
    PAN_CARD = models.CharField(max_length=200, default="PanCard")

    is_gst_verified = models.BooleanField(default=False)
    is_pan_verified = models.BooleanField(default=False)

    is_complete = models.BooleanField(default=False)

    def __str__(self):
        return str(self.farm_name)


class Shed(models.Model):
    SHED_TYPES = (('Layer', 'Layer'), ('Grower', 'Grower'), ('Feed Shed', 'Feed Shed'), ('Broiler', 'Broiler'))
    shed_type = models.CharField(choices=SHED_TYPES, max_length=100)
    shed_name = models.CharField(max_length=200)
    farm = models.ForeignKey(Farm, on_delete=models.DO_NOTHING,
                             related_name="shed_farms")
    shed_iot_id = models.CharField(max_length=150, default="non-iot")
    total_active_bird_capacity = models.PositiveIntegerField(default=0)

    def __str__(self):
        return str(self.farm.farm_name)


class FlockBreed(models.Model):
    breed_name = models.CharField(max_length=200)

    def __str__(self):
        return self.breed_name


class Flock(models.Model):
    flock_name = models.CharField(max_length=200)
    flock_id = models.CharField(max_length=200)
    shed = models.ForeignKey(Shed, on_delete=models.DO_NOTHING,
                             related_name="flock_sheds")
    breed = models.ForeignKey(FlockBreed, on_delete=models.DO_NOTHING, null=True, blank=True,
                              related_name="flock_breeds")
    age = models.PositiveIntegerField(default=0, help_text="in days")
    initial_capacity = models.PositiveIntegerField(default=0)
    current_capacity = models.PositiveIntegerField(default=0)
    last_daily_input_date = models.DateField(null=True, blank=True)
    EGGS_TYPES = (('White', 'White'), ('Brown', 'Brown'), ('Kadaknath', 'Kadaknath'))
    egg_type = models.CharField(max_length=100, choices=EGGS_TYPES, null=True, blank=True)
    initial_production = models.PositiveIntegerField(default=0)
    total_production = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.flock_name


class TransferredBirdInput(models.Model):
    quantity = models.PositiveIntegerField(default=0)
    transfer_from = models.ForeignKey(Flock, on_delete=models.DO_NOTHING, related_name="transferFrom")
    transfer_to = models.ForeignKey(Flock, on_delete=models.DO_NOTHING, related_name="transferTo")
    transfer_at = models.DateTimeField(auto_now_add=True)


class DailyInput(models.Model):
    flock = models.ForeignKey(Flock, on_delete=models.DO_NOTHING, related_name="dailyinputs")
    date = models.DateField()
    egg_daily_production = models.PositiveIntegerField(default=0)
    broken_egg_in_production = models.PositiveIntegerField(default=0)
    broken_egg_in_operation = models.PositiveIntegerField(default=0)
    mortality = models.PositiveIntegerField(default=0)
    total_active_birds = models.PositiveIntegerField()
    feed = models.DecimalField(default=0, help_text='in Kg', max_digits=settings.DEFAULT_MAX_DIGITS,
                               decimal_places=settings.DEFAULT_DECIMAL_PLACES, )
    weight = models.DecimalField(default=0, help_text='in Kg', max_digits=settings.DEFAULT_MAX_DIGITS,
                                 decimal_places=settings.DEFAULT_DECIMAL_PLACES, )
    culls = models.PositiveIntegerField(default=0)
    transferred_quantity = models.IntegerField(default=0)
    transferred_input = models.ForeignKey(TransferredBirdInput, on_delete=models.DO_NOTHING,
                                          related_name="transferredInput", null=True, blank=True)
    remarks = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return str(self.flock.flock_name)

    class Meta:
        unique_together = ['flock', 'date']
        ordering = ('-date',)


class FeedMedicine(models.Model):
    name = models.CharField(max_length=200)
    TYPES = (('Vaccine', 'Vaccine'),
             ('Misc', 'Misc'))
    medicine_type = models.CharField(max_length=200, choices=TYPES, default='Misc')

    def __str__(self):
        return self.name

    class Meta:
        unique_together = ['name', 'medicine_type']


class FeedIngredient(models.Model):
    name = models.CharField(max_length=200)
    TYPES = (('Ingredient', 'Ingredient'),
             ('Medicine', 'Medicine'))
    ingredient_type = models.CharField(max_length=200, choices=TYPES, default='Ingredient')

    def __str__(self):
        return self.name

    class Meta:
        unique_together = ['name', 'ingredient_type']


class FeedFormulation(models.Model):
    date = models.DateField()
    name = models.CharField(max_length=200, default="formula name")
    feed_quantity = models.DecimalField(default=0, decimal_places=4, max_digits=15, help_text="in Kg")
    total_amount = models.DecimalField(default=0, decimal_places=4, max_digits=15, help_text="in Rs")
    feed_rate_per_kg = models.DecimalField(default=0, decimal_places=4, max_digits=15, help_text="in Rs")


class FeedIngredientFormulaData(models.Model):
    ingredient = models.ForeignKey(FeedIngredient, on_delete=models.CASCADE, null=True, blank=True,
                                   related_name="ingredient")
    feed_formulation = models.ForeignKey(FeedFormulation, on_delete=models.CASCADE, null=True, blank=True,
                                         related_name="formulation")
    rate_per_unit = models.DecimalField(default=0, decimal_places=4, max_digits=15, help_text="rate per kg or litre")
    quantity = models.DecimalField(default=0, decimal_places=4, max_digits=15, help_text="in Kg")
    amount = models.DecimalField(default=0, decimal_places=4, max_digits=15, help_text="in Rs")


class FlockFeedFormulation(models.Model):
    feed_formulation = models.ForeignKey(FeedFormulation, on_delete=models.CASCADE, null=True, blank=True,
                                         related_name="feed_formulation_flock")
    flock = models.ForeignKey(Flock, on_delete=models.CASCADE, null=True, blank=True,
                              related_name="formulation_flock")
    date = models.DateField()


class MedicineInput(models.Model):
    dailyInput = models.ForeignKey(DailyInput, on_delete=models.DO_NOTHING, related_name="medicine_inputs")
    feedMedicine = models.ForeignKey(FeedMedicine, on_delete=models.DO_NOTHING, related_name="medicine_inputs")
    quantity = models.DecimalField(default=0, help_text='in ltr', max_digits=settings.DEFAULT_MAX_DIGITS,
                                   decimal_places=settings.DEFAULT_DECIMAL_PLACES, )


class FarmerBankDetails(models.Model):
    farmer = models.ForeignKey(Farmer, on_delete=models.DO_NOTHING, blank=True, null=True, related_name="farmer_bank")
    benificiary_name = models.CharField(max_length=200)
    account_number = models.BigIntegerField()
    repeat_account_number = models.BigIntegerField()
    ifsc_code = models.CharField(max_length=200)

    def __str__(self):
        return str(self.farmer.farmer.name)


class FarmerOrder(models.Model):
    farm = models.ForeignKey(Farm, on_delete=models.DO_NOTHING, related_name='farm_orders')
    date = models.DateField()
    status = models.CharField(
        max_length=32, default=OrderStatus.CREATED, choices=OrderStatus.CHOICES
    )


class FarmerOrderInLine(models.Model):
    farmerOrder = models.ForeignKey(FarmerOrder, on_delete=models.DO_NOTHING, related_name='farmerOrderInlines')
    EGG_TYPES = (('White', 'White'), ('Brown', 'Brown'), ('Kadaknath', 'kadaknath'))
    egg_type = models.CharField(max_length=100, choices=EGG_TYPES)
    quantity = models.IntegerField(default=0)

    class Meta:
        unique_together = ['farmerOrder', 'egg_type']


class Party(models.Model):
    name = models.CharField(max_length=256)


class Expenses(models.Model):
    farmer = models.ForeignKey(Farmer, on_delete=models.DO_NOTHING, related_name='farmer_expenses')
    party = models.ForeignKey(Party, on_delete=models.DO_NOTHING, related_name='farmer_expenses')
    productSubDivision = models.ForeignKey(ProductSubDivision, on_delete=models.DO_NOTHING,
                                           related_name='farmer_expenses')
    date = models.DateField()
    quantity = models.IntegerField(default=0)
    amount = models.DecimalField(default=0, max_digits=settings.DEFAULT_MAX_DIGITS,
                                 decimal_places=settings.DEFAULT_DECIMAL_PLACES, )
    remark = models.CharField(max_length=256, null=True, blank=True)


class Post(TimeStampedModel):
    heading = models.CharField(_('Heading'), max_length=320)
    description = models.TextField(_('Description'))
    author = models.ForeignKey('custom_auth.User',
                               on_delete=models.CASCADE,
                               related_name='posts')
    publish_at = models.DateTimeField(_('Publish Time'), default=timezone.now, db_index=True)
    expire_at = models.DateTimeField(_('Expire Time'), null=True, blank=True, db_index=True)
    is_shown = models.BooleanField(_('Shown to user'), default=True, db_index=True)
    is_rejected = models.BooleanField(_('Is Rejected'), default=False, db_index=True)
    is_pinned = models.BooleanField(default=False, db_index=True)

    def __str__(self):
        return "%s - %s" % (self.is_shown, self.heading)

    class Meta:
        ordering = ('-publish_at', 'heading')
        verbose_name = _('Post')
        verbose_name_plural = _('Posts')


class PostImage(TimeStampedModel):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='post_images')
    image = models.FileField(upload_to=upload_to)
    image_order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.post.heading

    class Meta:
        ordering = ('-modified_at',)
        verbose_name = _('Post Image')
        verbose_name_plural = _('Post Images')


class PostLike(TimeStampedModel):
    user = models.ForeignKey('custom_auth.User', on_delete=models.CASCADE, related_name='post_likes')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='post_likes')
    is_liked = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ('-created_at',)
        unique_together = ('user', 'post')
        verbose_name = _('Post Like')
        verbose_name_plural = _('Post Like List')

    def __str__(self):
        return str(self.id)


class PostComment(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='commented_posts')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='commented_posts')
    comment_text = models.TextField(_('Comment Text'))
    is_active = models.BooleanField(default=True, db_index=True)
    is_pinned = models.BooleanField(default=False, db_index=True)
    parent_comment = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        ordering = ('-created_at',)
        verbose_name = _('Post commented by user')
        verbose_name_plural = _('Post commented by users')

    def __str__(self):
        return '{} - {}'.format(self.user, self.post)


class PostCommentLike(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='liked_post_comments')
    post_comment = models.ForeignKey(PostComment, on_delete=models.CASCADE, related_name='liked_post_comments')
    is_liked = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ('-created_at',)
        unique_together = ('user', 'post_comment')

    def __str__(self):
        return '{} - {}'.format(self.user, self.post_comment)


class FarmerBanner(TimeStampedModel):
    image = models.FileField(upload_to=upload_to)
    publish_at = models.DateTimeField(_('Publish Time'), default=timezone.now, db_index=True)
    expire_at = models.DateTimeField(_('Expire Time'), null=True, blank=True, db_index=True)
    is_shown = models.BooleanField(_('Shown to user'), default=True, db_index=True)


class FarmerAlert(TimeStampedModel):
    heading = models.CharField(_('Heading'), max_length=320)
    description = models.TextField(_('Description'), default='desc')
    start_at = models.TimeField(_('Start Time'), default='00:00:00', db_index=True)
    end_at = models.TimeField(_('End Time'), default='23:59:59', db_index=True)
    is_shown = models.BooleanField(_('Shown to user'), default=True, db_index=True)
