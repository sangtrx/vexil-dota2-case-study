# Vexil Dota 2 — Adversarial and Operational Review

**13 November 2026 | Independent research branch, stacked on submission PR #8**

## Decision

**Do not change selected M1 or promote P20.** The strongest contribution
is a measurable correctness contract, two invalid-payload repairs, and
a quantified lack of stable model lift. The original 106-match held-out
evaluation remains frozen.

## Executed red-team cases

The deterministic adversarial QA suite uses seed 20261113, the original
**291 TRAIN matches** and synthetic/fake data. It does not query
OpenDota or score the original validation/test outcomes.

| Family | Actual cases | Purpose |
|---|---:|---|
| Real historical prefix consistency | 2,813 | Raw parsed features equal truncated-to-minute features |
| Future poison invariance | 1,050 | Future winner/gold/XP/objectives/kills/purchases cannot change current features |
| Event clock boundary oracle | 2,700 | Exact 60*t inclusion, +1 second exclusion, both sides and all key events |
| Invalid clock/data handling | 1,980 | NaN, +/-Inf, booleans, null, string, malformed structures and fallback |
| M1 in-horizon gold monotonic comparisons | 3,000 | A larger gold lead should not lower M1 win probability at fixed minute |
| Outside-training-horizon warnings | 45 | Quantify negative gold slope when extrapolated |
| Fault-injected API requests | 225 | 429/503 backoff; 401/403/404 fail-closed; bounded transport failures |
| Paired grouped bootstrap arithmetic | 250 | Exact proper score identities, paired resamples, bounds |
| **Total** | **12,063** | **PASS** on isolated research branch |

The original seed 20261113 and a second independent RNG stream
seed 20261114 each completed **12,063/12,063 cases PASS**:
**24,126 total case evaluations**, with identical family counts.
These are deterministic case assertions, **not** 24,126 independent
professional games or OOS outcomes. HTTP faults use mocks, not
a real saturated OpenDota server. The source is versioned in
research/adversarial_cases.py and research/reseed_adversarial_cases.py,
with one receipt per random stream.

## Two private Kaggle QA kernels: both COMPLETE

The 12,063-case red-team kernel and the second exhaustive 10,683-minute
TRAIN-only PIT kernel have both completed on private Kaggle CPU with
Internet OFF. Downloaded cloud receipts confirm **22,746 QA-case
executions**, 0 actual API calls and 0 original validation/test labels
scored. Both source notebooks were pulled back from Kaggle and verified
against committed source, including private execution metadata.

- [Adversarial 12,063](https://www.kaggle.com/code/sangtruong/vexil-binary-train-redteam-qa-20261113):
  8/8 family totals and all observations match local exactly.
- [Every TRAIN minute](https://www.kaggle.com/code/sangtruong/vexil-binary-train-fullpit-qa-20261113):
  all 10,683 historical cutoffs and both feature families passed.

The original archive upload was auto-extracted by Kaggle, so the first
kernel pair failed before QA. A second binary private dataset fixed the
mount problem, with SHA-256 verified before extraction. Both final
success receipts are committed under research/results/hosted_kaggle_*.
These are reproducibility checks on previously inspected train games,
not 22,746 independent outcome samples or a new model edge.

## Concrete defects and isolated fixes

1. **Nonfinite objective event time:** float NaN passed numeric-type
   validation but the expression (NaN > cutoff) is false, causing
   an invalid event to be counted at an earlier minute.
   A real prefix-truncation test found raw and truncated features
   disagreed. The research branch now demands a finite numeric
   event time and rejects boolean timestamps.
2. **Duplicate player slots:** the player kill counter had required
   five Radiant and five Dire player objects but had not rejected
   duplicate player-slot identities, allowing invalid double-counting.
   The research branch now requires the exact ten canonical slots.
3. **Malformed gold/XP observation:** True previously passed a
   Python integer check (bool subclasses int). Boolean, NaN and
   infinite numeric readings are now rejected, with last valid
   earlier value used when available.
4. These were detected on **synthetic corrupt inputs**. They
   are not claimed to have occurred in the original 500 games.

After the timestamp fixes, the full cached 500-match notebook ran
from top to bottom and **all eight exported tables matched the prior
scientific output**, including 3,837 identical held-out probabilities.
The duplicate-slot fix is covered by separate regression tests and
is subject to the same final full replay before release.

## Five embargoed rolling-origin TRAIN-only evaluations

The test protocol was committed before outcomes were examined.
Initial percent cutoffs produced a two-game evaluation block; this
was rejected **before scoring** and the outcome-blind correction was
documented. All five windows use earlier completed train matches
and keep series whole.

| Fold | Later games | M1 - M0 log loss | P20 - M1 log loss |
|---|---:|---:|---:|
| 1 | 22 | +0.006050 | +0.031323 |
| 2 | 44 | -0.011972 | -0.001252 |
| 3 | 27 | +0.000963 | +0.005240 |
| 4 | 22 | +0.021027 | +0.007339 |
| 5 | 22 | -0.003429 | -0.002752 |

**Negative favors the first model.** Under minute-weighted loss,
M1 was better than M0 only **2/5** times; P20 was better than M1
only **2/5** times. Under equal-match weighting, M1 was better
**3/5**, P20 **1/5**. There is no prospective or independent
model confirmation from these reused development labels.

## Operational latency and extrapolation

The existing M1 path from parsed snapshot to one-row Pandas dataframe
to imputer/scaler/logistic prediction took **p50 1.74 ms**,
**p95 2.09 ms**, **p99 2.47 ms** over 1,200 warm
in-memory BigLinux CPU calls. This excludes all external API,
queue, IPC, network, persisted state, UI, restart, and concurrency
latency. This is NOT a live endpoint SLA.

The derivative of fitted M1 log-odds in thousands of Radiant gold is

\[
\frac{\partial \operatorname{logit}p}{\partial \mathrm{gold}_k}
= 0.4779636485 - 0.2005838119 \log(1+t/10).
\]

It stays positive across original training minutes 0-85 but crosses
zero around minute **98.36**; at minute **99** it predicts a
lower win probability for a *larger* gold lead. This is
outside all training-time support, not a real-match performance result.
A separate guard refuses silent out-of-support predictions.

Original train population by minute: minute 0 **291 games**,
minute 30 **214**, minute 50 **27**, minute 60 **5**,
minute 70 **2**, minute 85 **1**. Even a positive
gold slope with just one supporting game is not calibrated.
Production systems need explicit age/coverage status and a
documented abstain or baseline fallback policy.

## Verdict and limitations

**GO for isolated research QA, HOLD for automatic change to PR #8**.
This is correctness and reliability evidence, not evidence of
trading PnL, a causal item effect, OOS model superiority, or a
true live inference feed.

An independent Claude Sonnet review was attempted but timed out
without a verdict; that attempt is not represented as a completed
external sign-off. Full source and receipts accompany this branch.
