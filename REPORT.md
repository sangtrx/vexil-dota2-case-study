# Live Dota 2 Win Probability

**Truong Quang Sang · Vexil Capital · Senior Data Scientist take-home · 16 November 2026**

**Research question:** Does the same gold lead map to the same win probability at minute 10 and minute 30? I compared the required gold-only logistic baseline with a time-dependent challenger and tested the apparent score gain against match dependence and late-game uncertainty.

**Result:** Across 106 TEST games, M1 improved minute-weighted log loss **0.5164 → 0.5040** and Brier **0.1719 → 0.1684** as point estimates, but **both primary paired 95% intervals cross zero**. One 55-row match supplies **54.9%** of the log-loss gain; M1's Brier after minute 30 is **0.00455 worse** with wide uncertainty. **Decision: keep M0 as reference; shadow-test M1.**

## 1. Study design and data integrity

I collected **500 parsed professional OpenDota matches**, 250 from patch 59 and 250 from patch 60, using OpenDota `/proMatches` and `/matches/{match_id}`. They cover **21–26 March 2026**, a short **5.26-day** patch-transition window. The sample is narrow, and requiring parsed records may bias the league and game mix. It cannot represent later patches or all leagues.

The **18,292 minute-level rows are forecast opportunities, not independent game outcomes**. For a forecast at game minute *t*, economy arrays use indices at most *t*; event features use timestamps no later than `60*t`. A later **author-cache** audit compared **all 18,292** snapshots against future-truncated payloads, with zero feature differences; player clocks also match team economy (raw JSON not bundled). Winner, post-game totals, future events and final duration do not enter features. The corrected notebook imposes the **strict pre-terminal** condition `60*t < duration`: an audit found and removed 12 end-boundary rows (8 TRAIN, 3 VALIDATION, 1 TEST). This was a correction **after the original TEST was opened**, not a second blind evaluation.

Matches are ordered chronologically and entire professional series stay in one partition: **291 TRAIN / 103 VALIDATION / 106 TEST**, with **10,675 / 3,781 / 3,836** minute rows. TRAIN contains 41 patch-60 games; both later partitions are entirely patch 60. This tests later games within the observed environment, **not generalization to an unseen patch**. Five TRAIN labels were not mature at first VALIDATION start (at most 1,606 seconds by end-time proxy). Refitting all four fixed models on **286 mature TRAIN games** still selects M1 on **reused VAL** (log loss **0.5202** versus M0 **0.5329**). At the VAL→TEST boundary, **0/103 VAL games** were unfinished by the same proxy, but the margin was only **143 seconds**. Neither audit establishes live received-at times or creates a new TEST.

## 2. Model design and validation selection

I fixed four interpretable candidates before the first held-out comparison. All models, including imputation/scaling, were fit on **291 TRAIN games only** with L2 logistic regression (C=1, fixed rather than tuned). The **103 validation games selected M1**; neither validation nor TEST was used for refitting. At minute zero, **101/106** TEST M1 forecasts are between 45% and 55%: without a pre-game team/draft-strength prior, this model has little opening signal.

| Model | Minute-*t* inputs | Validation log loss | Brier |
| --- | --- | ---: | ---: |
| **M0 · Required baseline** | Gold difference | 0.5325 | 0.1811 |
| **M1 · Time value** | Gold, minute, gold × log(1 + minute/10) | **0.5197** | **0.1759** |
| M2 · Lead fragility | M1 + XP + available ≤5-minute gold/XP change | 0.5224 | 0.1778 |
| M3 · Objective conversion | M2 + timestamped towers, barracks, Roshan, kills | 0.5282 | 0.1806 |

M1 models a time-dependent mapping from a fixed gold lead to win probability. That is **not** a claim that gold becomes less discriminative late in a match. M2 and M3 added plausible state information but scored worse on validation; I kept the simpler M1 **for this sample**.

---

## 3. What the model actually learned

At fixed **+2,000 Radiant gold**, M1 predicts **66.5%** at minute 10 versus **59.4%** at minute 30. A **post-selection TRAIN-only** bootstrap (2,000 refits, 149 series + 22 singleton games) gives a **+7.1 pp** contrast, 95% interval **[−1.1,+13.8] pp** crossing zero. This combines time and interaction, **not a causal effect**. At minutes 10/30, 60/291 and 87/214 TRAIN games had ≥+2k lead. Figure 1 masks conditions with fewer than ten nearby TRAIN games.

