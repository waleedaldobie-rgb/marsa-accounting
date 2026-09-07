from decimal import Decimal, ROUND_HALF_UP
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from apps.audit.services import log_event
from apps.inventory.models import StockMovement
from apps.inventory.services import apply_movement
from .models import PaymentTransaction, Sale, SalesReturn, SalesReturnItem

Q=Decimal('0.01')
def money(v): return Decimal(v).quantize(Q, rounding=ROUND_HALF_UP)

@transaction.atomic
def approve_sales_return(*, sales_return, location, user, request=None):
    ret=SalesReturn.objects.select_for_update().select_related('sale','branch').get(pk=sales_return.pk)
    if ret.status==SalesReturn.Status.APPROVED: return ret
    if ret.status!=SalesReturn.Status.DRAFT: raise ValidationError('لا يمكن اعتماد المرتجع في حالته الحالية.')
    if ret.sale.status!=Sale.Status.ISSUED: raise ValidationError('لا يمكن إرجاع فاتورة غير صادرة.')
    if not user.is_superuser and getattr(user,'role',None) not in {'OWNER','ACCOUNTANT','BRANCH_MANAGER'}: raise ValidationError('لا تملك صلاحية اعتماد مرتجع.')
    if not user.is_superuser and getattr(user,'role',None)!='OWNER' and user.branch_id!=ret.branch_id: raise ValidationError('لا يمكنك اعتماد مرتجع خارج فرعك.')
    if not location or location.kind != location.Kind.BRANCH or location.branch_id != ret.branch_id: raise ValidationError('موقع المرتجع يجب أن يكون مخزن الفرع.')
    items=list(ret.items.select_related('sale_item','sale_item__product').order_by('sale_item_id'))
    if not items: raise ValidationError('لا يمكن اعتماد مرتجع بدون أصناف.')
    total=Decimal('0')
    for ri in items:
        if ri.raw_weight<=0 or ri.raw_weight>ri.sale_item.raw_weight: raise ValidationError('كمية المرتجع غير صالحة.')
        already=SalesReturnItem.objects.filter(
            sale_item=ri.sale_item, sales_return__status=SalesReturn.Status.APPROVED
        ).exclude(sales_return=ret).aggregate(v=Sum('raw_weight'))['v'] or Decimal('0')
        if already + Decimal(ri.raw_weight) > Decimal(ri.sale_item.raw_weight):
            raise ValidationError(f'الكمية المرتجعة للصنف {ri.sale_item.product.name} تتجاوز الكمية المتاحة للمرتجع.')
        raw_sold=Decimal(ri.sale_item.raw_weight)
        unit_price_raw=Decimal(ri.sale_item.sale_amount)/raw_sold if raw_sold else Decimal('0')
        amount=money(Decimal(ri.raw_weight)*unit_price_raw)
        ri.refund_amount=amount; ri.save(update_fields=['refund_amount'])
        apply_movement(product=ri.sale_item.product, location=location, movement_type=StockMovement.Type.SALES_RETURN,
                       quantity=ri.raw_weight, unit_cost=ri.sale_item.unit_cost, user=user,
                       reference_type='SalesReturnItem', reference_id=ri.pk, reason=ret.reason)
        total += amount
    ret.refund_amount=money(total); ret.status=SalesReturn.Status.APPROVED; ret.approved_by=user; ret.approved_at=timezone.now()
    ret.save(update_fields=['refund_amount','status','approved_by','approved_at'])
    sale_items=list(ret.sale.items.all())
    fully_returned=True
    for si in sale_items:
        returned=SalesReturnItem.objects.filter(sale_item=si, sales_return__status=SalesReturn.Status.APPROVED).aggregate(v=Sum('raw_weight'))['v'] or Decimal('0')
        if returned < Decimal(si.raw_weight):
            fully_returned=False; break
    if fully_returned and sale_items:
        ret.sale.status=Sale.Status.REFUNDED
        ret.sale.save(update_fields=['status'])
    PaymentTransaction.objects.create(branch=ret.branch, shift=None, amount=ret.refund_amount,
        payment_method=ret.payment_method, direction=PaymentTransaction.Direction.OUT,
        reference_type='SalesReturn', reference_id=ret.pk, created_by=user)
    log_event(user=user, action='APPROVE', entity='SalesReturn', entity_id=ret.pk,
              new_value={'refund_amount':str(ret.refund_amount),'sale_id':ret.sale_id}, request=request)
    return ret

@transaction.atomic
def cancel_sales_return(*, sales_return, user, request=None):
    ret=SalesReturn.objects.select_for_update().get(pk=sales_return.pk)
    if ret.status!=SalesReturn.Status.DRAFT: raise ValidationError('لا يمكن إلغاء مرتجع معتمد أو ملغى.')
    if not user.is_superuser and getattr(user,'role',None) not in {'OWNER','ACCOUNTANT','BRANCH_MANAGER'}: raise ValidationError('لا تملك صلاحية إلغاء المرتجع.')
    if not user.is_superuser and getattr(user,'role',None)!='OWNER' and user.branch_id!=ret.branch_id: raise ValidationError('لا يمكنك إلغاء مرتجع خارج فرعك.')
    ret.status=SalesReturn.Status.CANCELLED; ret.cancelled_at=timezone.now(); ret.save(update_fields=['status','cancelled_at'])
    log_event(user=user, action='CANCEL', entity='SalesReturn', entity_id=ret.pk, request=request)
    return ret
