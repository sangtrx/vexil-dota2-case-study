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
| Time-series groups | 103 games, 53 positive series | Six contiguous series-aware time blocks |
| Model selection instability | All C(6,3)=20 complementary block splits | Winner had *worse log loss than M1* on other half in **10/20** splits |
| Complementary rank reversal | 20 block splits, 29 models | In **6/20** splits the selected model ranked below the median of 29 on the other half |
| Series out-of-bag selection | 3,000 seeded, whole-series bootstrap draws | Selected model worse than M1 on omitted groups in **51.47%** |
| P20 selection frequency | 3,000 in-bag selections | P20 chosen **45.43%**, not a stable universal winner |
| Familywise 28 comparisons | 5,000 whole-series max-t bootstrap draws | All 28 original confidence intervals reproduced, multiplier **3.079034** |
| Historical research ledger | Prior PR #3, #4, #5 and #6 | **38 known model-attempt records**, not 38 independent trials; some prior explorations are not fully enumerated |

**Interpretation:** Even an apparently attractive point estimate
can arise from selection across multiple candidates and depend
on evaluation weighting. This is not the official PBO statistic:
our 20 complementary splits reuse already-inspected development
labels and models fitted on common earlier training data. It
cannot restore a blind holdout or estimate future PnL.

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
P20 in only **1/3** folds, and its 28-way simultaneous series
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

Three PRIVATE Kaggle-ready CPU notebooks have been generated:
proper scores, selection stability and 28-way familywise
bootstrap. All three were **executed locally** with a Jupyter
kernel (not just imported), and their independent calculations
passed all numeric parity checks. In local environment:
Python 3.12.3, NumPy 2.2.6, pandas 2.3.3.

**New hosted Kaggle runs: 0.** The BigLinux Kaggle CLI
currently reports no authentication, and neither a private
dataset nor these three notebooks has been uploaded or run
in Kaggle cloud. Earlier independent Kaggle run of the
original 500-match notebook was verified in PR #3 and
is a different experiment.

When Kaggle login is restored, follow kaggle/README.md:
create a new PRIVATE dataset once; run three PRIVATE kernels
with internet/GPU OFF; download hosted receipts and verify
numerical parity. Do not label a launch as COMPLETE before
the hosted outputs and source hashes are checked.

## Machine-verifiable assets

- research/bible/stability.py — 29 models × 3 weightings,
  six blocks, 20 complementary selections, 3,000 whole-series
  OOB draws and match/series influence.
- research/bible/build_trial_ledger.py — 38 documented attempts.
- research/bible/results/ — timestamped data, all estimates,
  all bootstrap selections, trial ledger and SHA-256 receipt.
- kaggle/verify_bible.py — three independent executable QA modes.
- kaggle/kernel_scores/, kernel_instability/, kernel_maxt/
  — private notebook and metadata files.
- kaggle/prepare_private_runs.py, run_private_kernels.sh,
  verify_hosted_kernels.sh and verify_hosted_receipts.py
  — data packaging, private execution and numeric parity.
- Original PR #3 notebooks, REPORT.md and main remain unchanged.

### Verification

The outcome is not a new model effect or a PhD-level theorem.
It is rigorous and economically modest: a transparent negative
model-selection result, explicit dependence, an incomplete
trial ledger and runnable cross-environment audit protocol.
