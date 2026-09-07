from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.branches.models import Branch, Location
from apps.catalog.models import Product
from .models import StockBalance, StockMovement, WasteAdjustment
from .services import apply_movement
from .waste_services import approve_waste


class WasteWorkflowTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.branch = Branch.objects.create(code='BR01', name='الفرع 1')
        self.location = Location.objects.create(name='الفرع 1 - مخزن', kind=Location.Kind.BRANCH, branch=self.branch)
        self.user = User.objects.create_user(username='manager', password='x', role='BRANCH_MANAGER', branch=self.branch)
        self.product = Product.objects.create(name='سمك تجريبي', sku='FISH-01')
        apply_movement(product=self.product, location=self.location, movement_type=StockMovement.Type.PURCHASE_IN, quantity=Decimal('10'), unit_cost=Decimal('5'), user=self.user, reference_type='Test', reference_id='1')

    def test_draft_has_no_stock_effect(self):
        waste = WasteAdjustment.objects.create(branch=self.branch, location=self.location, product=self.product, quantity=Decimal('2'), waste_type=WasteAdjustment.WasteType.SPOILAGE, reason='تلف', created_by=self.user)
        self.assertEqual(StockBalance.objects.get(product=self.product, location=self.location).quantity, Decimal('10'))
        self.assertEqual(waste.status, WasteAdjustment.Status.DRAFT)

    def test_approved_waste_reduces_stock_and_records_cost(self):
        waste = WasteAdjustment.objects.create(branch=self.branch, location=self.location, product=self.product, quantity=Decimal('2'), waste_type=WasteAdjustment.WasteType.SPOILAGE, reason='تلف', created_by=self.user)
        approve_waste(waste=waste, user=self.user)
        balance = StockBalance.objects.get(product=self.product, location=self.location)
        movement = StockMovement.objects.get(reference_type='WasteAdjustment', reference_id=str(waste.pk))
        self.assertEqual(balance.quantity, Decimal('8'))
        self.assertEqual(movement.unit_cost, Decimal('5'))
        self.assertEqual(waste.status, WasteAdjustment.Status.APPROVED)

    def test_insufficient_stock_rolls_back(self):
        waste = WasteAdjustment.objects.create(branch=self.branch, location=self.location, product=self.product, quantity=Decimal('11'), waste_type=WasteAdjustment.WasteType.SPOILAGE, reason='تلف', created_by=self.user)
        with self.assertRaises((ValidationError, ValueError)):
            approve_waste(waste=waste, user=self.user)
        self.assertEqual(StockBalance.objects.get(product=self.product, location=self.location).quantity, Decimal('10'))
        self.assertFalse(StockMovement.objects.filter(reference_type='WasteAdjustment', reference_id=str(waste.pk)).exists())
