from django.core.validators import RegexValidator
from django.db import models
from uuid_upload_path import upload_to

from base.models import TimeStampedModel
from farmer.models import Farmer


class Feedback(models.Model):
    feedback_date = models.DateTimeField(auto_now_add=True)
    first_name = models.CharField(max_length=256, help_text="first name")
    last_name = models.CharField(max_length=256, help_text="last name")
    email = models.EmailField(blank=True)
    phone_regex = RegexValidator(regex=r'^\d{10,10}$',
                                 message="Phone number must be entered in the format: '999999999'. Up to 10 digits "
                                         "allowed.")
    phone = models.CharField(validators=[phone_regex], max_length=10,
                             blank=False, null=False)  # validators should be a list
    query_type = models.CharField(max_length=256, default="General Query")
    message = models.CharField(max_length=300)
    is_resolved = models.BooleanField(default=False)

    class Meta:
        ordering = ('feedback_date',)
        verbose_name = "Feedback"
        verbose_name_plural = "Feedbacks"

    def __str__(self):
        return '{} -{}'.format(self.phone, self.first_name)


class FarmerFeedback(TimeStampedModel):
    farmer = models.ForeignKey(Farmer, on_delete=models.DO_NOTHING, related_name="farmer_feedbacks")
    title = models.CharField(max_length=200,null=True,blank=True)
    query_type = models.CharField(max_length=256, default="Help Query")
    message = models.TextField()
    file = models.FileField(upload_to=upload_to,null=True, blank=True)
    is_resolved = models.BooleanField(default=False)

    def __str__(self):
        return self.farmer.farmer.name


class CustomerFeedback(TimeStampedModel):
    name = models.CharField(max_length=256, help_text="name")
    email = models.EmailField(blank=True)
    phone_regex = RegexValidator(regex=r'^\d{10,10}$',
                                 message="Phone number must be entered in the format: '999999999'. Up to 10 digits "
                                         "allowed.")
    phone = models.CharField(validators=[phone_regex], max_length=10,
                             blank=False, null=False)  # validators should be a list
    packaging_date = models.DateField()
    batch_no = models.CharField(max_length=200)
    issue_type = models.CharField(max_length=256, default="General Query")
    issue = models.CharField(max_length=300)
    is_resolved = models.BooleanField(default=False)

    class Meta:
        ordering = ('created_at',)
        verbose_name = "Customer Feedback"
        verbose_name_plural = "Customer Feedbacks"

    def __str__(self):
        return '{} -{}'.format(self.phone, self.name)
