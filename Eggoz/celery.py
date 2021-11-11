import os

from celery import Celery

# Set DJANGO_SETTINGS_MODULE if we're running directly from a celery worker
# todo why local settings are set for celery worker?
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Eggoz.settings')

app = Celery('Eggoz')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
