# Vexil / Quant Research Bible — tested findings

**Date: 2026-11-13 | Research branch only | Model promotion: HOLD**

## Executive result

Applied the actual private quant-research-bible v1.4.1 main commit
8e6374c8ac8c62da6611104555ce98f1cf40a528,
specifically hypothesis discipline (1.2–1.4), point-in-time
information contracts (3), dependent label sampling (4.3),
chronological versus selection validation (5), search bias and
cluster inference (6), proper scoring (7), and immutable receipts (14).

The original 500-match take-home selected simple M1 gold×time;
the later 28-candidate factory found **zero models meeting its
precommitted advancement criteria**. All results below are a
retrospective diagnostic on those SAME 103 already-inspected
validation matches. No new model is trained and no held-out
match is consumed.

## What the additional real checks found

| Audit | Executed | Result |
|---|---:|---|
| Proper-scoring reproduction | 29 models, 3,784 minute rows | Every original log loss and Brier value reproduced to 1e-12 |
| Phase-specific score reproduction | 29 models × 5 phases | All 145 original rows reproduced |
| Ordered series buckets | 103 games, 53 series-or-singleton groups | Six earliest-start buckets; 4/5 temporal boundaries overlap, NOT strict chronological blocks |
| Model selection instability | 20 directional splits (10 complementary pairs), ordered series buckets | Winner had *worse log loss than M1* on other half in **10/20** splits |
| Complementary rank reversal | 20 directions / 10 pairs, 29 models | In **6/20** splits the selected model ranked below the median of 29 on the other half |
| Series out-of-bag selection | 3,000 seeded series-block draws | Chosen non-M1 model worse than M1 on omitted groups in **51.47%** (1,544/3,000) |
| P20 selection frequency | 3,000 in-bag selections | P20 chosen **45.43%**, not a stable universal winner |
| Approximate simultaneous correction, 28 comparisons only | 5,000 whole-series max-t bootstrap draws | All 28 original intervals reproduced, multiplier **3.079034** |
| Historical research ledger | Prior PR #3, #4, #5 and #6 | **38 known model-attempt records**, not 38 independent trials; some prior explorations are not fully enumerated |

**Interpretation:** Even an apparently attractive point estimate
can arise from selection across multiple candidates and depend
on evaluation weighting. This is not the official PBO statistic:
the 20 directions of 10 complementary pairs reuse already-inspected development
labels and models fitted on common earlier training data. It
cannot restore a blind holdout or estimate future PnL.

## Post-run correction: the original six buckets are NOT strict chronology

A separate read-only audit used cached match start times and parsed
game durations, grouped all matches from the same professional series,
then formed maximal overlap-connected components. The original six
buckets ordered series by their earliest game start but **four of
the five boundaries overlap** even under the optimistic approximate
end time start_time+game_duration. That timestamp can understate actual
elapsed wall clock when games contain pauses, so it is not a
certified receive-time end.

Only **four approximately disjoint chronological components** are
identifiable in this sample: **62, 2, 3 and 36 matches**, comprising
34, 1, 1 and 17 series groups respectively. Thus the 20 complementary
3-of-6 splits above cannot honestly be described as six-way strict
chronological cross-validation or a forward-deployment simulation.
They are **post-hoc ordered-series-bucket robustness diagnostics**
only. Their rank-reversal numbers are retained as historical evidence
and explicitly downgraded.

On the four actual approximate components, P20−M1 minute-weighted
log-loss point differences are:

| Approximate component | Matches | P20 − M1 log loss |
|---|---:|---:|
| Earliest | 62 | −0.001133 |
| Intermediate A | 2 | −0.008827 |
| Intermediate B | 3 | −0.018977 |
| Latest | 36 | −0.011046 |

The two tiny middle groups have no useful standalone statistical
power. The earliest, largest group had only a marginal
improvement. There are too few well-separated groups to derive
a credible six-block chronological model-selection result from
the existing 103 matches. This limitation reinforces HOLD,
and cannot be fixed by simply increasing the number of
bootstrap draws on the same games.

Machine-verifiable reconstruction:
research/bible/chronology_audit.py, chronology_receipt.json,
validation_approx_intervals.csv, series_approx_intervals.csv,
chronology_components.csv, old_six_bucket_overlap_audit.csv and
chronology_4component_scores.csv.

## Different-implementation reference arithmetic

A second implementation uses only Python's standard library
(csv, math and random.Random), NOT NumPy/Pandas source routines.
It reproduces P20−M1 log-loss differences: minute **−0.005247828**,
equal-match **−0.004491210**, equal-series **−0.002869280**,
plus Brier difference **−0.002025427**. Its *different-seed*
4,000-draw grouped bootstrap gives approximate 95% CI
**[−0.012605,+0.002214]**, still including zero, consistent
with the prior [-0.013028,+0.002012] approximate interval.
This checks implementation arithmetic, not independent labels
or statistical coverage.

The Bible's own reference tests **66/66 PASS** and its
23-chapter/71-reference executable document audit PASS on
the Vexil Python environment (not the exact separately pinned
Bible dependency versions). Source tests do not certify
each literature claim or live trading profitability.

## Selection-variability qualifications

The 20 six-bucket selections are **10 complementary block pairs
evaluated in both directions**, not 20 independent experiments.
The 10/20 worse-than-M1 statistic is the average across those
20 dependent directions, not an estimated 50% probability of failure
under a defined null. Similarly, 6/20 below-panel-median
has no simple null distribution because all 29 candidates are
strongly correlated and the entire panel was evaluated on
previously exposed labels.

