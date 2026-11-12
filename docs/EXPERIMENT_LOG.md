# Experiment log

Log experiments here **after execution**. Do not invent outcomes or select hypotheses based on the held-out test.

| ID | Date (ICT) | Hypothesis / change | Data split / protocol | Validation log loss | Validation Brier | Decision | Commit |
| --- | --- | --- | --- | ---: | ---: | --- | --- |
| E00 | TBD | API reachability, parsed match eligibility and patch coverage | Data audit only | — | — | Not run | TBD |
| E01 | TBD | Gold-only logistic regression | Chronological series-purged train / val | — | — | Not run | TBD |
| E02 | TBD | Time-dependent economic lead | Same fixed split | — | — | Not run | TBD |
| E03 | TBD | XP and short-term momentum | Same fixed split | — | — | Not run | TBD |
| E04 | TBD | Objectives / Roshan / kill events | Same fixed split | — | — | Not run | TBD |
| E05 | TBD | Final selected model vs baseline | Untouched test, paired cluster bootstrap | — | — | Not run | TBD |

## Required notes for each experiment

State the hypothesis before seeing its results; exact feature set; assumptions on event timing; parameter choices; seed; match and row counts; reason for accepting/rejecting; calibration failure modes; whether an improvement was meaningfully larger than uncertainty.

## Protocol freeze

Once the final candidate is selected on validation, do not tune it or rerun feature selection in response to test scores. Any discovered leakage bug requires correcting the pipeline, disclosing the correction, and regenerating all dependent results, never quietly changing only a reported number.
