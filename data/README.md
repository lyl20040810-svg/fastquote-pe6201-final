# Data provenance and dictionary

## Catalog

`project/data/price_list.json` is the runtime source of truth; `data/FastQuote_Price_List.xlsx` is a readable copy for inspection. Both describe a 73-row subset transcribed from two project-owner-supplied photographs of a DIN933 A2 external hex bolt price list. The original photographs are not included here because local copies were unavailable when this package was frozen. `source_page` in JSON refers to photograph/page 1 or 2, not to a public URL. Rows whose price or packaging could not be read reliably were left out. This is not a complete supplier catalog or an automatically updated feed.

Each JSON row contains `sku`, `standard`, `diameter`, `length_mm`, `list_price_per_thousand_cny`, `pieces_per_box`, `boxes_per_carton`, `source_page`, and `verified`. The top-level metadata records material (`A2 stainless steel`), product, currency, price unit, transcription date, and scope note. `A2` should not be silently relabeled as a specific steel grade. Runtime lookup requires an exact standard, diameter, and length. A missing SKU is flagged rather than estimated.

The catalog contains commercially sensitive real prices. The project owner permitted their inclusion in this project. No customer names, API keys, or live transaction records are included.

## Evaluation inputs

`project/data/dev_eval_inputs.jsonl` and `project/data/dev_eval_answers.jsonl` are 16 development cases used while building the demo. Their answers cover extraction, flagging, and approval, but not independent numeric gold for every case. They are **not** the final test.

`evals/final_eval_inputs.jsonl` contains 50 user-provided final requests. `evals/final_eval_answers.jsonl` and `evals/gold_audit.csv` are the separately supplied standard answers. The gold was not stored inside the application's pricing path or sent in the OpenRouter request. `evals/README.md` explains the chronology, schemas, and comparison method.
