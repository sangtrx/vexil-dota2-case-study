# Experiment log

Log experiments here **after execution**. Do not invent outcomes or select hypotheses based on the held-out test.

| ID | Date (ICT) | Hypothesis / change | Data split / protocol | Validation log loss | Validation Brier | Decision | Commit |
| --- | --- | --- | --- | ---: | ---: | --- | --- |
| E00 | 2026-11-13 | API/Kaggle reachability and parsed-match schema sample | Data audit only; not a model run | — | — | Kaggle HTTP 200; local 23 parsed/1 unparsed in 24-recent-game sample; patch coverage for 500 pending | TBD |
| E01 | TBD | Gold-only logistic regression | Chronological series-purged train / val | — | — | Not run | TBD |
| E02 | TBD | Time-dependent economic lead | Same fixed split | — | — | Not run | TBD |
| E03 | TBD | XP and short-term momentum | Same fixed split | — | — | Not run | TBD |
| E04 | TBD | Objectives / Roshan / kill events | Same fixed split | — | — | Not run | TBD |
| E05 | TBD | Final selected model vs baseline | Untouched test, paired cluster bootstrap | — | — | Not run | TBD |

## Required notes for each experiment

State the hypothesis before seeing its results; exact feature set; assumptions on event timing; parameter choices; seed; match and row counts; reason for accepting/rejecting; calibration failure modes; whether an improvement was meaningfully larger than uncertainty.

## Protocol freeze

Once the final candidate is selected on validation, do not tune it or rerun feature selection in response to test scores. Any discovered leakage bug requires correcting the pipeline, disclosing the correction, and regenerating all dependent results, never quietly changing only a reported number.

### Engineering verification checkpoint — 2026-11-13

- 16/24 offline contract tests passed; synthetic end-to-end smoke passed. Synthetic loss numbers are not retained as empirical evidence.
- Private Kaggle CPU smoke on one account printed `OPEN_DOTA_KAGGLE_SMOKE_PASS 200 100`.
- The first full-payload scan was interrupted before it produced empirical results; the patch-metadata-only preflight justified a more API-efficient sample definition.

### Environment incident — first full Kaggle attempt

- The private CPU job was accepted and executed, but aborted during Setup: in-kernel pin replacement caused `AttributeError: 'numpy.ufunc' object has no attribute '__module__'` while importing scikit-learn/SciPy.
- This is an execution-environment failure, not a model outcome. No data selection or holdout evidence is claimed from that run.
- Correction: skip binary dependency replacement in an already-running Kaggle kernel; record actual package versions instead. Retry must use the same predeclared model and evaluation design.

### Kaggle environment diagnosis — 2026-11-13

- Second attempt failed at Setup because Kaggle reported `COLAB_RELEASE_TAG`, incorrectly activating Colab package installation.
- Isolated private Kaggle environment smoke test showed both Kaggle and Colab flags, base versions numpy 2.1.3 / scipy 1.16.3 / sklearn 1.6.1, and OpenDota HTTP 200.
- Added explicit Kaggle-first detection and a regression test, without changing any data, features, models, split or evaluation logic.

### Patch metadata discovery — 2026-11-13, before model outcomes
- A bounded page scan of 30 proMatches pages sampled patch 60 throughout June–November 2026; the last 500 games would not cover a patch transition.
- Stopped our original exploratory Kaggle run and removed its scratch kernel before seeing results. The earlier plan would have fetched thousands of unnecessary full matches.
- Recorded a preregistered, label-blind 250/250 patch-boundary cohort instead, preserving model candidates and held-out protocol. The resulting selection does **not** estimate performance over all contemporary professional matches.
- Unit tests for bounded discovery, exact equal patch counts and eligibility passed. Real dataset construction remains unverified.

### Preregistered descriptive diagnostic — before held-out outcomes
Fixed game minute 20 and |gold lead| >=3,000. Compare eventual leader-loss rates in held-out matches with declining vs stable/improving five-minute gold momentum; report numerator, denominator and Wilson interval. This analysis does not select any model or feature and cannot support causal conclusions.


### Audit repairs — 2026-11-13, before any held-out result
- Independent review found stale unparsed-cache, error-classification, optional-event missingness and boundary-page selection risks. Repaired each with targeted tests; the finite model family is unchanged.
- Added a data-quality table (per-patch missing logs and short gold-series tails), and paired whole-match sensitivity excluding the last two recorded minutes.
- Synthetic Run All now executes 14 code cells and produces four figures plus derived audit files; **its losses and predictions are synthetic and not scientific evidence**.
- The unfrozen data-selection run on Kaggle is a development-only run. Accept/reject the final model only under the previously specified validation protocol.

### PIT missingness invariant repair — 2026-11-13
Independent review identified a potential data-quality problem. The feature extractor already represented missing event logs as unknown (NaN), but the adversarial prefix test fabricated empty lists for those missing fields. The test oracle is now semantically consistent; a new negative fixture proves that missing event data remains missing after past-only truncation. 26 offline tests pass. This is a correctness repair and not a model trial.


### E01 — Frozen data manifest, 2026-11-13 (before viewing held-out results)
- Outcome-blind first patch boundary at proMatches page approximately 93, patches 59 → 60.
- 500 usable distinct games; patch 59: 250 games dated 2026-03-21 through 2026-03-24; patch 60: 250 games dated 2026-03-24 through 2026-03-26.
- 256 distinct positive series IDs across the 500 matches.
- API calls 705 (49 cache hits), 46 nonselected candidates: 45 wrong-patch and one unparsed/short. No selection based on winner.
- Ordered-ID SHA256: f2be53e16ae29df1f62aa9907187fdba846d9af9fb7a3f69e7dd7504be43b776.
- All 500 IDs embedded in the notebook. 26 offline contract tests passed BEFORE any held-out metric was inspected.
- Result and report remain pending. The March 2026 patch-transition sample is a specific historical evaluation, not an estimate for November 2026 professional games.
