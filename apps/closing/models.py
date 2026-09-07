from django.conf import settings
from django.db import models

class ShiftClosing(models.Model):
    class Status(models.TextChoices):
        DRAFT='DRAFT','Draft'; APPROVED='APPROVED','Approved'; REJECTED='REJECTED','Rejected'
    shift=models.OneToOneField('sales.Shift',on_delete=models.PROTECT,related_name='closing')
    expected_cash=models.DecimalField(max_digits=16,decimal_places=2,default=0)
    actual_cash=models.DecimalField(max_digits=16,decimal_places=2,default=0)
    difference=models.DecimalField(max_digits=16,decimal_places=2,default=0)
    status=models.CharField(max_length=20,choices=Status.choices,default=Status.DRAFT)
    approved_by=models.ForeignKey(settings.AUTH_USER_MODEL,null=True,blank=True,on_delete=models.PROTECT)
    created_at=models.DateTimeField(auto_now_add=True)
    approved_at=models.DateTimeField(null=True,blank=True)
