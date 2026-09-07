from django.contrib import admin
from .models import Shift, Sale, SaleItem, PaymentTransaction
admin.site.register([Shift, Sale, SaleItem, PaymentTransaction])
