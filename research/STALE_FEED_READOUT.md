# Does a stale gold feed warrant holding the last forecast?

**Counterfactual offline TRAIN-only test. Not observed ingress latency.**

137 games; 5081 snapshots; 70 professional series/singletons.

## Proper scores vs fresh original M1

| Forecast stream | Log loss | ΔLL vs fresh | Brier | ΔBrier vs fresh | 30+ Brier |
| --- | ---: | ---: | ---: | ---: | ---: |
| FRESH | 0.612086 | +0.000000 | 0.212744 | +0.000000 | 0.183109 |
| CLOCK1 | 0.626112 | +0.014026 | 0.218444 | +0.005700 | 0.200558 |
| HOLD1 | 0.627745 | +0.015659 | 0.218889 | +0.006145 | 0.201058 |
| CLOCK3 | 0.648923 | +0.036837 | 0.228006 | +0.015262 | 0.228156 |
| HOLD3 | 0.654000 | +0.041914 | 0.229391 | +0.016647 | 0.230678 |

## HOLD vs current clock with delayed gold (negative = HOLD better)

| Lag | Δ LL HOLD−CLOCK | 95% series CI | Bonferroni 97.5% series CI | Δ Brier HOLD−CLOCK | 30+ Δ Brier |
| --- | ---: | --- | --- | ---: | ---: |
| 1 min | +0.001633 | [+0.000181,+0.003218] | [-0.000106,+0.003529] | +0.000445 | +0.000500 |
| 3 min | +0.005077 | [+0.000880,+0.009681] | [+0.000060,+0.010441] | +0.001386 | +0.002522 |

## All four forward TRAIN folds

| Fold | Games | Fresh LL | CLOCK1 LL | HOLD1 LL | CLOCK3 LL | HOLD3 LL |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 22 | 0.652097 | 0.665938 | 0.669054 | 0.687783 | 0.697289 |
| 2 | 44 | 0.621876 | 0.634513 | 0.636674 | 0.653985 | 0.660305 |
| 3 | 32 | 0.594860 | 0.609758 | 0.610170 | 0.634070 | 0.635801 |
| 4 | 39 | 0.594053 | 0.609032 | 0.610304 | 0.634917 | 0.639048 |

## Scientific decision

**Future independent mitigation gate:** REJECTED (no promotion)

The FRESH stream is a historical hypothetical oracle for unavailable current gold under an actual feed delay. CLOCK and HOLD are deterministic counterfactuals. This cannot measure the real frequency of delayed packets, UI latency, player utility, calibration under drift, or performance after missing events. Bootstrap CIs are descriptive on retrospectively reused TRAIN data and do not correct many prior screens.

Original submission, pre-scored VAL/TEST, reviewer package and applicant-owned hours/disclosure are unchanged.
