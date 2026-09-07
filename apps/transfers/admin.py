from django.contrib import admin
from .models import Transfer, TransferItem
admin.site.register([Transfer, TransferItem])
