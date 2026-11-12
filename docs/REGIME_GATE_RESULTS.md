# Stage-gate not confirmed: M1 retained on the latest cohort

**13 November 2026 — independent third-cohort result — HOLD (do not promote the gate)**

The fixed stage-aware shrinkage hypothesis was registered in git commit
40d8961, before the third chronological cohort was scored.
Its one-shot evaluator was locked at 9043370. The earlier 200-game forward-manifest commit b61750f predates this gate hypothesis; it is NOT the third-cohort manifest. After independent Sonnet
red-team review, the metadata freeze and statistical QA were finalized
and committed at 4c11b48, still before this cohort was scored.

The original 500-match take-home notebook and its Draft PR #3 remain
unchanged. This work belongs to separate research Draft PR #4.

## Mechanism and an outcome-blind third cohort

A time interaction improved the original gold-only logistic model's
proper scores, especially near the start of games. A subsequent
200-game time-forward check showed weaker aggregate improvement
and late-game deterioration. This motivated one explicitly post-hoc
hypothesis: use M1 through minute 10, blend it linearly toward M0
for minutes 11–19, and use M0 from minute 20 onward.

This is a fixed, non-learned convex mixture, not an attention model or
a new neural architecture. There was no cutoff grid search. M0 and
M1 were fitted only on the original 500 games.

The third chronological cohort comprises **200 new professional games
from 30 March to 2 April 2026**, patch 60, with 6,827 minute-level
observations. It shares no match IDs or positive series IDs with
the original 500 or intermediate 200. There are **97 series-or-singleton
groups**, including four games without a recorded series ID.

All 200 outcome-blind match records were committed before test
evaluation. Full metadata SHA-256:
afd6c0e63d9795ef74369a025c2cb8d714f7b5ed83134db2078368e7b5ed8bca.
The analysis was executed **once** at locked HEAD 4c11b48.
The one-shot lock and result receipt remain in the QA artifacts.

The source was audited over 95 cached OpenDota professional-match
pages: 9,500 distinct IDs, no conflicting repeated metadata entries.
An independent post-run check confirmed the 200 unique IDs, expected
minute rows, gate weights and input/result hashes. The 2,112
prefix-truncation PIT checks passed with zero API calls during scoring.

## Fixed-comparison results

| Phase | Games | Minute rows | M0 log loss | M1 log loss | Gate log loss | M0 Brier | M1 Brier | Gate Brier |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Overall | 200 | 6,827 | 0.54507 | **0.53370** | 0.53985 | 0.18647 | **0.18242** | 0.18430 |
| 0–9 | 200 | 2,000 | 0.66781 | 0.65844 | 0.65844 | 0.23765 | 0.23341 | 0.23341 |
| 10–19 | 200 | 1,986 | 0.57207 | 0.55971 | 0.56355 | 0.19479 | 0.19054 | 0.19161 |
| 20–29 | 198 | 1,824 | 0.43389 | 0.42995 | 0.43389 | 0.14180 | 0.14094 | 0.14180 |
| 30+ | 129 | 1,017 | 0.45038 | 0.42369 | 0.45038 | 0.14971 | 0.14065 | 0.14971 |

On this cohort the gate has a lower loss point estimate than M0, but a higher one than full M1. The gate-minus-M1 CI still includes zero; worse observed loss does not establish a population-level disadvantage. In the 20+ minute subsets, M1 had lower observed loss than M0, so using M0 there did not help on this sample. A pattern seen in an earlier cohort did not replicate consistently.

### Calibration, descriptive only

A ten-bin fixed-width, minute-weighted expected calibration error
(ECE) audit was computed from the already-saved predictions. This
summary has no series-cluster confidence interval and was not used
to choose or tune the gate.

| Phase | M0 ECE | M1 ECE | Gate ECE |
|---|---:|---:|---:|
| Overall | 0.03696 | **0.01834** | 0.02222 |
| 0–9 | 0.05959 | 0.02192 | 0.02192 |
| 10–19 | 0.06521 | **0.02866** | 0.04617 |
| 20–29 | 0.04124 | **0.03582** | 0.04124 |
| 30+ | 0.05553 | **0.05279** | 0.05553 |

The artifact exports complete reliability-bin frequencies and
distinct match counts, plus exploratory paired whole-match
confidence intervals for each phase. Phase findings are not
multiplicity-adjusted across reporting periods.

The prespecified 10,000-draw series-or-singleton cluster bootstrap and simultaneous two-sided, studentized max-t familywise 95% intervals (centered on the observed differences) gave:

| Contrast (gate minus comparator) | Log-loss difference | Simultaneous 95% series-cluster interval |
|---|---:|---|
| Gate − M0 | −0.005225 | [−0.011826, +0.001376] |
| Gate − M1 | **+0.006146** | [−0.002836, +0.015127] |

The rule required at least **0.005 improvement over BOTH** M0 and
M1, BOTH simultaneous upper confidence bounds below zero, and
Brier no worse than either. The gate fails against M1 on the required gain magnitude, simultaneous confidence bound, and Brier point estimate. It beats M0 by more than 0.005 in the observed loss, but fails its confidence requirement.

**Decision: HOLD the gate, STOP its development on this consumed
200-game set.** The 10–20-minute weights and loss threshold remain
unchanged; no alternative phase boundary is selected after inspecting
these outcomes. This particular gate did not meet the precommitted
requirements; that is not proof every stage-aware model must fail.

