from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from apps.branches.models import Branch, Location
from apps.accounts.models import User
from apps.sales.models import Shift, PaymentTransaction
from .models import ShiftClosing
from .services import create_closing, approve_closing

class ClosingWorkflowTests(TestCase):
    def setUp(self):
        self.branch = Branch.objects.create(code='BR01', name='الفرع الأول')
        self.location = Location.objects.create(name='مخزن الفرع', kind=Location.Kind.BRANCH, branch=self.branch)
        self.cashier = User.objects.create_user(username='cashier', password='x', role=User.Role.CASHIER, branch=self.branch)
        self.accountant = User.objects.create_user(username='accountant', password='x', role=User.Role.ACCOUNTANT, branch=self.branch)
        self.shift = Shift.objects.create(branch=self.branch, cashier=self.cashier, opening_cash=Decimal('100.00'))

    def test_expected_cash_uses_cash_ledger(self):
        PaymentTransaction.objects.create(branch=self.branch, shift=self.shift, amount=Decimal('250.00'), payment_method='CASH', direction='IN', reference_type='Sale', reference_id='1', created_by=self.cashier)
        PaymentTransaction.objects.create(branch=self.branch, shift=self.shift, amount=Decimal('20.00'), payment_method='CARD', direction='IN', reference_type='Sale', reference_id='2', created_by=self.cashier)
        closing = create_closing(shift=self.shift, actual_cash=Decimal('340.00'), user=self.cashier)
        self.assertEqual(closing.expected_cash, Decimal('350.00'))
        self.assertEqual(closing.difference, Decimal('-10.00'))

    def test_approved_closing_closes_shift(self):
        closing = create_closing(shift=self.shift, actual_cash=Decimal('100.00'), user=self.cashier)
        approve_closing(closing=closing, user=self.accountant)
        self.shift.refresh_from_db()
        self.assertEqual(closing.__class__.objects.get(pk=closing.pk).status, ShiftClosing.Status.APPROVED)
        self.assertEqual(self.shift.status, Shift.Status.CLOSED)

    def test_cashier_cannot_approve(self):
        closing = create_closing(shift=self.shift, actual_cash=Decimal('100.00'), user=self.cashier)
        with self.assertRaises(ValidationError):
            approve_closing(closing=closing, user=self.cashier)
