# Live Dota 2 Win Probability

**Truong Quang Sang · Vexil Capital · Senior Data Scientist take-home · 14 November 2026**

**Research question:** Does the same +2,000 gold lead carry the same information at minute 10 and minute 30? I test the **time value of an economic lead** using a simple gold-by-time interaction, then challenge it with richer game-state features, temporal checks and error analysis.

**Result:** On 106 held-out games, M1 reduces log loss **0.5164 → 0.5040** and Brier **0.1719 → 0.1684** versus gold-only M0. **Both primary paired 95% intervals include zero.** One 55-row game accounts for **54.9% of the total log-loss improvement**. I would shadow-test M1, not replace M0 yet.

## Data, information cutoff and validation design

I retrieved **500 parsed professional matches** using only the permitted OpenDota endpoints: **250 on patch 59 and 250 on patch 60**, selected around the March 2026 patch boundary without filtering by winner. Discovery used 705 API calls (49 cache hits); 46 candidate games were outside the two target patches or ineligible. These games cover **21–26 March 2026, just 5.26 days**. This is a deliberately concentrated patch-transition cohort, **not** representative of November games.

There are **18,292 admissible minute-level forecasts, not 18,292 independent outcomes**. At minute *t*, gold/XP use array indices no later than *t*, while objective and kill events use timestamps ≤ 60*t* seconds, including pre-horn events. All ten parsed player clocks align with aggregate team economy. Final kills, total net worth, duration and the winner do not enter model features. A strict pre-terminal rule now excludes snapshots at or after game end: **12 original end-boundary rows (8 TRAIN, 3 VALIDATION, 1 TEST)** were removed and the 500-game notebook was re-executed. The notebook also includes prefix truncation and future-field poisoning; the earlier full-cohort audit passed **3,342 historical point-in-time probes**. These establish a retrospective game-clock cutoff, **not** authenticated live-feed arrival times.

I split games by start time without dividing a professional series: **291 TRAIN / 103 VALIDATION / 106 TEST games** (**10,675 / 3,781 / 3,836** minute rows). TRAIN contains **250 patch-59 + 41 patch-60** games; validation/test are entirely patch 60. It is a later-match test, **not an unseen-patch experiment**. Five training games may have finished after validation began (maximum estimated overlap 1,606 seconds); excluding them from training in a development-only sensitivity still selects M1. Historical feed receipt and result-availability times remain unverified.

## Model, time-value hypothesis and falsification

All models use training-only imputation/scaling and fixed **L2 logistic regression, C = 1**. The original candidate family was fixed before the primary held-out evaluation; validation log loss selects M1.

| Model | Information available at minute t | Validation log loss | Brier |
|---|---|---:|---:|
| M0 · required baseline | Current gold lead only | 0.5325 | 0.1811 |
| **M1 · time value** | Gold + minute + gold × log(1 + minute/10) | **0.5197** | **0.1759** |
| M2 · lead fragility | M1 + XP + trailing five-minute gold/XP changes | 0.5224 | 0.1778 |
| M3 · objective conversion | M2 + timestamped towers, barracks, Roshan, kills | 0.5282 | 0.1806 |

**More features did not automatically help.** Relative to selected M1, M2 and M3 worsened validation log loss by **+0.0027** and **+0.0085**. A separate post-hoc TRAIN-only forward audit found M1 better than M0 in only **one of three** earlier folds (pooled M1−M0 difference **+0.0012**, worse). I treat the interaction as a testable hypothesis, not a verified mechanism or stable population effect.

**What the fitted interaction means:** holding Radiant's lead at **+2,000 gold**, M1 predicts **66.5%** win probability at minute 10 versus **59.4%** at minute 30. The original training sample supports these lead values at both minutes (at least +2k in 60/291 minute-10 games and 87/214 minute-30 games). Figure 1 masks unsupported regions. This conditional contrast is **not** evidence that adding gold or delaying the game causes the change.

![Figure 1. Time-value at fixed gold leads, masked outside measured training support.](docs/figures/time_value_scenarios.png)

*Figure 1. Conditional model predictions, shown only with at least 10 distinct nearby TRAIN games (gold ±1k, minute ±2); not game trajectories.*

I explored economic concentration (S2), strategic options (M4), timestamped item completions (P20), draft/nonlinear specifications and phase-dependent alternatives. Across **at least 38 overlapping development trials**, including a **28-candidate screen** on previously reused validation games, **none of the 28 passed its recorded promotion gates**. In the *corrected notebook*, P20 scored **0.5145** versus M1 **0.5197** on **reused validation**. Separately, the *earlier, pre-correction* screen found P20 better than M1 in only **one of three** TRAIN-forward folds, and its **28-way adjusted** 95% interval **[−0.0169,+0.0064]** contains zero. These mixed-version findings are exploratory, **not** an independent held-out test or grounds for replacing M1.

