from decimal import Decimal
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.branches.models import Branch
from apps.expenses.models import Expense
from apps.sales.models import PaymentTransaction, Shift, Sale, SaleItem


class ReportsAccessTests(TestCase):
    def setUp(self):
        self.branch = Branch.objects.create(code="BR01", name="فرع 1")
        self.user = User.objects.create_user(username="owner", password="pass", role=User.Role.OWNER)
        self.user.branch = self.branch
        self.user.save(update_fields=["branch"])
        self.client.login(username="owner", password="pass")

    def test_report_pages_are_reachable(self):
        for name in ("reports:dashboard", "reports:sales", "reports:inventory", "reports:waste", "reports:financial_ledger"):
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 200)

    def test_date_filter_is_accepted(self):
        response = self.client.get(reverse("reports:sales"), {"date_from": "2026-01-01", "date_to": "2026-01-31"})
        self.assertEqual(response.status_code, 200)
