from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import models


class Supplier(models.Model):
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=60, unique=True)
    unit = models.CharField(max_length=10, default="KG", editable=False)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def clean(self):
        self.sku = self.sku.strip().upper()
        self.name = self.name.strip()
        if not self.name:
            raise ValidationError({"name": "اسم المنتج مطلوب."})
        if self.unit != "KG":
            raise ValidationError({"unit": "الوحدة الأساسية للنظام هي الكيلوغرام (KG)."})

    def __str__(self):
        return f"{self.name} ({self.sku})"

    @property
    def current_price(self):
        from django.utils import timezone
        now = timezone.now()
        return self.prices.filter(starts_at__lte=now).filter(
            models.Q(ends_at__isnull=True) | models.Q(ends_at__gt=now)
        ).first()


class ProductPrice(models.Model):
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="prices")
    price = models.DecimalField(max_digits=12, decimal_places=2)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-starts_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(price__gte=Decimal("0.00")),
                name="catalog_price_non_negative",
            ),
        ]

    def clean(self):
        if self.price < 0:
            raise ValidationError({"price": "السعر لا يمكن أن يكون سالبًا."})
        if self.ends_at and self.ends_at <= self.starts_at:
            raise ValidationError({"ends_at": "تاريخ انتهاء السعر يجب أن يكون بعد تاريخ البداية."})
        overlap = ProductPrice.objects.filter(product=self.product).exclude(pk=self.pk).filter(
            starts_at__lt=self.ends_at if self.ends_at else models.F("starts_at")
        )
        # Explicit interval overlap check, including open-ended intervals.
        for existing in ProductPrice.objects.filter(product=self.product).exclude(pk=self.pk):
            existing_end = existing.ends_at
            if self.ends_at and existing.starts_at >= self.ends_at:
                continue
            if existing_end and existing_end <= self.starts_at:
                continue
            raise ValidationError("فترة السعر تتداخل مع فترة سعر أخرى لنفس المنتج.")

    def __str__(self):
        return f"{self.product.name} — {self.price}"
