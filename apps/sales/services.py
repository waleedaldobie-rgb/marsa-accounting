from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.inventory.models import StockBalance, StockMovement
from apps.inventory.services import apply_movement
from apps.processing.models import ProcessingRecord
from apps.audit.services import log_event
from apps.accounts.permissions import can_create_sale, can_issue_sale
from .models import PaymentTransaction, Sale, SaleItem, Shift
from .invoice_sequence import allocate_invoice_number

MONEY_Q = Decimal("0.01")


@transaction.atomic
def create_sale_draft(*, user, shift, branch, items):
    """Create a draft sale only; inventory and financial ledgers are untouched."""
    if shift.status != shift.Status.OPEN:
        raise ValidationError("الوردية يجب أن تكون مفتوحة.")
    if not can_create_sale(user, branch.pk, shift):
        raise ValidationError("لا تملك صلاحية إنشاء البيع لهذه الوردية أو الفرع.")
    if not items:
        raise ValidationError("أضف صنفًا واحدًا على الأقل.")
    sale = Sale.objects.create(
        invoice_no=allocate_invoice_number(branch=branch),
        shift=shift, branch=branch, created_by=user, status=Sale.Status.DRAFT, total=Decimal("0")
    )
    total=Decimal("0")
    for item in items:
        product=item["product"]
        raw=Decimal(item["raw_weight"]); cleaned=Decimal(item["cleaned_weight"]); price=Decimal(item["unit_price"])
        class _Item:
            pass
        draft_item=_Item(); draft_item.raw_weight=raw; draft_item.cleaned_weight=cleaned; draft_item.unit_price=price; draft_item.product_id=product.pk
        validate_sale_item(draft_item)
        amount=_money(cleaned*price)
        SaleItem.objects.create(sale=sale, product=product, raw_weight=raw, cleaned_weight=cleaned, unit_price=price, sale_amount=amount)
        total += amount
    sale.total=_money(total); sale.save(update_fields=["total"])
    return sale

def _money(value):
    return Decimal(value).quantize(MONEY_Q, rounding=ROUND_HALF_UP)


def validate_sale_item(item):
    raw = Decimal(item.raw_weight)
    cleaned = Decimal(item.cleaned_weight)
    price = Decimal(item.unit_price)
    if raw <= 0:
        raise ValidationError(f"الوزن الخام للمنتج {item.product_id} يجب أن يكون أكبر من صفر.")
    if cleaned <= 0:
        raise ValidationError(f"الوزن المنظف للمنتج {item.product_id} يجب أن يكون أكبر من صفر.")
    if cleaned > raw:
        raise ValidationError("الوزن المنظف لا يمكن أن يتجاوز الوزن الخام.")
    if price < 0:
        raise ValidationError("سعر البيع لا يمكن أن يكون سالبًا.")
    return raw, cleaned, price


@transaction.atomic
def issue_sale(*, sale, location, user, payment_method):
    """Issue a complete sale atomically: stock-out raw weight, processing, COGS, and one payment."""
    sale = Sale.objects.select_for_update().select_related("shift", "branch").get(pk=sale.pk)
    if not can_issue_sale(user, sale):
        raise ValidationError("لا تملك صلاحية إصدار بيع خارج نطاقك.")
    if sale.status == Sale.Status.ISSUED:
        return sale
    if sale.status != Sale.Status.DRAFT:
        raise ValidationError("لا يمكن إصدار هذه الفاتورة في حالتها الحالية.")
    shift = Shift.objects.select_for_update().get(pk=sale.shift_id)
    if shift.status != Shift.Status.OPEN:
        raise ValidationError("لا يمكن إصدار فاتورة على وردية مغلقة.")
    if shift.branch_id != sale.branch_id:
        raise ValidationError("الوردية والفرع لا يتطابقان.")
    if getattr(location, "kind", None) != location.Kind.BRANCH or location.branch_id != sale.branch_id:
        raise ValidationError("موقع البيع يجب أن يكون مخزن فرع الفاتورة.")

    items = list(sale.items.select_related("product").order_by("product_id", "pk"))
    if not items:
        raise ValidationError("لا يمكن إصدار فاتورة بدون أصناف.")

    # Lock existing balances in deterministic order to reduce deadlock risk.
    balances = {}
    for item in items:
        if item.product_id in balances:
            continue
        balance = StockBalance.objects.select_for_update().filter(
            product_id=item.product_id, location_id=location.pk
        ).first()
        if balance is None:
            raise ValidationError(f"لا يوجد رصيد مخزون للمنتج {item.product.name} في هذا الموقع.")
        balances[item.product_id] = balance

    total = Decimal("0")
    for item in items:
        raw, cleaned, price = validate_sale_item(item)
        balance = balances[item.product_id]
        if balance.quantity < raw:
            raise ValidationError(f"الرصيد غير كافٍ للمنتج {item.product.name}.")
        cost = Decimal(balance.average_cost)
        amount = _money(cleaned * price)
        cogs = raw * cost
        item.unit_cost = cost
        item.sale_amount = amount
        item.cogs = cogs
        item.save(update_fields=["unit_cost", "sale_amount", "cogs"])
        apply_movement(
            product=item.product, location=location,
            movement_type=StockMovement.Type.SALE_OUT, quantity=raw,
            unit_cost=cost, user=user, reference_type="SaleItem",
            reference_id=item.pk, reason="Sale issue: raw weight out",
        )
        ProcessingRecord.objects.update_or_create(
            sale_item=item,
            defaults={"raw_weight": raw, "cleaned_weight": cleaned, "difference": raw - cleaned},
        )
        total += amount

    sale.total = _money(total)
    sale.status = Sale.Status.ISSUED
    sale.issued_at = timezone.now()
    sale.issued_by = user
    sale.save(update_fields=["total", "status", "issued_at", "issued_by"])

    PaymentTransaction.objects.create(
        branch=sale.branch, shift=sale.shift, amount=sale.total,
        payment_method=payment_method, direction=PaymentTransaction.Direction.IN,
        reference_type="Sale", reference_id=sale.pk, created_by=user,
    )
    log_event(user=user, action='ISSUE', entity='Sale', entity_id=sale.pk,
              new_value={'status': sale.status, 'total': str(sale.total)}, reason='إصدار فاتورة وخصم المخزون')
    return sale


# Backward-compatible single-item entry point. It now delegates to the atomic sale workflow.
def issue_sale_item(*, sale_item, location, user, payment_method):
    return issue_sale(sale=sale_item.sale, location=location, user=user, payment_method=payment_method)
