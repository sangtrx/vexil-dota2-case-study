# One Quant Bible path-dependence idea — actually tested on TRAIN

**Verdict:** FAILED predeclared gate; do not add Q1 to Vexil employer notebook.

This is a **post-original-TEST, 291-game TRAIN-only** sensitivity,
not an independent replication. The required notebook, M0/M1 selection,
TEST predictions and user-owned disclosure are unchanged.
The motivating question is whether recent drawdown, volatility and
directionality of gold lead add information after controlling for the
current lead and elapsed game time. Section 8 of the Quant Research
Bible treats transforms as additional models subject to selection risk.

**Predefined model:** five-feature Q1 = gold, time, signed ten-minute
adverse excursion, signed ten-minute lead realized volatility and
ten-minute directional path efficiency. No hyperparameter/window
search. All **10675**
source TRAIN forecasts passed causal-prefix and team-symmetry checks.

## Original TRAIN-only chronological forward scores

Rows are Q1 minus the named comparator; negative means Q1 wins.
**Unadjusted percentile 95% CI uses 5,000 paired resamples of
70 professional series/singletons.**
It is descriptive after historical model searches, not a new p-value.

| Comparator | Mean Δ log loss [95% CI] | Mean Δ Brier | Q1 better folds |
| --- | ---: | ---: | ---: |
| M0_gold | -0.006350 [-0.013632,+0.000561] | -0.001779 | 4/4 |
| A_additive | -0.008143 [-0.016305,-0.000744] | -0.002289 | 4/4 |
| M1_interaction | -0.006123 [-0.017362,+0.004680] | -0.002694 | 3/4 |

| Fold | Eval games | ΔLL vs additive | ΔLL vs M1 |
| --- | ---: | ---: | ---: |
| 1 | 22 | -0.011509 | -0.019838 |
| 2 | 44 | -0.011269 | +0.006374 |
| 3 | 32 | -0.000825 | -0.006897 |
| 4 | 39 | -0.009007 | -0.012461 |

| Comparator | Q1 Δ overall Brier | Q1 Δ Brier at minute 30+ | Largest favorable cluster / total LL gain |
| --- | ---: | ---: | ---: |
| M0_gold | -0.001779 | -0.009798 | 29.6% |
| A_additive | -0.002289 | -0.011226 | 31.3% |
| M1_interaction | -0.002694 | -0.007912 | 44.4% |

The largest favorable cluster's percentage is a concentration
**diagnostic**, not a probability. The uncertainty intervals in the
first table are **not adjusted for previous searches of 28+ features**;
the original TEST was opened before this idea was introduced.

**Design:** four existing forward TRAIN blocks, **137 games /
5081 minute forecasts**. A training label is admitted only
when the professional match ended before the next evaluation block
starts, *not* when true source `received_at` was observed (unavailable).
No original VALIDATION/TEST feature or outcome rows were loaded;
only the fixed split manifest of match IDs was inspected.
Q1 was tested once using the frozen window/features and regularization.

**Decision:** Q1 passes the directional and Brier point-estimate checks but fails the predeclared superiority condition versus M1: the 95% log-loss CI still includes zero. Do not promote it. A discarded
hypothesis with a clear negative control is evidence of scientific
creativity, not proof of predictive improvement or 10/10 from Vexil.
