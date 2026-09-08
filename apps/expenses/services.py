from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.sales.models import PaymentTransaction, Shift
from .models import Expense
from django.utils import timezone
from apps.audit.services import log_event
from apps.accounts.permissions import has_permission, require_same_branch


@transaction.atomic
def approve_expense(*, expense, user):
    expense = Expense.objects.select_for_update().select_related('branch').get(pk=expense.pk)
    if expense.status == Expense.Status.APPROVED:
        return expense
    if expense.status != Expense.Status.DRAFT:
        raise ValidationError('لا يمكن اعتماد المصروف في حالته الحالية.')
    if expense.amount <= 0:
        raise ValidationError('قيمة المصروف يجب أن تكون أكبر من صفر.')
    if not has_permission(user, 'approve_expenses'):
        raise ValidationError('اعتماد المصاريف متاح للمالك والمحاسب فقط.')
    if not require_same_branch(user, expense.branch_id):
        raise ValidationError('لا يمكنك اعتماد مصروف خارج فرعك.')

    shift = None
    if expense.payment_method == PaymentTransaction.Method.CASH:
        if not expense.shift_id:
            raise ValidationError('المصروف النقدي يجب ربطه بورديّة مفتوحة.')
        shift = Shift.objects.select_for_update().filter(pk=expense.shift_id, branch_id=expense.branch_id).first()
        if not shift or shift.status != Shift.Status.OPEN:
            raise ValidationError('الوردية المرتبطة بالمصروف النقدي غير موجودة أو مغلقة.')
    PaymentTransaction.objects.create(
        branch=expense.branch,
        shift=shift,
        amount=Decimal(expense.amount),
        payment_method=expense.payment_method,
        direction=PaymentTransaction.Direction.OUT,
        reference_type='Expense',
        reference_id=expense.pk,
        created_by=user,
    )
    expense.status = Expense.Status.APPROVED
    expense.approved_by = user
    expense.approved_at = timezone.now()
    expense.save(update_fields=['status','approved_by','approved_at'])
    log_event(user=user, action='APPROVE', entity='Expense', entity_id=expense.pk, new_value={'amount':str(expense.amount)})
    return expense


@transaction.atomic
def cancel_expense(*, expense, user):
    expense = Expense.objects.select_for_update().get(pk=expense.pk)
    if expense.status != Expense.Status.DRAFT:
        raise ValidationError('لا يمكن إلغاء مصروف معتمد أو ملغى.')
    if not has_permission(user, 'approve_expenses'):
        raise ValidationError('إلغاء المصاريف متاح للمالك والمحاسب فقط.')
    if not require_same_branch(user, expense.branch_id):
        raise ValidationError('لا يمكنك إلغاء مصروف خارج فرعك.')
    expense.status = Expense.Status.CANCELLED
    expense.cancelled_at = timezone.now()
    expense.save(update_fields=['status','cancelled_at'])
    log_event(user=user, action='CANCEL', entity='Expense', entity_id=expense.pk)
    return expense
