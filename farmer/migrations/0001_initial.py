# Generated by Django 3.1.2 on 2021-09-11 08:54

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import uuid_upload_path.storage


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('custom_auth', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CityNECCRate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('currency', models.CharField(default='INR', max_length=3)),
                ('current_rate', models.DecimalField(decimal_places=3, default=0, max_digits=12)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='DailyInput',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('egg_daily_production', models.PositiveIntegerField(default=0)),
                ('broken_egg_in_production', models.PositiveIntegerField(default=0)),
                ('broken_egg_in_operation', models.PositiveIntegerField(default=0)),
                ('mortality', models.PositiveIntegerField(default=0)),
                ('total_active_birds', models.PositiveIntegerField()),
                ('feed', models.DecimalField(decimal_places=3, default=0, help_text='in Kg', max_digits=12)),
                ('weight', models.DecimalField(decimal_places=3, default=0, help_text='in Kg', max_digits=12)),
                ('culls', models.PositiveIntegerField(default=0)),
                ('transferred_quantity', models.IntegerField(default=0)),
                ('remarks', models.CharField(blank=True, max_length=255, null=True)),
            ],
            options={
                'ordering': ('-date',),
            },
        ),
        migrations.CreateModel(
            name='Expenses',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('quantity', models.IntegerField(default=0)),
                ('amount', models.DecimalField(decimal_places=3, default=0, max_digits=12)),
                ('remark', models.CharField(blank=True, max_length=256, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Farm',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('farm_name', models.CharField(max_length=200)),
                ('billing_farm_address_same', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('number_of_layer_shed', models.IntegerField(default=0)),
                ('number_of_grower_shed', models.IntegerField(default=0)),
                ('number_of_broiler_shed', models.IntegerField(default=0)),
                ('farm_type', models.CharField(choices=[('Automatic', 'Automatic'), ('Manual', 'Manual')], default='Automatic', max_length=100)),
                ('farm_iot_id', models.CharField(default='non-iot', max_length=150)),
                ('farm_layer_type', models.CharField(choices=[('Layer', 'Layer'), ('Broiler', 'Broiler')], default='Layer', max_length=100)),
                ('is_feed_mixed', models.BooleanField(default=False)),
                ('feed_mix_photo_url', models.CharField(default='feed url', max_length=200, null=True)),
                ('feed_mix_remarks', models.CharField(default='feed', max_length=200)),
                ('is_fssai_license_present', models.BooleanField(default=False)),
                ('fssai_license_photo_url', models.CharField(default='license url', max_length=200, null=True)),
                ('fssai_license_no', models.CharField(default='fssai license', max_length=200)),
                ('is_fssai_verified', models.BooleanField(default=False)),
                ('is_vehicle_available', models.BooleanField(default=False)),
                ('vehicle_photo_url', models.CharField(default='vehicle url', max_length=200, null=True)),
                ('vehicle_no', models.CharField(blank=True, max_length=200, null=True)),
                ('GSTIN', models.CharField(default='GSTIN', max_length=200)),
                ('PAN_CARD', models.CharField(default='PanCard', max_length=200)),
                ('is_gst_verified', models.BooleanField(default=False)),
                ('is_pan_verified', models.BooleanField(default=False)),
                ('is_complete', models.BooleanField(default=False)),
                ('billing_address', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='billing_address', to='custom_auth.address')),
            ],
        ),
        migrations.CreateModel(
            name='Farmer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('farmer_iot_id', models.CharField(default='non-iot', max_length=150)),
                ('is_test_profile', models.BooleanField(default=False)),
                ('farmer', models.OneToOneField(on_delete=django.db.models.deletion.DO_NOTHING, related_name='farmer', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='FarmerAlert',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('heading', models.CharField(max_length=320, verbose_name='Heading')),
                ('description', models.TextField(default='desc', verbose_name='Description')),
                ('start_at', models.TimeField(db_index=True, default='00:00:00', verbose_name='Start Time')),
                ('end_at', models.TimeField(db_index=True, default='23:59:59', verbose_name='End Time')),
                ('is_shown', models.BooleanField(db_index=True, default=True, verbose_name='Shown to user')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='FarmerBanner',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('image', models.FileField(upload_to=uuid_upload_path.storage.upload_to)),
                ('publish_at', models.DateTimeField(db_index=True, default=django.utils.timezone.now, verbose_name='Publish Time')),
                ('expire_at', models.DateTimeField(blank=True, db_index=True, null=True, verbose_name='Expire Time')),
                ('is_shown', models.BooleanField(db_index=True, default=True, verbose_name='Shown to user')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='FarmerOrder',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('status', models.CharField(choices=[('draft', 'draft'), ('created', 'created'), ('confirmed', 'confirmed'), ('completed', 'completed'), ('packing', 'packing'), ('packed', 'packed'), ('on the way', 'on the way'), ('delivered', 'delivered'), ('closed', 'closed'), ('cancelled', 'cancelled'), ('open_purchase_order', 'open_po'), ('close_purchase_order', 'closed_po')], default='created', max_length=32)),
                ('farm', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='farm_orders', to='farmer.farm')),
            ],
        ),
        migrations.CreateModel(
            name='FeedFormulation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('name', models.CharField(default='formula name', max_length=200)),
                ('feed_quantity', models.DecimalField(decimal_places=4, default=0, help_text='in Kg', max_digits=15)),
                ('total_amount', models.DecimalField(decimal_places=4, default=0, help_text='in Rs', max_digits=15)),
                ('feed_rate_per_kg', models.DecimalField(decimal_places=4, default=0, help_text='in Rs', max_digits=15)),
            ],
        ),
        migrations.CreateModel(
            name='FeedIngredient',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('ingredient_type', models.CharField(choices=[('Ingredient', 'Ingredient'), ('Medicine', 'Medicine')], default='Ingredient', max_length=200)),
            ],
            options={
                'unique_together': {('name', 'ingredient_type')},
            },
        ),
        migrations.CreateModel(
            name='FeedMedicine',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('medicine_type', models.CharField(choices=[('Vaccine', 'Vaccine'), ('Misc', 'Misc')], default='Misc', max_length=200)),
            ],
            options={
                'unique_together': {('name', 'medicine_type')},
            },
        ),
        migrations.CreateModel(
            name='Flock',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('flock_name', models.CharField(max_length=200)),
                ('flock_id', models.CharField(max_length=200)),
                ('age', models.PositiveIntegerField(default=0, help_text='in days')),
                ('initial_capacity', models.PositiveIntegerField(default=0)),
                ('current_capacity', models.PositiveIntegerField(default=0)),
                ('last_daily_input_date', models.DateField(blank=True, null=True)),
                ('egg_type', models.CharField(blank=True, choices=[('White', 'White'), ('Brown', 'Brown'), ('Kadaknath', 'Kadaknath')], max_length=100, null=True)),
                ('initial_production', models.PositiveIntegerField(default=0)),
                ('total_production', models.PositiveIntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='FlockBreed',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('breed_name', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='NECCZone',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, unique=True)),
                ('desc', models.CharField(default='desc', max_length=254)),
            ],
        ),
        migrations.CreateModel(
            name='Party',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=256)),
            ],
        ),
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('heading', models.CharField(max_length=320, verbose_name='Heading')),
                ('description', models.TextField(verbose_name='Description')),
                ('publish_at', models.DateTimeField(db_index=True, default=django.utils.timezone.now, verbose_name='Publish Time')),
                ('expire_at', models.DateTimeField(blank=True, db_index=True, null=True, verbose_name='Expire Time')),
                ('is_shown', models.BooleanField(db_index=True, default=True, verbose_name='Shown to user')),
                ('is_rejected', models.BooleanField(db_index=True, default=False, verbose_name='Is Rejected')),
                ('is_pinned', models.BooleanField(db_index=True, default=False)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='posts', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Post',
                'verbose_name_plural': 'Posts',
                'ordering': ('-publish_at', 'heading'),
            },
        ),
        migrations.CreateModel(
            name='PostComment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('comment_text', models.TextField(verbose_name='Comment Text')),
                ('is_active', models.BooleanField(db_index=True, default=True)),
                ('is_pinned', models.BooleanField(db_index=True, default=False)),
                ('parent_comment', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='farmer.postcomment')),
                ('post', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='commented_posts', to='farmer.post')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='commented_posts', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Post commented by user',
                'verbose_name_plural': 'Post commented by users',
                'ordering': ('-created_at',),
            },
        ),
        migrations.CreateModel(
            name='TransferredBirdInput',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField(default=0)),
                ('transfer_at', models.DateTimeField(auto_now_add=True)),
                ('transfer_from', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='transferFrom', to='farmer.flock')),
                ('transfer_to', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='transferTo', to='farmer.flock')),
            ],
        ),
        migrations.CreateModel(
            name='Shed',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('shed_type', models.CharField(choices=[('Layer', 'Layer'), ('Grower', 'Grower'), ('Feed Shed', 'Feed Shed'), ('Broiler', 'Broiler')], max_length=100)),
                ('shed_name', models.CharField(max_length=200)),
                ('shed_iot_id', models.CharField(default='non-iot', max_length=150)),
                ('total_active_bird_capacity', models.PositiveIntegerField(default=0)),
                ('farm', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='shed_farms', to='farmer.farm')),
            ],
        ),
        migrations.CreateModel(
            name='PostLike',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('is_liked', models.BooleanField(db_index=True, default=True)),
                ('post', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='post_likes', to='farmer.post')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='post_likes', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Post Like',
                'verbose_name_plural': 'Post Like List',
                'ordering': ('-created_at',),
            },
        ),
        migrations.CreateModel(
            name='PostImage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('image', models.FileField(upload_to=uuid_upload_path.storage.upload_to)),
                ('image_order', models.PositiveIntegerField(default=0)),
                ('post', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='post_images', to='farmer.post')),
            ],
            options={
                'verbose_name': 'Post Image',
                'verbose_name_plural': 'Post Images',
                'ordering': ('-modified_at',),
            },
        ),
        migrations.CreateModel(
            name='PostCommentLike',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('is_liked', models.BooleanField(db_index=True, default=True)),
                ('post_comment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='liked_post_comments', to='farmer.postcomment')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='liked_post_comments', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('-created_at',),
            },
        ),
        migrations.CreateModel(
            name='NECCPriceStamp',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rate_value', models.DecimalField(decimal_places=3, default=0, max_digits=12)),
                ('start_date', models.DateTimeField(blank=True, null=True)),
                ('end_date', models.DateTimeField(blank=True, null=True)),
                ('city_necc_rate', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='farmer.cityneccrate')),
            ],
        ),
        migrations.CreateModel(
            name='NECCCity',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, unique=True)),
                ('desc', models.CharField(default='desc', max_length=254)),
                ('zone', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='necczonecity', to='farmer.necczone')),
            ],
        ),
        migrations.CreateModel(
            name='MedicineInput',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.DecimalField(decimal_places=3, default=0, help_text='in ltr', max_digits=12)),
                ('dailyInput', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='medicine_inputs', to='farmer.dailyinput')),
                ('feedMedicine', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='medicine_inputs', to='farmer.feedmedicine')),
            ],
        ),
        migrations.CreateModel(
            name='FlockFeedFormulation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('feed_formulation', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='feed_formulation_flock', to='farmer.feedformulation')),
                ('flock', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='formulation_flock', to='farmer.flock')),
            ],
        ),
        migrations.AddField(
            model_name='flock',
            name='breed',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='flock_breeds', to='farmer.flockbreed'),
        ),
        migrations.AddField(
            model_name='flock',
            name='shed',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='flock_sheds', to='farmer.shed'),
        ),
        migrations.CreateModel(
            name='FeedIngredientFormulaData',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rate_per_unit', models.DecimalField(decimal_places=4, default=0, help_text='rate per kg or litre', max_digits=15)),
                ('quantity', models.DecimalField(decimal_places=4, default=0, help_text='in Kg', max_digits=15)),
                ('amount', models.DecimalField(decimal_places=4, default=0, help_text='in Rs', max_digits=15)),
                ('feed_formulation', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='formulation', to='farmer.feedformulation')),
                ('ingredient', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='ingredient', to='farmer.feedingredient')),
            ],
        ),
        migrations.CreateModel(
            name='FarmerOrderInLine',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('egg_type', models.CharField(choices=[('White', 'White'), ('Brown', 'Brown'), ('Kadaknath', 'kadaknath')], max_length=100)),
                ('quantity', models.IntegerField(default=0)),
                ('farmerOrder', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='farmerOrderInlines', to='farmer.farmerorder')),
            ],
        ),
        migrations.CreateModel(
            name='FarmerBankDetails',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('benificiary_name', models.CharField(max_length=200)),
                ('account_number', models.BigIntegerField()),
                ('repeat_account_number', models.BigIntegerField()),
                ('ifsc_code', models.CharField(max_length=200)),
                ('farmer', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='farmer_bank', to='farmer.farmer')),
            ],
        ),
        migrations.AddField(
            model_name='farmer',
            name='necc_zone',
            field=models.ForeignKey(blank=True, default=1, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='necczonefarmer', to='farmer.necczone'),
        ),
        migrations.AddField(
            model_name='farm',
            name='farmer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='farmer_farm', to='farmer.farmer'),
        ),
        migrations.AddField(
            model_name='farm',
            name='necc_zone',
            field=models.ForeignKey(blank=True, default=1, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='necczonefarm', to='farmer.necczone'),
        ),
        migrations.AddField(
            model_name='farm',
            name='shipping_address',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='shipping_address', to='custom_auth.address'),
        ),
    ]