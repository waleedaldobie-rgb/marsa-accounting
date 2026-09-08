from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

from apps.branches.models import Branch, Location
from apps.catalog.models import Product
from apps.inventory.models import StockBalance, StockMovement
from apps.sales.models import Sale, Shift
from apps.delivery.models import Platform
from apps.delivery.services import create_delivery_order
from django.core.exceptions import ValidationError


class ApiSprint19Tests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.branch_a = Branch.objects.create(code="A", name="فرع A")
        self.branch_b = Branch.objects.create(code="B", name="فرع B")
        self.location_a = Location.objects.create(name="مخزن A", kind=Location.Kind.BRANCH, branch=self.branch_a)
        self.location_b = Location.objects.create(name="مخزن B", kind=Location.Kind.BRANCH, branch=self.branch_b)
        self.user = User.objects.create_user(username="cashier-a", password="secret", role="CASHIER", branch=self.branch_a)
        self.other = User.objects.create_user(username="cashier-b", password="secret", role="CASHIER", branch=self.branch_b)
        self.product = Product.objects.create(name="هامور", sku="HAM-1")

    def authenticate(self, username="cashier-a"):
        response = self.client.post(reverse("api-v1:token"), {"username": username, "password": "secret"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {response.data['token']}")

    def test_authentication_is_required(self):
        response = self.client.get(reverse("api-v1:inventory"))
        self.assertEqual(response.status_code, 401)

    def test_token_authentication_and_me(self):
        self.authenticate()
        response = self.client.get(reverse("api-v1:me"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["username"], "cashier-a")

    def test_branch_isolation_for_inventory(self):
        StockBalance.objects.create(product=self.product, location=self.location_a, quantity=10, average_cost=4)
        StockBalance.objects.create(product=self.product, location=self.location_b, quantity=20, average_cost=5)
        self.authenticate()
        response = self.client.get(reverse("api-v1:inventory"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["balances"]), 1)
        self.assertEqual(response.data["balances"][0]["location"], self.location_a.pk)

    def test_sale_draft_uses_service_and_rejects_invalid_weight(self):
        shift = Shift.objects.create(branch=self.branch_a, cashier=self.user, opening_cash=0)
        self.authenticate()
        response = self.client.post(reverse("api-v1:sales"), {"shift": shift.pk, "items": [{"product": self.product.pk, "raw_weight": "1", "cleaned_weight": "2", "unit_price": "30"}]}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Sale.objects.count(), 0)

    def test_sale_draft_and_issue_preserve_inventory_rules(self):
        shift = Shift.objects.create(branch=self.branch_a, cashier=self.user, opening_cash=0)
        StockBalance.objects.create(product=self.product, location=self.location_a, quantity=10, average_cost=Decimal("4"))
        self.authenticate()
        response = self.client.post(reverse("api-v1:sales"), {"shift": shift.pk, "items": [{"product": self.product.pk, "raw_weight": "2", "cleaned_weight": "1.5", "unit_price": "30"}]}, format="json")
        self.assertEqual(response.status_code, 201)
        sale_id = response.data["id"]
        response = self.client.post(reverse("api-v1:sale-issue", kwargs={"pk": sale_id}), {"location": self.location_a.pk, "payment_method": "CASH"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "ISSUED")
        self.assertTrue(StockMovement.objects.filter(movement_type="SALE_OUT", reference_type="SaleItem").exists())

    def test_branch_isolation_blocks_issue_of_other_branch_sale(self):
        other_shift = Shift.objects.create(branch=self.branch_b, cashier=self.other, opening_cash=0)
        self.client.force_authenticate(self.other)
        create = self.client.post(reverse("api-v1:sales"), {"shift": other_shift.pk, "items": [{"product": self.product.pk, "raw_weight": "1", "cleaned_weight": "1", "unit_price": "20"}]}, format="json")
        self.assertEqual(create.status_code, 201)
        self.client.force_authenticate(self.user)
        issue = self.client.post(reverse("api-v1:sale-issue", kwargs={"pk": create.data["id"]}), {"location": self.location_b.pk}, format="json")
        self.assertEqual(issue.status_code, 404)

    def test_direct_object_access_to_other_branch_is_hidden(self):
        shift = Shift.objects.create(branch=self.branch_b, cashier=self.other, opening_cash=0)
        sale = Sale.objects.create(invoice_no="B-1", shift=shift, branch=self.branch_b, created_by=self.other)
        self.authenticate()
        response = self.client.get(reverse("api-v1:sale-detail", kwargs={"pk": sale.pk}))
        self.assertEqual(response.status_code, 404)

    def test_cashier_cannot_escalate_to_catalog_write(self):
        self.authenticate()
        response = self.client.post(reverse("api-v1:catalog"), {"name": "محاولة", "sku": "ESC-1", "description": ""}, format="json")
        self.assertEqual(response.status_code, 403)

    def test_unauthorized_api_post_is_rejected(self):
        response = self.client.post(reverse("api-v1:shifts"), {"branch": self.branch_a.pk, "opening_cash": "0"}, format="json")
        self.assertEqual(response.status_code, 401)

    def test_branch_id_tampering_is_rejected(self):
        self.authenticate()
        response = self.client.post(reverse("api-v1:shifts"), {"branch": self.branch_b.pk, "opening_cash": "0"}, format="json")
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Shift.objects.filter(cashier=self.user).exists())

    def test_cashier_can_open_pos_issue_and_view_sale(self):
        shift = Shift.objects.create(branch=self.branch_a, cashier=self.user, opening_cash=0)
        StockBalance.objects.create(product=self.product, location=self.location_a, quantity=10, average_cost=Decimal("4"))
        self.authenticate()
        create = self.client.post(reverse("api-v1:sales"), {"shift": shift.pk, "items": [{"product": self.product.pk, "raw_weight": "1", "cleaned_weight": "1", "unit_price": "20"}]}, format="json")
        self.assertEqual(create.status_code, 201)
        issue = self.client.post(reverse("api-v1:sale-issue", kwargs={"pk": create.data["id"]}), {"location": self.location_a.pk}, format="json")
        self.assertEqual(issue.status_code, 200)
        detail = self.client.get(reverse("api-v1:sale-detail", kwargs={"pk": create.data["id"]}))
        self.assertEqual(detail.status_code, 200)

    def test_delivery_service_cannot_cross_branch(self):
        sale = Sale.objects.create(invoice_no="B-DEL-1", shift=Shift.objects.create(branch=self.branch_b, cashier=self.other), branch=self.branch_b, created_by=self.other, status=Sale.Status.ISSUED, total=100)
        platform = Platform.objects.create(name="منصة B", commission_rate=0)
        with self.assertRaises(ValidationError):
            create_delivery_order(sale=sale, platform=platform, external_order_no="B-1", user=self.user)
