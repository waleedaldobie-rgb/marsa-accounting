from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError

class Shift(models.Model):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        CLOSED = "CLOSED", "Closed"
    branch = models.ForeignKey("branches.Branch", on_delete=models.PROTECT)
    cashier = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    opening_cash = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)

class InvoiceSequence(models.Model):
    """Per-branch invoice counter. Row locking makes number allocation safe under concurrency."""
    branch = models.OneToOneField("branches.Branch", on_delete=models.PROTECT, related_name="invoice_sequence")
    next_number = models.PositiveBigIntegerField(default=1)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(next_number__gte=1), name="invoice_sequence_next_gte_1"),
        ]


class Sale(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        ISSUED = "ISSUED", "Issued"
        CANCELLED = "CANCELLED", "Cancelled"
        REFUNDED = "REFUNDED", "Refunded"
    class Channel(models.TextChoices):
        IN_STORE = "IN_STORE", "In Store"
        DELIVERY_APP = "DELIVERY_APP", "Delivery App"
    invoice_no = models.CharField(max_length=80, unique=True)
    shift = models.ForeignKey(Shift, on_delete=models.PROTECT, related_name="sales")
    branch = models.ForeignKey("branches.Branch", on_delete=models.PROTECT)
    channel = models.CharField(max_length=20, choices=Channel.choices, default=Channel.IN_STORE)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    total = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    issued_at = models.DateTimeField(null=True, blank=True)
    issued_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="issued_sales")

class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey("catalog.Product", on_delete=models.PROTECT)
    raw_weight = models.DecimalField(max_digits=14, decimal_places=3)
    cleaned_weight = models.DecimalField(max_digits=14, decimal_places=3)
    unit_price = models.DecimalField(max_digits=14, decimal_places=2)
    unit_cost = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    sale_amount = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    cogs = models.DecimalField(max_digits=16, decimal_places=4, default=0)

class PaymentTransaction(models.Model):
    class Method(models.TextChoices):
        CASH = "CASH", "Cash"
        CARD = "CARD", "Card"
        APP_CREDIT = "APP_CREDIT", "App Credit"
        OTHER = "OTHER", "Other"
    class Direction(models.TextChoices):
        IN = "IN", "In"
        OUT = "OUT", "Out"
    branch = models.ForeignKey("branches.Branch", on_delete=models.PROTECT)
    shift = models.ForeignKey(Shift, null=True, blank=True, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=16, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=Method.choices)
    direction = models.CharField(max_length=3, choices=Direction.choices)
    reference_type = models.CharField(max_length=60)
    reference_id = models.CharField(max_length=80)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["reference_type", "reference_id", "direction"],
                name="uniq_payment_reference_direction",
            )
        ]


class SalesReturn(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        APPROVED = "APPROVED", "Approved"
        CANCELLED = "CANCELLED", "Cancelled"

    sale = models.ForeignKey(Sale, on_delete=models.PROTECT, related_name="returns")
    branch = models.ForeignKey("branches.Branch", on_delete=models.PROTECT)
    reason = models.TextField()
    refund_amount = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    payment_method = models.CharField(max_length=20, choices=PaymentTransaction.Method.choices, default=PaymentTransaction.Method.CASH)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_sales_returns")
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="approved_sales_returns")
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def clean(self):
        if self.sale_id and self.branch_id and self.sale.branch_id != self.branch_id:
            raise ValidationError("فرع المرتجع يجب أن يطابق فرع الفاتورة.")
        if not self.reason.strip():
            raise ValidationError("سبب المرتجع مطلوب.")


class SalesReturnItem(models.Model):
    sales_return = models.ForeignKey(SalesReturn, on_delete=models.CASCADE, related_name="items")
    sale_item = models.ForeignKey(SaleItem, on_delete=models.PROTECT)
    raw_weight = models.DecimalField(max_digits=14, decimal_places=3)
    refund_amount = models.DecimalField(max_digits=16, decimal_places=2, default=0)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["sales_return", "sale_item"], name="uniq_sales_return_item")]

    def clean(self):
        if self.raw_weight <= 0:
            raise ValidationError({"raw_weight": "كمية المرتجع يجب أن تكون أكبر من صفر."})
        if self.sale_item_id and self.raw_weight > self.sale_item.raw_weight:
            raise ValidationError({"raw_weight": "كمية المرتجع لا يمكن أن تتجاوز الكمية الخام المباعة."})
