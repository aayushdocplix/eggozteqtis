from django.db import models
from phonenumber_field.modelfields import PhoneNumberField


# Create your models here.

# this model Stores the data of the Phones Verified


class PhoneModel(models.Model):
    phone_no = PhoneNumberField(unique=True)
    isVerified = models.BooleanField(blank=False, default=False)
    counter = models.IntegerField(default=0, blank=False)  # For HOTP Verification
    login_count = models.IntegerField(default=0, blank=False)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    def __str__(self):
        return str(self.phone_no)


class LoginStamp(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    phone_model = models.ForeignKey(PhoneModel, on_delete=models.CASCADE, related_name="phoneModel")
    login_response = models.CharField(max_length=100, default="Success")
