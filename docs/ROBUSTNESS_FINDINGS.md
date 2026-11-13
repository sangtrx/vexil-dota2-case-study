# Vexil: Temporal robustness and inference readiness

13 November 2026. This appendix is a negative/control-focused
follow-up to the original 500-match take-home, not a new predictive
model release or an attempt to improve the 106-game test score.

## 1. Does added complexity generalize consistently?

Using only the **291 original TRAIN games**, evaluate five model
specifications in five later, series-safe evaluation blocks.
The first training slice contains 154 matches; later slices expand
as outcomes become available. A prior game is excluded from each
training slice if its approximate end time is after the first
evaluation start. Folds three and four respectively embargoed
four and two not-yet-complete training games.

The original protocol initially produced a two-match evaluation
block because positive series IDs span large stretches of start
time. It was revised using series/time metadata **before seeing any
model scores**, with this correction retained in the repository.

| Train / later eval matches | M1 minus M0 log loss | P20 minus M1 log loss | Best of five in that block |
|---|---:|---:|---|
| 154 / 22 | +0.00605 | +0.03132 | M0 |
| 176 / 44 | -0.01197 | -0.00125 | M3 |
| 216 / 27 (4 embargoed) | +0.00096 | +0.00524 | M2 |
| 245 / 22 (2 embargoed) | +0.02103 | +0.00734 | M3 |
| 269 / 22 | -0.00343 | -0.00275 | P20 |

Negative differences are better. M1 beats M0 in **2/5
minute-weighted** folds, or **3/5 when all matches receive equal
weight**. P20 beats M1 in only **2/5 minute-weighted** folds,
or **1/5 equal-match** folds. No consistently dominant model
emerges; each block favors a different structure.

These fold results reuse the original development population
and share overlapping earlier training samples. They are
retrospective robustness diagnostics, not an independent
prospective trial or a calibrated 95% null test. Original
103-match validation and 106-match held-out labels were never
accessed by the study scripts.

**Disposition:** keep the existing gold-only M0 as reference;
M1 is a reasonable shadow candidate under the original
selection protocol but is not proven superior. P20's favorable
103-match validation point estimate is not an advancement
gate because earlier train-only performance varies markedly.

## 2. Are the economic inputs actually time-aligned?

An independent all-500-match cached source audit checked that,
at every available integer match minute, aggregate Radiant
gold/XP lead matches the signed sum of the ten players' gold_t
and xp_t series at **the same index**.

- 500/500 matches: complete 10-player arrays and slot coverage.
- 18,304/18,304 gold checks: exact within arithmetic tolerance.
- 18,304/18,304 XP checks: exact within arithmetic tolerance.
- 5,000/5,000 player purchase logs and kill logs present.
- Zero network requests; original model estimates unchanged.

The semantic contract still has a real limitation:
match-clock availability in a retrospectively parsed JSON
does not verify that the live game-event feed would have
delivered that observation before the forecast was issued.
All claimed latency results below **exclude** network receipt.

The full 500-match research notebook now calculates SHA-256
fingerprints of canonical model-input rows for all 500 games
and each partition; it also hashes cumulative purchase-event
features over the development sample. This distinguishes
material changes in gold/XP/events from irrelevant auxiliary
OpenDota JSON reparse differences. The frozen 291-train hash
was also reproduced by a separately coded reconstruction.

## 3. Can the selected model be served cheaply and safely?

Model M1 is a median-imputed, scaled three-feature logistic
regression. A one-snapshot, one-row inference contract was
tested against the original fitted batch pipeline:

- 297 single-row/batch forecasts matched to 1e-13.
- 180 future/outcome-poisoning tests passed.
- 1,200 warm CPU inference calls: p50 **1.74 ms**, p95
  **2.09 ms**, p99 **2.47 ms** on BigLinux.
- Measured path includes raw cached snapshot feature parsing,
  one-row Pandas construction and scikit-learn prediction.
  It excludes HTTP/API, serialization and cold model loading.

The fitted gold-response slope remains positive over the
observed TRAIN minute support **0-85**. Analytically, the
unconstrained M1 interaction would reverse the sign at
approximately minute **98.36**, so blind extrapolation into
very long future games is unsafe. A reference serving
function explicitly returns OUTSIDE_TRAIN_TIME_SUPPORT
with no probability beyond 85; an approved fallback to M0
would require independent verification. The original
take-home forecasts and held-out scoring were NOT modified
by this operational guardrail.

## 4. Quality gates and next scientific step

Current branch includes executable train-only protocols,
raw clock/source audits, a small serving contract and
self-contained notebook. The original six output CSVs
and two development item CSVs remain numerically identical
to the earlier hosted Kaggle V2 execution. Thirty-five
offline regression tests were passing when the full
notebook was last run.

The next *scientific* check, if there were a genuine
deployment, would be a separately frozen later series cohort
with end-time information available before refitting;
compare proper log loss, Brier, calibration, error concentration,
model-support exceedances and live source receipt latency.
Neither 500 retrospective matches nor four already
consulted forward cohorts provide unspent confirmatory
evidence for post-selected P20.

The Kaggle V3 cold run of these added source-lineage and
serving-contract outputs has been submitted, but should
not be called COMPLETE or numerically verified until the
cloud receipts are downloaded and checked. A hosted Google
Colab Run All and actual author-hours disclosure are still
separate acceptance requirements for final submission.

The value here is not a complicated predictor or a
dashboard. It is an auditable forecast backed by point-in-time
source contracts, short CPU prediction time, explicit failure
states, and a scientifically conservative promotion policy.
