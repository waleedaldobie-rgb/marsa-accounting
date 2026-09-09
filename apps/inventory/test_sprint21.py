from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.audit.models import AuditLog
from apps.branches.models import Branch, Location
from apps.catalog.models import Product
from apps.inventory.adjustment_services import approve_adjustment, create_adjustment
from apps.inventory.models import StockAdjustment, StockBalance, StockMovement


class StockAdjustmentSprint21Tests(TestCase):
    def setUp(self):
        self.branch_a = Branch.objects.create(code='ADJ-A', name='Adjustment A')
        self.branch_b = Branch.objects.create(code='ADJ-B', name='Adjustment B')
        self.location_a = Location.objects.create(name='A warehouse', kind=Location.Kind.BRANCH, branch=self.branch_a)
        self.location_b = Location.objects.create(name='B warehouse', kind=Location.Kind.BRANCH, branch=self.branch_b)
        self.manager = User.objects.create_user(username='manager-adj', password='x', role=User.Role.BRANCH_MANAGER, branch=self.branch_a)
        self.accountant = User.objects.create_user(username='accountant-adj', password='x', role=User.Role.ACCOUNTANT, branch=self.branch_a)
        self.other = User.objects.create_user(username='other-adj', password='x', role=User.Role.BRANCH_MANAGER, branch=self.branch_b)
        self.product = Product.objects.create(name='Adjustment fish', sku='ADJ-1')
        self.balance = StockBalance.objects.create(product=self.product, location=self.location_a, quantity=10, average_cost=4)

    def test_adjustment_lifecycle_changes_stock_only_on_approval(self):
        adjustment = create_adjustment(user=self.manager, branch=self.branch_a, location=self.location_a, reason='جرد دوري', items=[{'product': self.product, 'counted_quantity': Decimal('8')}])
        self.balance.refresh_from_db()
        self.assertEqual(self.balance.quantity, Decimal('10'))
        approve_adjustment(adjustment=adjustment, user=self.accountant)
        self.balance.refresh_from_db()
        self.assertEqual(self.balance.quantity, Decimal('8'))
        self.assertEqual(StockMovement.objects.filter(reference_type='StockAdjustment', reference_id=str(adjustment.pk)).count(), 1)
        self.assertEqual(AuditLog.objects.filter(entity='StockAdjustment', entity_id=str(adjustment.pk)).count(), 1)

    def test_duplicate_approval_does_not_duplicate_movement(self):
        adjustment = create_adjustment(user=self.manager, branch=self.branch_a, location=self.location_a, reason='جرد', items=[{'product': self.product, 'counted_quantity': Decimal('12')}])
        approve_adjustment(adjustment=adjustment, user=self.accountant)
        approve_adjustment(adjustment=adjustment, user=self.accountant)
        self.assertEqual(StockMovement.objects.filter(reference_type='StockAdjustment', reference_id=str(adjustment.pk)).count(), 1)

    def test_wrong_branch_cannot_approve(self):
        adjustment = create_adjustment(user=self.manager, branch=self.branch_a, location=self.location_a, reason='جرد', items=[{'product': self.product, 'counted_quantity': Decimal('9')}])
        with self.assertRaises(ValidationError):
            approve_adjustment(adjustment=adjustment, user=self.other)

    def test_stale_system_quantity_is_rejected(self):
        adjustment = create_adjustment(user=self.manager, branch=self.branch_a, location=self.location_a, reason='جرد', items=[{'product': self.product, 'counted_quantity': Decimal('9')}])
        self.balance.quantity = 11
        self.balance.save(update_fields=['quantity'])
        with self.assertRaises(ValidationError):
            approve_adjustment(adjustment=adjustment, user=self.accountant)


class Sprint21ApiTests(APITestCase):
    def setUp(self):
        self.branch = Branch.objects.create(code='API-A', name='API A')
        self.location = Location.objects.create(name='API warehouse', kind=Location.Kind.BRANCH, branch=self.branch)
        self.owner = User.objects.create_user(username='owner-21', password='x', role=User.Role.OWNER, branch=self.branch)
        self.manager = User.objects.create_user(username='manager-21', password='x', role=User.Role.BRANCH_MANAGER, branch=self.branch)

    def test_audit_is_read_only_and_anonymous_is_denied(self):
        self.assertEqual(self.client.get(reverse('api-v1:audit')).status_code, 401)
        self.client.force_authenticate(self.manager)
        self.assertEqual(self.client.get(reverse('api-v1:audit')).status_code, 403)
        self.client.force_authenticate(self.owner)
        self.assertEqual(self.client.post(reverse('api-v1:audit'), {}).status_code, 405)

    def test_owner_can_create_user_without_exposing_password(self):
        self.client.force_authenticate(self.owner)
        response = self.client.post(reverse('api-v1:users'), {'username': 'new-user-21', 'password': 'Strong-pass-21', 'role': 'CASHIER', 'branch': self.branch.pk}, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertNotIn('password', response.data)
        user = User.objects.get(username='new-user-21')
        self.assertTrue(user.check_password('Strong-pass-21'))

    def test_owner_cannot_disable_last_owner(self):
        self.client.force_authenticate(self.owner)
        response = self.client.patch(reverse('api-v1:user-detail', kwargs={'pk': self.owner.pk}), {'is_active': False}, format='json')
        self.assertEqual(response.status_code, 403)


class Sprint21WebUiTests(TestCase):
    def setUp(self):
        self.branch = Branch.objects.create(code='WEB-A', name='Web A')
        self.location = Location.objects.create(name='Web warehouse', kind=Location.Kind.BRANCH, branch=self.branch)
        self.owner = User.objects.create_user(username='owner-web-21', password='x', role=User.Role.OWNER, branch=self.branch)
        self.manager = User.objects.create_user(username='manager-web-21', password='x', role=User.Role.BRANCH_MANAGER, branch=self.branch)
        self.cashier = User.objects.create_user(username='cashier-web-21', password='x', role=User.Role.CASHIER, branch=self.branch)
        self.product = Product.objects.create(name='Web fish', sku='WEB-1')

    def test_adjustment_pages_are_reachable_and_cashier_is_denied(self):
        self.client.force_login(self.manager)
        self.assertEqual(self.client.get(reverse('inventory:adjustment_list')).status_code, 200)
        self.assertEqual(self.client.get(reverse('inventory:adjustment_create')).status_code, 200)
        self.client.force_login(self.cashier)
        self.assertEqual(self.client.get(reverse('inventory:adjustment_list')).status_code, 403)

    def test_audit_and_user_pages_are_owner_only_as_defined(self):
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(reverse('audit:list')).status_code, 200)
        self.assertEqual(self.client.get(reverse('accounts:user_list')).status_code, 200)
        self.client.force_login(self.cashier)
        self.assertEqual(self.client.get(reverse('audit:list')).status_code, 403)
        self.assertEqual(self.client.get(reverse('accounts:user_list')).status_code, 403)

    def test_web_adjustment_create_saves_draft(self):
        self.client.force_login(self.manager)
        response = self.client.post(reverse('inventory:adjustment_create'), {'location': self.location.pk, 'product': self.product.pk, 'counted_quantity': '3', 'reason': 'جرد واجهة', 'item_reason': 'ملاحظة'}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(StockAdjustment.objects.filter(created_by=self.manager, status=StockAdjustment.Status.DRAFT).exists())
