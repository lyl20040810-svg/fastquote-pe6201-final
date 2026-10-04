"""Evaluation metrics that separate extraction, coverage, and flag behavior."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from decimal import Decimal

from .service import QuoteService


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON on line {line_number} of {path.name}") from exc
    return rows


def evaluate(
    service: QuoteService,
    inputs_path: Path,
    answers_path: Path,
    mode: str,
    include_case_details: bool = True,
) -> dict[str, Any]:
    inputs = {row["id"]: row for row in read_jsonl(inputs_path)}
    answers = {row["id"]: row for row in read_jsonl(answers_path)}
    if set(inputs) != set(answers):
        missing_answers = sorted(set(inputs) - set(answers))
        missing_inputs = sorted(set(answers) - set(inputs))
        raise ValueError(
            f"Input/answer IDs differ. Missing answers: {missing_answers}; missing inputs: {missing_inputs}"
        )

    details = []
    clear_count = clear_auto = clear_false_flags = extraction_correct = 0
    flag_expected = flag_correct = workflow_correct = fully_correct = 0
    arithmetic_assessed = arithmetic_correct = 0
    for case_id, input_row in inputs.items():
        expected = answers[case_id]
        result = service.quote(input_row["request"], mode=mode)
        actual_flagged = result["processing_status"] == "flagged"
        expected_flagged = expected["expected_processing_status"] == "flagged"
        if expected_flagged:
            flag_expected += 1
            if actual_flagged:
                flag_correct += 1
        else:
            clear_count += 1
            if not actual_flagged:
                clear_auto += 1
            else:
                clear_false_flags += 1

        extraction_ok = False
        if not expected_flagged and not actual_flagged:
            actual = result["extraction"]
            extraction_ok = all(
                actual.get(field) == expected.get(field)
                for field in ("standard", "diameter", "length_mm", "quantity", "unit")
            )
            if extraction_ok:
                extraction_correct += 1

        status_ok = actual_flagged == expected_flagged
        approval_ok = True
        if expected.get("approval_status") is not None and not actual_flagged:
            approval_ok = result["pricing"]["approval_status"] == expected["approval_status"]
        flag_reason_ok = not expected_flagged or result.get("flag_reason") == expected.get("flag_reason")
        pricing_expected = expected.get("expected_pricing")
        pricing_ok = None
        if not expected_flagged and pricing_expected is not None:
            arithmetic_assessed += 1
            pricing_ok = not actual_flagged and all(
                Decimal(str(result["pricing"].get(field))) == Decimal(str(value))
                for field, value in pricing_expected.items()
            )
            arithmetic_correct += int(pricing_ok)
        case_workflow_ok = status_ok and (
            flag_reason_ok if expected_flagged else extraction_ok and approval_ok
        )
        workflow_correct += int(case_workflow_ok)
        case_fully_correct = case_workflow_ok and (expected_flagged or pricing_ok is True)
        fully_correct += int(case_fully_correct)
        if include_case_details:
            details.append({
                "id": case_id,
                "expected_status": expected["expected_processing_status"],
                "actual_status": result["processing_status"],
                "extraction_correct": extraction_ok,
                "approval_correct": approval_ok,
                "flag_reason_correct": flag_reason_ok,
                "arithmetic_correct": pricing_ok,
                "workflow_correct": case_workflow_ok,
                "fully_correct": case_fully_correct if expected_flagged or pricing_expected is not None else None,
            })

    total = len(inputs)
    metrics = {
        "case_count": total,
        "clear_case_count": clear_count,
        "flag_expected_count": flag_expected,
        "extraction_exact_match_rate": _rate(extraction_correct, clear_count),
        "automatic_processing_coverage": _rate(clear_auto, clear_count),
        "false_flag_rate_on_clear_cases": _rate(clear_false_flags, clear_count),
        "appropriate_flag_recall": _rate(flag_correct, flag_expected),
        "workflow_correct_rate_excluding_arithmetic": _rate(workflow_correct, total),
        "arithmetic_case_count": arithmetic_assessed,
        "arithmetic_exact_match_rate": _rate(arithmetic_correct, arithmetic_assessed),
        "end_to_end_fully_correct_rate": (
            _rate(fully_correct, total) if arithmetic_assessed == clear_count else None
        ),
    }
    output = {"mode": mode, "metrics": metrics}
    if include_case_details:
        output["cases"] = details
    return output


def _rate(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return round(numerator / denominator, 4)

