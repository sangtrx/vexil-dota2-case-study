# INVALID P0 — WRONG GOLD x TIME FORMULA; DO NOT USE NUMBERS BELOW

This is the preserved invalid first execution from code commit 12c11b7. CLOCK arms used gold_k*minute10, but original M1 was fitted with gold_k*log1p(minute10). Values below are scientifically invalid; not a performance result and not eligible for gate advancement.

---

# Does a stale gold feed warrant holding the last forecast?

**Counterfactual offline TRAIN-only test. Not observed ingress latency.**

137 games; 5081 snapshots; 70 professional series/singletons.

## Proper scores vs fresh original M1

| Forecast stream | Log loss | ΔLL vs fresh | Brier | ΔBrier vs fresh | 30+ Brier |
| --- | ---: | ---: | ---: | ---: | ---: |
| FRESH | 0.612086 | +0.000000 | 0.212744 | +0.000000 | 0.183109 |
| CLOCK1 | 1.042949 | +0.430863 | 0.311370 | +0.098626 | 0.543522 |
| HOLD1 | 0.627745 | +0.015659 | 0.218889 | +0.006145 | 0.201058 |
| CLOCK3 | 0.963001 | +0.350916 | 0.299433 | +0.086689 | 0.485530 |
| HOLD3 | 0.654000 | +0.041914 | 0.229391 | +0.016647 | 0.230678 |

## HOLD vs current clock with delayed gold (negative = HOLD better)

| Lag | Δ LL HOLD−CLOCK | 95% series CI | Bonferroni 97.5% series CI | Δ Brier HOLD−CLOCK | 30+ Δ Brier |
| --- | ---: | --- | --- | ---: | ---: |
| 1 min | -0.415204 | [-0.577235,-0.271167] | [-0.608092,-0.254478] | -0.092481 | -0.342465 |
| 3 min | -0.309002 | [-0.461195,-0.174791] | [-0.490487,-0.160904] | -0.070042 | -0.254852 |

## All four forward TRAIN folds

| Fold | Games | Fresh LL | CLOCK1 LL | HOLD1 LL | CLOCK3 LL | HOLD3 LL |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 22 | 0.652097 | 0.844529 | 0.669054 | 0.780876 | 0.697289 |
| 2 | 44 | 0.621876 | 1.019052 | 0.636674 | 0.958513 | 0.660305 |
| 3 | 32 | 0.594860 | 1.203875 | 0.610170 | 1.087981 | 0.635801 |
| 4 | 39 | 0.594053 | 1.039300 | 0.610304 | 0.959055 | 0.639048 |

## Scientific decision

**Future independent mitigation gate:** PASSED for prospective evaluation only

The FRESH stream is a historical hypothetical oracle for unavailable current gold under an actual feed delay. CLOCK and HOLD are deterministic counterfactuals. This cannot measure the real frequency of delayed packets, UI latency, player utility, calibration under drift, or performance after missing events. Bootstrap CIs are descriptive on retrospectively reused TRAIN data and do not correct many prior screens.

Original submission, pre-scored VAL/TEST, reviewer package and applicant-owned hours/disclosure are unchanged.
