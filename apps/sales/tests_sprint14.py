from django.test import SimpleTestCase
from pathlib import Path


class POSContractTests(SimpleTestCase):
    def test_pos_contains_weight_fields(self):
        template = Path(__file__).resolve().parents[2] / "templates" / "sales" / "pos.html"
        text = template.read_text(encoding="utf-8")
        self.assertIn('name="raw_weight"', text)
        self.assertIn('name="cleaned_weight"', text)
        self.assertIn('name="unit_price"', text)

    def test_sales_list_has_filters_and_pagination(self):
        template = Path(__file__).resolve().parents[2] / "templates" / "sales" / "sales.html"
        text = template.read_text(encoding="utf-8")
        self.assertIn('name="q"', text)
        self.assertIn('page_obj.has_other_pages', text)
