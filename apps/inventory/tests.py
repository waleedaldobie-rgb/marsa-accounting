from decimal import Decimal
from django.test import SimpleTestCase

class WeightedAverageCostTests(SimpleTestCase):
    def test_weighted_average_formula(self):
        old_qty, old_cost = Decimal('100'), Decimal('20')
        new_qty, new_cost = Decimal('50'), Decimal('30')
        result = ((old_qty*old_cost)+(new_qty*new_cost))/(old_qty+new_qty)
        self.assertEqual(result.quantize(Decimal('0.01')), Decimal('23.33'))
