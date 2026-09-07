from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.branches.models import Branch
from apps.sales.models import PaymentTransaction
from .models import Expense
from .services import approve_expense, cancel_expense


class ExpenseWorkflowTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.branch = Branch.objects.create(code='BR01', name='الفرع 1')
        self.user = User.objects.create_user(username='accountant', password='x', role='ACCOUNTANT', branch=self.branch)

    def test_draft_has_no_ledger_effect(self):
        expense = Expense.objects.create(branch=self.branch, category='كهرباء', amount=Decimal('100'), payment_method='CASH', created_by=self.user)
        self.assertFalse(PaymentTransaction.objects.filter(reference_type='Expense', reference_id=str(expense.pk)).exists())

    def test_approved_expense_creates_one_out_transaction(self):
        expense = Expense.objects.create(branch=self.branch, category='نقل', amount=Decimal('125.50'), payment_method='CASH', created_by=self.user)
        approve_expense(expense=expense, user=self.user)
        self.assertEqual(expense.status, Expense.Status.APPROVED)
        tx = PaymentTransaction.objects.get(reference_type='Expense', reference_id=str(expense.pk), direction='OUT')
        self.assertEqual(tx.amount, Decimal('125.50'))
        approve_expense(expense=expense, user=self.user)
        self.assertEqual(PaymentTransaction.objects.filter(reference_type='Expense', reference_id=str(expense.pk)).count(), 1)

    def test_cancelled_expense_has_no_ledger_effect(self):
        expense = Expense.objects.create(branch=self.branch, category='أخرى', amount=Decimal('30'), created_by=self.user)
        cancel_expense(expense=expense, user=self.user)
        self.assertEqual(expense.status, Expense.Status.CANCELLED)
        self.assertFalse(PaymentTransaction.objects.filter(reference_type='Expense', reference_id=str(expense.pk)).exists())
