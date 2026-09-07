from django.contrib import admin
from .models import StockBalance, StockMovement, WasteAdjustment

admin.site.register(StockBalance)
admin.site.register(StockMovement)
admin.site.register(WasteAdjustment)