Across 3,000 separate whole-series bootstrap draws, M1 itself
was **never** the in-bag winner, so the 51.47% worse-than-M1
rate is also 51.47% conditional on a non-M1 winner (3,000/3,000).
A naive, non-independent Monte Carlo standard error for that
draw fraction is ~0.91 percentage points. The selected winner's
omitted-series log-loss difference had mean **+0.001434**,
median **+0.000164**, and 5th–95th percentile
**[−0.008242, +0.015465]**. These omitted series are
NOT a true new holdout because feature ideas/model selection
already depended on the old development labels.

The complementary buckets select models using **equal-match**
proper loss, whereas the 3,000 in-bag bootstrap draws select
using **minute-weighted** loss. These diagnostics ask different
questions. Neither establishes the coverage of the approximate
28-comparison max-t interval, which does not correct for
the broader incomplete 38+ trial history.

## P20 item-purchase result across estimands

P20 was the strongest point estimate of 28 new candidates:
its validation log loss 0.514098 versus 0.519346 for M1.
But the effect is not equally strong under each definition of
independent decision:

| Weighting | P20 − M1 log loss (negative favors P20) |
|---|---:|
| Each minute contributes equally | **−0.005248** |
| Each of 103 matches contributes equally | **−0.004491** |
| Each of 53 series groups contributes equally | **−0.002869** |

P20 relative difference by phase: minutes 0–9 **−0.000920**,
10–19 **−0.002820**, 20–29 **−0.008241**, 30+
**−0.010590**. The 30+ group contains only 78 of the 103
games. Such phase conditioning selects on how long the
game survives; it is not an intervention or causal effect.

A single series removal leaves P20's overall minute-weighted
log-loss difference in the range
**[−0.006362, −0.002824]**. This describes influence within
the inspected period and does **not** establish long-run
generalization. Prior train-only chronological folds favored
P20 in only **1/3** folds, and its approximate 28-comparison simultaneous series
95% interval **[−0.016929, +0.006434]** still contains zero.

## Why the search-family ledger matters

The visible experiment history has at least 38 evaluation
records: initial M0–M3; structural S1–S4; one event-state M4;
one independent fixed stage gate; and P01–P28. This is an
inventory of records, NOT a count of statistically independent
trials or a certified complete history. Earlier model selection
had already inspected development and forward outcomes, so
a retrospective 28-way adjustment alone does not remove
adaptive-search inflation across the full project.

The Bible's recommendation is to stop recycling the same
validation set, retain failed attempts and define any new
mechanistic hypothesis and fresh temporal cohort before
viewing the outcomes. It does not recommend blindly applying
CPCV/PBO as a substitute for forward deployment tests.

## Practical value and decision

The central prediction contract is binary final Radiant
outcome given the actual game state at minute t. OpenDota
match-clock histories can support reproducible retrospective
features, not verified live receive-time availability. These
two endpoints contain no executable betting-market odds,
market depth, spreads, fills or settlement-cost evidence.
Neither high classification accuracy nor lower log loss is
automatically a revenue-generating trading edge.

**HOLD all P01–P28; keep the original M1 gold×time model.**
No new prospective model claim or merge into original PR #3.

The production-relevant work is accuracy and availability
contracts, deterministic PIT snapshots, reproducible
prediction receipts and near-instant lookup of already
computed model outputs, not a visually ornate dashboard.

## Kaggle verification status (important)

Four PRIVATE Kaggle-ready CPU notebooks have been generated:
proper scores, selection stability, 28-way familywise
bootstrap and chronology correction. All four were **executed locally** with a Jupyter
kernel (not just imported), and their independent calculations
passed all numeric parity checks. In local environment:
Python 3.12.3, NumPy 2.2.6, pandas 2.3.3.

**New hosted Kaggle runs: 0.** The BigLinux Kaggle CLI
currently reports no authentication, and neither a private
dataset nor these four notebooks has been uploaded or run
in Kaggle cloud. Earlier independent Kaggle run of the
original 500-match notebook was verified in PR #3 and
is a different experiment.

When Kaggle login is restored, follow kaggle/README.md:
create a new PRIVATE dataset once; run four PRIVATE kernels
with internet/GPU OFF; download hosted receipts and verify
numerical parity. Do not label a launch as COMPLETE before
the hosted outputs and source hashes are checked.

## Machine-verifiable assets

- research/bible/stability.py — 29 models × 3 weightings,
  six blocks, 20 complementary selections, 3,000 whole-series
  OOB draws and match/series influence.
- research/bible/build_trial_ledger.py — 38 documented attempts.
- research/bible/independent_reference_check.py — standard-library
  arithmetic and alternative RNG bootstrap reference.
- docs/INDEPENDENT_BIBLE_REVIEW_DISPOSITION.md — scope and
  response to independent pre-fix statistical critique.
- research/bible/results/ — timestamped data, all estimates,
  all bootstrap selections, trial ledger and SHA-256 receipt.
- kaggle/verify_bible.py — four reproducible, same-method parity checks.
- kaggle/kernel_scores/, kernel_instability/, kernel_maxt/, kernel_chronology/
  — private notebook and metadata files.
- kaggle/prepare_private_runs.py, run_private_kernels.sh,
  verify_hosted_kernels.sh and verify_hosted_receipts.py
  — data packaging, private execution and numeric parity.
- Original PR #3 notebooks, REPORT.md and main remain unchanged.

### Verification

**All results are post-hoc on consumed development labels;
reproduction is not new evidence; no fresh OOS, formal PBO,
PnL or hosted-run claim is made.** These four notebooks
replicate fixed-seed arithmetic and original inputs, not
an independently conceived statistical estimator.

The outcome is not a new model effect or a PhD-level theorem.
It is transparent and economically modest: a negative
model-selection result, explicit dependence, an incomplete
trial ledger and runnable cross-environment audit protocol.
