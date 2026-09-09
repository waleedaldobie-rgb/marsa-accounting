from django.conf import settings
from django.db import models


class StockBalance(models.Model):
    product = models.ForeignKey('catalog.Product', on_delete=models.PROTECT)
    location = models.ForeignKey('branches.Location', on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    average_cost = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['product', 'location'], name='uniq_stock_balance')]


class StockAdjustment(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        APPROVED = 'APPROVED', 'Approved'
        CANCELLED = 'CANCELLED', 'Cancelled'

    branch = models.ForeignKey('branches.Branch', on_delete=models.PROTECT, related_name='stock_adjustments')
    location = models.ForeignKey('branches.Location', on_delete=models.PROTECT, related_name='stock_adjustments')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    reason = models.TextField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='stock_adjustments_created')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name='stock_adjustments_approved')
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.location.kind != self.location.Kind.BRANCH or self.location.branch_id != self.branch_id:
            raise ValidationError({'location': 'موقع التسوية يجب أن يكون مخزن الفرع المحدد.'})
        if not self.reason.strip():
            raise ValidationError({'reason': 'سبب التسوية مطلوب.'})


class StockAdjustmentItem(models.Model):
    adjustment = models.ForeignKey(StockAdjustment, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('catalog.Product', on_delete=models.PROTECT)
    system_quantity = models.DecimalField(max_digits=14, decimal_places=3)
    counted_quantity = models.DecimalField(max_digits=14, decimal_places=3)
    difference = models.DecimalField(max_digits=14, decimal_places=3)
    reason = models.TextField(blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['adjustment', 'product'], name='uniq_stock_adjustment_product')]


class StockMovement(models.Model):
    class Type(models.TextChoices):
        PURCHASE_IN = 'PURCHASE_IN', 'Purchase In'
        TRANSFER_OUT = 'TRANSFER_OUT', 'Transfer Out'
        TRANSFER_IN = 'TRANSFER_IN', 'Transfer In'
        SALE_OUT = 'SALE_OUT', 'Sale Out'
        WASTE_OUT = 'WASTE_OUT', 'Waste Out'
        ADJUSTMENT_IN = 'ADJUSTMENT_IN', 'Adjustment In'
        ADJUSTMENT_OUT = 'ADJUSTMENT_OUT', 'Adjustment Out'
        PURCHASE_RETURN = 'PURCHASE_RETURN', 'Purchase Return'
        SALES_RETURN = 'SALES_RETURN', 'Sales Return'
        CORRECTION = 'CORRECTION', 'Correction'

    product = models.ForeignKey('catalog.Product', on_delete=models.PROTECT)
    location = models.ForeignKey('branches.Location', on_delete=models.PROTECT)
    movement_type = models.CharField(max_length=30, choices=Type.choices)
    quantity = models.DecimalField(max_digits=14, decimal_places=3)
    unit_cost = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    total_cost = models.DecimalField(max_digits=16, decimal_places=4, default=0)
    reference_type = models.CharField(max_length=60, blank=True)
    reference_id = models.CharField(max_length=80, blank=True)
    reason = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)


class WasteAdjustment(models.Model):
    class WasteType(models.TextChoices):
        CLEANING = 'CLEANING', 'Cleaning'
        DAMAGE = 'DAMAGE', 'Damage'
        SPOILAGE = 'SPOILAGE', 'Spoilage'
        ICE_MELTING = 'ICE_MELTING', 'Ice Melting'
        STOCK_SHORTAGE = 'STOCK_SHORTAGE', 'Stock Shortage'
        INVALID_RETURN = 'INVALID_RETURN', 'Invalid Return'
        OTHER = 'OTHER', 'Other'

    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        APPROVED = 'APPROVED', 'Approved'
        CANCELLED = 'CANCELLED', 'Cancelled'

    branch = models.ForeignKey('branches.Branch', on_delete=models.PROTECT)
    location = models.ForeignKey('branches.Location', on_delete=models.PROTECT)
    product = models.ForeignKey('catalog.Product', on_delete=models.PROTECT)
    processing_record = models.ForeignKey(
        'processing.ProcessingRecord', null=True, blank=True,
        on_delete=models.PROTECT, related_name='waste_adjustments'
    )
    quantity = models.DecimalField(max_digits=14, decimal_places=3)
    waste_type = models.CharField(max_length=30, choices=WasteType.choices)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='created_waste_adjustments')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name='approved_waste_adjustments')
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['processing_record'],
                condition=models.Q(processing_record__isnull=False),
                name='uniq_waste_processing_record',
            )
        ]

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.quantity <= 0:
            raise ValidationError({'quantity': 'كمية الهدر يجب أن تكون أكبر من صفر.'})
        if not self.reason.strip():
            raise ValidationError({'reason': 'سبب الهدر مطلوب.'})
        if self.location.kind != self.location.Kind.BRANCH:
            raise ValidationError({'location': 'الهدر التشغيلي يسجل على مخزن الفرع فقط.'})
        if self.location.branch_id != self.branch_id:
            raise ValidationError({'location': 'موقع الهدر يجب أن يتبع الفرع المحدد.'})
