# Vexil proposal factory — all 28 outcomes, including failures
**13 November 2026 · one-shot exploratory screen · DO NOT PROMOTE**

## Registered before outcomes

- Proposal cards: research/proposals/P01...P28; registry SHA256:
  650819d80fef51aaa7a9f1057639f06e2de169a698f8975bea36bf001e95a525.
- Immutable code and screen-registration commit:
  bc134daa6f8db0ad8e090f2102d694b700eb5f67.
- Source: original 500-match OpenDota cache, **291 training games**
  and **103 previously inspected validation games**. No external datasets
  or endpoints were introduced. None of the original 106-match test,
  first 200-match forward test or second 200-match gate-confirmation
  test labels were loaded in this 28-model evaluation.
- The feature builder passed **4,154** real
  prefix-truncation, endpoint-cutoff and postgame-label poison checks
  on all 394 development games. Earlier separate audits checked
  900 cached games and 32,106 clock/gold-sum indexes.
- **28 hypotheses** fixed; three train-only chronological, series-safe
  folds; one full 291-train vs 103-validation comparison per model;
  log loss, Brier, per-game sensitivity, ECE/phase reporting.
- **5,000** paired **series-or-singleton** block bootstraps across
  **53 clusters**, using ONE simultaneous 95% max-|t| familywise
  adjustment over all 28 candidate-minus-M1 differences.
  This attempts to control the finite search family but does not
  repair earlier adaptive reuse of the same validation outcomes.

## Verdict

**0 of 28 models met the complete precommitted advancement screen.**
The original M1 gold×time remains the selected take-home model.
No new blind cohort is needed, and NO existing consumed test set
was opened to rescue a seemingly strong candidate.

The best point estimate was **P20 (High-impact item completions)**,
log loss **0.514098** vs M1 **0.519346**:
difference **-0.005248**. Its Brier was
0.173742 vs 0.175767. The top candidate achieved the point-estimate loss threshold.
But only **1/3** earlier training-only
time folds favored it; the simultaneous 95% upper bound was
**0.006434**, above zero. Both the
ordinary paired CI [-0.013028,
0.002012] and adjusted interval
[-0.016929,
0.006434] span zero. **HOLD.**

Earlier training-only fold deltas for P20
(negative is better):
0.031323, -0.001252, 0.006253.
The fixed non-parametric phase score table below is DESCRIPTIVE
because it uses the same previously inspected 103 validation games.

| Phase | M1 log loss | P20 log loss | P20−M1 |
|---|---:|---:|---:|
| overall | 0.519346 | 0.514098 | -0.005248 |
| 0-9 | 0.654990 | 0.654070 | -0.000920 |
| 10-19 | 0.539328 | 0.536508 | -0.002820 |
| 20-29 | 0.440163 | 0.431921 | -0.008241 |
| 30+ | 0.409073 | 0.398483 | -0.010590 |

## Full 28-way ranking (all candidates retained)

Positive candidate-minus-M1 log loss is WORSE, and a positive
adjusted upper interval bound is insufficient for evidence
of improvement. The fold count is a direction check, not a p-value.

