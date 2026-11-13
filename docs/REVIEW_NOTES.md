# Vexil notebook — research and QA ledger

## Current acceptance state (13 November 2026)

- Original 500 parsed OpenDota professional matches, 250 per patch, frozen by ID.
  One self-contained 26-cell notebook, 18,304 minute rows,
  train/validation/held-out = 291/103/106 matches.
- M1 gold-by-time remains selected from the original M0–M3 family.
  The 3,837 original held-out forecasts and six original output CSVs
  are numerically unchanged. Local full 500-match cached Run All PASS;
  cold Kaggle pass of earlier four-model version already documented
  below.
- A development-only post-selection item-purchase hypothesis is
  explicitly labeled exploratory: validation log loss 0.514098
  versus 0.519346 for M1, 1/3 favorable prior training-only folds,
  paired series CI crossing zero. No held-out item-model evaluation.
- 394 development games and 1,847 timestamps: independent purchase
  feature PIT/source parity PASS; missing purchase logs = 0.
- Five train games with approximate end after first validation start
  were identified; excluding these from an audit refit still
  selects M1, 286 completed train games and 103 validation games.
  The original selected model and held-out scores stay fixed.
- 30/30 latest offline unit tests PASS, including bounded
  429/503 network-failure behavior. Four Quant Bible
  reproducibility QA kernels (separate PR #7) completed on Kaggle.
- The report is rendered and visually inspected as **two A4 pages**,
  with editable REPORT.md and explicit AI/public-code disclosure.
- A cold hosted Kaggle Run All of this exact extended item-timing
  version is being retested after an OpenDota transport failure.
  **Do not claim its new hosted status COMPLETE without its receipt.**
  The Colab branch passed an emulated local setup, but a genuine
  hosted Google Colab Run All remains **unverified**.
- Submission HOLD until actual candidate human hours are recorded
  in the notebook/report, hosted Colab is verified and reviewers
  have access to this private GitHub repository. No false hours,
  no unverified cloud pass, no P20 model promotion.

## Historical notes (earlier checkpoints; current state above supersedes their statuses)

### Early independent review and delivery gates

Status: development protocol and synthetic smoke tests complete; no 500-match result exists yet. This document is a **research checklist**, not empirical evidence or a score claim.

## Priority 0 — block submission

1. **Deterministic dataset:** verify 500 eligible parsed professional matches, span two adjacent patch cohorts of 250 eligible games each, freeze all 500 IDs in notebook source, and rerun once from a clean cache. Retain exclusions and source-drift caveats. A moving recent-match feed cannot support exact reproducibility. *Methodology: Bible v1.4.1 §§3.1–3.6, 14.1–14.2.*
2. **Information-time semantics:** run prefix truncation and poisoned-future checks on real matches; confirm event types and side conventions from raw objective examples; never use final totals, result or duration as a feature. OpenDota retrospective event times meet the brief's stated information convention but do not establish true historical network receive times. *Methodology: §§3.1–3.3, 13.2, 14.3.*
3. **Series-aware chronology:** ensure no match or series crosses partitions and only train fits transforms. The late holdout stays inaccessible to model selection. *Methodology: §§4.3, 5.1–5.6.*
4. **Live notebook execution:** prove one-account Kaggle CPU/private Internet reachability and then run the exact notebook with output saved. Fresh Colab and laptop Run All must also work, using only allowed API endpoints and no existing cache, keys or local data files. *Methodology: §§14.1–14.2, 14.8.*

## Priority 1 — scientific credibility and creativity

5. Gold-only logistic baseline vs three predeclared explanations of **time-value, lead fragility and objective conversion**, all fitted and chosen using training/validation only. If objectives are incomplete or side semantics uncertain, exclude M3 from candidacy and document why; do not silently derive final towers from end-game fields. *Methodology: §§1.2–1.4, 2.4, 7.7, 13.1.*
6. Report held-out log loss/Brier by phase and overall with paired 95% **whole-match** bootstrap confidence intervals and calibration plots with bin counts. Also calculate equal-match-weighted sensitivity; the primary minute-row score and CI answer different questions. *Methodology: §§4.3, 6.5, 7.2–7.5.*
7. Provide an insight about the **conditional value of an economic lead** and a predeclared descriptive comeback case, without claiming causal effects from observational data. Admit if additional features do not beat gold alone. *Methodology: §§1.4, 7.1, 12.1, 13.1.*
8. Submit a separate report of **≤4 pages**, documenting sample construction, ablations (including failures), uncertainty, which model to ship and not ship, data limitations, actual work time, and accurate disclosure of tools/public code. Never invent metrics. *Methodology: §§1.1–1.4, 14.1.*

## Priority 2 — do only if evidence demands it

- A shallow nonlinear model only if the predeclared simple family fails on validation and an explicit new candidate budget is recorded. No deep neural net, hero embedding, elaborate CV, CPCV, Sharpe/DSR, transaction-cost or Kelly framework for a 500-match **prediction-only** exercise. *Methodology: §§1.3, 7.7, 12.1.*
- No external model code unless its use can be cited and its incremental value tested independently.

## Audit results to date

- OpenDota smoke: two permitted endpoints return data. The latest pro match was unparsed; a neighboring parsed match contained gold/XP arrays and heterogeneous objective events. This demonstrates why eligibility filtering and event schema tests are mandatory.
- An offline synthetic end-to-end execution covered feature extraction, 3-way series-safe split, four predeclared models, log loss/Brier, paired cluster bootstrap and both reliability plots. **Synthetic metrics are not empirical results** and are excluded from the report.
- 26 offline contract tests pass, including pre-horn and exact-minute event boundaries, counterfactual future-data poisoning, label changes, allowed endpoints, split disjointness, baseline feature count, paired bootstrap and requirements parity.
- Remaining blockers: frozen real 500-match manifest, Kaggle final 500-match execution, real held-out scores, saved real outputs, fresh Colab/laptop acceptance and final report.

## References

- Assignment: *Vexil Capital - Take-Home Modelling Project*, pages 1–4.
- Private internal methodology: *Quant Research Bible* **v1.4.1**, sections cited above; *Theory Reading Paths*, `Before starting any deep dive`. No private source text, code or credentials are included here.
- Public implementation: OpenDota API documentation and scikit-learn probability calibration guide (linked from the research plan).

- Notebook now exports derived run artifacts (CSV, calibration PNG, versioned receipt) for audit and report preparation. Synthetic end-to-end verification confirmed valid exports; real outputs still pending.


## Independent code review disposition — 2026-11-13
- **P0 retained:** the 500 real-match IDs are not yet frozen in notebook source. No claim of reproducibility across runs or readiness to submit.
- **P0 fixed:** cache no longer preserves transient unparsed matches; corrupted cached JSON is refetched; only a genuine HTTP 404 is marked not found; malformed JSON/transport failures retry within a bounded budget.
- **P1 fixed:** the boundary page selection includes qualifying older-patch matches at the tail of the preceding page, without downloading that full page of current-patch payloads. Avoid claiming that patch IDs must be consecutive.
- **P1 fixed:** missing objective/kill event logs yield NaN, not an observed zero. Gold-series tail staleness and missing log rates are audited by patch.
- **P1 addressed:** required all-minute scores remain the primary evaluation; excluding the final two minutes is a whole-match paired-bootstrap sensitivity, not a second model-selection target.
- **P1 documented:** 250/250 patch cohorts imply that the held-out population may contain only the newer patch. The split crosstab and inferential limits must be prominent in the report. Do not claim cross-patch causality.
- **P2 deferred:** phase-faceted reliability and recalibration slopes are optional given small held-out bins. Fixed-bin overall reliability with counts, plus mandatory phase log loss/Brier/whole-match CIs, remains primary.
- **P1 outstanding:** fresh Colab ABI/package compatibility, final 500-game Run All, executed outputs and report still require evidence.
No model candidate or cutoff was changed in response to a held-out score.


## Local real-data acceptance — 2026-11-13
- One pinned, frozen-source notebook executed all 14 code cells on BigLinux with 500 real parsed matches, 18,304 minute forecasts, 4 PNG plots, full held-out table and exported audit receipt. Source matched the frozen code committed before results.
- 26/26 contract tests pass, including frozen-manifest no-resample and missing-payload errors.
- M1 selected by validation; overall held-out log-loss/Brier point estimates are better than M0, but paired 95% match-bootstrap intervals both include zero. A late-game Brier degradation and post-hoc calibration concerns require cautious interpretation.
- Major unresolved gates: Kaggle fresh API run in the same account, fresh Colab Run All, verify report page budget and actual candidate work-time entry.
- Leave Draft PR open until independent execution evidence is available. No further model tuning on the held-out set.


## Independent report review and factual repairs — 2026-11-13
A read-only Sonnet review checked the completed report against the brief and highlighted missing sensitivity numbers, unusually wide late-game loss uncertainty, calibration/base-rate shift, CI dependence and provenance wording. These were addressed without modifying the frozen model or data:

- Added equal-match-weighted log loss (M1 0.495052, M0 0.509507) and Brier (M1 0.164904, M0 0.169773) as already predeclared sensitivity point estimates.
- Verified that one 25-row late-game match (8744971178) contributes -26.61273 to a total 30+ log-loss difference sum of -4.91722. A post-hoc removal of that match yields +0.031262 (M1 worse) on the remaining 694 late-minute rows. The report identifies this as an influence diagnostic, not a new model-selection criterion.
- Reported partition base-rate drift (Radiant 51.2% train, 48.5% validation, 59.4% test), the match-level bootstrap percentile method (2000 resamples, seed 20261113), and residual within-series dependence.
- Clarified that overlapping games across phases and unadjusted multiple comparisons prevent strong phase-specific claims.
- Made the minute-20 momentum contrast explicitly inconclusive/underpowered, with Wilson intervals for both groups.
- Reported source freeze commit 3258a76 and pre-results model-family commit e49e853; the same model, features and cutoff rules remain unchanged.
- Machine-checked all 10 held-out phase-metric table entries and all 4 validation rows (rounded scores and interval endpoints) against the executed CSV outputs. PASS.
**Still blocked:** actual human hours, independent Kaggle acceptance, fresh Colab, and final report page-budget/packaging check.


## All-500-match leakage acceptance — 2026-11-13
The full cohort of 500 selected parsed games passed **3,342** adversarial PIT prefix checks (patch 59: 1,667; patch 60: 1,675) without making API requests. The previously reported 128-game/512-check audit was a smaller pre-freeze smoke test and is superseded by the complete result. This is feature-logic evidence only, not proof of live network-time delivery or model superiority.


## Independent Kaggle scientific-output acceptance — 2026-11-13

**Result: PASS for the scientific outputs; raw JSON identity is NOT established.**
The private Kaggle CPU kernel sangtruong/vexil-dota2-patch-cohorts-20261113 completed its full 500-ID live OpenDota fetch and generated all derived files. The Kaggle log reports no Python exception, shows patch counts 250/250, PIT sample checks 72 across both patches, M1 selected on validation, and 3,837 held-out predictions. BigLinux and Kaggle agree on the source match-manifest digest e227b630a71b3bbc1673f281908ae13b3f6ee5b4edcfb896bce268732a74dfea, 500 matches, 18,304 minute rows and 291/103/106 match split.

The independent comparison aligned primary keys and compared every numeric column in five CSV result files:
- Held-out predictions: 3,837 rows, **max absolute difference 4.440892098500626e-16**.
- Validation ablations: 4 model rows, max difference 3.0531133177191805e-16.
- Held-out metric/CIs: 10 rows, max difference 1.9992688060632702e-16.
- Terminal-minute sensitivity: 2 rows, max difference 1.1102230246251565e-16.
- Minute-20 comeback: 2 rows, zero difference.
- Match-manifest CSV: 500 rows, identical.

**Important limitation:** raw OpenDota JSON payload digests differed between the local cached inputs and Kaggle's later live request (local 7328f1f8df8f3925765e390f997168a084aa6bded1c1bb031da81e8e8092281b; Kaggle 25ad644bcd0c8d9d045be2d7de789de44d91daa3c455c6b83fcb15cfe3c70ddf). A separate low-rate live-vs-cache inspection of 10 selected IDs observed changes in the players field for two games; a deeper inspection identified computed_mmr values as a changed auxiliary field in one such game. Computed MMR is never accessed by snapshot features. The checks support numerical reproducibility of the selected 500-match study across these two executions, **not exact identity of every upstream JSON field**.

Local Python 3.12.3 with numpy 2.2.6 and sklearn 1.7.2 differed from Kaggle Python 3.13.18 with numpy 2.1.3 and sklearn 1.6.1. All 26 offline contract tests and 3,342 full-cohort PIT checks passed separately. A fresh hosted Google Colab run has not been verified; the Colab codepath was only emulated on BigLinux. Candidate-supplied actual human time is still required.


## Report page-budget and rendered-layout check — 2026-11-13
The committed REPORT.md byte stream (SHA-256 7fbd9bfc80dbcff71976af298abe302ab362cc5e3e777a1357d2568188842f79) was independently rendered to a plain typographic A4 PDF preview using Markdown and WeasyPrint. The resulting PDF is **three pages** against a **four-page maximum**. A renderer pass extracted the complete report text and inspected images of pages 1–3; the evaluation and ablation tables remained unbroken and no text overflow was observed. The preview is a layout check only; the canonical deliverable remains REPORT.md, and the user must still supply real time-spent information. Fresh hosted Colab is not yet certified.
