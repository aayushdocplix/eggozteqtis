from datetime import datetime
from typing import Union

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    Permission,
    PermissionsMixin, _user_has_perm,
)
from django.db import models
from django.db.models import Q, QuerySet
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField

from Eggoz.settings import CURRENT_ZONE
from base.models.ModelWithMetaData import ModelWithMetadata
from base.permissions import AccountPermissions, get_permissions, BasePermissionEnum
from distributionchain.models import DistributionPersonProfile
from finance.models import FinanceProfile
from operationschain.models import OperationsPersonProfile
from saleschain.models import SalesPersonProfile
from supplychain.models import SupplyPersonProfile
from warehouse.models import WarehousePersonProfile, Warehouse
from .Department import Department
from .UserProfile import UserProfile, UserData


class UserManager(BaseUserManager):

    def _create_user(self, name, email, password, is_staff, is_active, is_superuser, phone_no, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')
        now = datetime.now(tz=CURRENT_ZONE)
        email = self.normalize_email(email)
        user = self.model(
            name=name,
            email=email,
            phone_no=phone_no,
            is_staff=is_staff,
            is_active=is_active,
            is_superuser=is_superuser,
            last_login=now,
            date_joined=now,
            **extra_fields
        )
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, name=None, email=None, password=None, phone_no=None, **extra_fields):
        return self._create_user(name, email, password, False, True, False, phone_no, **extra_fields)

    def create_superuser(self, email, password, phone_no, **extra_fields):
        user = self._create_user("Admin", email, password, True, True, True, phone_no, **extra_fields)
        user.save(using=self._db)
        return user

    def customers(self):
        return self.get_queryset().filter(
            Q(is_staff=False) | (Q(is_staff=True) & Q(orders__isnull=False))
        )

    def staff(self):
        return self.get_queryset().filter(is_staff=True)

    class Meta:
        ordering = ("email",)
        permissions = (
            (AccountPermissions.MANAGE_RETAILERS.codename, "Manage retailers."),
            (AccountPermissions.MANAGE_FARMER.codename, "Manage farmer."),
            (AccountPermissions.MANAGE_SALES.codename, "Manage sales."),
            (AccountPermissions.MANAGE_SUPPLY.codename, "Manage supply."),
            (AccountPermissions.MANAGE_OPERATIONS.codename, "Manage operations."),
            (AccountPermissions.MANAGE_CUSTOMERS.codename, "Manage customers."),
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._effective_permissions = None

    # def get_by_natural_key(self, email):
    #     return self.get(email=email)

    @property
    def effective_permissions(self) -> "QuerySet[Permission]":
        if self._effective_permissions is None:
            self._effective_permissions = get_permissions()
            if not self.is_superuser:
                self._effective_permissions = self._effective_permissions.filter(
                    Q(user=self) | Q(group__user=self)
                )
        return self._effective_permissions

    @effective_permissions.setter
    def effective_permissions(self, value: "QuerySet[Permission]"):
        self._effective_permissions = value
        # Drop cache for authentication backend
        self._effective_permissions_cache = None

    def get_short_name(self):
        return self.email

    def has_perm(self, perm: Union[BasePermissionEnum, str], obj=None):  # type: ignore
        # This method is overridden to accept perm as BasePermissionEnum
        perm = perm.value if hasattr(perm, "value") else perm  # type: ignore

        # Active superusers have all permissions.
        if self.is_active and self.is_superuser and not self._effective_permissions:
            return True
        return _user_has_perm(self, perm, obj)


class User(AbstractBaseUser, ModelWithMetadata, PermissionsMixin):
    email = models.EmailField(max_length=254, unique=True)
    phone_no = PhoneNumberField(region='IN', unique=True)
    addresses = models.ManyToManyField(
        'Address', blank=True, related_name="user_addresses_user"
    )
    default_address = models.ForeignKey(
        'Address', related_name="default_address_user", null=True, blank=True, on_delete=models.SET_NULL
    )
    name = models.CharField(max_length=150, blank=True)
    image = models.ImageField(null=True, blank=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_phone_verified = models.BooleanField(default=False)
    is_otp_verified = models.BooleanField(default=False)
    is_profile_verified = models.BooleanField(default=False)
    last_login = models.DateTimeField(null=True, blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'email'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = ['phone_no']

    objects = UserManager()

    def get_absolute_url(self):
        return "/users/%i/" % self.pk

    def get_email(self):
        return self.email

    def get_name(self):
        return self.name

    def get_phone_no(self):
        return self.phone_no


class FcmToken(models.Model):
    user = models.OneToOneField('custom_auth.User', on_delete=models.DO_NOTHING, related_name="fcm_token_user")
    token = models.CharField(max_length=254, )

    def __str__(self):
        return "{}-{}".format(self.user.name, self.token)


class AdminProfile(models.Model):
    user = models.OneToOneField('custom_auth.User', on_delete=models.DO_NOTHING, related_name="admin")

    warehouses = models.ManyToManyField('warehouse.Warehouse',related_name="warehouse_admin",)
    address = models.ForeignKey('custom_auth.Address', null=True, blank=True, on_delete=models.DO_NOTHING)
    management_choice = (('Master Admin', 'Master Admin'),
                         ('Zonal Admin', 'Zonal Admin'),
                         ('Regional Admin', 'Regional Admin'))
    management_status = models.CharField(max_length=100, choices=management_choice, default="Regional Admin")

    def __str__(self):
        return self.user.name


class FarmAdminProfile(models.Model):
    user = models.OneToOneField('custom_auth.User', on_delete=models.DO_NOTHING, related_name="farm_admin")

    address = models.ForeignKey('custom_auth.Address', null=True, blank=True, on_delete=models.DO_NOTHING)
    management_choice = (('Master Admin', 'Master Admin'),
                         ('Zonal Admin', 'Zonal Admin'),
                         ('Regional Admin', 'Regional Admin'))
    management_status = models.CharField(max_length=100, choices=management_choice, default="Regional Admin")

    def __str__(self):
        return self.user.name


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        user_profile = UserProfile.objects.create(user=instance)
        attrs_needed = ['department']
        if all(hasattr(instance, attr) for attr in attrs_needed):
            department_name = instance.department
            # TODO use this later when multiple warehouses are built
            # warehouse = Warehouse.objects.filter(city=instance.default_address.city).first()
            # if warehouse:
            #     pass
            # else:
            #     warehouse = Warehouse.objects.filter(city_id=1).first()
            warehouse = Warehouse.objects.filter(city_id=1).first()
            print(department_name)
            if department_name:
                user_department = Department.objects.filter(name=department_name).first()
                if user_department:
                    user_profile.department.add(user_department)
                    user_profile.save()
                    if department_name == "Sales":
                        sales_profile = SalesPersonProfile.objects.create(user=instance, warehouse=warehouse)
                        sales_profile.save()

                    elif department_name == "Supply":
                        supply_profile = SupplyPersonProfile.objects.create(user=instance, warehouse=warehouse)
                        supply_profile.save()

                    elif department_name == "Operations":
                        operations_profile = OperationsPersonProfile.objects.create(user=instance, warehouse=warehouse)
                        operations_profile.save()

                    elif department_name == "Warehouse":
                        warehouse_profile = WarehousePersonProfile.objects.create(user=instance, warehouse=warehouse)
                        warehouse_profile.save()

                    elif department_name == "Admin":
                        admin_profile = AdminProfile.objects.create(user=instance)
                        admin_profile.save()
                        admin_profile.warehouses.add(warehouse)

                    elif department_name == "Finance":
                        finance_profile = FinanceProfile.objects.create(user=instance)
                        finance_profile.save()

                    elif department_name == "Distribution":
                        distribution_profile = DistributionPersonProfile.objects.create(user=instance, warehouse=warehouse)
                        distribution_profile.save()

                    elif department_name == "FarmAdmin":
                        farm_admin_profile = FarmAdminProfile.objects.create(user=instance)
                        farm_admin_profile.save()


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.userProfile.save()
    user_profile = UserProfile.objects.filter(user=instance).first()
    attrs_needed = ['department']
    if all(hasattr(instance, attr) for attr in attrs_needed):
        department_name = instance.department
        if department_name:
            user_department = Department.objects.filter(name=department_name).first()
            # warehouse = Warehouse.objects.filter(city=instance.default_address.city).first()
            # if warehouse:
            #     pass
            # else:
            #     warehouse = Warehouse.objects.filter(city_id=1).first()
            warehouse = Warehouse.objects.filter(city_id=1).first()
            if user_department:
                user_profile.department.add(user_department)
                user_profile.save()
                user_data = UserData.objects.filter(userProfile=user_profile).first()
                if not user_data:
                    UserData.objects.create(userProfile=user_profile, rating=5.0)

                if department_name == "Admin":
                    admin_profile,created = AdminProfile.objects.get_or_create(user=instance)
                    admin_profile.save()
                    admin_profile.warehouses.add(warehouse)
                elif department_name == "Sales":
                    sales_profile,created  = SalesPersonProfile.objects.get_or_create(user=instance, warehouse=warehouse)
                    sales_profile.save()
                elif department_name == "Supply":
                    supply_profile,created  = SupplyPersonProfile.objects.get_or_create(user=instance, warehouse=warehouse)
                    supply_profile.save()
                elif department_name == "Operations":
                    operation_profile,created  = OperationsPersonProfile.objects.get_or_create(user=instance, warehouse=warehouse)
                    operation_profile.save()
                elif department_name == "Warehouse":
                    warehouse_profile,created  = WarehousePersonProfile.objects.get_or_create(user=instance, warehouse=warehouse)
                    warehouse_profile.save()

                elif department_name == "Finance":
                    finance_profile, created = FinanceProfile.objects.get_or_create(user=instance)
                    finance_profile.save()

                elif department_name == "Distribution":
                    distribution_profile,created = DistributionPersonProfile.objects.get_or_create(user=instance, warehouse=warehouse)
                    distribution_profile.save()

                elif department_name == "FarmAdmin":
                    farm_admin_profile, created = FarmAdminProfile.objects.get_or_create(user=instance)
                    farm_admin_profile.save()
