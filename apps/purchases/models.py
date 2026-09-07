from django.conf import settings
from django.db import models

class Purchase(models.Model):
    class Status(models.TextChoices): DRAFT='DRAFT','Draft'; APPROVED='APPROVED','Approved'; CANCELLED='CANCELLED','Cancelled'
    supplier=models.ForeignKey('catalog.Supplier',on_delete=models.PROTECT)
    location=models.ForeignKey('branches.Location',on_delete=models.PROTECT)
    invoice_no=models.CharField(max_length=80)
    status=models.CharField(max_length=20,choices=Status.choices,default=Status.DRAFT)
    total=models.DecimalField(max_digits=16,decimal_places=2,default=0)
    created_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name='purchases_created')
    approved_by=models.ForeignKey(settings.AUTH_USER_MODEL,null=True,blank=True,on_delete=models.PROTECT,related_name='purchases_approved')
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['supplier','invoice_no'],name='uniq_purchase_supplier_invoice')]

class PurchaseItem(models.Model):
    purchase=models.ForeignKey(Purchase,on_delete=models.CASCADE,related_name='items')
    product=models.ForeignKey('catalog.Product',on_delete=models.PROTECT)
    quantity=models.DecimalField(max_digits=14,decimal_places=3)
    unit_cost=models.DecimalField(max_digits=14,decimal_places=4)

class PurchaseReturn(models.Model):
    class Status(models.TextChoices): DRAFT='DRAFT','Draft'; APPROVED='APPROVED','Approved'; CANCELLED='CANCELLED','Cancelled'
    purchase=models.ForeignKey(Purchase,on_delete=models.PROTECT,related_name='returns')
    location=models.ForeignKey('branches.Location',on_delete=models.PROTECT)
    reference_no=models.CharField(max_length=80)
    status=models.CharField(max_length=20,choices=Status.choices,default=Status.DRAFT)
    total=models.DecimalField(max_digits=16,decimal_places=2,default=0)
    reason=models.TextField()
    created_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name='purchase_returns_created')
    approved_by=models.ForeignKey(settings.AUTH_USER_MODEL,null=True,blank=True,on_delete=models.PROTECT,related_name='purchase_returns_approved')
    created_at=models.DateTimeField(auto_now_add=True)
    approved_at=models.DateTimeField(null=True,blank=True)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['purchase','reference_no'],name='uniq_purchase_return_reference')]

class PurchaseReturnItem(models.Model):
    purchase_return=models.ForeignKey(PurchaseReturn,on_delete=models.CASCADE,related_name='items')
    product=models.ForeignKey('catalog.Product',on_delete=models.PROTECT)
    quantity=models.DecimalField(max_digits=14,decimal_places=3)
    unit_cost=models.DecimalField(max_digits=14,decimal_places=4)
