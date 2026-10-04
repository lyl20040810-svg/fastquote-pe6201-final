from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastquote.catalog import Catalog
from fastquote.pricing import calculate_quote


class PricingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.row = Catalog(ROOT / "data" / "price_list.json").find("DIN933", "M16", 50)

    def test_one_carton_gets_three_percent_discount(self):
        quote = calculate_quote(self.row, 1, "carton")
        self.assertEqual(quote["total_pieces"], 210)
        self.assertEqual(quote["discount_rate"], 0.03)
        self.assertEqual(quote["base_selling_price_per_thousand_cny"], 2722.0)
        self.assertEqual(quote["discounted_price_per_thousand_cny"], 2640.34)
        self.assertEqual(quote["small_order_surcharge_cny"], 0.0)
        self.assertEqual(quote["approval_status"], "normal")

    def test_five_cartons_get_five_percent_discount(self):
        quote = calculate_quote(self.row, 5, "carton")
        self.assertEqual(quote["discount_rate"], 0.05)
        self.assertGreaterEqual(quote["gross_margin_percent"], 10)

    def test_ten_cartons_get_ten_percent_discount_without_approval(self):
        quote = calculate_quote(self.row, 10, "carton")
        self.assertEqual(quote["discount_rate"], 0.10)
        self.assertEqual(quote["gross_margin_percent"], 11.11)
        self.assertEqual(quote["approval_status"], "normal")

    def test_small_order_can_still_need_manager_approval(self):
        quote = calculate_quote(self.row, 18, "piece")
        self.assertEqual(quote["small_order_surcharge_cny"], 5.0)
        self.assertEqual(quote["gross_margin_percent"], 9.8)
        self.assertEqual(quote["approval_status"], "manager_approval")

    def test_less_than_one_box_adds_five_yuan_to_cost(self):
        quote = calculate_quote(self.row, 34, "piece")
        self.assertEqual(quote["total_pieces"], 34)
        self.assertEqual(quote["small_order_surcharge_cny"], 5.0)
        self.assertEqual(quote["goods_cost_cny"], 74.04)
        self.assertEqual(quote["total_cost_cny"], 79.04)

    def test_exactly_one_box_does_not_add_surcharge(self):
        quote = calculate_quote(self.row, 1, "box")
        self.assertEqual(quote["total_pieces"], 35)
        self.assertEqual(quote["small_order_surcharge_cny"], 0.0)
        self.assertEqual(quote["goods_cost_cny"], quote["total_cost_cny"])

    def test_two_boxes_do_not_add_surcharge(self):
        quote = calculate_quote(self.row, 2, "box")
        self.assertEqual(quote["small_order_surcharge_cny"], 0.0)

    def test_invalid_quantity_rejected(self):
        with self.assertRaises(ValueError):
            calculate_quote(self.row, 0, "box")


if __name__ == "__main__":
    unittest.main()

