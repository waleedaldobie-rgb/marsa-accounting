from django.contrib import admin
from .models import Supplier, Product, ProductPrice
admin.site.register([Supplier, Product, ProductPrice])
