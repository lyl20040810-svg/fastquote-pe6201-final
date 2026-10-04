from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastquote.service import QuoteService


class WorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.service = QuoteService(ROOT)

    def test_clear_request_is_quoted(self):
        result = self.service.quote("Please quote M16x50, 2 cartons.", mode="rules")
        self.assertEqual(result["processing_status"], "quoted")
        self.assertEqual(result["extraction"]["standard"], "DIN933")
        self.assertEqual(result["catalog_match"]["sku"], "DIN933-M16x50")
        self.assertEqual(result["catalog_match"]["material"], "A2 stainless steel")
        self.assertEqual(result["pricing"]["total_pieces"], 420)
        self.assertIn("CNY", result["customer_reply_draft"])
        self.assertNotIn("DIN933", result["customer_reply_draft"])
        self.assertNotRegex(result["customer_reply_draft"].lower(), r"margin|approval|10\s*%")

    def test_missing_length_is_flagged(self):
        result = self.service.quote("Need M16 bolts, 3 boxes.", mode="rules")
        self.assertEqual(result["processing_status"], "flagged")
        self.assertEqual(result["flag_reason"], "ambiguous_or_incomplete")

    def test_unsupported_exact_sku_is_flagged(self):
        result = self.service.quote("Quote M18x100, 2 cartons.", mode="rules")
        self.assertEqual(result["processing_status"], "flagged")
        self.assertEqual(result["flag_reason"], "no_exact_catalog_match")

    def test_small_order_requires_approval(self):
        result = self.service.quote("Quote M16x50, 18 pieces.", mode="rules")
        self.assertTrue(result["manager_approval_required"])
        reply = result["customer_reply_draft"].lower()
        self.assertIn("internal manager approval", reply)
        self.assertIn("approval is not guaranteed", reply)
        self.assertIn("lowest price", reply)
        self.assertIn("would like to continue", reply)
        self.assertNotIn("0% discount", reply)
        self.assertNotIn("18 pieces (18 pieces)", reply)
        self.assertNotRegex(reply, r"margin|10\s*%")

        extraction, _ = self.service.extract("Quote M16x50, 18 pieces.", mode="rules")
        unsafe_reply = self.service._fill_reply(
            "This quote requires manager approval because the margin is below 10%.",
            result["catalog_match"],
            extraction,
            result["pricing"],
        )
        unsafe_reply = unsafe_reply.lower()
        self.assertIn("internal manager approval", unsafe_reply)
        self.assertIn("approval is not guaranteed", unsafe_reply)
        self.assertNotRegex(unsafe_reply, r"margin|10\s*%")


if __name__ == "__main__":
    unittest.main()

