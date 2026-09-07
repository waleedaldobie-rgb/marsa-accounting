from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from apps.audit.services import log_event
from apps.inventory.models import StockMovement
from apps.inventory.services import apply_movement
from .models import Purchase, PurchaseReturn

@transaction.atomic
def approve_purchase(*, purchase_id, user):
    purchase=Purchase.objects.select_for_update().prefetch_related('items').get(pk=purchase_id)
    if purchase.status == Purchase.Status.APPROVED: return purchase
    if purchase.status != Purchase.Status.DRAFT: raise ValidationError('لا يمكن اعتماد الشراء في حالته الحالية.')
    if not purchase.items.exists(): raise ValidationError('أضف صنفًا واحدًا على الأقل قبل الاعتماد.')
    total=Decimal('0')
    for item in purchase.items.all():
        if item.quantity <= 0 or item.unit_cost < 0: raise ValidationError('الكمية والتكلفة غير صالحتين.')
        total += item.quantity * item.unit_cost
        apply_movement(product=item.product,location=purchase.location,movement_type=StockMovement.Type.PURCHASE_IN,quantity=item.quantity,unit_cost=item.unit_cost,user=user,reference_type='Purchase',reference_id=purchase.pk)
    purchase.total=total; purchase.status=Purchase.Status.APPROVED; purchase.approved_by=user; purchase.save(update_fields=['total','status','approved_by'])
    log_event(user=user,action='APPROVE',entity='Purchase',entity_id=purchase.pk,new_value={'total':str(total),'status':purchase.status})
    return purchase

@transaction.atomic
def cancel_purchase(*, purchase, user, reason):
    purchase=Purchase.objects.select_for_update().get(pk=purchase.pk)
    if purchase.status != Purchase.Status.DRAFT: raise ValidationError('لا يمكن إلغاء شراء غير مسودة.')
    if not reason.strip(): raise ValidationError('سبب الإلغاء مطلوب.')
    purchase.status=Purchase.Status.CANCELLED; purchase.save(update_fields=['status'])
    log_event(user=user,action='CANCEL',entity='Purchase',entity_id=purchase.pk,reason=reason,old_value={'status':'DRAFT'},new_value={'status':'CANCELLED'})
    return purchase

@transaction.atomic
def approve_purchase_return(*, return_obj, user):
    ret=PurchaseReturn.objects.select_for_update().prefetch_related('items').select_related('purchase').get(pk=return_obj.pk)
    if ret.status == PurchaseReturn.Status.APPROVED: return ret
    if ret.status != PurchaseReturn.Status.DRAFT: raise ValidationError('لا يمكن اعتماد المرتجع في حالته الحالية.')
    if ret.purchase.status != Purchase.Status.APPROVED: raise ValidationError('لا يمكن إرجاع شراء غير معتمد.')
    if not ret.reason.strip(): raise ValidationError('سبب المرتجع مطلوب.')
    if not ret.items.exists(): raise ValidationError('أضف صنفًا واحدًا على الأقل.')
    total=Decimal('0')
    for item in ret.items.all():
        if item.quantity <= 0 or item.unit_cost < 0: raise ValidationError('بيانات المرتجع غير صالحة.')
        total += item.quantity * item.unit_cost
        apply_movement(product=item.product,location=ret.location,movement_type=StockMovement.Type.PURCHASE_RETURN,quantity=item.quantity,unit_cost=item.unit_cost,user=user,reference_type='PurchaseReturn',reference_id=ret.pk)
    ret.total=total; ret.status=PurchaseReturn.Status.APPROVED; ret.approved_by=user; ret.approved_at=timezone.now(); ret.save(update_fields=['total','status','approved_by','approved_at'])
    log_event(user=user,action='APPROVE',entity='PurchaseReturn',entity_id=ret.pk,new_value={'total':str(total),'status':ret.status},reason=ret.reason)
    return ret
