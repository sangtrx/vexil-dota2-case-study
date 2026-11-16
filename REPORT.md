# Live Dota 2 Win Probability

**Truong Quang Sang · Vexil Capital · Senior Data Scientist take-home · 16 November 2026**

**Research question:** Does the same gold lead map to the same win probability at minute 10 and minute 30? I tested that question against the required gold-only baseline **and** a stronger additive gold + time control. The aim was a trustworthy probability, not the best-looking classifier.

**Result:** On 106 TEST games, M1's minute-weighted log loss was **0.5040 vs 0.5164** for M0 (Brier **0.1684 vs 0.1719**). These are point estimates: **both primary paired 95% intervals cross zero**, one game explains **54.9%** of the log-loss gain, and 30+ Brier is **0.00455 worse**. **Decision: M0 remains the reference; M1 is shadow-only.**

## 1. Study design and data integrity

**Why these 500 games:** Original 13 Nov collection paged `/proMatches` to an observed patch boundary near page 93 and fetched **250 eligible games per patch** from `/matches/{match_id}`. The ordered IDs were frozen in commit **3258a762** before held-out scoring. Today `Run all` refetches those same IDs, **not** the moving `/proMatches` feed; the original selection code and dated evidence are in **docs/DISCOVERY_PROVENANCE.md**. These March **21–26, 2026** games span only **5.26 days** and are not a representative sample of all leagues or future patches. Raw historical discovery pages were not archived.

The **18,292 minute-level rows are forecast opportunities, not independent outcomes**. At minute *t*, features use economy indices ≤*t* and events timestamped ≤`60*t`; winner, final totals and duration never enter the predictors. An **author-cache** future-deletion audit found zero differences across **all 18,292** feature snapshots (raw payloads not bundled). I imposed the **strict pre-terminal** condition `60*t < duration` and removed 12 exact-end rows (8 TRAIN, 3 VALIDATION, 1 TEST) **after the original TEST was opened**. The repaired scores are **not a second blind evaluation** of the TEST.

I split by start time, keeping entire series together: **291 TRAIN / 103 VALIDATION / 106 TEST** games (**10,675 / 3,781 / 3,836** minute rows). TRAIN includes 41 patch-60 games; VAL/TEST are both patch 60, **not an unseen-patch test**. At first VAL start, five TRAIN labels had not matured by an end-time proxy. Excluding them and refitting on **286 mature TRAIN games** still favored M1 on **reused VAL** (log loss **0.5202 vs 0.5329**). At TEST start, 0/103 VAL games remained unfinished, but the minimum proxy margin was just **143 seconds**. Actual live received-at timing remains unknown.

## 2. Model design and validation selection

I fixed four interpretable candidates before TEST and trained each (including imputation/scaling) on **291 TRAIN games only**, using L2 logistic regression with fixed C=1. The **103 VAL games selected M1**. Neither VAL nor TEST refit its coefficients. Without a draft/team prior, M1 has little early signal: **101/106** minute-zero TEST forecasts sit between 45% and 55%.

| Model | Minute-*t* inputs | Validation log loss | Brier |
| --- | --- | ---: | ---: |
| **M0 · Required baseline** | Gold difference | 0.5325 | 0.1811 |
| **M1 · Time value** | Gold, minute, gold × log(1 + minute/10) | **0.5197** | **0.1759** |
| M2 · Lead fragility | M1 + XP + available ≤5-minute gold/XP change | 0.5224 | 0.1778 |
| M3 · Objective conversion | M2 + timestamped towers, barracks, Roshan, kills | 0.5282 | 0.1806 |

M1 models a time-dependent mapping from a fixed gold lead to win probability. That is **not** a claim that gold becomes less discriminative late in a match. M2 and M3 added plausible state information but scored worse on validation; I kept the simpler M1 **for this sample**.

---

## 3. What the model actually learned

**An economic lead has context.** For a fixed **+2,000 Radiant gold**, M1 predicts **66.5%** at minute 10 and **59.4%** at minute 30. The implied **+7.1 pp** contrast has a **post-selection TRAIN-only** 95% bootstrap interval **[−1.1,+13.8] pp**, **crossing zero** (2,000 refits over 149 series and 22 singleton games). This is **not a causal effect** or confirmed incremental interaction. The +2k state appears in 60/291 TRAIN games at minute 10 and 87/214 still-playing games at 30; Figure 1 hides unsupported neighborhoods.

![Fitted model probabilities at fixed gold leads and time, masked outside observed training support.](docs/figures/time_value_scenarios.png)

*Figure 1. Conditional M1 curves at 0, ±3k and ±6k gold. The +2k contrast and bootstrap bands are not plotted. Not causal.*

**A concrete limitation of gold-only state.** Two patch-59 TRAIN games at minute 25 had gold **+1,901/+1,929** and XP **+6,964/+6,862**, so M1 gave nearly identical **60.3%/60.5%**. Yet their tower differentials were **0/−1** and Roshan kills **+2/−1**; original source recorded an Aegis pickup at 24:39 in game A (raw JSON not bundled). **Both Radiant teams won.** Figure 2 reconstructs this contrast from frozen TRAIN features. It illustrates **omitted game state**, *not* proven added predictive lift.

![Two fixed TRAIN matches with nearly identical gold and XP at minute 25, different objective control, and nearly identical M1 forecasts.](docs/figures/train_matched_state_aliasing.png)

*Figure 2. Descriptive TRAIN-only matches, selected historically on economic similarity; not chosen on TEST error. Objective deltas are timestamped inputs, not evidence of incremental predictive lift.*

## 4. What did not survive model selection

**The stronger null is the real check.** Against **gold + time without interaction**, M1's TRAIN-forward log-loss difference was **−0.0020** with a 70-series 95% interval **[−0.0148,+0.0090]**. I cannot claim that the interaction adds reliable information. Of **at least 38** historical research checks, **0/28** follow-ups cleared promotion gates on **reused validation**. One tempting item model (P20) scored **0.5145 vs 0.5197**, but only **1/3 pre-correction TRAIN** folds favored it, and its **pre-correction, 28-way adjusted** interval **[−0.0169,+0.0064]** included zero. A 200-game stage blend also failed. **No new model was promoted** (docs/EXPERIMENT_REGISTER.md).

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

**Stress tests did not settle the decision.** On **100 already completed** November 11–15 games (4,355 minutes, **56 series/singletons**, **85 games** from two leagues), M1−M0 log loss was **−0.0080**, CI **[−0.0284,+0.0087]**; Brier CI **[−0.0077,+0.0027]**; both contain zero. **Omitting one league reverses the gain**; **68 games overlap** earlier research. Patch 60 is not unseen. This is **not independent confirmation** (docs/FORWARD_100_STRESS.md).

The post-hoc **54-series** resample put log-loss CI at **[−0.0283,+0.0001]** and Brier CI at **[−0.0067,−0.0004]**; match-bootstrap Brier still reaches **+0.0002**. Results sit near the decision boundary. A single 55-row game explains **54.9%** of observed log-loss gain; excluding it for diagnosis cuts the gain from **0.0124 to 0.0057** and flips remaining 30+ log-loss difference to **+0.0314 (M1 worse)**. The official TEST and scores keep that game.

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
