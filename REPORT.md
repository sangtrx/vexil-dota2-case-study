# Live Dota 2 Win Probability

**Truong Quang Sang · Vexil Capital · Senior Data Scientist take-home · 19 November 2026**

**Decision.** I kept the gold-only logistic baseline (M0) as the reference and M1 in shadow mode. On 106 held-out games, M1 reduced minute-weighted log loss from **0.5164 to 0.5040** and Brier score from **0.1719 to 0.1684**. Both primary paired 95% confidence intervals include zero. That point-estimate improvement is not enough to promote M1.

**Question.** Does adding game time improve the probability assigned to a given gold lead? I compared four models with a chronological, series-disjoint split and tested the interaction against a simpler additive gold + time model.

## 1. Data and prediction-time validity

The cohort contains **500 professional OpenDota matches**, 250 on each side of a patch change, played **21–26 March 2026**. The original `/proMatches` discovery and frozen IDs are documented in **docs/DISCOVERY_PROVENANCE.md**. Raw historical discovery pages were not archived. This is a narrow five-day sample, not a representative cross-league study.

I split entire series by match start time: **291 TRAIN / 103 VALIDATION / 106 TEST** games, or **10,675 / 3,781 / 3,836** admissible minute forecasts. TRAIN already contains **41 patch-60 games**; VALIDATION and TEST are also patch 60, so this is not a test on an unseen patch.

Each forecast uses economy snapshots through minute *t* and events timestamped at or before 60*t. The strict pre-terminal rule is `60*t < duration`. A future-deletion check found no feature changes across **18,292** snapshots in the original author-controlled raw cache (not bundled). After TEST had first been inspected, I removed **12 exact-terminal rows** (8 TRAIN, 3 VALIDATION, 1 TEST). **The corrected TEST is not a fresh blind holdout.**

Five TRAIN labels were incomplete at the first VALIDATION start under a **game-duration end proxy**. A sensitivity using **286 mature TRAIN games** retained M1, but **headline TEST scores use the original 291-game TRAIN fit**. The **143 seconds** between estimated last VAL end and first TEST start is **not a verified label-arrival margin**. Under hypothetical +60-minute delay, only 277 TRAIN and 96 VAL outcomes qualify; M2 narrowly beats M1 on reused mature VAL (**0.517823 vs 0.518090** log loss). No model or TEST score was changed (docs/REVIEWER_SCIENTIFIC_LIMITS.md).

## 2. Models and selection

I used L2 logistic regression (C=1), fitting imputation and scaling on TRAIN only. The **103 VALIDATION games selected M1** by log loss. However, the terminal-row correction occurred after initial TEST inspection and required refitting on corrected TRAIN; this remains a retrospective comparison, **not a newly blind TEST**.

| Model | Minute-*t* information | VAL log loss | Brier |
| --- | --- | ---: | ---: |
| M0 · Required baseline | Gold lead | 0.5325 | 0.1811 |
| M1 · Time-aware | Gold, minute, gold × log(1 + minute/10) | **0.5197** | **0.1759** |
| M2 · Lead dynamics | M1 + XP and available recent gold/XP changes | 0.5224 | 0.1778 |
| M3 · Objectives | M2 + timestamped towers, barracks, Roshan and kills | 0.5282 | 0.1806 |

XP and objective features added complexity without lowering validation loss, so I kept M1. The full register of later, non-promoted experiments is in **docs/EXPERIMENT_REGISTER.md**.

**Additional models:** On reused TRAIN-forward folds, Q1 scored **0.605963** against M1's **0.612086**, but its uncertainty includes zero. XGB3 (**0.615597**) and LGB3 (**0.616196**) did not beat Q1. Tuning, transfer and feed-delay checks gave me no reason to change the model decision. These are **post-result TRAIN/replay studies, not a new held-out TEST**; see docs/CREATIVE_FEATURE_EXPERIMENT_ATLAS.md.

---

## 3. Does the interaction earn its complexity?

Figure 1 shows M1's fitted probabilities at fixed gold leads. The curves are displayed only where the original TRAIN data support the corresponding game states. They describe the fitted function, not an effect caused by time.

![Fitted gold-time scenarios within observed training support.](docs/figures/time_value_scenarios.png)

