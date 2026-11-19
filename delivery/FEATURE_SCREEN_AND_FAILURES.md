# Feature experiments and failed hypotheses

This appendix covers exploratory work outside the original 500-game
model-selection exercise. The four-page report states the main decision.
Historical labels were repeatedly inspected; these are not new independent
TESTs, and the original 500-game notebook does **not** run all these models.

## Original models

| Model | Input added | Original VAL log loss | Decision |
| --- | --- | ---: | --- |
| M0 | Gold lead | 0.5325 | Baseline |
| M1 | Time and gold-by-time interaction | **0.5197** | Chosen on original VAL |
| M2 | Gold/XP dynamics | 0.5224 | Worse |
| M3 | Structures, kills, Roshan | 0.5282 | Worse |

## Structural and option-state features on reused VALIDATION

| ID | Feature question | Old VAL log loss | Outcome |
| --- | --- | ---: | --- |
| S1 | Relative team economy | 0.518253 | Insufficient practical gain; same candidate as P05 |
| S2 | Gold concentration in top two players | 0.517384 | Worse in 3/3 preceding TRAIN folds |
| S3 | Gold-lead fragility | 0.524593 | Failed VAL despite 3/3 earlier TRAIN folds |
| S4 | Parsimonious joint state | 0.520049 | Failed; similar signal to P12 |
| M4 | Aegis, buybacks and structures | 0.520596 | Failed grouped uncertainty gate |

The P01–P28 screen is a separate adaptive comparison on the **historical,
reused** VAL snapshot. Its M1 log-loss reference was **0.519346**, rather
than the corrected applicant score 0.5197. The familywise interval covers
the 28 screened hypotheses, **not all earlier searches**.
**0/28 candidates qualified for promotion.**

## All 28 screened feature candidates

| ID | Feature idea | VAL log loss | Brier | ΔLL vs M1 | 95% max-T upper | TRAIN folds favoured | Advance? |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| P20 | High-impact item completions (items) | 0.514098 | 0.173742 | -0.005248 | 0.006434 | 1/3 | NO |
| P08 | Support and farming topology (economic) | 0.515840 | 0.174408 | -0.003505 | 0.005137 | 0/3 | NO |
| P15 | Recent lethal fights (objectives) | 0.517020 | 0.175106 | -0.002326 | 0.012956 | 2/3 | NO |
| P05 | Relative team economy (economic) | 0.518253 | 0.175137 | -0.001093 | 0.001409 | 2/3 | NO |
| P18 | Buyback commitment (option-state) | 0.518400 | 0.175156 | -0.000946 | 0.002091 | 3/3 | NO |
| P11 | Short-term volatility (dynamics) | 0.518548 | 0.175442 | -0.000798 | 0.001211 | 1/3 | NO |
| P02 | Early/late slope continuity (time-shape) | 0.519032 | 0.175579 | -0.000314 | 0.002805 | 0/3 | NO |
| P21 | Recent item investment impulse (items) | 0.519167 | 0.175690 | -0.000179 | 0.000323 | 0/3 | NO |
| P01 | Convex lead utility (time-shape) | 0.519376 | 0.176116 | 0.000030 | 0.003281 | 0/3 | NO |
| P07 | Top-two carry concentration (economic) | 0.519438 | 0.175775 | 0.000092 | 0.001165 | 0/3 | NO |
| P03 | Asinh gold scale (time-shape) | 0.519550 | 0.176108 | 0.000204 | 0.002694 | 2/3 | NO |
| P09 | Five-minute economic shock (dynamics) | 0.519689 | 0.176341 | 0.000343 | 0.010379 | 2/3 | NO |
| P10 | Acceleration of lead (dynamics) | 0.519737 | 0.176561 | 0.000391 | 0.011390 | 3/3 | NO |
| P12 | Directional persistence (dynamics) | 0.520048 | 0.176644 | 0.000703 | 0.009012 | 3/3 | NO |
| P19 | Economy versus structures (option-state) | 0.520337 | 0.176473 | 0.000991 | 0.008862 | 2/3 | NO |
| P04 | Smooth time curvature (time-shape) | 0.520392 | 0.176383 | 0.001046 | 0.003549 | 0/3 | NO |
| P17 | Aegis claim window (option-state) | 0.520974 | 0.176396 | 0.001628 | 0.005043 | 2/3 | NO |
| P06 | XP purchasing power (economic) | 0.521304 | 0.177304 | 0.001958 | 0.024062 | 2/3 | NO |
| P28 | Strong-regularized time-value (shape) | 0.521667 | 0.176660 | 0.002321 | 0.006691 | 2/3 | NO |
| P25 | Additive B-spline gold and time (shape) | 0.523213 | 0.177192 | 0.003867 | 0.011408 | 0/3 | NO |
| P27 | Event-state bundle (synthesis) | 0.524031 | 0.178222 | 0.004686 | 0.012520 | 2/3 | NO |
| P13 | Weighted map structure (objectives) | 0.524753 | 0.178280 | 0.005407 | 0.021327 | 1/3 | NO |
| P16 | Roshan and tower sequencing (objectives) | 0.525120 | 0.178901 | 0.005774 | 0.013189 | 3/3 | NO |
| P26 | Strategic conversion bundle (synthesis) | 0.528841 | 0.180177 | 0.009495 | 0.029287 | 2/3 | NO |
| P14 | Recent tower conversion (objectives) | 0.528961 | 0.180257 | 0.009616 | 0.027557 | 1/3 | NO |
| P23 | Shallow nonlinear gold/time (shape) | 0.532511 | 0.179920 | 0.013165 | 0.031488 | 1/3 | NO |
| P24 | Shallow calibrated macro-state tree (shape) | 0.539473 | 0.183276 | 0.020127 | 0.040017 | 2/3 | NO |
| P22 | High-dimensional hero draft encoding (draft) | 1.581239 | 0.368861 | 1.061894 | 1.637817 | 0/3 | NO |

