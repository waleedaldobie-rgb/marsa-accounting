from django.db import models
class Platform(models.Model):
    name=models.CharField(max_length=120,unique=True); commission_rate=models.DecimalField(max_digits=6,decimal_places=3,default=0)
    def __str__(self): return self.name
class DeliveryOrder(models.Model):
    class Status(models.TextChoices): COMPLETED='COMPLETED','Completed'; CANCELLED='CANCELLED','Cancelled'; RETURNED='RETURNED','Returned'; REJECTED='REJECTED','Rejected'
    sale=models.OneToOneField('sales.Sale',on_delete=models.PROTECT,related_name='delivery_order'); platform=models.ForeignKey(Platform,on_delete=models.PROTECT); external_order_no=models.CharField(max_length=100); status=models.CharField(max_length=20,choices=Status.choices,default=Status.COMPLETED); commission=models.DecimalField(max_digits=16,decimal_places=2,default=0); net_settlement=models.DecimalField(max_digits=16,decimal_places=2,default=0)
class Settlement(models.Model):
    delivery_order=models.ForeignKey(DeliveryOrder,on_delete=models.PROTECT,related_name='settlements'); amount=models.DecimalField(max_digits=16,decimal_places=2); settled_at=models.DateTimeField(null=True,blank=True); note=models.TextField(blank=True)
