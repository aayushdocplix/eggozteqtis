from django.db import models

from warehouse.models import StockInline


class Wastage(models.Model):
    stock_inline = models.ForeignKey(StockInline, related_name="wastage_inline",
                                     on_delete=models.CASCADE)
    WASTAGE_CHOICES = (('Broken', 'Broken'), ('Chatki', 'Chatki'))
    wastage_type = models.CharField(choices=WASTAGE_CHOICES, max_length=100)
    name = models.CharField(max_length=256, default="name")
    expected_quantity = models.IntegerField(default=0)
    counted_quantity = models.IntegerField(default=0)
    wastage_remark = models.CharField(max_length=256, default="wastage remark")