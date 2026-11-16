# Research decision trail

**Reader's map, written on 16 November 2026.** This is a retrospective index of real research artifacts and decisions, **not** an invented day-by-day diary or a claim that these paragraphs preceded the experiments. Original commit times are retained. See [curation provenance](CURATION_PROVENANCE.md).

## Decision, not model complexity

**Question.** Does the same gold advantage imply the same Radiant win probability at minute 10 and minute 30?

**Experiment.** [Original `/proMatches` patch-boundary discovery and the 13 Nov ID freeze](DISCOVERY_PROVENANCE.md) produced 500 parsed professional OpenDota matches (250 patch 59, 250 patch 60). Group professional series, order by game start time: **291 TRAIN / 103 VALIDATION / 106 TEST** games. Strict preterminal cutoff yields **18,292 forecasts**, including **3,836 TEST** minutes. Source event time is not verified live receipt time.

**Comparator.** M0 is gold-only logistic regression; M1 adds elapsed minute and gold-by-log-time interaction. M1 wins on VALIDATION log loss **0.5197 vs 0.5325**; the richer M2/M3 do not. This justifies testing the hypothesis, not deploying M1.

**Decision.** Original TEST M1 log loss **0.5040 vs M0 0.5164**, Brier **0.1684 vs 0.1719**. Both primary paired whole-match 95% confidence intervals for the difference include zero. One 55-row game contributes **54.9%** of the total log-loss improvement. M1 has a worse late (30+) Brier point estimate (**0.1074 vs 0.1028**) with uncertain interval; only **2/5** additional TRAIN-only rolling folds favored M1. **Retain M0; shadow-test M1 until independent new evidence clears a predeclared gate.**

## The falsification trail

| Research path | Actual finding | Decision | Original evidence |
| --- | --- | --- | --- |
| Economic concentration and path fragility | Small gains disappear in dependence/forward checks | HOLD; no promoted model | [PR #4](https://github.com/sangtrx/vexil-dota2-win-probability/pull/4) |
| Aegis, buybacks and persistent objectives | Matched training games show state aliasing but no confirmed predictive lift | Retain as an interpretation, not an uplift claim | [PR #5](https://github.com/sangtrx/vexil-dota2-win-probability/pull/5), [PR #8](https://github.com/sangtrx/vexil-dota2-win-probability/pull/8) |
| Twenty-eight follow-up specifications | **0/28** passed reused-VALIDATION gates; selected winner unstable under resampling | Stop model search | [PR #6](https://github.com/sangtrx/vexil-dota2-win-probability/pull/6), [PR #7](https://github.com/sangtrx/vexil-dota2-win-probability/pull/7) |
| Red team and rolling folds | Parsing, support and label-maturity hazards exposed; M1 better in only 2/5 TRAIN folds | Correct implementation and disclose fragility | [PR #9](https://github.com/sangtrx/vexil-dota2-win-probability/pull/9) |
| Grouped uncertainty | Post-hoc 54-series bootstrap LL difference still crosses zero, Brier boundary differs by resampling unit | Prioritize the prespecified match CI; do not cherry-pick | [PR #14](https://github.com/sangtrx/vexil-dota2-win-probability/pull/14) |
| November sample | 100 games overlap a prior 120-game cohort by **68 IDs**; two leagues supply 85 games | Not independent replication | [Overlap receipt](NOVEMBER_COHORT_OVERLAP_RECEIPT.json) |
| Value-of-freshness idea | Proposed headline estimator telescoped to endpoint effects | **Rejected** and preserved | [PR #15](https://github.com/sangtrx/vexil-dota2-win-probability/pull/15) |

The [fixed TRAIN matched-state figure](figures/train_matched_state_aliasing.png), regenerated from the frozen development archive by `research/render_train_state_aliasing_figure.py`, visualizes the historical Aegis/objective-state counterexample without using TEST or claiming objective-feature uplift.

The [portable development-label audit](DEVELOPMENT_MATURITY_AND_CREATIVE_NULL.md) refits the same four models on the 286 mature TRAIN games; original M1 selection holds on reused VAL. A separate [500-game future-deletion receipt](FULL_500_PREFIX_AUDIT_RECEIPT.json) checks all 18,292 forecast opportunities (requires author raw cache), and [fixed-bin grouped reliability CIs](CALIBRATION_FIXED_BIN_GROUPED_CI.md) characterize post-hoc calibration uncertainty. The stronger additive gold + time null and rejected TRAIN-only calibration offset are also quantified there. This is an additional post-result sensitivity, not a fresh holdout.

The current reviewer-facing notebook additionally appends two explicitly post-TEST, **non-selecting in-memory verification cells**. These recalculate all 18,292 at-time feature snapshots, original proper losses, ECE, no-skill and the stronger additive TRAIN-only null. The exact original 14-cell notebook is archived separately with its old SHA and historical Colab receipt; reviewer appendix does not create a new blind TEST.\n\nThe follow-ups often used **already observed** validation/TEST cohorts. A written protocol for a subsequent analysis does not make an exposed outcome newly blind.

## Three risks that control the decision

**Point-in-time.** Feature extraction uses snapshots/events no later than the forecast minute. After TEST was opened, a stricter end-of-game check removed 12 rows (8 TRAIN, 3 VALIDATION, 1 TEST). Five TRAIN outcomes may have matured after the first validation game started; removing these in an embargo sensitivity preserved M1 selection. Retrospective event timestamps cannot prove received-at time for live use.

**Dependence and calibration.** 3,836 TEST minute forecasts share only 106 game outcomes and 54 series/singletons. On already used VALIDATION the M1 mean bias is **+0.0300** (53-series CI [−0.0436,+0.1001]); on inspected TEST **−0.0617** (54-series CI [−0.1410,+0.0250]). Both intervals cross zero. The sign reversal is a sampling/composition warning, not established drift or a justification for TEST recalibration.

**Pre-game information.** Without a trusted draft/team-strength prior, **101/106** M1 TEST minute-zero forecasts lie between 45% and 55%. This is a genuine representation limitation, not an invitation to tune on opened TEST.

## New evidence required for promotion

Freeze the models and an explicit forward-data protocol before observing new outcomes. Collect genuinely unopened **multi-league and series-level** games; choose loss, calibration, phase and promotion gates before seeing them. Measure event-to-received-at delay and feature watermark/completeness, track fallbacks and run M1 in shadow against M0. Require a material proper-score gain and supported uncertainty without unacceptable late-phase deterioration. No measured betting alpha or real-trading return follows from this study.

Ground truth: [four-page report](../REPORT.pdf), [executed notebook](../live_dota2_win_probability.ipynb), [frozen TEST probabilities](../artifacts/heldout_predictions.csv), and [experiment register](EXPERIMENT_REGISTER.md).
