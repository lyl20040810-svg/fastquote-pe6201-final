# Target and reached metrics

The proposal's pre-project target was **at least 50 cases and at least 90% fully correct end-to-end quotations**. Instructor feedback asked that extraction, flagging behavior, and arithmetic be separated. The original proposal did not pre-register numerical thresholds for those component metrics; they are reported as diagnostics, not retroactively invented targets.

| Metric | Denominator and definition | First run | Post-fix run |
| --- | --- | ---: | ---: |
| Clear-request extraction exact match | Correct SKU, diameter, length, quantity, unit / 35 gold clear requests | 31/35 (88.57%) | **35/35 (100%)** |
| Automatic coverage on clear requests | Quoted / 35 gold clear requests | 35/35 (100%) | **35/35 (100%)** |
| False-flag rate on clear requests | Incorrectly flagged / 35 gold clear requests | 0/35 (0%) | **0/35 (0%)** |
| Appropriate flag recall | Flagged / 15 gold flag requests, regardless of reason | 11/15 (73.33%) | **15/15 (100%)** |
| Gold numeric agreement | All audited numeric fields agree / 35 gold clear requests | 32/35 (91.43%) | **35/35 (100%)** |
| Approval decision agreement | `YES/NO` mapped to gold approval label / 35 gold clear requests | 35/35 (100%) | **35/35 (100%)** |
| Reply includes calculated total | Draft contains the computed CNY total / 35 gold clear requests | 14/35 (40%) | **35/35 (100%)** |
| Strict structured end-to-end | Status + extraction + approval + numeric values, or correct flag reason / all 50 | 42/50 (84%) | **45/50 (90%)** |

The post-fix run met the original **90%** target under this strict structured definition, but it is a **post-feedback regression on the same cases**, not a second blind evaluation. If flag reasons are ignored and only the safe decision to quote or flag is scored, the post-fix run is **50/50**; that is a different, less strict metric and must not replace the 45/50 headline.

The remaining five strict failures are `FINAL-046` through `FINAL-050`. All five were flagged rather than priced, which is the safer outcome, but the system labeled them `ambiguous_or_incomplete` while gold labels them `no_exact_catalog_match`. Nothing in the evidence shows that the quote was sent, accepted, or approved. Manual-versus-assisted preparation time was not measured. Customer prose quality beyond presence of the computed total was not comprehensively graded. These limitations should accompany any presentation of the percentages.
