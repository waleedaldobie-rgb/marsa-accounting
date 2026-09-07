from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.accounts.permissions import has_role
from apps.sales.models import PaymentTransaction, Shift
from .models import ShiftClosing


def expected_cash_for_shift(shift):
    """Cash expected in the drawer: opening cash + cash IN - cash OUT for this shift."""
    opening = Decimal(shift.opening_cash or 0)
    incoming = PaymentTransaction.objects.filter(
        shift=shift, payment_method=PaymentTransaction.Method.CASH,
        direction=PaymentTransaction.Direction.IN,
    ).values_list('amount', flat=True)
    outgoing = PaymentTransaction.objects.filter(
        shift=shift, payment_method=PaymentTransaction.Method.CASH,
        direction=PaymentTransaction.Direction.OUT,
    ).values_list('amount', flat=True)
    return opening + sum(incoming, Decimal('0')) - sum(outgoing, Decimal('0'))


@transaction.atomic
def create_closing(*, shift, actual_cash, user):
    shift = Shift.objects.select_for_update().get(pk=shift.pk)
    if shift.status != Shift.Status.OPEN:
        raise ValidationError('لا يمكن إنشاء إغلاق لوردية مغلقة.')
    if not has_role(user, 'OWNER', 'ACCOUNTANT') and shift.cashier_id != user.pk:
        raise ValidationError('لا يمكنك إغلاق وردية ليست ورديتك.')
    actual_cash = Decimal(actual_cash)
    if actual_cash < 0:
        raise ValidationError('النقد الفعلي لا يمكن أن يكون سالبًا.')
    expected = expected_cash_for_shift(shift)
    closing, created = ShiftClosing.objects.select_for_update().get_or_create(
        shift=shift,
        defaults={'expected_cash': expected, 'actual_cash': actual_cash,
                  'difference': actual_cash - expected, 'status': ShiftClosing.Status.DRAFT},
    )
    if not created:
        if closing.status != ShiftClosing.Status.DRAFT:
            raise ValidationError('يوجد إغلاق نهائي لهذه الوردية بالفعل.')
        expected = expected_cash_for_shift(shift)
        closing.expected_cash = expected
        closing.actual_cash = actual_cash
        closing.difference = actual_cash - expected
        closing.save(update_fields=['expected_cash', 'actual_cash', 'difference'])
    return closing


@transaction.atomic
def approve_closing(*, closing, user):
    closing = ShiftClosing.objects.select_for_update().select_related('shift', 'shift__branch').get(pk=closing.pk)
    if closing.status == ShiftClosing.Status.APPROVED:
        return closing
    if closing.status != ShiftClosing.Status.DRAFT:
        raise ValidationError('لا يمكن اعتماد هذا الإغلاق في حالته الحالية.')
    if not has_role(user, 'OWNER', 'ACCOUNTANT'):
        raise ValidationError('اعتماد الإغلاق متاح للمالك والمحاسب فقط.')
    if not user.is_superuser and user.branch_id != closing.shift.branch_id:
        raise ValidationError('لا يمكنك اعتماد إغلاق خارج فرعك.')
    shift = Shift.objects.select_for_update().get(pk=closing.shift_id)
    if shift.status != Shift.Status.OPEN:
        raise ValidationError('الوردية مغلقة بالفعل.')
    expected = expected_cash_for_shift(shift)
    closing.expected_cash = expected
    closing.difference = closing.actual_cash - expected
    closing.status = ShiftClosing.Status.APPROVED
    closing.approved_by = user
    closing.approved_at = timezone.now()
    closing.save(update_fields=['expected_cash', 'difference', 'status', 'approved_by', 'approved_at'])
    shift.status = Shift.Status.CLOSED
    shift.closed_at = timezone.now()
    shift.save(update_fields=['status', 'closed_at'])
    return closing


@transaction.atomic
def reject_closing(*, closing, user):
    closing = ShiftClosing.objects.select_for_update().get(pk=closing.pk)
    if closing.status != ShiftClosing.Status.DRAFT:
        raise ValidationError('لا يمكن رفض إغلاق غير مسودة.')
    if not has_role(user, 'OWNER', 'ACCOUNTANT'):
        raise ValidationError('رفض الإغلاق متاح للمالك والمحاسب فقط.')
    closing.status = ShiftClosing.Status.REJECTED
    closing.approved_by = user
    closing.approved_at = timezone.now()
    closing.save(update_fields=['status', 'approved_by', 'approved_at'])
    return closing
