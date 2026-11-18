# Creative Feature Engineering & Experiment Atlas

**Truong Quang Sang | Vexil Capital Senior Data Scientist take-home | supplementary research inventory | 18 November 2026**

**Read this after the FOUR-PAGE `REPORT.pdf`.** This is an optional, full scientific experiment ledger rather than another required report or a second executable notebook. It enumerates the original modelling and subsequent creative investigations, including discarded ideas, source limitations and failures. Not all studies below are executed by the submitted notebook. The single 16-code-cell notebook remains the only required executable study; it fits M0-M3 (plus a development-only item diagnostic). The extra research model source and protocols live in the private GitHub **research** branches, not in the standalone reviewer ZIP. The archived readouts included here are reviewable but are **not automatically independently reproducible without the research source and raw author cache**.

## One-minute decision

The original 500-game point-in-time observational study finds TEST minute-log-loss M0 gold baseline **0.516444** versus M1 time-aware **0.504015** on 106 games / 3,836 predictions. The paired 95% match bootstrap for M1−M0 **[-0.0304,+0.0014]** includes zero, and M1 worsens minute-30+ Brier **0.1028→0.1074**. So the defensible recommendation remains **M0 reference, M1 shadow only**. This is not a negative result on the candidate's creativity; it is evidence-led model selection.

### Evidence tiers — never mix these scores as if they were one TEST

| Tier | Data/decision stage | What may be concluded |
| --- | --- | --- |
| **A: original applicant evaluation** | 500 March games; 291 TRAIN / 103 VAL / 106 TEST; 18,292 decisions; point-in-time filtered | Main M0-M3 notebook evidence, with corrected-after-inspection TEST boundary made explicit |
| **B: reused development labels** | P01-P28, S1-S4, M4 and historical pre-correction scores on the already-inspected 103 VAL games | Creative attempted hypotheses and **failures**, not a new validation or model-promotion claim |
| **C: March TRAIN-only forward** | Four original chronological mature-label folds; 137 games, 5,081 forecast minutes, 70 series/singletons | Independent-within-TRAIN fold *descriptive* comparisons; still after many candidate searches, **not a fresh out-of-project test** |
| **D: later October/November retrospective replays** | October 180 games; Nov 22 or Nov 17 distinct sources; some overlaps with earlier research | Stress for drift and feature transfer, **not new prospective live receipts**, sometimes source labels had been inspected |
| **E: operational/fault simulation** | Artificial 1/3-minute delays, event lag, abstain/smoothing, malformed inputs | Risk discovery, not measured network/stream packet availability or betting profit |

## 1. The original four executable models (tier A)

| Model | Feature hypothesis | VALIDATION minute log loss | Brier | Decision |
| --- | --- | ---: | ---: | --- |
| M0 gold-only logistic | Gold lead / 1000 only | 0.5325 | 0.1811 | Required reference |
| M1 time-aware logistic | Gold, minute / 10, gold×log(1+minute/10) | **0.5197** | **0.1759** | Original selected challenger; shadow-only after TEST |
| M2 lead dynamics logistic | M1 + XP and observed recent gold/XP movement | 0.5224 | 0.1778 | Rejected on original VAL |
| M3 objective conversion logistic | M2 + timestamped towers, barracks, Roshan, kills | 0.5282 | 0.1806 | Rejected on original VAL |

