# Causal live-forecast filter: TRAIN-only locked evaluation

**Status:** post-result exploratory, no applicant submission change. Only the original TRAIN cohort was used.

## Forecast safeguard (delta minus existing M1, positive = worse)

| Policy | Delta LL | Two-policy adj. 97.5% interval | Delta Brier | Late30 Brier delta | LL within +.002 folds |
| --- | ---: | --- | ---: | ---: | ---: |
| S1_fixed | +0.003703 | [+0.002767, +0.004663] | +0.001688 | +0.006874 | 0/4 |
| S2_event_reset | +0.000308 | [-0.000215, +0.000865] | +0.000135 | -0.000049 | 4/4 |

## Live-output operational proxy, not demonstrated user benefit

137 games, 4944 intra-game revisions, 3269 observable-event resets (S2).

| Stream | Mean abs revision | >5pp revision count | Total variation / game |
| --- | ---: | ---: | ---: |
| M1_interaction | 0.044975 | 1675 | 1.62302 |
| S1_fixed | 0.033787 | 1127 | 1.21928 |
| S2_event_reset | 0.042432 | 1526 | 1.53128 |

## Fold-by-fold LL (all blocks)

| Fold | Games | M0 | M1 | Q1 | S1 | S2 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 22 | 0.646066 | 0.652097 | 0.632260 | 0.655617 | 0.652699 |
| 2 | 44 | 0.633853 | 0.621876 | 0.628250 | 0.625045 | 0.621754 |
| 3 | 32 | 0.588280 | 0.594860 | 0.587963 | 0.598323 | 0.595741 |
| 4 | 39 | 0.589960 | 0.594053 | 0.581592 | 0.598675 | 0.594209 |

## Rivals and decision

| Policy | Vs M0 LL | Vs Q1 LL | Revision decline | >5pp count decline | Gate |
| --- | ---: | ---: | ---: | ---: | --- |
| S1_fixed | +0.003476 | +0.009826 | 24.9% | 32.7% | REJECT |
| S2_event_reset | +0.000082 | +0.006431 | 5.7% | 8.9% | REJECT |

No policy is promoted to the Vexil employer notebook or private reviewer ZIP. A stable-looking forecast can still be statistically worse; series-cluster intervals are descriptive for the retrospectively reused TRAIN cohort. Signed event-net counts omit cancelling same-minute fights; actual received-at timestamps remain unavailable. Neither policy is certified live-safe.