![Fitted model probabilities at fixed gold leads and time, masked outside observed training support.](docs/figures/time_value_scenarios.png)

*Figure 1. Conditional M1 curves at 0, ±3k and ±6k gold. The +2k contrast and bootstrap bands are not plotted. Not causal.*

**A matched TRAIN counterexample to gold as complete game state.** At minute 25, two patch-59 games have Radiant gold leads **+1,901 vs +1,929** and XP leads **+6,964 vs +6,862**. M1 assigns **60.3% vs 60.5%**, although the observed tower deltas are **0 vs −1** and Roshan-kill deltas **+2 vs −1**. The source-frozen TRAIN feature archive reproduces these values. An Aegis pickup at 24:39 is recorded in the original raw payload for game A (not bundled). **Both Radiant teams eventually won.** Similar economy can conceal different objective states; this comparison does **not** establish that objective features predict better.

![Two fixed TRAIN matches with nearly identical gold and XP at minute 25, different objective control, and nearly identical M1 forecasts.](docs/figures/train_matched_state_aliasing.png)

*Figure 2. Descriptive TRAIN-only matches, selected historically on economic similarity; not chosen on TEST error. Objective deltas are timestamped inputs, not evidence of incremental predictive lift.*

## 4. What did not survive model selection

After four fixed models, **0/28** follow-ups passed gates on **reused validation** (S2 economy, M4 objectives, P20 items; **at least 38** research checks total). P20 scored **0.5145** versus M1 **0.5197**, but only **1/3 pre-correction TRAIN** folds favored it; the **pre-correction, 28-way adjusted** CI **[−0.0169,+0.0064]** crossed zero. More importantly, M1 did not reliably beat the additive **gold + time without interaction** null in TRAIN-forward folds (ΔLL **−0.0020**, 70-series CI **[−0.0148,+0.0090]**). A 200-game stage blend failed. **No new model was promoted** (docs/EXPERIMENT_REGISTER.md).

---

## 5. Held-out forecast quality and uncertainty

The target is proper loss **per admissible minute-level forecast opportunity**; longer games receive more weight. The notebook reports **individual model 95% CIs** and the paired M1−M0 CI for **each phase and metric**. All use **whole-match bootstraps** (2,000 draws), not independent minute rows. Common-series dependence may widen uncertainty; the table below shows paired differences.

| Phase (games) | Log loss M0 → M1 | Difference 95% CI | Brier M0 → M1 | Difference 95% CI |
| --- | --- | --- | --- | --- |
| **All (106)** | 0.5164 → **0.5040** | **[−0.0304,+0.0014]** | 0.1719 → **0.1684** | **[−0.0069,+0.0002]** |
| 0–9 (106) | 0.6651 → 0.6506 | [−0.0252,−0.0030] | 0.2362 → 0.2295 | [−0.0117,−0.0014] |
| 10–19 (106) | 0.5695 → 0.5499 | [−0.0343,−0.0031] | 0.1927 → 0.1853 | [−0.0131,−0.0013] |
| 20–29 (105) | 0.4131 → 0.4065 | [−0.0111,−0.0015] | 0.1312 → 0.1293 | [−0.0036,−0.0001] |
| **30+ (79)** | 0.3623 → 0.3555 | [−0.0947,+0.0415] | **0.1028 → 0.1074 (worse)** | [−0.0037,+0.0109] |

**No-skill scale:** A constant probability equal to the TRAIN game-win rate (149/291 = 0.5120) gives TEST log loss **0.6884** and Brier **0.2476** on these same 3,836 minute forecasts. Both fitted models beat that reference, although M1's gain over M0 remains uncertain.

The early-phase differences favor M1 **without multiplicity adjustment**. The 30+ subset selects longer games: M1's Brier point estimate is **about 0.00455 worse** (unrounded scores), but its paired interval **[−0.0037,+0.0109]** includes zero. The correct conclusion is *late-game uncertainty*, not a confirmed failure. Equal-match-weighted log loss was 0.5097 (M0) versus 0.4952 (M1); removing the final two admissible minutes gave 0.5386 versus 0.5250, with no refit.

![Phase-specific ECE and Brier differences from fixed TEST forecasts.](docs/figures/phase_error_audit.png)

*Figure 3. Descriptive phase Brier/ECE on the original TEST. Rows from one game share a label; bars are not independent uncertainty estimates.*