## Secondary, hypothesis-generating M1 comparison

M1's direct, descriptive third-cohort comparison against the original
gold-only M0 is worth preserving:

- Log-loss M1−M0 **−0.011371**, standalone paired series-cluster
  95% interval **[−0.022317, −0.000707]**.
- Brier M1−M0 **−0.004057**, standalone series-cluster 95% interval
  **[−0.007829, −0.000266]**.
- Classification accuracy: M0 **71.16%**, M1 **71.14%**,
  stage gate **71.06%**.

These direct M1–M0 intervals were calculated descriptively AFTER
the gate confirmation, and are **not** the registered gate's GO
criterion. They are not familywise-adjusted for this second layer
of outcome examination, and do not constitute independent confirmatory proof. The two older chronological test cohorts also had
negative overall M1−M0 log-loss point estimates, but their
paired 95% intervals included zero.

A narrower observation is supported: the existing fixed gold-by-time model had lower overall log-loss point estimates across three sequential cohorts, but only the third unadjusted descriptive series-bootstrap interval excludes zero. The late-game M1−M0 point difference changed sign between the second and third cohorts. There is no meaningful win/lose accuracy breakthrough and no guarantee of transportability to other patches, opponents or leagues.

## What the feature engineering taught us

Four mechanism-based families were independently tested using only
the original 291 train and 103 validation games:
- S1: gold lead relative to total team economic scale;
- S2: resource concentration in the two richest players per team;
- S3: normalized five-minute economic shocks and lead persistence;
- S4: a parsimonious combination of those components.

S2 reduced validation log loss by 0.001962 against M1, but
was worse in all three earlier train-only walk-forward folds.
After adjustment for four hypotheses using simultaneous
series-cluster intervals, its improvement was no longer decisive
(CI [−0.004100, +0.000176]). S1 was also below the practical gain
threshold. S3 had a worse validation point estimate. With only 103 validation games, these results fail to establish incremental benefit; they do not prove the underlying mechanisms are absent. No structural model qualified for independent confirmation.

These feature families have concrete economic interpretations but did not meet the previously declared practical and statistical criteria for promotion. More variables alone are not proof of useful prediction.

## Research and submission implications

The most promising next research, on a new, uninspected
cohort, would register a narrow hypothesis linking **timestamped
item purchase/completion** and **draft-specific hero power spikes**
to conditional win probability. A separate design could test
objective-conversion hazards and calibration drift by patch and
tournament. Both require strict point-in-time event semantics,
cross-series replication and a genuinely fresh dataset.

Those are proposals, **not tested results**. Do not retrofit them
to the now-consumed cohorts, invent a winning model, or merge this
failed gate into the primary take-home notebook.

A probability win-rate model is **not** a betting or trading edge
without market price, execution and costs. OpenDota match-clock
timestamps are retrospective and do not prove real-time
network arrival. The primary loss is minute-weighted, so longer matches contribute more rows. Later phase subsets condition on future-known match duration (200, 200, 198 and 129 games). The 97 series-or-singleton groups mitigate, but do not eliminate, shared tournament, team and opponent dependence. The independent sample and statistical power remain limited.

## Reproducible, post-outcome audit assets

The following derived outputs are versioned in the private repository
under research/results/v3_confirmation/:

- gate_confirmation_predictions.csv — all 6,827 minute-level predictions,
  outcomes and three per-row proper losses;
- gate_confirmation_phase_results.csv — phase-level loss, Brier and accuracy;
- gate_confirmation_series_ci.csv and gate_confirmation_match_ci.csv —
  the registered overall two-comparator max-t intervals;
- gate_confirmation_phase_match_ci_exploratory.csv — descriptive
  whole-match uncertainty for the individual reported phases;
- gate_confirmation_calibration_by_phase.csv and
  gate_confirmation_reliability_bins.csv — fixed 10-bin descriptive
  calibration, with row and distinct-match counts;
- m1_vs_m0_secondary_unadjusted_ci.csv — the explicitly post-hoc
  two-model direct comparison, separately labeled;
- gate_confirmation_evaluation_receipt.json and
  gate_confirmation_consumed.lock.json — frozen input/code hashes,
  library versions, locked HEAD and one-shot evaluation provenance;
- post_run_independent_QA.json — checks on input manifest, model-mixture
  identity, output row counts and loss arithmetic.

The post-outcome reporting_audit.py script only RECOMPUTES
descriptive statistics from saved predictions; it does not refit,
reselect or run the consumed confirmation experiment. All six
loss/Brier numbers in each phase row, both familywise CIs and
15 calibration ECE figures were checked against the saved CSVs
within their stated rounding precision.

**Shipping decision:** keep original PR #3's M1/M0 analysis.
Keep PR #4 as research evidence, unmerged. The third confirmation
cohort is consumed; a new optimization needs a new blind dataset
and a separately frozen protocol.

Methods are self-contained in the registered protocol, Python source and exported CSVs: finite hypothesis families, point-in-time contracts, temporal validation, paired grouped bootstrap and strictly proper losses. An internal Quant Research Bible v1.4.1 (Sections 1–7, 13–14) informed the design but is not needed to reproduce this report.