| ID | Family | Log loss ↓ | Brier ↓ | Δlogloss vs M1 | MAX-T upper 95% | favorable folds | passes |
|---|---|---:|---:|---:|---:|---|---|
| P20 | items | 0.514098 | 0.173742 | -0.005248 | 0.006434 | 1/3 | NO |
| P08 | economic | 0.515840 | 0.174408 | -0.003505 | 0.005137 | 0/3 | NO |
| P15 | objectives | 0.517020 | 0.175106 | -0.002326 | 0.012956 | 2/3 | NO |
| P05 | economic | 0.518253 | 0.175137 | -0.001093 | 0.001409 | 2/3 | NO |
| P18 | option-state | 0.518400 | 0.175156 | -0.000946 | 0.002091 | 3/3 | NO |
| P11 | dynamics | 0.518548 | 0.175442 | -0.000798 | 0.001211 | 1/3 | NO |
| P02 | time-shape | 0.519032 | 0.175579 | -0.000314 | 0.002805 | 0/3 | NO |
| P21 | items | 0.519167 | 0.175690 | -0.000179 | 0.000323 | 0/3 | NO |
| P01 | time-shape | 0.519376 | 0.176116 | 0.000030 | 0.003281 | 0/3 | NO |
| P07 | economic | 0.519438 | 0.175775 | 0.000092 | 0.001165 | 0/3 | NO |
| P03 | time-shape | 0.519550 | 0.176108 | 0.000204 | 0.002694 | 2/3 | NO |
| P09 | dynamics | 0.519689 | 0.176341 | 0.000343 | 0.010379 | 2/3 | NO |
| P10 | dynamics | 0.519737 | 0.176561 | 0.000391 | 0.011390 | 3/3 | NO |
| P12 | dynamics | 0.520048 | 0.176644 | 0.000703 | 0.009012 | 3/3 | NO |
| P19 | option-state | 0.520337 | 0.176473 | 0.000991 | 0.008862 | 2/3 | NO |
| P04 | time-shape | 0.520392 | 0.176383 | 0.001046 | 0.003549 | 0/3 | NO |
| P17 | option-state | 0.520974 | 0.176396 | 0.001628 | 0.005043 | 2/3 | NO |
| P06 | economic | 0.521304 | 0.177304 | 0.001958 | 0.024062 | 2/3 | NO |
| P28 | shape | 0.521667 | 0.176660 | 0.002321 | 0.006691 | 2/3 | NO |
| P25 | shape | 0.523213 | 0.177192 | 0.003867 | 0.011408 | 0/3 | NO |
| P27 | synthesis | 0.524031 | 0.178222 | 0.004686 | 0.012520 | 2/3 | NO |
| P13 | objectives | 0.524753 | 0.178280 | 0.005407 | 0.021327 | 1/3 | NO |
| P16 | objectives | 0.525120 | 0.178901 | 0.005774 | 0.013189 | 3/3 | NO |
| P26 | synthesis | 0.528841 | 0.180177 | 0.009495 | 0.029287 | 2/3 | NO |
| P14 | objectives | 0.528961 | 0.180257 | 0.009616 | 0.027557 | 1/3 | NO |
| P23 | shape | 0.532511 | 0.179920 | 0.013165 | 0.031488 | 1/3 | NO |
| P24 | shape | 0.539473 | 0.183276 | 0.020127 | 0.040017 | 2/3 | NO |
| P22 | draft | 1.581239 | 0.368861 | 1.061894 | 1.637817 | 0/3 | NO |

Reference M1: log loss 0.519346, Brier
0.175767; P22 high-dimensional hero one-hot scored
substantially WORSE than M1. This is consistent with risk from
fitting 160 signed hero indicators on only 291 independent
training games replicated over many correlated minute rows;
it is NOT proof hero drafts lack predictive value.

## Scientific interpretation

1. **P20 item-purchase events** produce the most encouraging
   validation point difference, but the sign reverses in
   training-only forward folds, and both unadjusted and familywise
   confidence intervals include zero. Purchase-log entries are
   a proxy for reported item acquisition, NOT verified inventory
   possession or live network receipt.
2. **P08 economic distribution** has the second-best validation
   point estimate but performed worse than M1 in **all three
   earlier train-only folds**. This is exactly the false-positive
   pattern a large idea search can create.
3. **P15 recent kills** favors M1 less consistently; it does not
   meet the practical gain or uncertainty criterion. Its events
   may largely be reflected in gold/XP.
4. Shallow tree models, additive B-splines and a raw
   hero-identity model were not rewarded with a compelling
   gain; network capacity is not scientific novelty.
5. Some predictors overlap negative feature experiments
   already explored in separate PR #4 and #5. This factory
   DOES NOT make those old validations independent.

## Code, lineage and stopping rule

- research/execute_proposal_factory.py — single screen, fixed
  familywise selection rule; no model search grid or hidden test.
- research/proposal_factory_features.py — 201 feature columns,
  all fields strictly from OpenDota observations through minute t.
- research/proposal_factory_registry.py — frozen 28-hypothesis spec.
- research/results/all_28_candidate_scores.csv — full-precision
  metrics, Brier, equal-match sensitivity, familywise bounds.
- research/results/train_only_3fold_scores.csv — 87 recorded rows
  (29 models including M1 × 3 folds).
- research/results/calibration_and_phase_scores.csv — 145 rows,
  all 29 models × five phases; fixed-bin descriptive ECE.
- research/results/dev_validation_predictions_28.csv —
  3,784 validation minute rows × 29 probability series, with
  match/series IDs, minutes and observed labels; PRIVATE repo only.
- research/results/screen_receipt.json and lock.json — code
  registration, source SHA, exact input split and STOP result.
- research/results/outcomes/P01...P28 — individual unfiltered
  model verdicts so no failed proposal disappears from view.

**Do not ship any of P01–P28 on the present evidence.**
The statistically defensible next move is to formulate ONE
narrower hypothesis with independently observable item life
cycle or stronger team-state semantics, register it prospectively,
and verify it on a genuinely fresh later cohort ONLY after
a strong development screen. It may still be negative.

The original notebook and ≤4-page take-home REPORT.md in
Draft PR #3 remain unchanged and separately submission-ready
only after their own outstanding Colab and human-hours checks.