A phase-blend candidate failed a separately committed gate on another 200-game research cohort (log loss 0.5399 versus M1 0.5337). M1 also scored below M0 (0.5337 versus 0.5451) there, but this secondary comparison was computed after the gate and before the terminal-boundary repair: **supporting evidence, not confirmation**. All 28 historical candidate scores and negative results remain in the [experiment register](https://github.com/sangtrx/vexil-dota2-win-probability/blob/main/docs/EXPERIMENT_REGISTER.md); those branches are not part of notebook Run All.

## Proper scoring and where the model fails

The primary estimand is the mean proper loss per **minute-level forecast opportunity**, so longer games carry more weight. I report **2,000 paired whole-match bootstrap resamples**, never resampling correlated minute rows as independent. Same-series games can still depend on one another.

| Phase (games) | Log loss M0 → M1 | Difference 95% CI | Brier M0 → M1 | Difference 95% CI |
|---|---|---|---|---|
| **Overall (106)** | 0.5164 → **0.5040** | **[−0.0304,+0.0014]** | 0.1719 → **0.1684** | **[−0.0069,+0.0002]** |
| 0–9 (106) | 0.6651 → 0.6506 | [−0.0252,−0.0030] | 0.2362 → 0.2295 | [−0.0117,−0.0014] |
| 10–19 (106) | 0.5695 → 0.5499 | [−0.0343,−0.0031] | 0.1927 → 0.1853 | [−0.0131,−0.0013] |
| 20–29 (105) | 0.4131 → 0.4065 | [−0.0111,−0.0015] | 0.1312 → 0.1293 | [−0.0036,−0.0001] |
| **30+ (79)** | 0.3623 → 0.3555 | [−0.0947,+0.0415] | **0.1028 → 0.1074 (worse)** | [−0.0037,+0.0109] |

**Neither overall primary interval excludes zero.** Phase intervals are not multiple-testing adjusted. Later phases also select games that last longer. Post-hoc alternative resampling by 54 series, equal-match weighting and removal of the last two recorded minutes are sensitivity checks, **not** new independent experiments or selection rules.

**Calibration exposes a failure mode.** Overall 10-bin ECE favors M1 (**0.0750** versus M0 **0.0895**), but the post-hoc series-bootstrap difference interval **[−0.0203,+0.0020]** includes zero. At **30+ minutes**, M1's ECE **worsens from 0.0559 to 0.0680**, as does Brier. M1's mean probability is **0.5429** against a held-out row-weighted Radiant win fraction of **0.6045**. In its 0.5–0.6 bin, the mean prediction is 0.540 but the observed win fraction is 0.653 (787 correlated rows). TRAIN Radiant wins were **51.2% of games**, versus **59.4% on TEST**; the gap may reflect sample shift as well as model calibration error, which 106 games cannot disentangle. I do **not** recalibrate on TEST.

![Figure 2. Conditional calibration ECE and Brier differences by game phase.](docs/figures/phase_error_audit.png)

*Figure 2. Post-hoc error diagnostics, not a new selection criterion: M1's late-game Brier and ECE are worse than M0.*

![Figure 3. Both models' held-out reliability, with correlated minute-row counts.](docs/figures/heldout_reliability.png)

*Figure 3. Descriptive reliability on the corrected held-out cohort; bin annotations are minute-row counts, not independent outcomes.*

**Influence matters:** match **8744971178** contributes **54.9%** of M1's aggregate log-loss advantage across its 55 minute rows. Removing it as a **post-hoc descriptive check** changes the overall M1−M0 difference from **−0.0124 to −0.0057** (still favorable). At minute 30+, 25 rows of this game dominate the apparent late log-loss advantage; deleting them reverses the remaining late-phase point difference to **+0.0314** (M1 worse). This is not a replacement primary score.

I also preselected a **minute-20 comeback test**. For games with |gold lead| ≥ 3,000, the current leader lost **5/44** times with a stable/improving lead versus **1/8** with deteriorating gold momentum. The comparison is underpowered and inconclusive. I do not turn an unverified comeback narrative into a release feature.

## Decision, reproducibility and assistance

**What I would ship:** keep gold-only M0 as a reference and run M1 in **shadow mode**. Record model version, match ID, minute, probability, source receipt time and input completeness; monitor log loss, calibration, late-game error, patch/league drift and latency. Replace M0 only after a fresh, genuinely later-series cohort with verified source availability supports a replicable gain. Historical OpenDota parsing is not a live authenticated feed. There are no betting odds, execution simulations or trading-profit claims.

The pre-test model family (**e49e853**) and match manifest (**3258a76**) were fixed before the first TEST evaluation. After the 12-row game-end repair, the **same models were refitted and executed locally** (500 cached matches, zero new HTTP calls, 14/14 cells). Earlier cold Kaggle/Colab runs checked the **previous inclusive-boundary revision**, not this one. The corrected [error audit](https://github.com/sangtrx/vexil-dota2-win-probability/blob/main/docs/ERROR_ANALYSIS.md) recomputes scores, calibration and match influence from all **3,836 frozen forecasts**; source arrival timestamps remain unverified.

**Time spent:** Approximately **10 hours of active work**, excluding unattended AI runs, API collection and cloud runtime.

**Assistance disclosure:** ChatGPT Web assisted with code, experiments, tests and drafting; Claude Sonnet/Fable with review. I checked the findings and directed follow-up tests. No third-party Dota predictor was copied. AI reviews are not independent human peer review.
