from django.db import models

from Eggoz import settings


# Create your models here.
class IOTData(models.Model):
    stamp = models.CharField(max_length=200)
    client_topic = models.CharField(max_length=255, help_text="863958048443779")
    temperature = models.DecimalField(default=0, help_text='40.92', max_digits=15,decimal_places=6 )
    humidity = models.DecimalField(default=0, help_text='95726.73', max_digits=15,decimal_places=6 )
    ammonia_r = models.DecimalField(default=0, help_text='23', max_digits=15,decimal_places=6 )
    ammonia_ppm = models.DecimalField(default=0, help_text='9.66429', max_digits=15,decimal_places=6 )
    Sq = models.DecimalField(default=0, help_text='25', max_digits=15,decimal_places=6 )
    BATV = models.DecimalField(default=0, help_text='3.29', max_digits=15,decimal_places=6 )
    BATQ = models.DecimalField(default=0, help_text='247', max_digits=15,decimal_places=6 )
