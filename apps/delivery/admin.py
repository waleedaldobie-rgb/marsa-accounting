from django.contrib import admin
from .models import Platform, DeliveryOrder, Settlement
admin.site.register([Platform, DeliveryOrder, Settlement])
