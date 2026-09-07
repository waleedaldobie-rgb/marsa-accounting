from django.conf import settings
from django.db import models
class Transfer(models.Model):
    class Status(models.TextChoices): DRAFT='DRAFT','Draft'; APPROVED='APPROVED','Approved'; SENT='SENT','Sent'; RECEIVED='RECEIVED','Received'; CANCELLED='CANCELLED','Cancelled'
    source=models.ForeignKey('branches.Location',on_delete=models.PROTECT,related_name='transfers_out'); destination=models.ForeignKey('branches.Location',on_delete=models.PROTECT,related_name='transfers_in'); status=models.CharField(max_length=20,choices=Status.choices,default=Status.DRAFT); note=models.TextField(blank=True); created_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT); sent_at=models.DateTimeField(null=True,blank=True); received_at=models.DateTimeField(null=True,blank=True)
class TransferItem(models.Model):
    transfer=models.ForeignKey(Transfer,on_delete=models.CASCADE,related_name='items'); product=models.ForeignKey('catalog.Product',on_delete=models.PROTECT); sent_quantity=models.DecimalField(max_digits=14,decimal_places=3); received_quantity=models.DecimalField(max_digits=14,decimal_places=3,null=True,blank=True); difference_reason=models.TextField(blank=True)