*Figure 1. M1 scenarios for 0, ±3k and ±6k gold lead. Values outside observed TRAIN support are masked.*

The stronger comparison is **M1 versus additive gold + time without the interaction**. Across four chronological TRAIN-forward blocks (137 evaluation games, 70 series/singletons), M1 improved log loss in only **1/4 folds**. The pooled M1−additive log-loss difference was **−0.0020**, with a 95% grouped interval of **[−0.0148,+0.0090]**. Its pooled Brier difference was **+0.000405 (worse)**, interval **[−0.003059,+0.003857]**. There is **no confirmed incremental benefit** from the interaction. This post-result TRAIN-only check was run after the fitted result was examined; it used TRAIN only, not an additional blind TEST.

![Four TRAIN-forward folds comparing interaction and additive controls.](docs/figures/train_interaction_vs_additive_null.png)

*Figure 2. M1 minus additive gold + time log loss; negative favors M1. Pooled interval covers zero.*

The separate TRAIN-only leader-state comparison is descriptive: among games with an absolute 2–4k gold lead, leaders eventually won **66/82** at 10 minutes and **11/25** at 30 minutes, but **only 7 matches occur in both groups**. Different surviving games, not a measured within-game time effect (docs/TRAIN_LEADER_STATE_EMPIRICAL.md).

### Creative feature and model search (full inventory: `docs/CREATIVE_FEATURE_EXPERIMENT_ATLAS.md`)

**28 adaptive screens:** I tested time-shape, team-economy allocation, gold shocks, towers, Roshan/Aegis, buyback, Blink/BKB item completion and hero draft. Best historical *reused-VAL* point estimate was **P20** (LL **0.514098** vs old M1 **0.519346**), but the adjusted 28-way interval includes zero; **0/28 promoted**.

**81 engineered features:** 19 gold dynamics, 13 XP, 19 player allocation, 17 objectives and 13 interactions. An event-team parsing bug made two Roshan columns zero in the original supplementary study; one other column was duplicated. The corrected parser is evaluated separately on TRAIN, without revisiting TEST.

---

## 4. Held-out forecast quality

I score **each admissible minute forecast**, so longer games receive more weight. The paired intervals resample whole matches (2,000 draws), not individual minutes. The notebook includes model-specific intervals as well as differences.

| Phase (games) | Log loss M0 → M1 | Δ 95% CI | Brier M0 → M1 | Δ 95% CI |
| --- | --- | --- | --- | --- |
| **All (106)** | 0.5164 → **0.5040** | **[−0.0304,+0.0014]** | 0.1719 → **0.1684** | **[−0.0069,+0.0002]** |
| 0–9 (106) | 0.6651 → 0.6506 | [−0.0252,−0.0030] | 0.2362 → 0.2295 | [−0.0117,−0.0014] |
| 10–19 (106) | 0.5695 → 0.5499 | [−0.0343,−0.0031] | 0.1927 → 0.1853 | [−0.0131,−0.0013] |
| 20–29 (105) | 0.4131 → 0.4065 | [−0.0111,−0.0015] | 0.1312 → 0.1293 | [−0.0036,−0.0001] |
| **30+ (79)** | 0.3623 → 0.3555 | [−0.0947,+0.0415] | **0.1028 → 0.1074 (worse)** | [−0.0037,+0.0109] |

A constant TRAIN-win-rate forecast gives TEST log loss **0.6884** and Brier **0.2476**. Both trained models beat it. The phase comparisons are exploratory and unadjusted; they do not establish eight separate wins. **At minute 30+, M1's Brier score is about 0.00455 worse.** A separate, post-result **137-game TRAIN-forward** comparison finds M0 vs M1 log loss **0.612312 vs 0.612086** (difference only −0.000226) and Brier **0.211828 vs 0.212744 (M1 worse)**. Its four smaller rolling-prefix fits and mixed patches differ from full-fit VAL (M0 LL 0.5325) and TEST (0.5164), so these levels do not establish drift. Thus the TEST point improvement was not stable across development folds. Conversely, TRAIN-forward minute-30+ Brier **favored M1 (0.183109 vs M0 0.184996)**, opposite to the TEST late30 Brier point difference: even the phase-specific direction is unstable.

![Phase-specific calibration and Brier diagnostics.](docs/figures/phase_error_audit.png)

