# prod_settings.py
# Aws My sql DB

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# if 'RDS_HOSTNAME' in os.environ:
#     DATABASES = {
#         'default': {
#             'ENGINE': 'django.db.backends.mysql',
#             'NAME': os.environ['RDS_DB_NAME'],
#             'USER': os.environ['RDS_USERNAME'],
#             'PASSWORD': os.environ['RDS_PASSWORD'],
#             'HOST': os.environ['RDS_HOSTNAME'],
#             'PORT': os.environ['RDS_PORT'],
#         }
#     }

# DATABASES = {
#         'default': {
#             'ENGINE': 'django.db.backends.mysql',
#             'NAME': 'eggozdb',
#             'USER': 'eggoz',
#             'PASSWORD': 'Eggoz$1234',
#             'HOST': 'db-eggoz-prod.csuqkvngahdb.ap-southeast-1.rds.amazonaws.com',
#             'PORT': 3306,
#         }
#     }

DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'eggozdb',
            'USER': 'eggoz',
            'PASSWORD': 'Eggoz$1234',
            'HOST': 'eggoz-oms-prod.c5mgychujutg.ap-south-1.rds.amazonaws.com',
            'PORT': 3306,
        }
    }