P20, a timestamped Blink/BKB and high-impact-item feature, gave the lowest
VAL point loss (0.514098), but its simultaneous adjusted interval
[-0.016929,+0.006434] includes zero and only 1/3 earlier TRAIN folds favoured
it. P22 raw hero-draft encoding scored **1.581239** log loss; this rejects
that underregularized specification, not all hero-draft modelling.

## 81 engineered fields tested with 3 M1 inputs

Five groups were implemented. The historical extractor yielded two constant
Roshan fields and one duplicate economic feature; the 19 November repair
attributed Roshan kills using the available team identifier. The corrected
Q2/Q3/XGB84/LGB84 comparisons used TRAIN-forward only. Most October/November
rich-feature transfer and ALL60 results were **not rerun after the repair**.

| Family | Number | Idea | Actual implemented fields |
| --- | ---: | --- | --- |
| **gold** | 19 | Gold history: momentum (1/3/5/10 minutes), acceleration, realized volatility, ranges, drawdowns/retreats, efficiency, reversals and recency of a prior peak | `gold_d1`, `gold_d3`, `gold_d5`, `gold_d10`, `gold_acc3`, `gold_acc5`, `gold_vol3`, `gold_vol5`, `gold_vol10`, `gold_range5`, `gold_range10`, `gold_retreat5`, `gold_retreat10`, `gold_eff5`, `gold_eff10`, `gold_flips10`, `gold_peak_age10`, `gold_slope5`, `gold_ewma_gap10` |
| **xp** | 13 | XP level/dynamics, volatility, retreat, directional persistence and disagreement between XP and gold flow | `xp_level`, `xp_d3`, `xp_d5`, `xp_d10`, `xp_acc5`, `xp_vol5`, `xp_vol10`, `xp_retreat10`, `xp_eff10`, `xp_flips10`, `xp_slope5`, `gold_xp_gap`, `gold_xp_flow_gap` |
| **players** | 19 | Who holds team resources: top carry, bottom support, Gini/concentration, player gold growth, last hits, denies and team-role redistribution | `p_gold_top1_diff`, `p_gold_top2_diff`, `p_gold_bottom2_diff`, `p_gold_median_diff`, `p_gold_std_diff`, `p_gold_gini_diff`, `p_gold_top1_share_diff`, `p_gold_top2_share_diff`, `p_gold_bottom2_share_diff`, `p_gold_growth3_top2_diff`, `p_gold_growth5_bottom2_diff`, `p_xp_top2_share_diff`, `p_xp_gini_diff`, `p_lh_total_diff`, `p_lh_top2_diff`, `p_lh_growth3_diff`, `p_dn_total_diff`, `p_lh_balance_diff`, `p_concentration_gap` |
| **objectives** | 17 | Timestamped tower/rax/kills, structural recency, Roshan/Aegis availability, high-ground and objective pace; Roshan team (2/3) available; historical parser ignored it | `o_tower_delta`, `o_rax_delta`, `o_roshan_delta`, `o_kills_delta`, `o_tower5_delta`, `o_tower10_delta`, `o_kill3_delta`, `o_kill5_delta`, `o_last_tower_age_diff`, `o_last_kill_age_diff`, `o_roshan10_delta`, `o_aegis5_delta`, `o_tower_weighted`, `o_rax10_delta`, `o_firstblood_side`, `o_highground_delta`, `o_objective_tempo` |
| **interactions** | 13 | Regime/shape terms: gold per square-root time, volatility-adjusted lead, gold vs towers/kills discrepancies, early/late terms, high volatility + retreat | `x_gold_per_sqrt_time`, `x_xp_per_sqrt_time`, `x_economy_gap`, `x_gold_vol_adj`, `x_opp_kill_mismatch`, `x_gold_tower_mismatch`, `x_xp_tower_mismatch`, `x_gold_early`, `x_gold_late`, `x_gold_times_abs_tower`, `x_tower_times_abs_gold`, `x_gold_times_abs_kill`, `x_volatile_retreat` |