*Figure 3. Descriptive phase results from inspected TEST forecasts; minute rows share match outcomes.*

One 55-minute match (8744971178) accounts for **54.9%** of M1's aggregate log-loss gain. Removing it for *influence diagnosis only* reduces the overall gain from 0.0124 to 0.0057; in the minute-30+ slice, M1−M0 log loss **flips from −0.00678 to +0.03139** (719 vs 694 forecasts), and Brier worsens from **+0.00455 to +0.00748**. No model was retuned on this observation. The exact calculation is preserved in docs/ERROR_AUDIT_RECEIPT.json and recomputed by the offline error-audit test.

Whole-match bootstrap CIs include zero for both scores. In a **post-hoc 54-series bootstrap**, log-loss CI **[−0.02828,+0.00012]** straddles zero, while Brier CI **[−0.00670,−0.00038]** narrowly excludes it. Resampling unit and near-zero endpoints change the inference; shared teams/leagues remain. A separate 100-game November check is inconclusive: **both intervals contain zero**, removing one league reverses the gain, and **68 games overlap** earlier research (docs/SERIES_CI_RECEIPT.json; docs/FORWARD_100_STRESS.md).

---

## 5. Calibration and deployment decision

On inspected TEST, M1's ECE-10 was **0.0750**, compared with **0.0895** for M0; the grouped difference interval **[−0.0203,+0.0020]** contains zero. In the 30+ phase, ECE worsened from **0.0559 to 0.0680**. M1's average TEST forecast was **0.5429**, versus a **minute-weighted** observed win frequency of **0.6045**; the distinct **game-weighted** win fraction is **63/106 Radiant-winning games = 0.5943**. These are different estimands: the observed gap is not a claim of persistent drift or evidence supporting TEST-based recalibration.

![Held-out reliability diagram.](docs/figures/heldout_reliability.png)

*Figure 4. Reliability curves from the inspected TEST. Repeated minute rows are not independent games.*

**Recommendation:** Keep M0 as the reference and run M1 in shadow mode. A new promotion decision should use a *precommitted*, multi-league series cohort and require at least **0.005 lower log loss** with clustered uncertainty excluding no gain, alongside no material regression in overall or 30+ Brier. That is a future decision rule, not a threshold retrofitted to these scores.

For an actual live service I would log match/model version, minute, event timestamp, `received_at`, feature watermark and completeness. These historical API records cannot establish packet availability at decision time, and this study does not estimate betting profitability.

## 6. Reproduction and assistance

The deliverable contains **one executed 16-code-cell notebook**: 14 core study cells (including edits and diagnostics after initial TEST inspection) and two appended reviewer QA cells. A pinned **Python 3.12** local replay reproduces the 3,836 TEST forecasts and original figures byte-for-byte from the author-controlled cache (docs/REVIEWER_APPENDIX_FRESH_KERNEL_RECEIPT.json). The earlier 16-cell Colab Run All reproduced metrics to six decimals on its preinstalled stack (docs/COLAB_16CELL_RUN_RECEIPT.json). The recorded Colab run used an earlier 16-cell notebook revision; a new exact-version cloud run has **not** been verified, although the shipped notebook's saved outputs and source-frozen local replay were checked. The notebook's post-inspection appendix is diagnostic and does not create a new blind TEST. Original research commits and branches are retained; PR discussions remain private.

**Time spent:** Approximately **10 hours of active work** on the study design, reviewing model results and failure cases, and checking the final submission. Unattended runs are excluded.

**Assistance disclosure:** I directed the research and took responsibility for the model choice, evaluation and final conclusions. ChatGPT Web drafted and revised much of the notebook code, tests and report. Claude Sonnet and Fable AI conducted read-only critiques; their feedback led to further source and uncertainty checks. AI reviews are not independent human peer review. **Public code/tools:** The notebook uses NumPy, pandas, SciPy, scikit-learn, Matplotlib, Requests, tqdm and Jupyter Notebook, with top-level versions pinned in requirements.txt. Separate research used XGBoost 3.4.1, LightGBM 4.7.0 and Narwhals 2.21.2; these are **not notebook dependencies** (versions in research/BOOSTED_TREES_DIRECT_READOUT.md). **No third-party Dota predictor was copied.**
