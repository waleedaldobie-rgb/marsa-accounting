from django.db import models

class ProcessingRecord(models.Model):
    sale_item = models.OneToOneField("sales.SaleItem", on_delete=models.PROTECT, related_name="processing")
    raw_weight = models.DecimalField(max_digits=14, decimal_places=3)
    cleaned_weight = models.DecimalField(max_digits=14, decimal_places=3)
    difference = models.DecimalField(max_digits=14, decimal_places=3)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
