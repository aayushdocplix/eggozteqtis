from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from .Department import Department


class UserProfile(models.Model):
    user = models.OneToOneField('User', related_name="userProfile", on_delete=models.CASCADE, unique=True)
    department = models.ManyToManyField(Department, blank=True, related_name="user_department")

    def __str__(self):
        return self.user.email


class UserData(models.Model):
    userProfile = models.OneToOneField(UserProfile, related_name="userData", on_delete=models.CASCADE, unique=True)
    employee_id = models.CharField(max_length=100, null=True)
    profile_photo_url = models.CharField(max_length=254, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    online = models.BooleanField(default=False)
    latitude = models.FloatField(null=True, blank=True)  # dependent on 3rd party, hence accepts null
    longitude = models.FloatField(null=True, blank=True)
    location_updated_at = models.DateTimeField(null=True, blank=True)
    is_profile_complete = models.BooleanField(default=False)
    is_profile_verified = models.BooleanField(default=False)
    experience = models.IntegerField(default=None, null=True, blank=True)  # in months
    rating = models.DecimalField(max_digits=2, decimal_places=1, default=10, null=True)
    status_choices = (('not-verified', 'not-verified'), ('uploaded', 'uploaded'), ('verified', 'verified'))

    aadhar_photo_url = models.CharField(max_length=254, null=True, blank=True)
    aadhar_no = models.CharField(max_length=100, null=True, blank=True)
    aadhar_status = models.CharField(max_length=20, choices=status_choices, default='not-verified')

    pancard_photo_url = models.CharField(max_length=254, null=True, blank=True)
    pancard_no = models.CharField(max_length=100, null=True, blank=True)
    pancard_status = models.CharField(max_length=20, choices=status_choices, default='not-verified')


    def __str__(self):
        return self.userProfile.user.email
