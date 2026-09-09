from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.accounts.permissions import can_approve_adjustment, can_create_adjustment
from apps.audit.services import log_event
from .models import StockAdjustment, StockAdjustmentItem, StockBalance, StockMovement
from .services import apply_movement


@transaction.atomic
def create_adjustment(*, user, branch, location, reason, items):
    if not can_create_adjustment(user, branch.pk):
        raise ValidationError('لا تملك صلاحية إنشاء تسوية لهذا الفرع.')
    if not reason or not reason.strip():
        raise ValidationError('سبب التسوية مطلوب.')
    if location.kind != location.Kind.BRANCH or location.branch_id != branch.pk:
        raise ValidationError('موقع التسوية يجب أن يتبع الفرع المحدد.')
    if not items:
        raise ValidationError('أضف صنفًا واحدًا على الأقل.')

    adjustment = StockAdjustment.objects.create(
        branch=branch, location=location, reason=reason.strip(), created_by=user,
    )
    seen = set()
    for item in items:
        product = item['product']
        if product.pk in seen:
            raise ValidationError('لا يمكن تكرار المنتج في نفس التسوية.')
        seen.add(product.pk)
        counted = Decimal(item['counted_quantity'])
        if counted < 0:
            raise ValidationError('الكمية المعدودة لا يمكن أن تكون سالبة.')
        balance = StockBalance.objects.filter(product=product, location=location).first()
        system = balance.quantity if balance else Decimal('0')
        StockAdjustmentItem.objects.create(
            adjustment=adjustment, product=product, system_quantity=system,
            counted_quantity=counted, difference=counted - system,
            reason=(item.get('reason') or '').strip(),
        )
    return adjustment


@transaction.atomic
def approve_adjustment(*, adjustment, user):
    adjustment = StockAdjustment.objects.select_for_update().select_related('branch', 'location').get(pk=adjustment.pk)
    if not can_approve_adjustment(user, adjustment):
        raise ValidationError('لا تملك صلاحية اعتماد هذه التسوية.')
    if adjustment.status == StockAdjustment.Status.APPROVED:
        return adjustment
    if adjustment.status != StockAdjustment.Status.DRAFT:
        raise ValidationError('لا يمكن اعتماد التسوية في حالتها الحالية.')
    if not adjustment.reason.strip():
        raise ValidationError('سبب التسوية مطلوب.')

    items = list(adjustment.items.select_related('product').order_by('product_id'))
    if not items:
        raise ValidationError('لا يمكن اعتماد تسوية بلا أصناف.')
    for item in items:
        balance = StockBalance.objects.select_for_update().filter(
            product=item.product, location=adjustment.location,
        ).first()
        current = balance.quantity if balance else Decimal('0')
        if current != item.system_quantity:
            raise ValidationError('تغير الرصيد منذ إنشاء التسوية؛ أنشئ تسوية جديدة.')
        difference = item.counted_quantity - current
        if difference == 0:
            continue
        cost = balance.average_cost if balance else Decimal('0')
        movement_type = StockMovement.Type.ADJUSTMENT_IN if difference > 0 else StockMovement.Type.ADJUSTMENT_OUT
        apply_movement(
            product=item.product, location=adjustment.location, movement_type=movement_type,
            quantity=abs(difference), unit_cost=cost, user=user,
            reference_type='StockAdjustment', reference_id=adjustment.pk,
            reason=adjustment.reason,
        )

    adjustment.status = StockAdjustment.Status.APPROVED
    adjustment.approved_by = user
    adjustment.approved_at = timezone.now()
    adjustment.save(update_fields=['status', 'approved_by', 'approved_at'])
    log_event(
        user=user, branch=adjustment.branch, action='APPROVE', entity='StockAdjustment', entity_id=adjustment.pk,
        old_value={'status': StockAdjustment.Status.DRAFT},
        new_value={'status': adjustment.status, 'reason': adjustment.reason}, reason=adjustment.reason,
    )
    return adjustment


@transaction.atomic
def cancel_adjustment(*, adjustment, user, reason=''):
    adjustment = StockAdjustment.objects.select_for_update().select_related('branch').get(pk=adjustment.pk)
    if not can_create_adjustment(user, adjustment.branch_id):
        raise ValidationError('لا تملك صلاحية إلغاء هذه التسوية.')
    if adjustment.status != StockAdjustment.Status.DRAFT:
        raise ValidationError('لا يمكن إلغاء تسوية معتمدة أو ملغاة.')
    if not reason or not reason.strip():
        raise ValidationError('سبب الإلغاء مطلوب.')
    adjustment.status = StockAdjustment.Status.CANCELLED
    adjustment.cancelled_at = timezone.now()
    adjustment.save(update_fields=['status', 'cancelled_at'])
    log_event(user=user, branch=adjustment.branch, action='CANCEL', entity='StockAdjustment', entity_id=adjustment.pk,
              old_value={'status': StockAdjustment.Status.DRAFT}, new_value={'status': adjustment.status}, reason=reason.strip())
    return adjustment
