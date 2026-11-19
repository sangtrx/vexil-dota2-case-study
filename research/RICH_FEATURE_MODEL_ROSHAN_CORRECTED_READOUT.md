# Rich feature lab: 81 as-of Dota 2 state features

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
| Q2_sparse | M0_gold | +0.017506 | [-0.007438,+0.042524] | [-0.009999,+0.046596] | +0.002905 | -0.009138 | 1/4 |
| Q2_sparse | A_additive | +0.015713 | [-0.008655,+0.040550] | [-0.011952,+0.044136] | +0.002395 | -0.010566 | 1/4 |
| Q2_sparse | M1_interaction | +0.017733 | [-0.009202,+0.047748] | [-0.012136,+0.053563] | +0.001990 | -0.007252 | 1/4 |
| Q2_sparse | Q1_path | +0.023856 | [-0.002790,+0.052481] | [-0.006253,+0.056789] | +0.004684 | +0.000660 | 1/4 |
| Q3_tree | M0_gold | +0.009902 | [-0.013612,+0.033010] | [-0.016875,+0.036293] | +0.005160 | -0.003014 | 1/4 |
| Q3_tree | A_additive | +0.008109 | [-0.016484,+0.031780] | [-0.019679,+0.035578] | +0.004650 | -0.004442 | 1/4 |
| Q3_tree | M1_interaction | +0.010129 | [-0.009700,+0.030798] | [-0.012449,+0.033904] | +0.004244 | -0.001127 | 1/4 |
| Q3_tree | Q1_path | +0.016252 | [-0.004998,+0.038047] | [-0.007819,+0.041761] | +0.006939 | +0.006785 | 1/4 |

## Every forward block (not cherry-picked)

| Fold | Games | Q2 LL | Q3 LL | M1 LL | Q1 LL | Q2 active / 84 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 22 | 0.701271 | 0.695345 | 0.652097 | 0.632260 | 40 |
| 2 | 44 | 0.668261 | 0.600752 | 0.621876 | 0.628250 | 42 |
| 3 | 32 | 0.559548 | 0.604477 | 0.594860 | 0.587963 | 45 |
| 4 | 39 | 0.607357 | 0.622765 | 0.594053 | 0.581592 | 48 |

## Locked outcome

| Model | Future-candidate gate | Largest favorable group / total M1 LL gain |
| --- | --- | ---: |
| Q2_sparse | FAILED | n/a |
| Q3_tree | FAILED | n/a |

Important: model feature importance is diagnostic only. Correlated engineered signals are not evidence of causal influence. The real-time feed receipt timestamp is unknown; a historical replay cannot establish true received-at time.

**No applicant submission update.** The untouched Vexil notebook, original 3,836 TEST rows, 4-page PDF, private AI disclosure, existing Colab verification and reviewer ZIP are preserved.
