from django.db import models


class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    is_visible = models.BooleanField(default=False)

    def __str__(self):
        return self.name