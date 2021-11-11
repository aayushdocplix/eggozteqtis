from collections import defaultdict

import i18naddress
from django import forms
from django.core.exceptions import ValidationError
from django.forms import BoundField  # type: ignore
from django_countries import countries

from base.widgets import DatalistTextWidget
from custom_auth.models.Address import Address

COUNTRY_FORMS = {}
UNKNOWN_COUNTRIES = set()

AREA_TYPE = {
    "area": "Area",
    "county": "County",
    "department": "Department",
    "district": "District",
    "do_si": "Do/si",
    "eircode": "Eircode",
    "emirate": "Emirate",
    "island": "Island",
    "neighborhood": "Neighborhood",
    "oblast": "Oblast",
    "parish": "Parish",
    "pin": "PIN",
    "postal": "Postal code",
    "prefecture": "Prefecture",
    "province": "Province",
    "state": "State",
    "suburb": "Suburb",
    "townland": "Townland",
    "village_township": "Village/township",
    "zip": "ZIP code",
}