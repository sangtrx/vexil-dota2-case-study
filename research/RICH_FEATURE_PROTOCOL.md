# Vexil wide feature engineering — locked exploratory research protocol

**Date:** 17 November 2026. **Source baseline:** the separately reviewed Q1 PathRisk branch at `ed3f2f78f73a4f02de7e84d4303bf3cd619536be`. Original TEST and many prior TRAIN/VAL model trials have already been inspected. This is **post-result exploratory research**, not preregistration of the main assignment and not fresh blind validation. Never promote directly to the employer submission.

## Question and scope

Does a broad, mechanically defined state representation of **lead trajectories, XP paths, player economy inequality, timestamped objectives, and economic/structural contradictions** improve Radiant win-probability log loss relative to M1 or Q1?

Use **only the 291 original TRAIN match IDs (10,675 minute forecasts)** from the SHA256-locked `research/frozen_original_train_features.csv.gz` and their exact original cached `/matches/{match_id}` JSON payloads. Never read or use VAL/TEST match IDs beyond the preexisting split-membership audit; do not train/evaluate against their labels. Raw match JSON files remain outside Git. Every engineered feature must be computed from arrays **sliced to <=t** and log events with timestamps **<=60t**; do not reference final-score or end-of-game player fields.

### Locked 81 features (five mechanistic families)

- gold: **19** features — `gold_d1`, `gold_d3`, `gold_d5`, `gold_d10`, `gold_acc3`, `gold_acc5`, `gold_vol3`, `gold_vol5`, `gold_vol10`, `gold_range5`, `gold_range10`, `gold_retreat5`, `gold_retreat10`, `gold_eff5`, `gold_eff10`, `gold_flips10`, `gold_peak_age10`, `gold_slope5`, `gold_ewma_gap10`
- xp: **13** features — `xp_level`, `xp_d3`, `xp_d5`, `xp_d10`, `xp_acc5`, `xp_vol5`, `xp_vol10`, `xp_retreat10`, `xp_eff10`, `xp_flips10`, `xp_slope5`, `gold_xp_gap`, `gold_xp_flow_gap`
- players: **19** features — `p_gold_top1_diff`, `p_gold_top2_diff`, `p_gold_bottom2_diff`, `p_gold_median_diff`, `p_gold_std_diff`, `p_gold_gini_diff`, `p_gold_top1_share_diff`, `p_gold_top2_share_diff`, `p_gold_bottom2_share_diff`, `p_gold_growth3_top2_diff`, `p_gold_growth5_bottom2_diff`, `p_xp_top2_share_diff`, `p_xp_gini_diff`, `p_lh_total_diff`, `p_lh_top2_diff`, `p_lh_growth3_diff`, `p_dn_total_diff`, `p_lh_balance_diff`, `p_concentration_gap`
- objectives: **17** features — `o_tower_delta`, `o_rax_delta`, `o_roshan_delta`, `o_kills_delta`, `o_tower5_delta`, `o_tower10_delta`, `o_kill3_delta`, `o_kill5_delta`, `o_last_tower_age_diff`, `o_last_kill_age_diff`, `o_roshan10_delta`, `o_aegis5_delta`, `o_tower_weighted`, `o_rax10_delta`, `o_firstblood_side`, `o_highground_delta`, `o_objective_tempo`
- interactions: **13** features — `x_gold_per_sqrt_time`, `x_xp_per_sqrt_time`, `x_economy_gap`, `x_gold_vol_adj`, `x_opp_kill_mismatch`, `x_gold_tower_mismatch`, `x_xp_tower_mismatch`, `x_gold_early`, `x_gold_late`, `x_gold_times_abs_tower`, `x_tower_times_abs_gold`, `x_gold_times_abs_kill`, `x_volatile_retreat`

All features are directional **Radiant minus Dire** or explicitly signed by the current lead, so features should reverse sign under team swapping. Existing baseline columns `gold_k`, `minute10`, `gold_x_time` are kept separate; Q2/Q3 each have **84 inputs**.

**Fixed windows only:** 1,3,5,10 minutes; trailing windows may use shorter prefixes near game start. Lead acceleration is the difference of consecutive fixed-horizon changes. Volatility is root mean squared lead *increments*, not return volatility. Path efficiency is net move divided by absolute movement. Retreat is current leading-side loss from its trailing best. Features using Roshan/Aegis/firstblood derive only from timestamped `objectives`; player statistics use original per-minute `gold_t/xp_t/lh_t/dn_t`, not final `net_worth`, hero-kill totals, GPM/XPM or victory labels. If an event has no authoritative side in its replay payload, it contributes neither positive nor negative count.

## Fixed candidate models

- **M0**: gold lead only (reference).
- **A**: gold + game minute (proper additive null).
- **M1**: gold + minute + gold×time (existing submission).
- **Q1**: prior fixed five-feature path-risk model, as a rival (not reselected).
- **Q2 SparseWide**: **84 inputs**, pipeline median imputer + StandardScaler + elastic-net logistic regression (`solver=saga,C=0.08,l1_ratio=0.70,max_iter=3000,tol=0.001,random_state=20261113`). This encourages a parsimonious set of mechanisms despite wide input.
- **Q3 ShallowTree**: the same inputs, median imputer + `HistGradientBoostingClassifier(max_iter=70,max_leaf_nodes=7,learning_rate=0.04,min_samples_leaf=250,l2_regularization=30,early_stopping=False,random_state=20261113)`. Fixed nonlinear interactions with conservative leaves.

No third candidate, no tuning, no modified window or features after viewing results. This deliberately includes multiple highly correlated features; interpret Q2 coefficients/selection only as *diagnostic*, not stable causal attribution.

## Locked validation and failure gate

Use the historical Q1 fixed TRAIN-forward chronological cutpoints **(154,176,220,252,291)**; compare series-disjoint folds, omit incomplete TRAIN labels under estimated match-end maturity, and keep evaluation unit as entire series/singleton. Expect **137 forward TRAIN games, 5,081 rows, 70 series/singletons**, four folds. Fit each scaler and estimator within each fold. Validate immutable M0/A/M1/Q1 prediction parity against existing Q1 receipt to avoid changes in benchmark.

Primary: minute-weighted log loss, paired differences Q2/Q3 versus M1 and Q1, **5,000 paired series bootstrap** (point plus descriptive 95% and Bonferroni two-model **97.5%** confidence interval). Secondary: overall and minute30+ Brier, fold sign, max single-cluster share of favorable LL gain. No action/model change on historic VAL/TEST.

A model earns at most an **unseen-future validation candidate**, not submission promotion, only if: LL gain against *both* M1 and Q1 >= **0.003**, Bonferroni 97.5% interval upper bound <0 on each comparison, >=3/4 forward folds improve both, overall & 30+ Brier no worse than both, and largest favorable cluster <50% of total LL gain against M1. Report both successes/failures and estimates for the other model without cherry-picking.

Multiplicities already incurred in earlier 28+ model screens remain; neither new 97.5% CI is a confirmatory familywise claim over the whole research history. Missing true `received_at` prevents retrospective live availability proof. Rich feat engineering might have **less** value than simpler models; retain adverse results.

## Hard safety / ownership

Original applicant notebook, TEST predictions, four-page report, Colab receipts, ZIP, AI disclosure and hours must be unchanged. Commit this protocol **before** implementing fit/evaluation outcomes. Keep all work on a separate private research branch; no push to reviewer branch/main, merge, submission, or employer access change.
