# Nested XGBoost/LightGBM sensitivity on TRAIN

**19 November correction:** The nested XGB84/LGB84 search used the old 81-feature Roshan parser and has not been rerun after that bug was fixed. Its scores are historical, not estimates for corrected inputs. XGB3/LGB3 did not use Roshan features. See [Roshan correction](ROSHAN_CORRECTION_20261119.md).

**Designed after the original four-candidate outer-fold failure; this is a post-result sensitivity test, not a fresh blind comparison.** Two series-group chronological inner folds select one of three fixed hyperparameter profiles per model family inside each original outer fit; no outer/eval label enters tuning.

March original TRAIN: 291 games / 10,675 minutes. Nested outer checks: 137 matches, 5,081 decisions, 70 professional groups, four existing outer folds.

| Family | Fixed config LL | Nested tuned LL | Tuned equal-game LL | Tuned Brier | Tuned late30 Brier | Fold choices |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| XGB3 | 0.615597 | 0.615597 | 0.592805 | 0.213477 | 0.187800 | conservative, conservative, conservative, conservative |
| XGB84 | 0.621809 | 0.621809 | 0.601351 | 0.216463 | 0.181491 | conservative, conservative, conservative, conservative |
| LGB3 | 0.616196 | 0.616196 | 0.593081 | 0.213476 | 0.187284 | conservative, conservative, conservative, conservative |
| LGB84 | 0.622936 | 0.622936 | 0.602626 | 0.217009 | 0.179798 | conservative, conservative, conservative, conservative |

## Strong frozen controls

| Control | Minute LL | Equal-game LL | Brier | Late30 Brier |
| --- | ---: | ---: | ---: | ---: |
| M1_interaction | 0.612086 | 0.587095 | 0.212744 | 0.183109 |
| Q1_path | 0.605963 | 0.582169 | 0.210050 | 0.175198 |
| M1_MATCH_EQUAL | 0.618253 | 0.591750 | 0.214388 | 0.185008 |

## Actual out-of-fold performance by outer fold

| Outer | Eval games | M1 LL | Q1 LL | XGB3 LL | XGB84 LL | LGB3 LL | LGB84 LL |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 22 | 0.652097 | 0.632260 | 0.647829 | 0.695751 | 0.656234 | 0.709633 |
| 2 | 44 | 0.621876 | 0.628250 | 0.624292 | 0.608595 | 0.624510 | 0.609073 |
| 3 | 32 | 0.594860 | 0.587963 | 0.605899 | 0.601790 | 0.606985 | 0.595919 |
| 4 | 39 | 0.594053 | 0.581592 | 0.596558 | 0.614386 | 0.592980 | 0.615396 |

## Whole-professional-series bootstrap comparisons (negative favors nested tree)

| Family | vs | Delta LL | 95% grouped CI | 99.375% 8-contrast CI | Brier delta | Late30 Brier delta | Forward fold wins |
| --- | --- | ---: | --- | --- | ---: | ---: | ---: |
| XGB3 | M1_interaction | +0.003511 | [-0.006206,+0.012072] | [-0.010256,+0.015628] | +0.000733 | +0.004691 | 1/4 |
| XGB3 | Q1_path | +0.009634 | [+0.002548,+0.017021] | [-0.000397,+0.020085] | +0.003427 | +0.012603 | 1/4 |
| XGB84 | M1_interaction | +0.009723 | [-0.006205,+0.026074] | [-0.012332,+0.031987] | +0.003719 | -0.001618 | 1/4 |
| XGB84 | Q1_path | +0.015846 | [-0.001467,+0.034202] | [-0.008161,+0.041590] | +0.006413 | +0.006293 | 1/4 |
| LGB3 | M1_interaction | +0.004110 | [-0.004982,+0.012145] | [-0.008513,+0.014861] | +0.000732 | +0.004174 | 1/4 |
| LGB3 | Q1_path | +0.010233 | [+0.003146,+0.018082] | [+0.000454,+0.020920] | +0.003426 | +0.012086 | 1/4 |
| LGB84 | M1_interaction | +0.010851 | [-0.007210,+0.029612] | [-0.013223,+0.036838] | +0.004265 | -0.003311 | 1/4 |
| LGB84 | Q1_path | +0.016974 | [-0.002140,+0.038237] | [-0.010587,+0.046750] | +0.006960 | +0.004601 | 1/4 |

## Research-only gate; never employer release

- XGB3: **FAILED**
- XGB84: **FAILED**
- LGB3: **FAILED**
- LGB84: **FAILED**

Nested tuning avoids consuming the same outer fold for parameter choice, but experiment design followed inspection of prior screens, and 70 outer groups are correlated by league/time; no familywise adjustment covers those prior searches. Bootstrap CIs are descriptive and real received_at is unavailable.
The original notebook and 3,836 TEST forecasts were unchanged. The report and ZIP were later rebuilt to disclose the correction. This reused-fold result does not justify replacing M1.
