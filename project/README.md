# FastQuote source project

This directory is the runnable Python source for the PE6201 FastQuote submission. The package-level `../README.md` contains the product architecture, persona, inputs and outputs, Colab instructions, data provenance, and measured results. If this directory is viewed on its own, the instructions below are sufficient to run and inspect it.

## Run

Python 3.10+ is required; the local app and tests use only the standard library.

```powershell
python -m unittest discover -s tests -v
python run_app.py
```

Open `http://127.0.0.1:8765/`. Select **Rules** for a no-key demo. For the LLM-backed mode, copy `.env.example` to `.env`, set `OPENROUTER_API_KEY` and `OPENROUTER_MODEL`, keep `.env` private, and select **OpenRouter**. Auto selects OpenRouter when configured and otherwise uses Rules. Never commit an API key.

Examples: `Please quote M16x50, 2 cartons.`; `Please quote M16x50, 18 pieces.`; `Need M16 bolts, 3 boxes.` The last example is intentionally flagged because length is missing.

## Module map

- `run_app.py` serves the UI and JSON quote endpoint.
- `fastquote/extractor.py` handles Rules/OpenRouter structured extraction and ambiguity guards.
- `fastquote/catalog.py` performs exact lookup against `data/price_list.json`.
- `fastquote/pricing.py` calculates packaging, discounts, costs, margin, and approval using Decimal.
- `fastquote/service.py` orchestrates the quote and validates the customer-reply draft.
- `fastquote/evaluation.py` and `run_eval.py` implement development/answer-file evaluation.
- `tests/` contains 21 deterministic unit and regression tests, including mocked OpenRouter responses.

No request is automatically sent to a customer or manager. All outputs require human review. The 73-row real-price dataset is a verified subset, not a complete catalog. See the parent package documentation for the recorded 50-case OpenRouter evaluation and its limitations.
