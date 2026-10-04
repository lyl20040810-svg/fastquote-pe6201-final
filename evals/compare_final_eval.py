"""Compare an observed FastQuote CSV against the independent gold audit."""

from __future__ import annotations

import csv
import json
import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path


EXTRACTION_FIELDS = ("sku", "diameter", "length_mm", "request_quantity", "request_unit")
NUMERIC_FIELDS = (
    "list_price_cny", "pieces_per_box", "boxes_per_carton", "pieces_per_carton",
    "total_pieces_unrounded", "carton_equivalent_unrounded", "discount_rate",
    "base_selling_price_per_thousand_unrounded_cny",
    "discounted_price_per_thousand_unrounded_cny", "goods_cost_unrounded_cny",
    "small_order_surcharge_cny", "total_cost_unrounded_cny", "revenue_unrounded_cny",
    "gross_margin_unrounded_percent",
)


def read(path: Path) -> dict[str, dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != len({row["id"] for row in rows}):
        raise ValueError(f"Duplicate IDs in {path}")
    return {row["id"]: row for row in rows}


def numeric_equal(actual: str, expected: str) -> bool:
    if not actual or not expected:
        return False
    a, e = Decimal(actual), Decimal(expected)
    return abs(a - e) <= Decimal("1e-9") * max(Decimal(1), abs(e))


def compare(actual_path: Path, gold_path: Path) -> dict:
    actual, gold = read(actual_path), read(gold_path)
    if set(actual) != set(gold):
        raise ValueError("Actual and gold IDs differ")
    totals = {name: 0 for name in (
        "total", "clear", "flag_expected", "actual_quoted", "actual_flagged", "api_errors",
        "clear_auto", "clear_false_flags", "flag_recalled", "flag_reason_correct",
        "extraction_correct", "approval_correct", "numeric_gold_correct",
        "workflow_correct", "end_to_end_correct", "reply_has_total",
        "correct_extraction_and_reply_has_total",
    )}
    issues = []
    for case_id, expected in gold.items():
        observed = actual[case_id]
        totals["total"] += 1
        status = observed["status"]
        totals["actual_quoted"] += status == "quoted"
        totals["actual_flagged"] += status == "flagged"
        totals["api_errors"] += status == "error"
        expected_flag = expected["status"] == "flagged"
        actual_flag = status == "flagged"
        if expected_flag:
            totals["flag_expected"] += 1
            totals["flag_recalled"] += actual_flag
            flag_ok = actual_flag and observed["flag_reason"] == expected["flag_reason"]
            totals["flag_reason_correct"] += flag_ok
            workflow_ok = flag_ok
            numeric_ok = None
            extraction_ok = None
            approval_ok = None
            reply_ok = None
        else:
            totals["clear"] += 1
            totals["clear_auto"] += status == "quoted"
            totals["clear_false_flags"] += actual_flag
            extraction_ok = status == "quoted" and all(
                observed[field] == expected[field] for field in EXTRACTION_FIELDS
            )
            totals["extraction_correct"] += extraction_ok
            approval_ok = status == "quoted" and observed["final_approval_status"] == {
                "normal": "NO", "manager_approval": "YES"
            }.get(expected["final_approval_status"])
            totals["approval_correct"] += approval_ok
            numeric_ok = status == "quoted" and all(
                numeric_equal(observed[field], expected[field]) for field in NUMERIC_FIELDS
            )
            totals["numeric_gold_correct"] += numeric_ok
            workflow_ok = extraction_ok and approval_ok
            rounded_total = Decimal(observed["revenue_unrounded_cny"]).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            ) if status == "quoted" else None
            reply_ok = status == "quoted" and f'{rounded_total:,.2f}' in observed.get("customer_reply_draft", "")
            totals["reply_has_total"] += reply_ok
            totals["correct_extraction_and_reply_has_total"] += extraction_ok and reply_ok
        totals["workflow_correct"] += workflow_ok
        totals["end_to_end_correct"] += workflow_ok and (expected_flag or numeric_ok)
        if not workflow_ok or (not expected_flag and (not numeric_ok or not reply_ok)):
            issues.append({
                "id": case_id,
                "expected_status": expected["status"],
                "actual_status": status,
                "extraction_mismatches": [field for field in EXTRACTION_FIELDS
                                          if observed[field] != expected[field]] if not expected_flag else [],
                "flag_reason_correct": observed["flag_reason"] == expected["flag_reason"] if expected_flag else None,
                "approval_correct": approval_ok,
                "numeric_gold_correct": numeric_ok,
                "reply_has_total": reply_ok,
            })
    return {"counts": totals, "issues": issues}


if __name__ == "__main__":
    print(json.dumps(compare(Path(sys.argv[1]), Path(sys.argv[2])), indent=2))