Pipeline: `SimpleImputer(median)` → `StandardScaler` → L2 `LogisticRegression(C=1)`; fit on TRAIN only; original VAL chooses M1; original TEST does not refit or select. The proposed causal question (“what is game time's effect?”) is **not** identified by observational comparison; model interaction is predictive, not a causal estimate.

## 2. First creative hypotheses: structure, team economy and Aegis (tier B; historical reused VAL)

| Experiment | Tested mechanism | Historical reused VAL log loss | Difference versus historical M1 0.519346 | Outcome |
| --- | --- | ---: | ---: | --- |
| S1 | Relative team economy | 0.518253 | -0.001093 | Gain below practical -0.005 threshold |
| S2 | Top-two player gold concentration | 0.517384 | -0.001962 | Worse 3/3 earlier TRAIN folds; simultaneous CI includes zero |
| S3 | Economic lead fragility | 0.524593 | +0.005248 | Worse on reused VAL despite 3/3 earlier TRAIN folds favorable |
| S4 | Parsimonious joint state | 0.520049 | +0.000703 | Negative |
| M4 | Recent Aegis, buyback and structures | 0.520596 | +0.001251 | CI crosses zero, gate failed |
| P20 | Timed high-impact item completions, including Blink/BKB | **0.514098** | **-0.005248** | Best of 28 historical VAL point estimates; adjusted 28-way CI [-0.016929,+0.006434] crosses zero; favorable only 1/3 earlier TRAIN folds |

P20 was creative but did **not** earn selection. The exact historical register preserves a real matched example: two March patch-59 games at minute 25 with gold leads only **28** apart and XP leads **102** apart, but different Aegis/structural states. Both Radiant teams won, so that example illustrates state aliasing, **not** evidence that Roshan or item features improved probability accuracy.

## 3. COMPLETE adaptive screen — all P01-P28 (tier B)

**These values belong to an older 18,304-row version before a 12-row terminal-boundary correctness repair.** The M1 reference in this *historical* screen is **0.519346**, not the corrected applicant VAL score 0.5197. All 103 VAL games had already been inspected; none of 28 passed the joint promotion gate. The 28-way interval only controls those 28 within-screen comparisons, **not prior adaptive research**. **0/28 candidates were promoted; this is not a new held-out TEST.**

| ID | Proposed and tested hypothesis | Val. LL | Val. Brier | Delta vs M1 | 95% max-T upper | Earlier TRAIN folds favorable | Advance? |
|---|---|---:|---:|---:|---:|---:|---|
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


Every P ID in the historical register is accounted for (P01 through P28); see `docs/EXPERIMENT_REGISTER.md` for original PRs, familywise caveats and the one later 200-game stage-gate test (M1 LL **0.533704**, stage blend **0.539850**, M0 **0.545075**; blend not promoted). Historical pre-correction and corrected metrics should never be merged or compared naively.

## 4. Rich 81-feature study: complete feature inventory (tier C)

Five families were **implemented** to represent lead history, player-role topology, objectives and conflicting strategic signals, with original three M1 features added for a total of **84 model inputs**. The exact field names below are extracted from `research/rich_feature_engineering.py` at research branch `research/vexil-xgb-lgbm-nested-train-20261118`.

| Family | Fields | Design hypothesis | All implemented engineered column names |
| --- | ---: | --- | --- |
| **gold** | 19 | Gold history: momentum (1/3/5/10 minutes), acceleration, realized volatility, ranges, drawdowns/retreats, efficiency, reversals and recency of a prior peak | `gold_d1`, `gold_d3`, `gold_d5`, `gold_d10`, `gold_acc3`, `gold_acc5`, `gold_vol3`, `gold_vol5`, `gold_vol10`, `gold_range5`, `gold_range10`, `gold_retreat5`, `gold_retreat10`, `gold_eff5`, `gold_eff10`, `gold_flips10`, `gold_peak_age10`, `gold_slope5`, `gold_ewma_gap10` |
| **xp** | 13 | XP level/dynamics, volatility, retreat, directional persistence and disagreement between XP and gold flow | `xp_level`, `xp_d3`, `xp_d5`, `xp_d10`, `xp_acc5`, `xp_vol5`, `xp_vol10`, `xp_retreat10`, `xp_eff10`, `xp_flips10`, `xp_slope5`, `gold_xp_gap`, `gold_xp_flow_gap` |
| **players** | 19 | Who holds team resources: top carry, bottom support, Gini/concentration, player gold growth, last hits, denies and team-role redistribution | `p_gold_top1_diff`, `p_gold_top2_diff`, `p_gold_bottom2_diff`, `p_gold_median_diff`, `p_gold_std_diff`, `p_gold_gini_diff`, `p_gold_top1_share_diff`, `p_gold_top2_share_diff`, `p_gold_bottom2_share_diff`, `p_gold_growth3_top2_diff`, `p_gold_growth5_bottom2_diff`, `p_xp_top2_share_diff`, `p_xp_gini_diff`, `p_lh_total_diff`, `p_lh_top2_diff`, `p_lh_growth3_diff`, `p_dn_total_diff`, `p_lh_balance_diff`, `p_concentration_gap` |
| **objectives** | 17 | Timestamped tower/rax/kills, structural recency, Roshan/Aegis availability, high-ground and objective pace; owner-side Roshan kill data NOT available | `o_tower_delta`, `o_rax_delta`, `o_roshan_delta`, `o_kills_delta`, `o_tower5_delta`, `o_tower10_delta`, `o_kill3_delta`, `o_kill5_delta`, `o_last_tower_age_diff`, `o_last_kill_age_diff`, `o_roshan10_delta`, `o_aegis5_delta`, `o_tower_weighted`, `o_rax10_delta`, `o_firstblood_side`, `o_highground_delta`, `o_objective_tempo` |
| **interactions** | 13 | Regime/shape terms: gold per square-root time, volatility-adjusted lead, gold vs towers/kills discrepancies, early/late terms, high volatility + retreat | `x_gold_per_sqrt_time`, `x_xp_per_sqrt_time`, `x_economy_gap`, `x_gold_vol_adj`, `x_opp_kill_mismatch`, `x_gold_tower_mismatch`, `x_xp_tower_mismatch`, `x_gold_early`, `x_gold_late`, `x_gold_times_abs_tower`, `x_tower_times_abs_gold`, `x_gold_times_abs_kill`, `x_volatile_retreat` |

**Hostile feature audit:** Exactly **2 of the 81** engineered columns (`o_roshan_delta`, `o_roshan10_delta`) are constant zero on these 291 TRAIN matches because Roshan-kill source events do not identify side ownership; do not falsely impute team ownership. Exactly **1** nonconstant column (`x_economy_gap`) duplicates `gold_xp_gap`. Therefore there are **78 distinct varying engineered fields**, not 81 independent signals. Source receipt found all **486** Roshan-kill chat events lacked `player_slot` or `slot`. The locked experiments retain those columns and count them honestly; no post-hoc feature removal / repeat tuning.

### Original TRAIN-forward evaluation of the 84-input models

| Candidate | Family | Pooled minute log-loss difference vs M1 | 95% series CI | 30+ Brier delta vs M1 | Favorable outer folds | Decision |
| --- | --- | ---: | --- | ---: | ---: | --- |
| Q2_sparse | Elastic-net logistic / 84 inputs | +0.017311 | [-0.009647,+0.048034] | -0.009578 | 1/4 | FAIL |
| Q3_tree | sklearn HistGradientBoosting / 84 inputs | +0.009180 | [-0.010909,+0.029947] | -0.002443 | 1/4 | FAIL |

Here **positive** loss difference means worse. A favorable late30 slice does not outweigh the worse primary loss. These are four TRAIN-forward blocks only; **no original VAL/TEST refit**. See `research/RICH_FEATURE_MODEL_READOUT.md` and `research/RICH_FEATURE_DIVERSITY_AUDIT.md`.

## 5. Quant/geometry-inspired and special-purpose research (tiers C/D)

| Research question | Candidate/design | Actual grounded observation | Scientific disposition |
| --- | --- | --- | --- |
| Does the **path taken** to reach a gold lead matter? | Q1: 5 fixed gold/time/path features | TRAIN-forward Q1−M1 ΔLL **-0.006123**, 95% CI [-0.017362,+0.004680], favorable 3/4 folds; versus additive ΔLL -0.008143 with 95% [-0.016305,-0.000744] | Predeclared multi-comparator gate **FAILED**; strong rival model but not confirmed upgrade |
| Does richer **path signature/durability** help? | C4 gold/XP path geometry | C4−Q1 ΔLL **+0.005380**, 95% [-0.004789,+0.016475], 1/4 folds | NO-GO |
| Does role redistribution add information? | RANK3 / COUPLING3 / RANK_COUPLING6 | On October, Q1 LL **0.489278** versus RANK3 **0.493744**; later Nov (22 games), COUPLING3 LL **0.440382** versus M1 **0.442682** | Mixed period effects; October and Nov outcomes already inspected; no promotion |
| Can an ensemble produce reliable **disagreement alerts**? | D max-model disagreement vs U M1 confidence uncertainty | Wrong-side AUROC **0.51856** disagreement vs **0.66576** uncertainty; grouped 95% interval of difference [-0.20475,-0.09307] | Disagreement **worse**, no deployment threshold |
| Can we weight **each game equally** rather than minute-count? | MATCH_EQUAL M1 | March TRAIN-forward minute LL **0.618253**, M1 **0.612086**; Oct equal-game LL **0.466953**, Q1 **0.468959**; Nov17 equal-game LL **0.389317** vs M1 **0.398011** | Estimand changes and period inconsistency; no single winner across primary and late30 slices |
| Can we use saturated economic representation? | E_SHARE1 / SAT_ASINH3 | Oct E_SHARE1 LL **0.493254** vs Q1 **0.489278** | Exploratory failure vs strong baseline |
| Do dozens of rich inputs transfer out of time? | ALL rich-features March-fitted model | Oct 180 games: ALL LL **0.493651** vs Q1 **0.489278**; Nov 22 games: ALL **0.445080** vs Q1 **0.449371**, grouped interval includes zero | Apparent advantage flips by period, not a robust lift |
| Can fixed **event lag** protect causal timing? | ALL60 = structural model with 60s delayed event fields | ALL60−Q1 ΔLL **-0.001947**, 95% [-0.011426,+0.007177]; stability gate FAIL | Not compelling and not real received-at |
| Does smoother **probability output** reduce loss? | S1_fixed / S2_event_reset | S1_fixed−M1 ΔLL **+0.003703** and late30 Brier +0.006874; S2_event_reset ΔLL +0.000308 | Smoothing can worsen proper scores; NO-GO |
| Can corrected stale observations be used? | FRESH vs CLOCK/HOLD lag1/lag3 with NO_DATA initial policy | Nov17 M1 FRESH LL **0.423054**, CLOCK3 **0.474476**, HOLD3 **0.465932** | Hypothetical lag stress on 17 already scored games; **not** measured live latency |
| Is the clock of parsed arrays self-consistent? | Player vs team gold/XP alignment | 2,910 player vectors; 10,685 raw snapshot indices; no aggregate mismatch | Parser consistency check, **not** actual event arrival assurance |

The earlier stale feed research had a **P0 code bug**: for lag d and minute t<d, it reused minute-zero data that had not arrived. The corrected policy emits NO_DATA p=0.5 without calling any model until a lagged snapshot genuinely exists; both the old invalid and corrected simulations remain archived, do not quietly substitute old scores.

## 6. Direct XGBoost and LightGBM versus simpler models (tier C; 18 Nov)

Exactly **four** fixed CPU candidates were declared in a dedicated protocol prior to scoring: each of XGBoost and LightGBM on **3** and **84** inputs. Their original March TRAIN-forward evaluation used 137 games / 5,081 forecasting rows / 70 professional groups. A distinct post-result *nested sensitivity* chose among three predeclared complexity profiles within training-only inner folds, without using outer evaluation labels for tuning. **All 16 family×outer selections chose conservative**.

| Model | Inputs | Pooled minute LL | Brier | Late30 Brier | Decision |
| --- | ---: | ---: | ---: | ---: | --- |
| Original M0 | 1 | 0.612312 | 0.211828 | 0.184996 | Reference |
| M1 interaction | 3 | 0.612086 | 0.212744 | 0.183109 | Historical comparator |
| **Q1 path** | 5 | **0.605963** | **0.210050** | **0.175198** | Best descriptive TRAIN-forward point loss; **not promoted** |
| M1 MATCH_EQUAL | 3 | 0.618253 | 0.214388 | 0.185008 | Rejected March primary |
| XGB3 | 3 | 0.615597 | 0.213477 | 0.187800 | FAIL |
| XGB84 | 84 | 0.621809 | 0.216463 | 0.181491 | FAIL |
| LGB3 | 3 | 0.616196 | 0.213476 | 0.187284 | FAIL |
| LGB84 | 84 | 0.622936 | 0.217009 | 0.179798 | FAIL |

XGB3−Q1 ΔLL **+0.009634**, 95% grouped series CI **[+0.002548,+0.017021]**. LGB3−Q1 ΔLL **+0.010233**, 95% **[+0.003146,+0.018082]**. Every candidate won vs Q1 in only **1/4** folds, failed the research gate and was not incorporated into the employer notebook. Neither tree implementation was present in the original applicant requirements; they were tested in a separate isolated Python environment. The 99.375% within-screen intervals and complete fold scores are in the included readouts.

The first XGBoost version pin `3.4.2` did **not** exist in BigLinux's package index; a **pre-score committed amendment** pinned `3.4.1` with LightGBM `4.7.0`, not a hidden substitution. Different model families may perform better on genuinely new data: this screen does **not** prove universal logistic superiority.

## 7. External time checks, stability and adverse evidence (tiers B/D)

- Original March TEST: 106 games, 3,836 forecasts. M1 vs M0 LL **0.504015 vs 0.516444**, paired 95% **[-0.0304,+0.0014]**. A single 55-minute game produced **54.9%** of the estimated improvement; late30 Brier **worsened**.
- Original separate historical 200-game stage-gate (30 Mar–2 Apr, 6,827 minutes, 97 series): phase-blend LL **0.539850**, worse than M1 **0.533704**; no promotion. Historical pre-correction evidence, not one of the original 500.
- November original 100-game check: overall LL CI includes zero, dropping one league reverses apparent improvement; **68 games overlap** an earlier 120-game research collection. Not independent replication.
- October 180-game research: Q1 **0.489278** vs M1 **0.493602** LL. The Oct and Nov comparisons were viewed during earlier candidate search; do not label subsequent tests independent.
- November22 study: small independent count (22 games/9 groups), insufficient to generalize, outcomes previously inspected; economic/rank/coupling advantage does not establish promotion.
- Fresh November17: 17 retrospective professional games, 711 minutes, 10 groups. M1 LL **0.423054**, MATCH_EQUAL **0.415423**, Q1 **0.428489**; MATCH_EQUAL−Q1 equal-match LL CI **98.75% [-0.036681,+0.002497]** includes zero. Minimum protocol required at least 30 games / 15 series, among other gates. NO-GO.
- Original historical robustness: 900-game parse checks / 9,000 player histories, 32,106 clock/gold indices and a 12,063-case adversarial assertion suite per two seeds. These are parser/tests evidence **not** 900 extra independent modelling games.
- Real-time operational claim remains **UNVERIFIED**: parser alignment, event timestamps and hypothetical stale-feed simulation cannot establish actual system `received_at` or source watermark. No betting ROI, trading profit, real-user uplift or causal interpretation is claimed.

## 8. Why the negative results are useful

The hypothesis path was substantive: economic advantage might hide allocation (carry vs support), path history, tower/Roshan control, item completion, draft synergies, phase-specific shifts and delivery delay. Many of these structures are genuinely meaningful in Dota 2. However, a prediction feature must improve **out-of-sample proper scores** after multiplicity and dependence checks; an interesting mechanism alone is not a statistically validated improvement. The candidate preserved failed ablations, sensitivity experiments, nulls and software faults rather than hiding them.

**Model choice is a decision under uncertainty:** M0 is the required reference; M1 is the originally selected challenger, with meaningful but uncertain point advantage. The justified next test is a *genuinely new, precommitted, diverse professional-series cohort with real source receipt timestamps*, a primary minute-weighted log-loss difference threshold and independent group confidence intervals, plus non-regression in 30+ Brier. No new model was refitted on original TEST in any supplementary experiment.

## 9. Where to inspect everything

The original `docs/EXPERIMENT_REGISTER.md` contains the 28-hypothesis ledger and original private PR map. The following evidence files are included in the optional reviewer ZIP as text-only research appendices. They are NOT extra executable notebooks:

- `research/QUANT_BIBLE_PATH_READOUT.md`
- `research/QUANT_PATH_SIGNATURES_READOUT.md`
- `research/OCT_NOV_FEATURE_TRANSFER_READOUT.md`
- `research/ROLE_DYNAMICS_TRANSFER_READOUT.md`
- `research/RICH_FEATURE_DIVERSITY_AUDIT.md`
- `research/MINIMAL_ECONOMY_SCORE_READOUT.md`
- `research/DISAGREEMENT_RELIABILITY_READOUT.md`
- `research/EVENT_DELAY_HOSTILE_READOUT.md`
- `research/CROSS_ARRAY_TIME_ALIGNMENT_READOUT.md`
- `research/FRESH_NOV17_EXTERNAL_READOUT.md`
- `research/CAUSAL_STALE_FEED_HOSTILE_READOUT.md`
- `research/STRICT_NODATA_TRAIN_FORWARD_REPAIR_READOUT.md`
- `research/CAUSAL_FORECAST_FILTER_READOUT.md`
- `research/RICH_FEATURE_MODEL_READOUT.md`
- `research/BOOSTED_TREES_DIRECT_READOUT.md`
- `research/BOOSTED_NESTED_FAIRNESS_READOUT.md`
- `research/BOOSTED_TREES_HOSTILE_DECISION_20261118.md`
- `research/POST_RESULT_EQUAL_MATCH_SENSITIVITY_NOTE_20261118.md`

Reproduction boundaries: the historical original 500-game notebook can refetch frozen match IDs from OpenDota and has saved figures/outputs. Many later experiments depended on the author's historical raw-cache snapshot, isolated XGBoost/LightGBM packages and frozen research-branch scripts; those raw payloads are **not bundled** in the reviewer ZIP. Numeric readouts are retained with original GitHub source-branch histories and are not passed off as new independent employer scores. All results and judgments here are based on inspected repository evidence, not an external Vexil reviewer.

**Disclosure boundary:** the full applicant's `REPORT.pdf` contains AI/public-code assistance and candidate-estimated active hours. The candidate must attest the time spent and genuine ownership before external submission. AI-written code and review are not independent human peer review.
