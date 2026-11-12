# Edge V2: economy topology and regime stability

**Status: hypothesis registration before evaluating the new forward-time holdout.**
This is a NEW research branch off PR #3. It does not alter the already-scored,
executed 500-game take-home notebook. We have seen the legacy 106-game
test results, so that set is no longer an unbiased test for new ideas.

## Target and constraints

Target: P(Radiant eventually wins | F_t), a calibrated minute-t probability.
Information at minute t may only use gold_t arrays through index t, OpenDota
gold advantage through index t, timestamped logs through 60*t and draft facts
observed before game start. Never use final items, final gold or full duration
as predictors. Source only OpenDota /proMatches and /matches/{id}.

The goal is an interpretable *incremental predictive edge over M1*, not a
positive backtest chosen after inspecting outcomes. Do not claim a tradable
or betting edge without prices, execution or costs.

## Existing benchmark (locked evidence)

M0 gold only, M1 gold/time interaction, M2 XP + trailing change, and
M3 objectives were compared on March 2026 games. M1 was validation-selected.
On its 106-game held-out period: M1 0.503906 log loss vs M0 0.516305;
paired 95% CI for M1-minus-M0 [-0.030286, +0.001400]. M1 accuracy 76.05%
vs M0 75.97% over 3,837 match-minute observations. These are *development
history*, not blind evidence for the new features. Late-game was unstable.

## Structural hypotheses, with feature definitions fixed before new outcomes

All candidate models use the SAME logistic pipeline (training-only median
imputation, training-only StandardScaler, regularized logistic C=1) and the
M1 inputs [gold_k, minute10, gold_x_time]. Additional input family:

S1, RELATIVE ECONOMIC LEVERAGE:
  econ_share_gap = 100*(G_R-G_D)/(G_R+G_D+1000)
where G_side is the sum of five players' cumulative gold_t[t]. For the same
absolute gold advantage, 5k means something different when total earned
gold is 30k vs 150k. This is not merely elapsed time: production speed varies
by draft and game pace. Candidate M1 + econ_share_gap (4 features).

S2, RESOURCE ALLOCATION / CORE DEPTH:
  top2_share_gap = sum(largest2(gold_R_i))/G_R
                   - sum(largest2(gold_D_i))/G_D
  core_gold_gap_share = (sum(largest2(gold_R_i))
                         - sum(largest2(gold_D_i)))/(G_R+G_D+1000)
The top two gold earners are an *observable proxy*, not guaranteed carry
heroes or permanent roles. These features test whether the distribution of
resources can predict victory conditional on the aggregate lead.
Candidate M1 + both features (5 features).

S3, LEAD FRAGILITY / PATH DEPENDENCE:
  relative_shock5 = (gold_adv[t]-gold_adv[max(0,t-5)])/
                    (abs(gold_adv[t])+3000)
  signed_lead_persistence10 = mean(sign(gold_adv[s]))
                              for s in [max(0,t-9),...,t]
A persistent lead differs from a recently reversed or contested lead,
even at the same point estimate. The normalization prevents larger economic
states from mechanically generating larger shocks. Candidate M1 + both (5).

S4, PARSIMONIOUS JOINT STATE:
  M1 + econ_share_gap + top2_share_gap + relative_shock5
Three mechanisms; M1 has 3 features and the joint model has 6.
Do not add item/hero one-hot features from a sample of only 500 games.

Model family: M1, S1, S2, S3, S4, fixed in advance.
Do not add or remove candidates because validation/test outputs look good.
No hyperparameter search or fitting on the new holdout.

## Data and validation protocol

Data development: original 291 train and 103 validation matches, frozen
chronological series-safe split. Only those 394 games may select a candidate
based on proper loss, plus expanding-window series-aware tests within the
original training slice to flag instability. The original 106-game held-out
set may be used *only* in a final training refit after model selection, since
it has been examined; never present a newly tuned result on those games as
independent.

Choose one S candidate if its validation mean log loss beats M1 by at least
0.005 AND a paired whole-match percentile bootstrap 95% CI has upper <0;
otherwise retain M1 and report the feature families as exploratory failures.
To avoid tuning to validation, do not choose between near-tied S variants
based on any other data; pick fewest predictors, then fixed S1,S2,S3,S4 order.
All comparisons include Brier and stage-specific diagnostic scores, but
neither can override this selection rule.

New out-of-time holdout (not yet fetched or scored): from the metadata-only
cached /proMatches pages select the **first 200 eligible parsed professional
matches** after the latest of the original 500 starts (March 26, 2026),
sorted by (start_time,match_id). Exclude match IDs in the original cohort,
and all games sharing a positive series_id with any original 500 games.
Require match patch 60, gold graph parsed and match duration >=600 seconds.
No selection by winner, performance or feature levels. Freeze IDs before
running models; stop with an explicit error if not enough matches. Enforce
separate series groups in the bootstrap; no leakage of outcome or future
snapshot into features. A runtime-level source hash accompanies every run.

Refit both M1 and preselected S candidate on the original 500, *then*
evaluate each model ONCE on the external 200 games without refitting or
choosing further variants. The external holdout is retrospective but
chronologically subsequent and previously uninspected for outcomes.

Primary metric: minute-weighted log loss, S minus M1. Primary uncertainty:
paired whole-match 95% bootstrap with 2,000 fixed-seed resamples, and an
additional series-cluster sensitivity for dependent games. Decision rule:
declare a practically meaningful incremental edge only if external
held-out log loss improves by >=0.010 absolute, its 95% whole-match
bootstrap upper bound is <0, Brier does not worsen, AND calibration is
not visibly degraded. Secondary: equal-match weighting, accuracy by
0-9 / 10-19 / 20-29 / 30+, reliability, stability across dates.
Time/patch/team-level generalization is limited; one 200-game test is not
proof of broad applicability.

No peeking at new holdout outcomes until model selection is locked.
After test, do post-hoc error analysis only with that label, not further
model retuning on this same 200-game set. The final take-home notebook
remains unchanged unless a new candidate actually clears these gates.

## Falsification and stop conditions

- PIT oracle: truncate every array and event at each sampled minute;
  every engineered predictor remains exactly unchanged. Negative tests
  replace future, end-of-match and player final values with poison.
- Missing player histories: return NaN, never fabricated zero; use only
  training-fitted imputation. Check schema coverage by patch and minute.
- Null hypothesis for every candidate: no stable improvement beyond M1.
- Guard against length-weighting artifacts (equal-match sensitivity),
  within-series dependence, patch distribution drift, low-probability
  confident misses, and 100% after-the-fact accuracy.
- If selection gate fails, write a clear negative result and stop;
  do not tune on the original 106-game legacy test or new 200-game test.

## Quant Research Bible v1.4.1

Sections 1.2-1.4 finite hypothesis search and falsification;
3.1-3.6 point-in-time contracts and provenance; 4.3 repeated observations;
5.1-5.6 chronological split and label maturity; 6.5 clustered bootstrap;
7.2-7.7 proper scoring and calibration; 13.1-13.2 causal modesty;
14.1-14.3 reproducibility and negative tests.
