# Event delay: tower and item updates arriving 60 seconds late

Only original 291 TRAIN games, unchanged four chronological, series-disjoint 137-game / 5,081-minute OOF split; this is **not** an unseen independent test.
**19 November correction:** ALL and ALL60 used the earlier rich-feature extraction that discarded Roshan kills. This delay sensitivity was **not rerun** on corrected Roshan inputs, and its numbers should not be applied to the corrected model. The main notebook and TEST forecasts remain unchanged. See [Roshan correction](ROSHAN_CORRECTION_20261119.md).

| Comparison (ALL60 minus ...) | Δ LL | 95% grouped CI | 97.5% two-primary CI | Δ Brier | 30+ Δ Brier | Equal-match Δ LL | Fold wins |
| --- | ---: | --- | --- | ---: | ---: | ---: | ---: |
| ALL | -0.000310 | [-0.000966,+0.000331] | [-0.001049,+0.000427] | -0.000083 | -0.000663 | -0.000162 | 2/4 |
| Q1_path | -0.001947 | [-0.011426,+0.007177] | [-0.012623,+0.008586] | -0.000554 | -0.003452 | -0.001823 | 2/4 |
| M1_interaction | -0.008070 | [-0.015267,-0.001393] | [-0.016413,-0.000645] | -0.003249 | -0.011364 | -0.006749 | 4/4 |

## Four chronological TRAIN-forward folds

| Fold | Games | Q1 LL | M1 LL | ALL0 LL | ALL60 LL |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 22 | 0.632260 | 0.652097 | 0.644877 | 0.645191 |
| 2 | 44 | 0.628250 | 0.621876 | 0.620516 | 0.619028 |
| 3 | 32 | 0.587963 | 0.594860 | 0.582862 | 0.582657 |
| 4 | 39 | 0.581592 | 0.594053 | 0.582268 | 0.582888 |

## Sensitivity and decision

- ALL60−Q1 delete-one-series LL range: [-0.003752,+0.000628]. No re-fitting or model selection from deletions.
- Original ALL0−Q1 LL: -0.001637; the previously registered ALL0 score is reconstructed from scratch.
- Frozen event-lag stability gate: FAIL / NO-GO.

This is simulated event source delay. Live timestamp arrival has NOT been measured. The user-owned 4-page submission, notebook, original TEST predictions, ZIP, original draft PR and main are unchanged. This historical 4-day TRAIN-window result cannot establish cross-patch or cross-league transport; original TEST is not blind anymore.
