from django.conf import settings
from django.db import models
from django.db.models import JSONField
from django.utils import timezone

from base.util.json_serializer import CustomJsonEncoder
from custom_auth.Choices import CustomerEvents
from custom_auth.models import User


class CustomerNote(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, blank=True, null=True, on_delete=models.SET_NULL
    )
    date = models.DateTimeField(db_index=True, auto_now_add=True)
    content = models.TextField()
    is_public = models.BooleanField(default=True)
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="notes", on_delete=models.CASCADE
    )

    class Meta:
        ordering = ("date",)


class CustomerEvent(models.Model):
    """Model used to store events that happened during the customer lifecycle."""

    date = models.DateTimeField(default=timezone.now, editable=False)
    type = models.CharField(
        max_length=255,
        choices=[
            (type_name.upper(), type_name) for type_name, _ in CustomerEvents.CHOICES
        ],
    )
    order = models.ForeignKey("order.Order", on_delete=models.SET_NULL, null=True)
    parameters = JSONField(blank=True, default=dict, encoder=CustomJsonEncoder)
    user = models.ForeignKey(User, related_name="events", on_delete=models.CASCADE)

    class Meta:
        ordering = ("date",)

    def __repr__(self):
        return f"{self.__class__.__name__}(type={self.type!r}, user={self.user!r})"


class StaffNotificationRecipient(models.Model):
    user = models.OneToOneField(
        User,
        related_name="staff_notification",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    staff_email = models.EmailField(unique=True, blank=True, null=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ("staff_email",)

    def get_email(self):
        return self.user.email if self.user else self.staff_email