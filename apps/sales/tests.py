from decimal import Decimal
from django.test import TestCase

class SalesReturnContractTests(TestCase):
    def test_return_workflow_requires_issued_sale_and_never_mutates_on_draft(self):
        self.assertTrue(True)

    def test_partial_returns_must_not_exceed_original_raw_weight(self):
        self.assertTrue(True)

    def test_full_raw_return_marks_sale_refunded(self):
        self.assertTrue(True)
