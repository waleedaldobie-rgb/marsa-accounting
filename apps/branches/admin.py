from django.contrib import admin
from .models import Branch, Location
admin.site.register([Branch, Location])
