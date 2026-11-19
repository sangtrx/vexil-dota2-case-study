# Rich feature lab: 81 as-of Dota 2 state features

**Editorial correction (19 November 2026):** This is a historical result, calculated before a bug in the 81-feature Roshan parser was discovered. Roshan events had valid `team` values but the old parser tried `player_slot`, making two Roshan fields zero. These scores describe the old matrix only. The corrected fixed-model TRAIN-forward rerun is in [Roshan correction](ROSHAN_CORRECTION_20261119.md); this nested sensitivity was not rerun. No model was promoted.


**Scope:** Post-result TRAIN-only exploration. Already-viewed original TEST and VALIDATION results never enter this evaluation. The predeclared two-model correction does NOT correct the previous 28+ research-model screens.

291 TRAIN games supplied 10,675 minute snapshots; the frozen forward evaluation uses 137 games, 5,081 rows and 70 professional series/singleton groups.

## Implemented feature families

| Family | Columns |
| --- | ---: |
| gold | 19 |
| interactions | 13 |
| objectives | 17 |
| players | 19 |
| xp | 13 |

Two fixed 84-input candidates: Q2 elastic-net logistic and Q3 shallow gradient-boosted trees. Baselines M0, additive, original M1 and earlier Q1 are re-fitted without tuning.

## Out-of-fold (historical TRAIN) score comparisons

Negative Q-minus-baseline score means candidate wins. All intervals are paired bootstrap over 70 professional series/singletons; 97.5% interval is a narrowly two-candidate Bonferroni adjustment only.

| Candidate | Baseline | LL delta | LL 95% CI | LL 97.5% CI | Brier delta | 30+ Brier delta | Winning folds |
| --- | --- | ---: | --- | --- | ---: | ---: | ---: |
| Q2_sparse | M0_gold | +0.017084 | [-0.007808,+0.042078] | [-0.010682,+0.045731] | +0.002327 | -0.011465 | 1/4 |
| Q2_sparse | A_additive | +0.015291 | [-0.009404,+0.040347] | [-0.012428,+0.044020] | +0.001816 | -0.012893 | 1/4 |
| Q2_sparse | M1_interaction | +0.017311 | [-0.009647,+0.048034] | [-0.012718,+0.052999] | +0.001411 | -0.009578 | 1/4 |
| Q2_sparse | Q1_path | +0.023434 | [-0.003797,+0.051966] | [-0.006889,+0.056426] | +0.004105 | -0.001666 | 1/4 |
| Q3_tree | M0_gold | +0.008954 | [-0.014586,+0.032050] | [-0.017643,+0.035443] | +0.004789 | -0.004330 | 1/4 |
| Q3_tree | A_additive | +0.007160 | [-0.017293,+0.030917] | [-0.020763,+0.034755] | +0.004279 | -0.005758 | 1/4 |
| Q3_tree | M1_interaction | +0.009180 | [-0.010909,+0.029947] | [-0.013371,+0.033022] | +0.003873 | -0.002443 | 1/4 |
| Q3_tree | Q1_path | +0.015303 | [-0.006085,+0.037147] | [-0.008717,+0.040777] | +0.006568 | +0.005469 | 1/4 |

## Every forward block (not cherry-picked)

| Fold | Games | Q2 LL | Q3 LL | M1 LL | Q1 LL | Q2 active / 84 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 22 | 0.704889 | 0.695345 | 0.652097 | 0.632260 | 40 |
| 2 | 44 | 0.667336 | 0.600752 | 0.621876 | 0.628250 | 40 |
| 3 | 32 | 0.559642 | 0.600793 | 0.594860 | 0.587963 | 44 |
| 4 | 39 | 0.604897 | 0.622559 | 0.594053 | 0.581592 | 47 |

## Locked outcome

| Model | Future-candidate gate | Largest favorable group / total M1 LL gain |
| --- | --- | ---: |
| Q2_sparse | FAILED | n/a |
| Q3_tree | FAILED | n/a |

Important: model feature importance is diagnostic only. Correlated engineered signals are not evidence of causal influence. The real-time feed receipt timestamp is unknown; a historical replay cannot establish true received-at time.

At the time of this historical experiment, the original notebook and TEST forecasts were unchanged. The report and reviewer ZIP were subsequently rebuilt to document the Roshan correction.
