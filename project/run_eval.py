"""Run development or blind evaluation and save a timestamped result."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from fastquote.evaluation import evaluate
from fastquote.service import QuoteService


ROOT = Path(__file__).resolve().parent


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate FastQuote.")
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--answers", type=Path, required=True)
    parser.add_argument("--mode", choices=["rules", "openrouter", "auto"], default="rules")
    parser.add_argument("--summary-only", action="store_true")
    parser.add_argument("--no-save", action="store_true")
    args = parser.parse_args()

    result = evaluate(
        QuoteService(ROOT),
        args.inputs,
        args.answers,
        args.mode,
        include_case_details=not args.summary_only,
    )
    result["run_metadata"] = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "inputs_sha256": sha256(args.inputs),
        "answers_sha256": sha256(args.answers),
        "price_list_sha256": sha256(ROOT / "data" / "price_list.json"),
    }
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    print(rendered)
    if not args.no_save:
        output_dir = ROOT / "evaluation_results"
        output_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        (output_dir / f"evaluation_{timestamp}.json").write_text(rendered + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

