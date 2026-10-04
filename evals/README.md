# Evaluation evidence and reproduction

## Files

| File | Purpose |
| --- | --- |
| `dev_eval_inputs.jsonl`, `dev_eval_answers.jsonl` | 16-case development checks (also in `project/data/`). |
| `final_eval_inputs.jsonl` | 50 independent customer-request inputs. |
| `final_eval_answers.jsonl` | User-supplied expected workflow and rounded pricing values. |
| `gold_audit.csv` | User-supplied detailed gold fields and unrounded arithmetic values used for the reported CSV comparison. |
| `final_openrouter_results_baseline.csv` | First OpenRouter run, before reviewing final-test errors. |
| `final_openrouter_results_post_fix.csv` | Second OpenRouter run, after targeted fixes. |

The result files are raw exports from the Colab evaluation notebook. They are **not** synthetic replacements for missing calls: each has 50 unique IDs and no `error` rows. The recorded extraction method is `openrouter:openai/gpt-4.1-mini` on quoted rows. Flagged rows may not expose an extraction method in the flattened CSV, so the mode is also documented by the notebook execution procedure.

## Chronology and leakage boundary

The 16-case development set informed the initial implementation. The 50-case final inputs were then run once in forced OpenRouter mode; those actual outputs are the baseline file. The baseline was compared with the user-supplied gold. **Only after this comparison** were unit interpretation, ambiguity handling, and reply completeness changed and regression tests added. The same 50 inputs were run again in forced OpenRouter mode; this is the post-fix file. Therefore the second score is useful as a regression check but must **not** be called an independent blind estimate of generalization.

The frozen source in `project/` and `notebooks/FastQuote_Colab.ipynb` is the **post-fix** build. The package includes the first-run CSV as immutable evidence but does not claim to contain a full snapshot of the pre-fix source. No further code tuning was made after the second run before this freeze.

## Reproduce the run

1. Upload `notebooks/FastQuote_Final_OpenRouter_Eval.ipynb` to Colab.
2. Add `OPENROUTER_API_KEY` in Colab Secrets and enable access.
3. Choose **Runtime > Run all**. The notebook embeds the 50 input requests, constructs the same source project, forces `mode="openrouter"`, and writes `final_openrouter_results.csv` plus a raw JSONL response log. It marks any API failure as `error` rather than falling back to Rules.
4. Compare the downloaded CSV with `gold_audit.csv` by `id`. Repeated LLM calls may vary; the included two CSVs are the recorded evidence, not a promise that a third run will be byte-identical.

From the package root, reproduce the two recorded score tables without an API call:

```powershell
python evals/compare_final_eval.py evals/final_openrouter_results_baseline.csv evals/gold_audit.csv
python evals/compare_final_eval.py evals/final_openrouter_results_post_fix.csv evals/gold_audit.csv
```

For local deterministic development checks, run `python -m unittest discover -s tests -v` from `project/`. The 21 tests use mocks for OpenRouter guardrails; they do not require or spend an API key. `python run_eval.py --inputs data/dev_eval_inputs.jsonl --answers data/dev_eval_answers.jsonl --mode rules --no-save` runs the development set. Its end-to-end numeric rate is unavailable because that development answer file omits complete numeric gold.

## Scoring rule

The detailed comparison uses `gold_audit.csv` and aligns rows by unique `id`. A clear request is extraction-correct only when SKU, diameter, length, quantity, and unit all match. Numerical fields are compared as Decimal values with a relative tolerance of `1e-9` to ignore representation-length differences in unrounded percentages. Actual `YES/NO` manager-approval values are mapped to gold `manager_approval/normal`. A flagged case is strict-workflow-correct only when both its status and `flag_reason` match. Strict end-to-end correctness adds numeric-field agreement for quoted cases. The customer-draft total-price check is reported separately because the original evaluator's end-to-end definition did not score prose quality.

The gold was user-supplied; the evaluation script checked row alignment and arithmetic consistency but did not independently verify every interpretation against the original customer or source photographs. This small, selected set is not a statistical claim about all customer traffic.
