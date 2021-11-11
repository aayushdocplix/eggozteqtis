from django.db import models
from uuid_upload_path import upload_to

from base import UPLOAD_TYPE_CHOICES
from custom_auth.models import User


class UploadData(models.Model):
    file = models.FileField(upload_to=upload_to)
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name="uploadFiles")
    created_at = models.DateTimeField(auto_now_add=True)
    upload_type = models.CharField(max_length=50, choices=UPLOAD_TYPE_CHOICES)
