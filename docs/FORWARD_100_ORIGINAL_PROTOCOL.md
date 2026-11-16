# Predeclared frozen-model forward-domain stress test (15 Nov 2026)

**Locked before requesting new OpenDota match data.**
This is optional research, NOT the recruiter 500-game notebook, not
model promotion, and not authenticated actual live feed timing.

## Fixed question, training models, and comparisons

Do the unchanged March 2026 fitted M0 (gold only) and
validation-selected M1 (gold, minute, gold x log(1+minute/10))
generalize to a later Oct-Nov 2026 professional-match population?

Model specification: original 291-game/10,675-minute TRAIN features
from research/frozen_original_train_features.csv.gz, whose original
SHA is pinned by the ZIP packer; sklearn pipeline median imputer
(keep_empty_features=True), StandardScaler, LogisticRegression
(C=1,max_iter=1000,random_state=20261113), all exactly from frozen
notebook science-code SHA
e9225bc9b270f7d1ae50352822b49930af39a8664fbbd749b05218411d707f7b.
Do not use later labels for fitting, selection, recalibration or blending.

## Fixed discovery/eligibility and stop

Query only /proMatches and /matches/{match_id}. Before opening any
outcome labels, freeze raw full page responses and candidate ID list;
scan **strictly descending match ID** with less_than_match_id cursor
from current OpenDota proMatches (up to 15 pages). Select the
**first 100 eligible** professional games in that order without
examining predictive metrics or winner balances. Start UTC must be
>= 2026-10-01T00:00:00Z and < 2026-11-16T00:00:00Z.

A game is eligible only if it has:
* valid match ID, start_time, patch, duration >=600s, Boolean result;
* nonempty Radiant gold and XP arrays; exactly ten player slots and
  explicit minute-indexed player times, gold_t/xp_t; 60t-duration
  strict horizon; numeric team economy consistent with players.
Use the ORIGINAL notebook strict player clock verification, not
handwritten approximations.
Failures (missing parsed data, wrong clocks, too short, out-of-window,
missing patch/label) are logged by match ID with their non-outcome
reasons. No retries of ineligible matches after seeing outcomes.
At most 500 detail downloads, 15 full pages, 9 bounded network retries
per transient error. If 100 eligible games cannot be found:
STOP, mark incomplete, disclose counts; do not shrink target, switch
window, relax criteria or report pseudo-confirmatory claims.

## Frozen scoring and interpretation

Apply ORIGINAL notebook minute-zero and point-in-time feature functions
on all eligible games. Strict 60*t < duration. No winner or duration
feature enters the model. Report all results regardless of direction.

Primary: minute-row-weighted log loss and Brier for M0, M1,
and paired M1-minus-M0. Draw 5,000 paired 95% group-bootstraps
(seed=20261115), group by positive series_id, otherwise match singleton,
preserving total minute opportunities. Also report equal-match-weighted
loss, observed Radiant win rate vs probability means, patch composition,
N games, N clusters, dates, all rejection reasons. Prespecified phase
scores: 0-9/10-19/20-29/30+ Brier and 10-bin ECE descriptive only.
Do not select/tune model or calibration based on forward results.

A future M1 promotion candidate would require LL advantage >=0.005,
paired grouped LL CI entirely favorable, and no material overall/30+
Brier regression. A 100-game cohort may still be underpowered;
NO deployment/promotion is authorized. This is forward post-TEST
stress testing, NOT pristine original model discovery or a live
network latency test. Archived March30-Apr2 200-game development
cohort is excluded from this fresh audit.

**Governance:** Keep original notebook and TEST files byte-identical;
research files stay on local BigLinux and private draft branch.
No public release, recruiter communication, private-repo sharing
or merge. If no data/network permission, document the limitation.
