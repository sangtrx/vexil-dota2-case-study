# What the fixed reliability curve can and cannot establish

**Descriptive TEST diagnostic, prepared 16 November 2026 after the original
TEST was opened. No probabilities were fitted, recalibrated or reselected.**

The notebook reports a fixed 10-bin calibration curve for both M0 and
M1. The original displayed counts are **forecast-minute rows**, not
3,836 independent winners: the same 106 outcomes reappear across
minutes, and those games form 54 positive-series or singleton clusters.
To make uncertainty more visible, this extra audit repeats the
**same prespecified 0.0–1.0 ten-bin partition** and resamples whole
professional series/singletons (5,000 seeded draws). Within each
sample it recalculates the bin's empirical win fraction and the
observed-minus-predicted gap, discarding resamples in which that
fixed bin contains no data.

For comparison, fixed M1 TEST 10-bin ECE is **0.0750** versus
M0 **0.0895**. These are **descriptive row-weighted ECE values**
from the original, already-opened TEST. M1 does not have a confirmed
population-level calibration advantage over M0.

## M1's high-confidence bins in the original 106-game TEST

| Forecast interval | Minute forecasts | Groups represented | Mean forecast | Observed win fraction | Winner minus forecast | 95% grouped CI for gap |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| 0.5–0.6 | 787 | 53 | 0.540 | 0.653 | +0.113 | [−0.009,+0.230] |
| 0.7–0.8 | 363 | 47 | 0.748 | 0.882 | +0.134 | [+0.049,+0.197] |
| 0.8–0.9 | 349 | 41 | 0.849 | 0.966 | +0.117 | [+0.061,+0.151] |
| 0.9–1.0 | 322 | 36 | 0.948 | 1.000 | +0.052 | [+0.047,+0.059] |

**Reading:** In this particular inspected TEST cohort, high-probability
minute forecasts tended to underpredict Radiant winners. Some
series-bootstrap intervals for individual bins are positive, but
**these are ten post-hoc, unadjusted bin checks** with repeated
minute outcomes. In M1's **0.9–1.0** bin, all **322/322 minute rows** are
Radiant-winning. Every nonempty grouped bootstrap resample therefore
also has an empirical winner fraction of **1.0**; its apparent
0.047–0.059 interval for observed-minus-predicted gap reflects only
variation in the **average forecast** under those already-all-winning
groups. It **does not** measure uncertainty about a future 90%-confident
forecast's true win rate. This is a potentially degenerate,
selection-conditioned interval, not a calibration guarantee.

Leagues and teams are correlated *across*
series; resampling 54 series does not repair that dependence
or validate calibration in the future. There is no new data,
no fitted TEST calibration layer, and no guarantee these intervals
have correct population coverage under drift.

All twenty original bin rows (M0/M1), raw counts,
mean predictions, empirical outcomes, conditional bootstrap coverage
and 95% observed-rate/gap intervals are stored in
[the exact frozen machine receipt](CALIBRATION_FIXED_BIN_GROUPED_CI_RECEIPT.json).

To reproduce offline from the ZIP:

    python research/cluster_reliability_bands.py

The original notebook calibration curves remain untouched.
An already-opened TEST is not an independent target on which to tune
probabilities or assert successful calibration. The correct Senior decision
remains **M0 reference, M1 shadow-only**, with a new unopened
series/league-diverse calibration gate required before deployment.
