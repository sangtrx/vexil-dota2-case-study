# Vexil win-probability: M1 shadow-mode operating contract

Validated on 13 November 2026. This model card covers the previously
selected model M1 (gold lead x game time), not a newly tuned candidate.

## 1. Business question and output

At game minute t, return P(Radiant ultimately wins) conditional on
the parsed match-clock state available at t. The prediction is
a **probability forecast**, not a bet or PnL forecast. No market odds,
fills, live trade decisions, order book, costs or slippage are observed.

Production-style prediction record:
- match_id, minute, feature schema/version and model version.
- p_radiant_win in [0, 1] when the input is supported.
- source timestamp semantics and any missing/truncated arrays.
- explicit error/status when gold input is absent or time is outside
  the fitted domain. Never fabricate the value.

## 2. Lightweight serving contract

Read-only snapshot extraction and scikit-learn preprocessing/logistic
prediction run on CPU. Measured with 1,200 warmed calls on the authorized
BigLinux host, including one raw snapshot extraction and DataFrame
construction, **excluding all network, parsing download, HTTP and
startup overhead**:

- p50 1.739 ms; p95 2.093 ms; p99 2.467 ms; max 2.854 ms.
- 297 single-snapshot forecasts matched the fitted batch pipeline
  within 1e-13; 180 future/outcome-poison tests also matched.
- No OpenDota HTTP requests were made in this benchmark.

These are measurements in one local environment, not a service SLA.
The model is so small that inference CPU is not the bottleneck;
source arrival, freshness and access remain the real operational risks.

## 3. Gold direction and out-of-support

The conditional derivative of M1 log-odds wrt +1,000 Radiant gold is:

    0.4779636485 - 0.2005838119 * log(1 + t/10)

It is positive for all observed TRAIN minutes 0-85; analytically
crosses zero at about minute 98.36. At 99+ min, blindly extrapolating
M1 could reverse the intuitive gold-direction relationship. This is
a **model-domain limitation**, not a bug found in observed training
predictions. A reference guarded function returns
OUTSIDE_TRAIN_TIME_SUPPORT with no probability beyond minute 85.
Any baseline fallback must be explicitly tested before release.
Original take-home held-out model scores and forecasts were not
changed by adding this research guardrail.

## 4. Strict point-in-time and source lineage

OpenDota retrospective match-clock arrays and event logs do NOT prove
historical live data arrival. A live integration would require a real
as-received event-time source contract. Never use outcome, duration,
end-of-match totals or future purchase events as live features.
Timestamped item counts are historical purchases, not possession.

The 10,683 original TRAIN minute rows had no missing primary feature
value. A canonical, sorted, eight-decimal SHA-256 fingerprint of
actual model inputs is saved as a separate receipt. This allows
re-parsed OpenDota JSON to be compared by *model-relevant feature
semantics* rather than by irrelevant auxiliary JSON fields. The
original frozen manifest and output hashes remain additional checks.
This feature-fingerprint mechanism has only been run on local
TRAIN data so far; it has not yet been executed in hosted Kaggle.

## 5. Statistical release criteria

The original 106-game held-out all-minute log-loss difference M1−M0
was negative at point estimate but its 95% match-bootstrap CI
crossed zero. Five additional embargoed rolling-origin folds
using only the original 291 TRAIN games found M1 better than M0 in
2/5 minute-weighted folds and 3/5 equal-match folds.
P20 purchase-time features did not consistently improve M1.

These are descriptive reused-development-label diagnostics,
not a new independent test. Keep M0 as a production reference
and M1 as shadow-only until a later fully frozen, non-overlapping
series cohort replicates log-loss, Brier and calibration gains.
No advantage on an unobserved betting market is claimed.

Monitor: source latency/completeness, model-payload hashes, probability
validity, p50/p95/p99 of local inference *separate from network
latency*, calibration by phase and patch, weighted proper scores,
and drift in match/series composition.
