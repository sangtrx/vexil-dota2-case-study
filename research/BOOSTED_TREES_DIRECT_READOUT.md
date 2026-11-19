# Direct fixed XGBoost vs LightGBM on March TRAIN-only forward folds

**Editorial correction (19 November 2026):** This is a historical result, calculated before a bug in the 81-feature Roshan parser was discovered. Roshan events had valid `team` values but the old parser tried `player_slot`, making two Roshan fields zero. These scores describe the old matrix only. The corrected fixed-model TRAIN-forward rerun is in [Roshan correction](ROSHAN_CORRECTION_20261119.md); this nested sensitivity was not rerun. No model was promoted.


**Post-selection exploratory model family test. Original March TEST and VAL are not accessed. No new blinded evidence or real-live receipt timestamps.**

Data: 291 TRAIN games / 10,675 minute rows; four mature-label chronological series-disjoint evaluation blocks, 137 games, 5,081 rows and 70 groups.

Versions: XGBoost 3.4.1, LightGBM 4.7.0, Narwhals 2.21.2, sklearn 1.7.2. All trees exactly 90 rounds with conservative fixed leaf constraints.

| Model | Inputs | Minute LL | Equal-game LL | Brier | Late30 Brier | Early9 Brier | ECE10 (descriptive) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| M0_gold | 1 | 0.612312 | 0.588718 | 0.211828 | 0.184996 | 0.243782 | 0.059329 |
| A_additive | 2 | 0.614106 | 0.590046 | 0.212339 | 0.186424 | 0.244744 | 0.061253 |
| M1_interaction | 3 | 0.612086 | 0.587095 | 0.212744 | 0.183109 | 0.243109 | 0.062059 |
| Q1_path | 5 | 0.605963 | 0.582169 | 0.210050 | 0.175198 | 0.245576 | 0.056530 |
| Q3_tree | 84 | 0.621266 | 0.601972 | 0.216617 | 0.180666 | 0.248868 | 0.071567 |
| M1_MATCH_EQUAL | 3 | 0.618253 | 0.591750 | 0.214388 | 0.185008 | 0.243538 | 0.070913 |
| XGB3 | 3 | 0.615597 | 0.592805 | 0.213477 | 0.187800 | 0.241926 | 0.058834 |
| XGB84 | 84 | 0.621809 | 0.601351 | 0.216463 | 0.181491 | 0.246827 | 0.069125 |
| LGB3 | 3 | 0.616196 | 0.593081 | 0.213476 | 0.187284 | 0.242418 | 0.060609 |
| LGB84 | 84 | 0.622936 | 0.602626 | 0.217009 | 0.179798 | 0.249071 | 0.077912 |

## All four frozen forward folds

| Fold | Eval games | Fit completed games | M1 LL | Q1 LL | MATCH_EQUAL LL | Q3 sklearn LL | XGB3 LL | XGB84 LL | LGB3 LL | LGB84 LL |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 22 | 154 | 0.652097 | 0.632260 | 0.663361 | 0.695345 | 0.647829 | 0.695751 | 0.656234 | 0.709633 |
| 2 | 44 | 176 | 0.621876 | 0.628250 | 0.628993 | 0.600752 | 0.624292 | 0.608595 | 0.624510 | 0.609073 |
| 3 | 32 | 218 | 0.594860 | 0.587963 | 0.598405 | 0.600793 | 0.605899 | 0.601790 | 0.606985 | 0.595919 |
| 4 | 39 | 252 | 0.594053 | 0.581592 | 0.598634 | 0.622559 | 0.596558 | 0.614386 | 0.592980 | 0.615396 |

## Paired whole-series uncertainty (negative delta favors boosted model)

| Boosted | vs control | Minute LL delta | 95% cluster CI | 99.375% screen-local CI | Brier delta | 30+ Brier delta | Winning folds |
| --- | --- | ---: | --- | --- | ---: | ---: | ---: |
| XGB3 | M1_interaction | +0.003511 | [-0.006206,+0.012072] | [-0.010256,+0.015628] | +0.000733 | +0.004691 | 1/4 |
| XGB3 | Q1_path | +0.009634 | [+0.002548,+0.017021] | [-0.000397,+0.020085] | +0.003427 | +0.012603 | 1/4 |
| XGB84 | M1_interaction | +0.009723 | [-0.006205,+0.026074] | [-0.012332,+0.031987] | +0.003719 | -0.001618 | 1/4 |
| XGB84 | Q1_path | +0.015846 | [-0.001467,+0.034202] | [-0.008161,+0.041590] | +0.006413 | +0.006293 | 1/4 |
| LGB3 | M1_interaction | +0.004110 | [-0.004982,+0.012145] | [-0.008513,+0.014861] | +0.000732 | +0.004174 | 1/4 |
| LGB3 | Q1_path | +0.010233 | [+0.003146,+0.018082] | [+0.000454,+0.020920] | +0.003426 | +0.012086 | 1/4 |
| LGB84 | M1_interaction | +0.010851 | [-0.007210,+0.029612] | [-0.013223,+0.036838] | +0.004265 | -0.003311 | 1/4 |
| LGB84 | Q1_path | +0.016974 | [-0.002140,+0.038237] | [-0.010587,+0.046750] | +0.006960 | +0.004601 | 1/4 |

## Frozen research-only decision gate

- XGB3: **FAIL / NO-GO**
- XGB84: **FAIL / NO-GO**
- LGB3: **FAIL / NO-GO**
- LGB84: **FAIL / NO-GO**

Each simultaneous interval only corrects eight comparisons within THIS screen; earlier many candidate searches and viewed March VALIDATION/TEST, Oct/Nov labels make all winner claims exploratory. 70 series are the meaningful independent units, not 5,081 IID observations. No source receive_at means no actual real-time PIT proof.
The apparent feature importances and ECE are descriptive; no automated post-TEST calibration or tuned model selection.
At the time of this historical experiment, the notebook and 3,836 TEST forecasts were unchanged. The report and reviewer ZIP were later rebuilt to disclose the parser correction.
