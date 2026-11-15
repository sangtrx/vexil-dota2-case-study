# Vexil Dota 2 — Full experiment register

**Version lineage and scoring boundary (14 Nov 2026):** The 28 exploratory screens below preserve the historical 18,304-row run. A correctness review removed 12 exact-at-match-end observations (8 TRAIN, 3 VAL, 1 TEST). The corrected recruiter notebook was refitted on 18,292 rows and exports 3,836 TEST forecasts; the old 28 candidate models were NOT re-screened or promoted after this fix. Their validation scores remain historical research evidence.

**Repository experiment log, not a second applicant report.** The required deliverables are the executable 500-game notebook and the separately bounded PDF report (at most four pages). Research PRs contain experiments and integrity tests that are *not all executed by the submitted notebook*. Read these summaries as attempts and negative findings, not nine independent model improvements.

**Research lineage:** This curated repository contains the executable M0-M3 notebook and frozen forecast evidence. The historical development branches, timestamps and PR discussions remain in the [separate original research repository](https://github.com/sangtrx/vexil-dota2-win-probability), indexed in [HISTORY.md](../HISTORY.md). All 28 historical candidate scores predate the strict pre-terminal correction and were not rerun as new blind validation.

**Historical pre-correction study:** 500 professional OpenDota matches, 291 train / 103 validation / 106 held-out; selected M1 gold × game time over the required gold-only M0 on validation. Held-out log loss M0 **0.5163**, M1 **0.5039**, 95% paired M1-minus-M0 CI **[-0.0303,+0.0014]** (includes zero). Held-out Brier M0 0.1719, M1 0.1683, interval includes zero; late-game M1 Brier is worse only as an **unconfirmed point estimate**. These historical scores predate the 12-row end-boundary correction.

**Rules of interpretation:** Follow-up S1-S4, M4, P01-P28 and P20 item-model results were screened on **103 previously inspected validation matches**. Registering their hypotheses before *their own* finite screen does not undo earlier adaptive use of those labels. A later 200-match cohort was used for one locked stage-gate test, not to reselect 28 candidates. All scores in the 28-way table are *development outcomes*. No trading PnL, verified live packet-arrival timestamps or two-layer neural model is claimed.

## Complete PR inventory and disposition

| PR | Executed research / engineering scope | What survived |
|---|---|---|
| [#3](https://github.com/sangtrx/vexil-dota2-win-probability/pull/3) | OpenDota input, point-in-time snapshots, M0-M3 ablation, chronological series grouping, paired whole-match bootstrap | Original M1 selected |
| [#4](https://github.com/sangtrx/vexil-dota2-win-probability/pull/4) | Economic topology S1-S4, stability/familywise checks; separate fixed stage gate on a later 200-game cohort | No incremental structural model or gate promoted |
| [#5](https://github.com/sangtrx/vexil-dota2-win-probability/pull/5) | Recent Aegis, buyback, structural control mismatch, real matched cases, 900-game time/event integrity | M4 screen failed; real contrast is descriptive |
| [#6](https://github.com/sangtrx/vexil-dota2-win-probability/pull/6) | All 28 distinct specifications, 3 TRAIN-only folds, 103-game reused validation, simultaneous series-cluster bootstrap | **0/28** pass complete screen |
| [#7](https://github.com/sangtrx/vexil-dota2-win-probability/pull/7) | Proper-score parity, 20 dependent stability selections, 3,000 OOB resamples, four hosted private Kaggle CPU checks | Model search unstable; no new blind outcomes |
| [#8](https://github.com/sangtrx/vexil-dota2-win-probability/pull/8) | Timestamped item-purchase ablation integrated into main notebook as development-only | P20 point estimate improved; not promoted |
| [#9](https://github.com/sangtrx/vexil-dota2-win-probability/pull/9) | Adversarial clock/label/fault tests, five TRAIN-only rolling folds, CPU latency and domain-support limits | Input contracts strengthened; prediction unchanged |
| [#10](https://github.com/sangtrx/vexil-dota2-win-probability/pull/10) | Frozen source/prediction, clock audit, Colab/Kaggle parity, reproducible package | Release integrity, not a new predictor |
| [#11](https://github.com/sangtrx/vexil-dota2-win-probability/pull/11) | Clean recruiter-facing notebook, report, artifacts, portable QA, version pins | Actual submission candidate; not employer-submitted |

## Mechanisms with exact negative and positive *point* estimates

All rows below use the **same reused development validation**, reference M1 log loss **0.519346**, lower is better. These historical summaries are retained for audit; the original exploratory branch scripts are available in the research PRs listed above.

| Mechanism | Val. LL | Delta vs M1 | Why no promotion |
|---|---:|---:|---|
| S1: relative team economy | 0.518253 | -0.001093 | Less than precommitted practical -0.005 threshold |
| S2: top-two-player gold allocation | 0.517384 | -0.001962 | Worse in **3/3** earlier TRAIN folds; 53-series simultaneous 95% interval [-0.004100,+0.000176] crosses zero |
| S3: economic lead fragility | 0.524593 | +0.005248 | Better in **3/3** prior TRAIN folds, worse in later validation |
| S4: parsimonious joint state | 0.520049 | +0.000703 | More signals worsened validation |
| M4: recent Aegis, buyback and structures | 0.520596 | +0.001251 | 53-series CI [-0.004386,+0.006336] and development gate failure |
| P20: purchase counts for impactful items and Blink/BKB | **0.514098** | **-0.005248** | Best of 28 on reused validation, **1/3** prior TRAIN folds favorable, adjusted 28-way 95% CI [-0.016929,+0.006434] spans zero |
| P08: support/farming topology | 0.515840 | -0.003505 | **0/3** prior TRAIN folds favorable |
| P15: recent lethal fights | 0.517020 | -0.002326 | Insufficient practical gain/uncertainty after multiplicity |
| P22: raw hero-draft encoding | 1.581239 | +1.061894 | This 160-indicator, effectively underregularized model failed; not evidence all hero drafts are useless |

**Real matched-game example:** At minute 25, patch-59 TRAIN matches 8739246794 and 8739992397 have Radiant gold leads +1,901 and +1,929 (only **28** apart), and XP leads +6,964 and +6,862 (**102** apart). One has an Aegis pickup at 24:39; the other has no recent Aegis and a gold-versus-structural-control mismatch. Both Radiant teams ultimately won. The contrast demonstrates missing state representation, **not incremental predictive lift or causality**. Exact case construction and event timestamps.

## Full 28-hypothesis screen: every candidate and negative result

The cards linked in each row were registered before this finite experiment. All 103 validation games and 53 series had already been accessed in earlier development. A simultaneous approximate max-T correction covers the **28 comparisons within this screen only**, not every overlapping prior experiment. Favorable fold counts come from three separate earlier TRAIN-only chronological checks. MAX-T upper = upper 95% interval for candidate-minus-M1 log loss; positive means insufficient evidence. Every candidate failed the joint promotion gate.

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


**All 28 have archived scores; zero were selected.** P20 is the best reused-validation point estimate, yet unstable across earlier time. The high-dimensional P22 hero model was severely underregularized relative to 291 independent TRAIN games, and says nothing decisive about *all* hero drafting architectures. Full outputs, Brier and five-phase scores.

## One locked stage gate on a separate third 200-game cohort

A fixed, non-learned mixture uses M1 until minute 10, transitions toward M0 in 11-19 and uses M0 after minute 20. The third chronological 200-game cohort (30 March-2 April 2026; 6,827 minute rows, 97 series-or-singleton groups) was frozen and scored once for this gate. It is **not part of the assignment's original 500 games**.

| Metric on separate 200 | M0 | M1 | Stage gate |
|---|---:|---:|---:|
| Log loss | 0.545075 | **0.533704** | 0.539850 |
| Brier | 0.18647 | **0.18242** | 0.18430 |

The gate-minus-M1 log-loss difference **+0.006146** has simultaneous series-cluster 95% CI **[-0.002836,+0.015127]**. It failed its preregistered improvement requirement against **both** M0 and M1; no thresholds were retuned on the consumed cohort. A direct M1-minus-M0 comparison calculated **after** the gate evaluation is *secondary and descriptive*, not registered familywise confirmation. The phase blend departs from M1 only **after minute 10**; its observed aggregate loss disadvantage does not identify the 30+ effect. See the archived source and stage-gate receipts in [original research PR #4](https://github.com/sangtrx/vexil-dota2-win-probability/pull/4).

## Robustness evidence (not additional independent model accuracy)

- A 900-game retrospective parse audit checked **9,000 player histories and 32,106 clock/gold indices**; 1,200 Roshan-to-Aegis event relationships and 876 first-blood summaries had internally consistent event clocks. This is parser-level consistency, **not live arrival certification**. PR #5.
- PR #9 ran **12,063 deterministic adversarial assertions under each of two seeds** (24,126 case evaluations), testing future-poisoning, exact timestamp boundaries, malformed values, duplicated player slots, mocked network faults and bootstrap arithmetic. Two hosted private Kaggle QA kernels verified the 12,063-case stream and 10,683 original TRAIN snapshots. These are tests, not professional matches; see the [original robustness review PR #9](https://github.com/sangtrx/vexil-dota2-win-probability/pull/9).
- Five additional embargoed TRAIN-only rolling-origin folds gave M1 better minute-weighted loss than M0 in **2/5**; P20 beat M1 in **2/5**. These reuse development labels, not a prospective test.
- PR #7 re-evaluated proper scores and dependence: a preferred candidate was worse than M1 in **10/20 dependent directional selections** and **51.47% of 3,000 series OOB selections**; six originally proposed time buckets had overlaps at four boundaries and were **not six genuinely chronological folds**. At least 38 known overlapping trials were recorded, an incomplete search-history estimate. **Four private Kaggle CPU verification notebooks** achieved matching fixed-input arithmetic but no fresh outcome labels. Selection-stability findings.
- Warm, local single-snapshot CPU inference took p50 **1.74 ms**, p95 **2.09 ms**, excluding all actual source/network latency. M1's fitted gold coefficient reverses sign analytically at approximately minute **98.36**, well outside the TRAIN support (only one game still present at minute 85); a future system should abstain outside validated range. Operational model card.

## Prior art and precise novelty boundary

The **specific feature hypotheses and their falsification exercises** are original to this assessment; **time-varying Dota win prediction is not a globally new research problem**. Bapela, Ranchod and Ingram, *Real-time Prediction of Dota 2 Match Outcomes using In-game Chat Logs* (AIIDE 2025; [DOI](https://doi.org/10.1609/aiide.v21i1.36822)), already compare LSTM/DistilBERT with logistic regression on a different, ranked-match chat/event dataset. *DotA 2 Match Outcome Prediction System Using Decision Tree Ensemble Algorithms* (2025; [DOI](https://doi.org/10.3390/bdcc9120302)) already investigates temporal phases, hero/item features and interpretable tree-based approaches using broader data sources. Neither paper is a numerical apples-to-apples comparator to our small professional-match, restricted-OpenDota cohort.

The evaluation emphasis follows established probabilistic forecasting practice: Waghmare and Ziegel, *Proper Scoring Rules for Estimation and Forecast Evaluation* (2026; [DOI](https://doi.org/10.1146/annurev-statistics-042424-050626)), and Gneiting and Raftery, *Strictly Proper Scoring Rules, Prediction, and Estimation* (2007; [DOI](https://doi.org/10.1198/016214506000001437)). These are **methods context**, not code reused or newly discovered theory. The limited **research contribution here** is a well-documented, point-in-time, series-aware *replication and failure analysis*: what additional economic/strategic signals did **not** reliably add under a finite sample. It is **not** a new estimator, causal game-mechanic identification, or publishable state-of-the-art claim.

The **pre-correction** 106-game TEST (3,837 minute rows) contained a descriptive 10-equal-width-bin M1 ECE **0.0748** versus M0 **0.0897** (M1−M0 **−0.0148**). An explicitly *post-hoc* 10,000-repetition, 54-series paired cluster bootstrap gave **[−0.0205,+0.0020]**, including zero. These are bin-sensitive, correlated minute-level summaries; they are **not** a tuning target or proof of prospective calibration.

## Final selection and reproducibility boundary

**M0 remains the required baseline; M1 remains the original chosen challenger.** The submitted notebook runs M0-M3 and the explicitly development-only item P20 check, not S1-S4, M4, the other 27 alternatives, later 200-game cohorts or extended QA kernels. Those are separate, unmerged **research PRs**, with source/results linked above. This ledger keeps negative trials visible without presenting previously consumed labels as newly independent evidence, or turning a descriptive difference into a causal, live-data or betting claim.
