from django.db import transaction
from django.utils import timezone
from apps.inventory.models import StockBalance, StockMovement
from apps.inventory.services import apply_movement
from apps.accounts.permissions import can_create_transfer, can_receive_transfer
from apps.audit.services import log_event
from .models import Transfer

@transaction.atomic
def send_transfer(*, transfer_id, user):
    t=Transfer.objects.select_for_update().prefetch_related('items').get(pk=transfer_id)
    if not can_create_transfer(user, t.source):
        raise ValueError('لا تملك صلاحية إرسال تحويل من هذا الفرع.')
    if t.status not in (Transfer.Status.APPROVED, Transfer.Status.DRAFT): raise ValueError('Transfer cannot be sent.')
    if t.source_id == t.destination_id: raise ValueError('Source and destination must differ.')
    for i in t.items.all():
        b=StockBalance.objects.select_for_update().filter(product=i.product,location=t.source).first()
        if not b or b.quantity < i.sent_quantity: raise ValueError('Insufficient stock for transfer.')
        apply_movement(product=i.product,location=t.source,movement_type=StockMovement.Type.TRANSFER_OUT,quantity=i.sent_quantity,unit_cost=b.average_cost,user=user,reference_type='Transfer',reference_id=t.pk)
    old_status = t.status
    t.status=Transfer.Status.SENT; t.sent_at=timezone.now(); t.save(update_fields=['status','sent_at'])
    log_event(user=user, branch=t.source.branch, action='SEND', entity='Transfer', entity_id=t.pk,
              old_value={'status': old_status}, new_value={'status': t.status})
    return t

@transaction.atomic
def receive_transfer(*, transfer_id, user):
    t=Transfer.objects.select_for_update().prefetch_related('items').get(pk=transfer_id)
    if not can_receive_transfer(user, t.destination):
        raise ValueError('لا تملك صلاحية استلام تحويل إلى هذا الفرع.')
    if t.status != Transfer.Status.SENT: raise ValueError('Only sent transfers can be received.')
    for i in t.items.all():
        qty=i.received_quantity if i.received_quantity is not None else i.sent_quantity
        if qty < 0 or qty > i.sent_quantity: raise ValueError('Invalid received quantity.')
        source_cost = StockMovement.objects.filter(reference_type='Transfer',reference_id=t.pk,product=i.product,movement_type=StockMovement.Type.TRANSFER_OUT).order_by('-id').values_list('unit_cost',flat=True).first() or 0
        if qty: apply_movement(product=i.product,location=t.destination,movement_type=StockMovement.Type.TRANSFER_IN,quantity=qty,unit_cost=source_cost,user=user,reference_type='Transfer',reference_id=t.pk)
    old_status = t.status
    t.status=Transfer.Status.RECEIVED; t.received_at=timezone.now(); t.save(update_fields=['status','received_at'])
    log_event(user=user, branch=t.destination.branch, action='RECEIVE', entity='Transfer', entity_id=t.pk,
              old_value={'status': old_status}, new_value={'status': t.status})
    return t
