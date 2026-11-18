# Frozen MATCH_EQUAL on fresh Nov17 professional games

**Retrospective after model selection on older inspected datasets.** New Nov17 source was discovered and selected after precommitted protocol/model hash, outcomes not used for inclusion. Not a live packet/arrival-time study.

Games: **17/17**; minute rows 711; independent series+singletons 10; leagues 4.

| Frozen March model | Minute LL | Equal-match LL | Brier | Brier >=30 |
| --- | ---: | ---: | ---: | ---: |
| M0_gold | 0.429328 | 0.412187 | 0.138903 | 0.078605 |
| M1_interaction | 0.423054 | 0.398011 | 0.134875 | 0.091816 |
| Q1_path | 0.428489 | 0.406415 | 0.138521 | 0.089195 |
| MATCH_EQUAL | 0.415423 | 0.389317 | 0.133069 | 0.090024 |

## Paired MATCH_EQUAL contrasts (negative is better)

| Comparator | Equal-game LL delta | 95% series CI | 98.75% series CI | Minute LL delta | 95% series CI | Brier delta | 30+ Brier delta |
| --- | ---: | --- | --- | ---: | --- | ---: | ---: |
| M1_interaction | -0.008695 | [-0.011740,-0.005220] | [-0.012326,-0.004113] | -0.007631 | [-0.011781,-0.003244] | -0.001806 | -0.001792 |
| Q1_path | -0.017099 | [-0.032593,-0.002325] | [-0.036681,+0.002497] | -0.013066 | [-0.034321,+0.005183] | -0.005452 | +0.000829 |

Research gate sufficiently populated: **False**.
Frozen research superiority gate passed: **False**.

No re-fit on November, no original March TEST read. Match outcome labels were not used in the listing selection or source validity filter.
Actual source received_at remains unavailable; source parser's game clock cannot certify live PIT availability.
The original employer notebook, original 3,836-forecast TEST, report/PDF and submission ZIP were not modified. Do not promote this to employer release.
