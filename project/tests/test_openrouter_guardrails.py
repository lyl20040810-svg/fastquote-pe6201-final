"""Regression cases for the first 50-case OpenRouter evaluation."""

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastquote.extractor import extract_with_openrouter
from fastquote.service import QuoteService


class OpenRouterGuardrailTests(unittest.TestCase):
    def extract(self, request, **overrides):
        parsed = {
            "standard": "DIN933",
            "diameter": "M16",
            "length_mm": 55,
            "quantity": 1,
            "unit": "box",
            "needs_clarification": False,
            "clarification_reason": "",
            "reply_template": "We can offer {{SPEC}} for {{QUANTITY}} {{UNIT}} at CNY {{TOTAL_PRICE}}.",
        }
        parsed.update(overrides)
        response = MagicMock()
        response.read.return_value = json.dumps({
            "choices": [{"message": {"content": json.dumps(parsed)}}]
        }).encode("utf-8")
        response.__enter__.return_value = response
        with patch("fastquote.extractor.urllib.request.urlopen", return_value=response):
            return extract_with_openrouter(request, [], "test-key", "test-model")

    def test_chinese_carton_overrides_model_box(self):
        result = self.extract("M16×55，麻烦给我来 1 箱。")
        self.assertEqual((result.quantity, result.unit), (1, "carton"))
        self.assertFalse(result.needs_clarification)

    def test_missing_unit_is_not_guessed(self):
        result = self.extract("M14×150，50。", diameter="M14", length_mm=150, quantity=50, unit="piece")
        self.assertTrue(result.needs_clarification)

    def test_model_clarification_is_not_overridden(self):
        result = self.extract(
            "M22×80，数量大概 5 箱。", diameter="M22", length_mm=80,
            quantity=5, unit="box", needs_clarification=True,
            clarification_reason="Quantity is approximate.",
        )
        self.assertTrue(result.needs_clarification)

    def test_approximate_quantity_is_flagged_even_when_model_quotes(self):
        result = self.extract("M22×80，数量大概 5 箱。", diameter="M22", length_mm=80,
                              quantity=5, unit="box")
        self.assertTrue(result.needs_clarification)

    def test_two_lengths_are_flagged(self):
        result = self.extract("M33×100/120，10箱，两个长度客户都可以。",
                              diameter="M33", length_mm=100, quantity=10)
        self.assertTrue(result.needs_clarification)

    def test_english_box_remains_box(self):
        result = self.extract("Please quote M16x55, 2 boxes.", quantity=2)
        self.assertEqual(result.unit, "box")
        self.assertFalse(result.needs_clarification)

    def test_incomplete_reply_gets_exact_total(self):
        service = QuoteService(ROOT)
        quote = service.quote("Please quote M16x50, 2 cartons.", mode="rules")
        extraction, _ = service.extract("Please quote M16x50, 2 cartons.", mode="rules")
        reply = service._fill_reply(
            "Please contact us for a formal price.",
            quote["catalog_match"], extraction, quote["pricing"],
        )
        self.assertIn(f'CNY {quote["pricing"]["revenue_cny"]:,.2f}', reply)
        self.assertIn("2 cartons", reply)


if __name__ == "__main__":
    unittest.main()
