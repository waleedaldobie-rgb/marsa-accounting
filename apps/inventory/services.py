from decimal import Decimal
from django.db import IntegrityError, transaction
from .models import StockBalance, StockMovement

IN_TYPES = {StockMovement.Type.PURCHASE_IN, StockMovement.Type.TRANSFER_IN, StockMovement.Type.ADJUSTMENT_IN, StockMovement.Type.SALES_RETURN}
OUT_TYPES = {StockMovement.Type.TRANSFER_OUT, StockMovement.Type.SALE_OUT, StockMovement.Type.WASTE_OUT, StockMovement.Type.ADJUSTMENT_OUT, StockMovement.Type.PURCHASE_RETURN}


def _decimal(value):
    try:
        return Decimal(value)
    except Exception as exc:
        raise ValueError('Invalid decimal value.') from exc


def _get_locked_balance(*, product, location, initial_cost):
    balance = StockBalance.objects.select_for_update().filter(product=product, location=location).first()
    if balance:
        return balance
    try:
        with transaction.atomic():
            balance = StockBalance.objects.create(product=product, location=location, quantity=0, average_cost=initial_cost)
    except IntegrityError:
        balance = StockBalance.objects.get(product=product, location=location)
    return StockBalance.objects.select_for_update().get(pk=balance.pk)


def _existing_reference(*, reference_type, reference_id, movement_type, product_id, location_id):
    if not reference_type or not reference_id:
        return None
    return StockMovement.objects.filter(
        reference_type=reference_type, reference_id=str(reference_id), movement_type=movement_type,
        product_id=product_id, location_id=location_id,
    ).first()


@transaction.atomic
def apply_movement(*, product, location, movement_type, quantity, unit_cost=Decimal('0'), user=None, reference_type='', reference_id='', reason=''):
    quantity = _decimal(quantity)
    requested_cost = _decimal(unit_cost)
    if quantity <= 0:
        raise ValueError('Movement quantity must be positive.')
    if movement_type == StockMovement.Type.CORRECTION:
        raise ValueError('Use an approved correction workflow; do not post CORRECTION directly.')
    if movement_type not in IN_TYPES | OUT_TYPES:
        raise ValueError('Unsupported movement type.')

    existing = _existing_reference(reference_type=reference_type, reference_id=reference_id, movement_type=movement_type, product_id=product.pk, location_id=location.pk)
    if existing:
        if existing.quantity != quantity:
            raise ValueError('Reference already exists with a different quantity.')
        return existing

    balance = _get_locked_balance(product=product, location=location, initial_cost=requested_cost)
    old_qty, old_cost = balance.quantity, balance.average_cost

    if movement_type in OUT_TYPES:
        if old_qty < quantity:
            raise ValueError('Insufficient stock.')
        movement_cost = old_cost
        balance.quantity = old_qty - quantity
    else:
        movement_cost = requested_cost
        new_qty = old_qty + quantity
        balance.average_cost = ((old_qty * old_cost) + (quantity * movement_cost)) / new_qty if new_qty else Decimal('0')
        balance.quantity = new_qty

    balance.save(update_fields=['quantity', 'average_cost', 'updated_at'])
    return StockMovement.objects.create(
        product=product, location=location, movement_type=movement_type,
        quantity=quantity, unit_cost=movement_cost, total_cost=quantity * movement_cost,
        reference_type=reference_type, reference_id=str(reference_id), reason=reason, created_by=user,
    )
