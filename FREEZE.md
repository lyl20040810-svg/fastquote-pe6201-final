# Frozen release record

- Frozen on: 2026-10-04 (Asia/Shanghai).
- Delivery correction on the same date: the README Colab link now points to this final repository; the notebook image URL, repeated-run module reload, and static cache headers were fixed. Pricing rules and recorded evaluation results are unchanged.
- Code state: post-fix build after the second 50-case OpenRouter run. No additional model prompting or pricing-rule changes are included after that run.
- Verification at freeze: 21 local unit tests passed; self-contained Colab notebook reconstruction, HTTP health check, sample quote, and static image checks passed; package scan found no API key or `.env` file.
- Baseline and post-fix CSVs, inputs, gold answers, price data, source code, and notebooks are preserved separately in this package. `SHA256SUMS.txt` records the packaged file hashes.
- The two price-list source photographs were not available as local files for inclusion; the structured transcript and readable spreadsheet are included instead. This is a documented data-provenance limitation.
- Repository layout: the archive can be used as the public repository root without an API key. `SHA256SUMS.txt` verifies the frozen payload, excluding itself.