**Later-game diagnostic, not independent confirmation:** Fixed M0/M1 were scored on **100 already completed** November 11–15 matches (4,355 minutes; **56 series/singletons**; 85 games from two leagues). M1−M0 log loss **−0.0080**, grouped CI **[−0.0284,+0.0087]**; Brier CI **[−0.0077,+0.0027]**: both contain zero. Omitting one league reverses the gain (*diagnosis only*); **68 games overlap** a previously scored 120-game study. The protocol preceded this run's detail fetch, **not the games themselves**. Patch 60 is not unseen. See docs/FORWARD_100_STRESS.md.

A post-hoc **54-series** bootstrap gives M1−M0 log-loss CI **[−0.0283,+0.0001]** and Brier CI **[−0.0067,−0.0004]**. The primary match-bootstrap Brier upper bound was **+0.0002**: these near-zero endpoints make inference **borderline and resampling-sensitive**, not a second independent confirmation.

**Influence check:** one 55-minute game (8744971178) accounts for **54.9%** of the sample's M1 log-loss gain. Removing it *for diagnosis only* reduces the observed gain from about 0.0124 to 0.0057. Excluding that game's 25 late-minute rows changes the remaining late-phase log-loss difference to **+0.0314 (M1 worse)**. I do not delete the game from the official metrics.

---

## 6. Calibration is a separate release risk

M1 predicts **0.5174** on used **VALIDATION** versus **0.4874** winners; on inspected **TEST** (63/106 game winners), **0.5429** versus **0.6045**. Forecast-minus-outcome bias is **+0.0300** (post-hoc **53-series** CI **[−0.0436,+0.1001]**) versus **−0.0617** (**54-series** CI **[−0.1410,+0.0250]**). Neither interval proves drift; M0 has similar bias. TEST ECE10 is **0.0895 (M0)** versus **0.0750 (M1)**, difference CI **[−0.0203,+0.0020]**; late-30+ ECE worsens **0.0559 → 0.0680**. A TRAIN-only offset improved reused VAL log loss **0.5197→0.5186**, but worsened ECE10 **0.0492→0.0561**: **HOLD**. Fixed-bin grouped uncertainty remains post-hoc (docs/CALIBRATION_FIXED_BIN_GROUPED_CI.md). **No TEST recalibration** (docs/CALIBRATION_BIAS_READOUT.md).

![Held-out fixed-bin reliability curves, minute rows not independent.](docs/figures/heldout_reliability.png)

*Figure 4. Calibration diagnostic from already inspected TEST, not a tuning target.*

## 7. Decision I would make in production

**Keep M0 as the reference; run M1 in shadow mode.** M1's aggregate TEST and November point scores are favorable, but **neither paired confidence interval establishes superiority**. League dependence, late-game Brier instability and unknown feed-arrival timing remain. I would size and preregister a fresh multi-league series cohort before a new decision. A future promotion gate is at least **0.005 lower log loss**, supported by clustered uncertainty and no material overall or 30+ Brier regression; this is **not** a retrospective significance threshold.

A real feed would need the match/model version, minute, **event time, received-at time, feature watermark and completeness**. The archived API cannot certify live data arrival or profitable betting without executable odds, fills and costs.

## 8. Reproducibility and assistance

Original research commits and branches are retained; PR discussions remain private (**no reviewer access granted**). Model **e49e853** and cohort **3258a762** predate TEST. The original 14-cell source is archived. The current notebook executes **16/16** cells, including two *post-TEST, non-selecting* checks of all **18,292 PIT snapshots**, frozen scores, calibration and the additive gold+time null. BigLinux's 500-game offline replay reproduced all **3,836 TEST predictions and three original figures byte-for-byte** (docs/REVIEWER_APPENDIX_FRESH_KERNEL_RECEIPT.json). **Fresh 16-cell Colab CPU Run All:** 510 API calls, 500 games, zero errors, matching six-decimal TEST scores and scientific/input hashes. **Cloud CSV byte parity remains unverified** (docs/COLAB_16CELL_RUN_RECEIPT.json); historical 14-cell cloud receipt retained.

**Time spent:** Approximately **10 hours of active work** (candidate estimate), excluding unattended AI, API and cloud execution.

**Assistance disclosure:** ChatGPT Web generated and revised much of the notebook code, tests and report under my research direction; **Claude Sonnet and Fable AI conducted read-only critiques**. BigLinux/Colab scripts checked numeric outputs; I retained negative results. **Public code:** Standard open-source NumPy, pandas, scikit-learn, Matplotlib and Requests, with versions pinned in requirements.txt. **No third-party Dota predictor was copied. AI reviews are not independent human peer review.**
