# Hostile review: missing live snapshot at first minutes, and lag stress

**Hypothetical stale-gold counterfactual on an ALREADY SCORED 17-game Nov17 cohort.** Not a live latency measurement or independent candidate confirmation.

## Correctness repair: do not cheat at minute t < lag

The existing TRAIN-only stale-feed study used max(0,t-lag), supplying gold[0]/p[0] before it could have arrived. This research uses **NO_DATA => p=0.5** until t>=lag; after that CLOCK recomputes at known game clock t with only data through s=t-lag, while HOLD retains the forecast actually available from s. Old receipt kept intact.

NO_DATA rows: lag 0: 0, lag 1: 17, lag 3: 51.

| Model | Stream | Minute LL | Equal-match LL | Brier | 30+ Brier |
| --- | --- | ---: | ---: | ---: | ---: |
| M0_gold | FRESH | 0.429328 | 0.412187 | 0.138903 | 0.078605 |
| M0_gold | CLOCK1 | 0.445188 | 0.429146 | 0.144796 | 0.083714 |
| M0_gold | HOLD1 | 0.445188 | 0.429146 | 0.144796 | 0.083714 |
| M0_gold | CLOCK3 | 0.475389 | 0.461766 | 0.156260 | 0.094169 |
| M0_gold | HOLD3 | 0.475389 | 0.461766 | 0.156260 | 0.094169 |
| M1_interaction | FRESH | 0.423054 | 0.398011 | 0.134875 | 0.091816 |
| M1_interaction | CLOCK1 | 0.440946 | 0.417547 | 0.141458 | 0.097212 |
| M1_interaction | HOLD1 | 0.437919 | 0.414202 | 0.140561 | 0.096211 |
| M1_interaction | CLOCK3 | 0.474476 | 0.454615 | 0.154087 | 0.107610 |
| M1_interaction | HOLD3 | 0.465932 | 0.445148 | 0.151458 | 0.104537 |
| Q1_path | FRESH | 0.428489 | 0.406415 | 0.138521 | 0.089195 |
| Q1_path | CLOCK1 | 0.443656 | 0.422669 | 0.144131 | 0.094268 |
| Q1_path | HOLD1 | 0.444033 | 0.423151 | 0.144293 | 0.094261 |
| Q1_path | CLOCK3 | 0.471213 | 0.453016 | 0.154467 | 0.101848 |
| Q1_path | HOLD3 | 0.472312 | 0.454435 | 0.154941 | 0.101825 |
| MATCH_EQUAL | FRESH | 0.415423 | 0.389317 | 0.133069 | 0.090024 |
| MATCH_EQUAL | CLOCK1 | 0.433393 | 0.408936 | 0.139592 | 0.095272 |
| MATCH_EQUAL | HOLD1 | 0.430456 | 0.405683 | 0.138776 | 0.094329 |
| MATCH_EQUAL | CLOCK3 | 0.467240 | 0.446357 | 0.152137 | 0.105442 |
| MATCH_EQUAL | HOLD3 | 0.458900 | 0.437090 | 0.149732 | 0.102587 |

## Post-result paired contrasts: MATCH_EQUAL minus control (negative is better)

| Policy | vs | Equal-match LL delta | 95% series CI | 98.75% series CI | Minute LL delta | 30+ Brier delta |
| --- | --- | ---: | --- | --- | ---: | ---: |
| FRESH | M1_interaction | -0.008695 | [-0.011740,-0.005220] | [-0.012326,-0.004113] | -0.007631 | -0.001792 |
| FRESH | Q1_path | -0.017099 | [-0.032593,-0.002325] | [-0.036681,+0.002497] | -0.013066 | +0.000829 |
| CLOCK1 | M1_interaction | -0.008610 | [-0.011634,-0.005157] | [-0.012237,-0.004076] | -0.007553 | -0.001940 |
| CLOCK1 | Q1_path | -0.013732 | [-0.027871,-0.000433] | [-0.031820,+0.003715] | -0.010263 | +0.001004 |
| HOLD1 | M1_interaction | -0.008519 | [-0.011576,-0.005051] | [-0.012185,-0.003976] | -0.007463 | -0.001882 |
| HOLD1 | Q1_path | -0.017468 | [-0.032669,-0.003118] | [-0.036778,+0.001585] | -0.013577 | +0.000068 |
| CLOCK3 | M1_interaction | -0.008258 | [-0.011242,-0.004884] | [-0.011801,-0.003866] | -0.007236 | -0.002168 |
| CLOCK3 | Q1_path | -0.006659 | [-0.017224,+0.003413] | [-0.020089,+0.006675] | -0.003973 | +0.003594 |
| HOLD3 | M1_interaction | -0.008058 | [-0.011134,-0.004623] | [-0.011735,-0.003649] | -0.007032 | -0.001950 |
| HOLD3 | Q1_path | -0.017346 | [-0.030895,-0.004455] | [-0.034218,+0.000151] | -0.013412 | +0.000763 |

## Model regret relative to its own fresh forecasts

| Model | Delayed stream | LL increase (negative improves) | Late30 Brier change |
| --- | --- | ---: | ---: |
| M0_gold | CLOCK1 | +0.015860 | +0.005110 |
| M0_gold | HOLD1 | +0.015860 | +0.005110 |
| M0_gold | CLOCK3 | +0.046061 | +0.015564 |
| M0_gold | HOLD3 | +0.046061 | +0.015564 |
| M1_interaction | CLOCK1 | +0.017891 | +0.005396 |
| M1_interaction | HOLD1 | +0.014865 | +0.004395 |
| M1_interaction | CLOCK3 | +0.051421 | +0.015794 |
| M1_interaction | HOLD3 | +0.042878 | +0.012721 |
| Q1_path | CLOCK1 | +0.015168 | +0.005073 |
| Q1_path | HOLD1 | +0.015544 | +0.005066 |
| Q1_path | CLOCK3 | +0.042724 | +0.012653 |
| Q1_path | HOLD3 | +0.043824 | +0.012630 |
| MATCH_EQUAL | CLOCK1 | +0.017970 | +0.005248 |
| MATCH_EQUAL | HOLD1 | +0.015033 | +0.004305 |
| MATCH_EQUAL | CLOCK3 | +0.051817 | +0.015418 |
| MATCH_EQUAL | HOLD3 | +0.043477 | +0.012564 |

## Deliberately impossible future-data sentinel — never use

One-minute **future** MATCH_EQUAL economic lead on 694 nonterminal rows changed log loss vs proper fresh predictor by **-0.018495**. This is a leakage sensitivity diagnostic, not a valid prediction technique or live advantage.

## Hostile decision

- Previous frozen research superiority gate remains **FAIL**, regardless of simulated delay. This cohort has 17 games/10 independent clusters, less than 30/15 required.
- All four March-trained models fixed; no new winner selection or model refit on Nov17.
- The original 137-game delayed-gold study's early-minute availability assumption was not valid; preserve prior receipt but avoid using it to assert real live performance.
- Historical raw replay arrays are internally aligned; no independently observed received_at or serving-feed net-worth/earned-gold parity. Real-time GO is blocked.
- This cohort's labels have already been used in previous model research. All new CIs are descriptive and do NOT adjust for previous model searching.
- Original applicant report, notebook, TEST predictions, ZIP and draft PR unchanged.
