# Stage-aware shrinkage: ONE new falsifiable hypothesis

**Hypothesis registered before viewing the third chronological cohort's results.**
This follows two disjoint earlier evaluations:
- Original 106 held-out games: M1-time vs M0-gold mean log-loss improvement
  of -0.0144 in minutes 0–9, but inconclusive all-minute improvement.
- 200 later forward games dated March 26–30, 2026: 0–9 improvement
  -0.02072 with paired whole-match 95% interval [-0.03097,-0.00993];
  overall difference -0.00485, CI [-0.01416,+0.00506]. From minute
  20 onward the M1 point estimates were worse than M0. All results
  were inspected BEFORE registration of this third-cohort experiment.

## Locked stage gate (no learned transition parameter)

P_gate(t) = w(t)*P_M1(t) + (1-w(t))*P_M0(t)
where the minute clock is an integer:
  w(t) = 1                if t <= 10
  w(t) = (20-t)/10        if 10 < t < 20
  w(t) = 0                if t >= 20

The transition is continuous at its discrete boundaries, always a
convex combination of two already-existing probabilities, and cannot
access any extra data or fields. Its 10/20 breakpoints were chosen once
from the already observed early/medium phase pattern, NOT learned on
the new confirmatory cohort. This is a post-hoc research hypothesis,
not a preregistered result of the original take-home.

The frozen M0 and M1 architectures, regularization C=1 and source
feature pipeline are unchanged. Fit both only once on the original
500 March 21–26 games; no tuning/refit on the March 26–30 development
replication nor on the third holdout. Do not change the mixture weights
or fit any reliability map based on confirmation outcomes.

## New third chronological test - completely separate

Pick the first 200 eligible, fully parsed OpenDota pro matches (patch
60, >=10 minutes, parsed radiant_gold_adv) after the LAST March 26–30
200-game start timestamp. Exclude all match IDs and positive series IDs
from BOTH prior 500- and 200-game sets. Sort proMatches metadata by
(start_time,match_id), apply outcome-blind eligibility only, freeze IDs
and SHA256 manifest receipt BEFORE calculating any win probabilities.
Only existing OpenDota /proMatches and /matches/{id} may be accessed.

Model fitting: the original 500 games only. Third holdout: evaluate
M0, M1 and the SINGLE gated mixture once, no candidate selection.
Primary metric: minute-weighted log loss, gate vs M0 AND gate vs M1.
Both comparisons are required; not just an easy baseline. Use the same
series-cluster, paired resampling indices to compute a simultaneous
95% max-t CI over the two comparisons (2000 resamples fixed seed).
Also print whole-match 95% CI and descriptive Brier/calibration/accuracy
by phase. Practical gain threshold: >=0.005 absolute log loss versus
BOTH existing alternatives, BOTH simultaneous upper bounds <0, AND no
degradation in Brier vs either. The threshold is a decision guardrail,
not a p-value.

Even if an early-only phase improves, that is not sufficient for a GO
on the overall stage-gated model. No reweighting post-results.
Label maturity, payload drift, intra-series dependence and 200-game
sample size are limitations. Neither predictive performance nor
Dota probability accuracy is a financial, trading or betting edge
without prices and execution.

If this gate fails, report the failure and STOP. The original PR #3
take-home remains unchanged. New tests after this one need a genuinely
new data set and a separately registered question.

Quant Research Bible v1.4.1: 1.2-1.4 finite claims, 3 PIT integrity,
4.3 dependent rows, 5 chronological splits, 6.5 clusters, 7.2-7.7
probability scores, 13 falsification, 14 reproducibility.
