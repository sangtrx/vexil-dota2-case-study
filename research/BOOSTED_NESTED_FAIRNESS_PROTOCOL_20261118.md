# Nested tuning stress for direct XGB/LGBM — post-result fairness exercise

18 Nov 2026 ICT. THIS IS DESIGNED AFTER INSPECTING THE FOUR-FIXED-CANDIDATE TRAIN OOF RESULTS, which all failed vs Q1. This cannot be considered independently blinded or prospectively predeclared from the overall original project. It is a bounded **sensitivity / fairness test** of whether the fixed conservative 90-tree configurations were too regularized, not model promotion or new evidence from uninspected outcomes.

## Scope and no-TEST rule
Exactly original March 291 TRAIN professional games and verified source 81-feature file. No original March VAL, original 106 TEST, Oct, Nov, or new APIs; preserve all employer applicant artifacts. Outer chronological folds same four original ordered series-disjoint cuts (154,176,220,252,291). Outer evaluation 22+44+32+39=137 games / 5081 decision minutes / 70 independent series/singletons. Mature-label proxy, original feature clock and no future same-series models unchanged.

## Strong nested contract
Within EACH historical outer training prefix, form independent professional series/singleton groups sorted by earliest match start (ties by stable group key). Freeze the following INNER two group-forward folds by *group rank*, no labels or scores:
- Inner1: group ranks 0 through floor(0.55*N)-1 are candidate training groups; evaluate group ranks [floor(0.55*N),floor(0.78*N)).
- Inner2: groups [0,floor(0.78*N)) training; evaluate groups [floor(0.78*N),N).
- Inside each inner train, exclude any historical match not FINISHED before inner eval's first start_time, using start_time+duration proxy; never use newer match outcomes/labels, match duration or final winner as features. Inner validation uses complete later groups' outcome labels only for INNER candidate choice, never enters outer fit/score.
- Fit preprocessing within each inner fold; within each of the four model families choose min aggregate *minute-weighted inner validation log loss across both validation folds*, pooled by minute rows, ties broken in fixed order conservative, moderate, flexible. Inner means may be noisy; show counts, group sizes and chosen config. Then re-fit selected config on entire mature outer training set and evaluate OUTER block exactly ONCE per predeclared family.

## Four fixed families and 3 precommitted parameter profiles each (12 possibilities)
Use original XGB3 / XGB84 / LGB3 / LGB84 features from preceding frozen code, and same pinned isolated Python/xgboost 3.4.1 / lightgbm 4.7.0 / narwhals 2.21.2. All CPU two threads, fixed random_state 20261118, correct losses, no early stopping, no class weighting, no outer-label tuning or calibration. Base lightgbm/xgb settings from previous BOOSTED_TREES_LOCKED_PROTOCOL.

XGB profile definitions (apply same to 3/84 inputs; colsample 1 for 3, 0.8 for 84):
- conservative: 90 estimators, max_depth2, learning_rate .04, min_child_weight35, reg_lambda25, gamma .2, subsample .85.
- moderate: 150 estimators, max_depth2, learning_rate .05, min_child_weight15, reg_lambda12, gamma .05, subsample .85.
- flexible: 180 estimators, max_depth3, learning_rate .04, min_child_weight8, reg_lambda8, gamma 0, subsample .9.

LGB profile definitions (same feature/colsample rule):
- conservative: 90 estimators, max_depth3, num_leaves5, learning_rate .04, min_child_samples175, min_child_weight25, reg_lambda25, min_split_gain .2.
- moderate: 150 estimators, max_depth3, num_leaves7, learning_rate .05, min_child_samples85, min_child_weight10, reg_lambda12, min_split_gain .05.
- flexible: 180 estimators, max_depth4, num_leaves9, learning_rate .04, min_child_samples50, min_child_weight5, reg_lambda8, min_split_gain 0.
For all LightGBM: subsample1, subsample_freq0, max_bin128, deterministic true, force_col_wise true. All XGB: tree_method hist, max_bin128, binary logistic.

## Primary and decision gate (pre-scoring for this sub-experiment)
Primary OUTER minute-weighted log loss (actual user requested per-minute forecasts), secondary equal-match LL, Brier, late30 Brier, early9 Brier, 10-bin descriptive ECE and per-fold performance. Comparators M1, Q1 and M1_MATCH_EQUAL re-fit on the same original outer mature fit and must reproduce previous direct booster receipt scores to <=1e-9. The previously fixed four configurations are shown as descriptive crosswalk, not used in nested selection.
Paired bootstrap full professional series/singletons 5000 seed 20261118; four families vs M1 and Q1 (8 comparisons, screen-local two-sided 99.375% intervals). Research-only gate: <=−0.005 LL vs both baseline, both corrected CI upper<0, no worse overall or late30 Brier, >=3/4 outer fold wins vs both. Even a gate pass is an exploratory candidate for future real live timestamped cohort, not employer model change. No more parameter searches on the same cohort after this sweep.
No GitHub Actions, no original notebook/PDF/ZIP/Gmail/PR9 or production changes, no send. Preserve positive and negative results in GitHub issue #2278.
