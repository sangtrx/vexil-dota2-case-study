# Vexil: Development-only operational robustness study

Date: 13 November 2026. Parent PR #8 code at
17bb57a25001a59b6d08ceef2cc6aac552dffd8e.

## Frozen scope and information contract

- Use ONLY the 291 original TRAIN games. Do not score original
  validation 103 or held-out 106 matches, or fit models on their labels.
- Candidate family is frozen here before this script is executed:
  M0 gold-only, M1 gold-time, M2 plus XP/velocity, M3 plus objective
  events, and P20 M1 plus two timestamped major-item purchase proxies.
- P20 was already selected from a broader adaptive search, so this
  study is retrospective and not newly independent confirmation.
- Fit same median imputer + StandardScaler + LogisticRegression C=1
  and seed 20261113, without any hyperparameter search.
- Five rolling-origin evaluation windows are chosen by nearest
  series-safe split boundaries at fractions 0.53, 0.62, 0.75, 0.84,
  0.92 and 1.00 of the time-ordered 291 train matches.
- Embargo prior training games with estimated completion
  start_time + match.duration greater than the earliest start of
  the evaluation block. Embargo entire series if needed.
- Compare minute-weighted and equal-match log loss and Brier.
  Report M1 minus M0 and P20 minus M1 per fold, including failures.
- Only the pre-existing cached raw OpenDota match payloads may be
  read. Network calls are forbidden: cache misses must fail.
- Do not modify the original M1 held-out evaluation, score
  new 103/106 labels or promote any model based on these folds.

Approximate game-end time ignores pauses and network arrival; these
folds are not a live deployment or textbook PBO/CPCV. A
hypothetical stability screen for future research (not model
promotion): benefit in at least 4 of 5 windows for both weighting
systems, without any >+0.015 catastrophic loss fold. Even a pass
is not independent evidence due previous research exposure.


## Outcome-blind design correction before scoring

The first script abort (no model was fitted or scored) exposed a
two-game evaluation fold. The original fractions produced series-safe
cut indices [154,156,176,221,269,291], with 2 games in the first
evaluation block. Series IDs cross many time-ordered match positions,
so arithmetic percentage splits are not valid by themselves.

Before inspecting any model prediction or label-derived metric,
the six metadata-only target fractions were shifted to
[0.53,0.62,0.75,0.84,0.92,1.00], which map to series-safe
cut indices [154,176,220,247,269,291] and evaluation
sizes [22,44,27,22,22]. This is a feasibility fix based only
on match start times and positive series_id grouping.
It is logged, not backdated or presented as the original design.
This series-safe split does not imply genuine label end-times:
the separate completion embargo is still required.
