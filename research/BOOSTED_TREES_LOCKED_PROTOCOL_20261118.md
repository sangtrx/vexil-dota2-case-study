# XGBoost vs LightGBM — fixed low-capacity Dota2 boosted tree benchmark
18 November 2026 ICT | Exploratory supplement, not the applicant take-home.

## Decision and source honesty
Vexil applicant-forwarded assignment requires gold-lead logistic baseline and applicant-owned model, NOT XGBoost/LightGBM specifically. Previous sklearn HistGradientBoosting 84-input candidate failed. The four new runs below are direct XGBoost and LightGBM benchmarks. The candidate/search history already looked at March TEST/VAL and several Oct-Nov cohorts: this is post-selection TRAIN-forward research, NOT a fresh independent test.

## Exact source and train/validation contract
Use only frozen original March 291 TRAIN games, 10,675 preterminal minute rows. Load rich 81 as-of features from source-verified immutable March TRAIN rich CSV; no March VAL or TEST rows, no Oct/Nov data at fit/score. Frozen chronological series-disjoint fold index cuts (154,176,220,252,291): evaluate 22+44+32+39=137 games, 5,081 minute rows, 70 professional series/singletons. Only earlier completed games (start_time+duration<=first_eval_start) for fitting. No same-series boundary leakage. Fit median imputer separately inside each training fold. No early stopping on eval fold. No parameter search. No refit from eval labels.

## Exactly four candidates, fixed before scoring
Versions xgboost==3.4.2 and lightgbm==4.7.0 isolated off applicant requirements. Stop before scoring if these versions cannot install; never silently substitute.
- XGB3: XGBClassifier, 3 M1 features gold_k,minute10,gold_x_time; binary logistic objective, 90 rounds, max_depth=2, learning_rate=.04, min_child_weight=35, reg_lambda=25, gamma=.2, subsample=.85, colsample_bytree=1, tree_method=hist, max_bin=128, n_jobs=2, seed 20261118, no early stopping.
- XGB84: exactly same settings but 84 BASE+RICH as-of features and colsample_bytree=.8.
- LGB3: LGBMClassifier, 3 M1 features; objective=binary, 90 rounds, max_depth=3, num_leaves=5, learning_rate=.04, min_child_samples=175, min_child_weight=25, reg_lambda=25, min_split_gain=.2, colsample_bytree=1, subsample=1, subsample_freq=0, max_bin=128, verbosity=-1, deterministic=True, force_col_wise=True, n_jobs=2, seed 20261118.
- LGB84: same LGBM settings but 84 BASE+RICH as-of features and colsample_bytree=.8.
No class weights, per-game weights, external predictions, team ID, patch, completed-game length or postterminal data in new candidates.

## Frozen reference models
M0 gold, A additive gold+time, M1 interaction gold/time, Q1 causal path, previous Q3 sklearn HistGB84, all unchanged and historical fold scores must agree with original RICH_FEATURE_MODEL_RECEIPT to within 1e-9. One predeclared stronger reference: MATCH_EQUAL version of original M1 with total TRAIN weight equal per completed game, normalized weight sum to total train rows, fit-specific scaler unweighted; weights never used as feature or in eval.

## Estimand, statistical guardrails and decision
Primary is minute-weighted proper log loss (live minute-forecast requirement). Secondary equal-match LL, overall Brier, Brier at minute>=30 and minutes0-9, calibration-in-the-large, fixed 10-bin ECE with counts, four fold LL values, and extreme group influence. Paired 5000 whole-series (70 groups) bootstrap seed 20261118 for four new candidates versus M1 and Q1. Report 95% and within-this-screen 99.375% two-sided intervals (8 contrasts Bonferroni); multiple earlier screens not corrected. Research candidate gate requires LL <=-0.005 vs both baselines, both 99.375% CI upper<0, no overall or late30 Brier regression, wins >=3/4 folds against both. If gate met, only candidate for truly future untouched evaluation; never employer promotion. Else NO-GO. All scores, including failures, published.

## Verification / operating boundary
Source and features SHA, no duplicate game/minute, 137 games / 5,081 minute rows / 70 series groups, original baseline fold parity, no model reading future folds or original March TEST, no feature reordering or future-suffix effects. Keep the original notebook and 3,836 TEST predictions frozen. Only original TRAIN data and pinned research environments were used for this retrospective comparison. Verify the fixed files and report results without rescoring the exposed March TEST.
