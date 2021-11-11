from django.db import models

from warehouse.models import StockInline


class QCEntry(models.Model):
    entry_date = models.DateTimeField(auto_now_add=True)
    batch_id = models.CharField(max_length=200)
    stock_inline = models.ForeignKey(StockInline, related_name="product_type_qc_inline",
                                     on_delete=models.CASCADE)
    quantity_used = models.IntegerField(default=0)
    ph_value = models.DecimalField(max_digits=12,
                                   decimal_places=3,
                                   blank=True,
                                   null=True)

    desc = models.CharField(max_length=200)

    class Meta:
        pass

    def __str__(self):
        entry_date = self.entry_date
        return entry_date.strftime('%d-%m-%Y %H:%M')


class QCLine(models.Model):
    qcEntry = models.ForeignKey(QCEntry, on_delete=models.DO_NOTHING, null=True, blank=True)
    name = models.CharField(max_length=200, default="name")
    ph_value = models.DecimalField(max_digits=12,
                                   decimal_places=3,
                                   blank=True,
                                   null=True)