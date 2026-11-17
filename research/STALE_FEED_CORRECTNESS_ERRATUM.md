# 18 Nov 2026: Mandatory correctness repair after INVALID first run

**The original pre-outcome protocol at fcf07a2 is not silently altered.** It
mistakenly described the CLOCK interaction as `gold_old*t/10`.
The shipped original TRAIN data instead has `gold_x_time = gold_k *
log1p(minute10)`, enforced by the existing validation contract at
`research/train_time_effect_ci.py:67`. All 10,675 TRAIN rows verify that
formula to absolute <=1e-12, and naive multiplication differs on many rows.

The initial execution (source commit 12c11b7) used the erroneous formula.
It reported anomalously large CLOCK log loss (CLOCK1 1.042949, CLOCK3
0.963001) and an apparent HOLD advantage; **those numerical comparisons
are INVALID** and cannot support any scientific or application decision.
The original JSON/readout are archived with INVALID labels, not cherry-picked
or overwritten.

**Repair before re-scoring:** The feature contract and negative zero-lag
oracle have been added to source/tests. CLOCK now computes
`gold_old*log1p(minute10_current)` while HOLD uses the last recorded
fresh forecast. All other locked parameters, 1/3 minute lags,
mature-label folds, outcomes, comparator, bootstrap 2,000, gates and
protected applicant artifacts are unchanged. The corrected run is a
**post-error repaired** run, not a fresh blind experiment; if it contradicts
the original story, report the corrected result without selecting a variant.
In addition to point-of-time feature parity, enforce direct zero-lag
feature parity to original frozen TRAIN inputs.