## Model comparisons and other negative results

| Experiment | Evidence | Decision |
| --- | --- | --- |
| Separate 200-game phase-blend gate | LL 0.539850 vs M1 0.533704 | Blend failed |
| Q1 five-input gold-path logistic | TRAIN LL 0.605963 vs M1 0.612086; 95% CI of difference [-0.0174,+0.0047] | No promotion |
| Corrected Q2/Q3 rich models | Δ LL vs M1 +0.017733 / +0.010129 | Both worse |
| XGB3/LGB3 | LL 0.615597 / 0.616196 vs Q1 0.605963 | Worse |
| Corrected XGB84/LGB84 | LL 0.621254 / 0.624856 | Both worse |
| C4 gold/XP-path signatures | Δ LL vs Q1 +0.005380; CI crosses zero | No promotion |
| Disagreement alert | Wrong-side AUROC 0.51856 vs baseline uncertainty 0.66576 | Worse |
| Fixed probability smoothing | Δ LL +0.003703 vs M1 | Worse |
| Lagged ALL60 feature stress | Δ LL -0.008070 vs M1 but only -0.001947 vs Q1; CI crosses zero | No promotion; old parser |
| November100/120 external checks | 68 games overlap; neither grouped interval excludes zero | Not independent replications |
| September locked external (optional) | 199/200 games, M0 LL 0.584431 vs M1 0.544803; series CI [-0.074261,-0.010790] | Limited external-support gate **PASS** |

**September is not a failed experiment and must not be concealed.** The
original model was fixed before a separately preregistered September cohort
was scored, outside the required 500 games. The 199 usable matches cover
only three leagues and repeated teams. Deleting five most favourable games
makes a post-hoc interval cross zero. This strengthens the case to *shadow*
M1, not a claim of universal superiority or measured live feed availability.

The private research repository contains the dated branches, separate
readouts, full cohort table and September frozen prediction CSV + offline
verifier. This ZIP is a compact summary and cannot reproduce every
exploratory run: historical raw match JSON, some model environments and
several old exploratory scripts are not bundled. The required 500-game
notebook and 3,836 TEST forecasts remain unchanged.
