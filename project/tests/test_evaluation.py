"""Check that evaluation does not call an unverified quote fully correct."""

from pathlib import Path
import json
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastquote.evaluation import evaluate


class FakeService:
    def quote(self, request, mode):
        return {
            "processing_status": "quoted",
            "extraction": {
                "standard": "DIN933", "diameter": "M16", "length_mm": 50,
                "quantity": 1, "unit": "box",
            },
            "pricing": {"revenue_cny": 95.27, "approval_status": "normal"},
        }


class EvaluationTests(unittest.TestCase):
    def run_case(self, expected):
        with tempfile.TemporaryDirectory() as directory:
            inputs = Path(directory) / "inputs.jsonl"
            answers = Path(directory) / "answers.jsonl"
            inputs.write_text(json.dumps({"id": "1", "request": "M16x50 1 box"}), encoding="utf-8")
            answers.write_text(json.dumps(expected), encoding="utf-8")
            return evaluate(FakeService(), inputs, answers, "rules")

    def test_missing_price_gold_is_not_fully_correct(self):
        expected = self.expected_answer()
        metrics = self.run_case(expected)["metrics"]
        self.assertEqual(metrics["workflow_correct_rate_excluding_arithmetic"], 1.0)
        self.assertIsNone(metrics["end_to_end_fully_correct_rate"])

    def test_wrong_price_fails_arithmetic_and_end_to_end(self):
        expected = self.expected_answer()
        expected["expected_pricing"] = {"revenue_cny": 95.28}
        metrics = self.run_case(expected)["metrics"]
        self.assertEqual(metrics["arithmetic_exact_match_rate"], 0.0)
        self.assertEqual(metrics["end_to_end_fully_correct_rate"], 0.0)

    @staticmethod
    def expected_answer():
        return {
            "id": "1", "expected_processing_status": "quoted",
            "standard": "DIN933", "diameter": "M16", "length_mm": 50,
            "quantity": 1, "unit": "box", "approval_status": "normal",
        }


if __name__ == "__main__":
    unittest.main()
