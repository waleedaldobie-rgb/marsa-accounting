from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import StockMovement, WasteAdjustment
from .services import apply_movement
from apps.audit.services import log_event
from apps.accounts.permissions import has_permission, require_same_branch


@transaction.atomic
def approve_waste(*, waste, user):
    waste = WasteAdjustment.objects.select_for_update().select_related('branch', 'location', 'product').get(pk=waste.pk)
    if waste.status == WasteAdjustment.Status.APPROVED:
        return waste
    if waste.status != WasteAdjustment.Status.DRAFT:
        raise ValidationError('لا يمكن اعتماد سجل الهدر في حالته الحالية.')
    if not has_permission(user, 'manage_waste'):
        raise ValidationError('لا تملك صلاحية اعتماد الهدر.')
    if not require_same_branch(user, waste.branch_id):
        raise ValidationError('لا يمكنك اعتماد هدر خارج فرعك.')
    waste.full_clean()
    if waste.processing_record_id:
        record = waste.processing_record
        if record.sale_item.product_id != waste.product_id:
            raise ValidationError('الصنف لا يطابق صنف سجل التنظيف.')
        if waste.quantity > record.difference:
            raise ValidationError('كمية هدر التنظيف لا يمكن أن تتجاوز فرق الوزن المسجل.')
    balance_qty = waste.location.stockbalance_set.filter(product_id=waste.product_id).values_list('quantity', flat=True).first()
    if balance_qty is None or balance_qty < waste.quantity:
        raise ValidationError('الرصيد غير كافٍ لتسجيل الهدر.')
    apply_movement(
        product=waste.product,
        location=waste.location,
        movement_type=StockMovement.Type.WASTE_OUT,
        quantity=waste.quantity,
        unit_cost=0,
        user=user,
        reference_type='WasteAdjustment',
        reference_id=waste.pk,
        reason=f'{waste.get_waste_type_display()}: {waste.reason}',
    )
    waste.status = WasteAdjustment.Status.APPROVED
    waste.approved_by = user
    waste.approved_at = timezone.now()
    waste.save(update_fields=['status', 'approved_by', 'approved_at'])
    log_event(user=user, branch=waste.branch, action='APPROVE', entity='WasteAdjustment', entity_id=waste.pk,
              new_value={'status': waste.status, 'quantity': str(waste.quantity)})
    return waste


@transaction.atomic
def cancel_waste(*, waste, user):
    waste = WasteAdjustment.objects.select_for_update().get(pk=waste.pk)
    if waste.status != WasteAdjustment.Status.DRAFT:
        raise ValidationError('لا يمكن إلغاء سجل هدر معتمد أو ملغى.')
    if not has_permission(user, 'manage_waste') or not require_same_branch(user, waste.branch_id):
        raise ValidationError('لا تملك صلاحية إلغاء هذا الهدر.')
    old_status = waste.status
    waste.status = WasteAdjustment.Status.CANCELLED
    waste.cancelled_at = timezone.now()
    waste.save(update_fields=['status', 'cancelled_at'])
    log_event(user=user, branch=waste.branch, action='CANCEL', entity='WasteAdjustment', entity_id=waste.pk,
              old_value={'status': old_status}, new_value={'status': waste.status})
    return waste
