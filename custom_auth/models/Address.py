from django.db import models
from django.db.models import Value
from django.forms import model_to_dict
from phonenumber_field.modelfields import PhoneNumberField

from Eggoz import settings
from base.models.Cluster import City, EcommerceSector


class AddressQueryset(models.QuerySet):
    def annotate_default(self, user):
        # Set default  address pk to None
        default_address_pk= None
        if user.default_address:
            default_address_pk = user.default_address.pk

        return user.addresses.annotate(
            user_default_address_pk=Value(
                default_address_pk, models.IntegerField()
            ),

        )


class Address(models.Model):
    address_name = models.CharField(max_length=256, blank=True)
    building_address = models.CharField(max_length=256, blank=True)
    street_address = models.CharField(max_length=256, blank=True)
    city = models.ForeignKey(City, on_delete=models.DO_NOTHING,null=True, blank=True)
    ecommerce_sector = models.ForeignKey(EcommerceSector, on_delete=models.DO_NOTHING,null=True, blank=True)
    billing_city = models.CharField(max_length=200, null=True, blank=True)
    landmark = models.CharField(max_length=254, null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)  # dependent on 3rd party, hence accepts null
    longitude = models.FloatField(null=True, blank=True)  # dependent on 3rd party, hence accepts null
    pinCode = models.IntegerField(null=True, blank=True)
    date_added = models.DateTimeField(auto_now_add=True)
    phone_no = PhoneNumberField(region='IN',null=True,blank=True)
    name = models.CharField(max_length=200,null=True,blank=True)
    # TODO state and district
    objects = AddressQueryset.as_manager()

    class Meta:
        ordering = ("pk",)

    @property
    def full_name(self):
        return self.address_name

    def __str__(self):
        city_name = self.city.city_name if self.city else None
        return '{}-{}-{}, {}, {}'.format(self.id, self.address_name,city_name, self.building_address, self.street_address)

    def __eq__(self, other):
        if not isinstance(other, Address):
            return False
        return self.as_data() == other.as_data()

    __hash__ = models.Model.__hash__

    def as_data(self):
        """Return the address as a dict suitable for passing as kwargs.
        Result does not contain the primary key or an associated user.
        """
        data = model_to_dict(self, exclude=["id", "user"])
        # if isinstance(data["country"], Country):
        #     data["country"] = data["country"].code
        return data

    def get_copy(self):
        """Return a new instance of the same address."""
        return Address.objects.create(**self.as_data())

class DeleteAddresses(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,related_name='user_delete_addresses',on_delete=models.DO_NOTHING)
    address = models.ForeignKey(Address,related_name='delete_addresses',on_delete=models.DO_NOTHING)

    class Meta:
        unique_together = ("address","user")
