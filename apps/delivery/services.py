from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from apps.accounts.permissions import has_role
from apps.audit.services import log_event
from apps.sales.models import PaymentTransaction, Sale
from .models import DeliveryOrder, Settlement

@transaction.atomic
def create_delivery_order(*, sale, platform, external_order_no, user):
    sale = Sale.objects.select_for_update().select_related('branch').get(pk=sale.pk)
    if sale.status != Sale.Status.ISSUED:
        raise ValidationError('لا يمكن إنشاء طلب توصيل قبل إصدار الفاتورة.')
    if not has_role(user, 'OWNER', 'ACCOUNTANT') and user.branch_id != sale.branch_id:
        raise ValidationError('لا يمكنك إنشاء توصيل لفرع آخر.')
    if DeliveryOrder.objects.filter(sale=sale).exists():
        return DeliveryOrder.objects.get(sale=sale)
    if not external_order_no.strip():
        raise ValidationError('رقم طلب التوصيل مطلوب.')
    commission = (sale.total * Decimal(platform.commission_rate) / Decimal('100')).quantize(Decimal('0.01'))
    order = DeliveryOrder.objects.create(sale=sale, platform=platform, external_order_no=external_order_no.strip(),
        commission=commission, net_settlement=sale.total - commission)
    log_event(user=user, action='CREATE', entity='DeliveryOrder', entity_id=order.pk,
              new_value={'sale_id': sale.pk, 'platform_id': platform.pk, 'external_order_no': order.external_order_no})
    return order

@transaction.atomic
def update_delivery_status(*, order, status, user, reason=''):
    order = DeliveryOrder.objects.select_for_update().select_related('sale__branch').get(pk=order.pk)
    if not has_role(user, 'OWNER', 'ACCOUNTANT') and user.branch_id != order.sale.branch_id:
        raise ValidationError('لا يمكنك تعديل توصيل لفرع آخر.')
    if order.status == status:
        return order
    old = order.status
    order.status = status
    order.save(update_fields=['status'])
    log_event(user=user, action='STATUS_CHANGE', entity='DeliveryOrder', entity_id=order.pk,
              old_value={'status': old}, new_value={'status': status}, reason=reason)
    return order

@transaction.atomic
def settle_delivery(*, order, amount, user, note=''):
    order = DeliveryOrder.objects.select_for_update().select_related('sale__branch').get(pk=order.pk)
    if not has_role(user, 'OWNER', 'ACCOUNTANT') and user.branch_id != order.sale.branch_id:
        raise ValidationError('لا يمكنك تسوية توصيل لفرع آخر.')
    amount = Decimal(amount)
    if amount <= 0:
        raise ValidationError('قيمة التسوية يجب أن تكون أكبر من صفر.')
    existing = order.settlements.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    if existing + amount > order.net_settlement:
        raise ValidationError('قيمة التسوية تتجاوز صافي المستحق.')
    settlement = Settlement.objects.create(delivery_order=order, amount=amount, settled_at=timezone.now(), note=note)
    PaymentTransaction.objects.create(branch=order.sale.branch, shift=None, amount=amount,
        payment_method=PaymentTransaction.Method.OTHER, direction=PaymentTransaction.Direction.IN,
        reference_type='DeliverySettlement', reference_id=settlement.pk, created_by=user)
    log_event(user=user, action='SETTLE', entity='DeliverySettlement', entity_id=settlement.pk,
              new_value={'delivery_order_id': order.pk, 'amount': str(amount)})
    return settlement
