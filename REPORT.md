# Live Dota 2 Win Probability

**Truong Quang Sang · Vexil Capital · Senior Data Scientist take-home · 14 November 2026**

**Result:** On 106 held-out games, the gold-and-time model M1 reduced log loss
from **0.5163 to 0.5039** and Brier score from **0.1719 to 0.1683** versus
the required gold-only M0. The overall matched-game bootstrap log-loss
difference still includes zero. I would retain M0 as the deployed reference
and evaluate M1 in shadow mode, not claim proven superiority.


## Question, dataset, and information cutoff

The target is the probability that Radiant eventually wins, estimated at each game minute. I treat this as a forecasting and calibration problem, not a last-minute classification contest.

I retrieved **500 distinct parsed professional matches** from the permitted OpenDota endpoints. The sample has exactly 250 games from patch 59 (21–24 March 2026) and 250 from patch 60 (24–26 March 2026), satisfying the brief's requirement to span a patch change. I located the patch boundary by probing only a few match details per page, then selected the nearest eligible games on each side without using the winner. The discovery used 705 API calls, with 49 cache hits; 45 candidate games were outside the target patches and one was unparsed/too short. This is deliberately a **patch-transition sample**, not a representative draw of November 2026 games.

The 500 games produce **18,304 minute-level observations**; median match duration is 34.2 minutes. For each prediction at minute *t*, gold/XP features use array indices no later than *t*, and event features use times at or before 60*t* seconds, including events before the horn. A separate **retrospective data-quality gate**, not a live-feed guarantee, requires all ten player clock arrays to align at 0, 60, 120, ... seconds with the aggregate gold/XP series; all 500 games passed. A live integration would validate only the received prefix. End-of-match totals, the winner, and match duration do not enter the model. Duration is used only to determine which minute rows exist. A prefix-truncation test and deliberately poisoned future/post-game fields check this invariant. A separate cached-cohort audit passed 3,342 point-in-time checks on all 500 games; the executable notebook also performs prefix/future poisoning checks across both patches. All selected games had the XP series and objective/kill logs required by the implemented features, and none needed a stale gold-series tail.

## Split and candidate models

I sorted matches by start time, then chose chronological boundaries that do not split a match or professional series. All imputation and scaling are fitted on training rows only. The actual split is **291 train / 103 validation / 106 held-out test games**, corresponding to **10,683 / 3,784 / 3,837 minute rows**. Training contains 250 patch-59 games and 41 patch-60 games; validation and test contain only patch 60. That is an intentionally difficult later-match holdout, but it is **not** an unseen-patch experiment. Series-safe start-time splits are not perfectly label-available: five training games have estimated end times up to 1,606 seconds after the first validation game begins. An exploratory check excluding those five from training still selects M1 (validation log loss 0.5198 versus M0 0.5325). End times use game duration and can omit pauses; the original model and held-out scores are unchanged. Radiant won 149/291 training games (51.2%), 50/103 validation games (48.5%) and 63/106 test games (59.4%).

I fixed a small nested family before observing held-out scores. Every candidate uses the same regularized logistic regression (C = 1 fixed in advance), with no hyperparameter grid. Equal validation losses break ties in favor of fewer predictors. The candidate family predates the full real-data test.

| Model | Features added to the preceding model | Validation log loss | Validation Brier |
|---|---|---:|---:|
| M0, mandatory baseline | Current gold lead only | 0.5321 | 0.1809 |
| **M1, time-value** | Game minute and gold × log elapsed time | **0.5193** | **0.1758** |
| M2, lead fragility | XP lead and trailing five-minute gold/XP changes | 0.5220 | 0.1777 |
| M3, objective conversion | Timestamped towers, barracks, Roshan and kill differential | 0.5278 | 0.1805 |

**M1 was selected on validation log loss**, before opening the held-out scores. M2 and M3 beat M0 but did not improve on M1 in validation. The fitted gold × time interaction is negative: holding gold lead at **+2,000**, M1 forecasts **66.5%** Radiant win probability at minute 10 but **59.4%** at minute 30. Both are within the observed training range (at least +2,000 gold in 60/291 minute-10 games and 87/214 minute-30 games). This is a conditional model comparison, not an intervention. The fixed absolute lead appears less decisive as the game progresses, but the data do not show that creating the same lead at a different minute causes that probability change.

### An exploratory item-timing hypothesis

After the original four-model family was fixed and evaluated, I tested whether **timestamped purchases of influential items** add information not captured by gold and time. A five-feature logistic model (M1 plus signed cumulative major-item and Blink/BKB purchase counts) achieved validation log loss **0.5141 versus 0.5193** for M1 and Brier **0.1737 versus 0.1758**. It beat M1 in only **one of three earlier train-only folds** (log-loss differences +0.0313, −0.0013, +0.0063). On 103 previously inspected validation games, the unadjusted paired series-bootstrap 95% interval for its log-loss difference is **[−0.012944, +0.001811]**, spanning zero. The idea was highlighted from a broader **28-candidate exploratory search after original held-out outcomes had already been examined**. The interval does not correct for that search; the prior held-out set is no longer an independent test of this idea. Purchase logs are not current inventory, and the item model was **never evaluated on the 106 held-out games or used to revise M1**. The notebook reproduces the development comparison and cutoff checks.

## Held-out scoring and uncertainty

The primary estimand is proper loss per **minute-level forecast opportunity**. This weights longer games more heavily, so I also calculated an equal-match-weighted sensitivity. The uncertainty analysis uses **2,000 paired percentile-bootstrap resamples of whole matches** (seed 20261113), not individual minutes. Same-series games remain dependent, so even these intervals may be too narrow. The table reports M0 → M1, followed by the 95% confidence interval for the **difference M1 minus M0**. Negative differences favor M1.

| Phase (matches) | Log loss M0 → M1 | Difference 95% CI | Brier M0 → M1 | Difference 95% CI |
|---|---|---|---|---|
| **Overall (106)** | 0.5163 → **0.5039** | [−0.0303, +0.0014] | 0.1719 → **0.1683** | [−0.0069, +0.0002] |
| 0–9 (106) | 0.6651 → 0.6507 | [−0.0251, −0.0030] | 0.2362 → 0.2295 | [−0.0116, −0.0014] |
| 10–19 (106) | 0.5695 → 0.5500 | [−0.0342, −0.0031] | 0.1927 → 0.1853 | [−0.0131, −0.0013] |
| 20–29 (105) | 0.4127 → 0.4061 | [−0.0110, −0.0015] | 0.1311 → 0.1291 | [−0.0036, −0.0001] |
| 30+ (79) | 0.3623 → 0.3554 | [−0.0945, +0.0414] | 0.1028 → 0.1074 (worse) | [−0.0037, +0.0109] |

M1 improves both overall point estimates, but **both primary overall confidence intervals include zero**. I therefore do not claim a conclusive overall advantage. A separate **post-hoc** 12,000-draw, 54-series cluster resampling gives a log-loss difference interval of **[−0.0286, +0.0002]** and Brier interval **[−0.0067, −0.0005]**. The latter excludes zero under this different resampling unit, but this sensitivity is neither a new independent test nor adjusted for model search or shared teams/leagues; overall log-loss uncertainty still crosses zero. The 0–29-minute phases favor M1 under this resampling scheme, but these exploratory phase intervals are **not adjusted for multiple comparisons**. Late-game uncertainty is much wider and Brier is worse at 30+. The 30+ log-loss gain is dominated by one 25-row game (match 8744971178), which contributes −26.61 loss-difference points to a total of −4.92. Removing that game makes the remaining late-phase difference +0.0313 (M1 worse). This is a post-hoc influence diagnostic, **not** a replacement for the primary score. Early-phase intervals are not independent of the overall interval: the same games contribute to several phases, and the unstable late-phase contribution changes whole-match bootstrap draws. Phase populations also differ because short games never reach later phases.

Equal-weighting each match gives log loss 0.5095 → 0.4951 and Brier 0.1698 → 0.1649 (sensitivity point estimates; no new model fit). The two reliability diagrams in the notebook indicate that neither model is fully calibrated. (See Figure 1.) In M1's 0.5–0.6 prediction bin, the mean forecast is **0.540** but the observed Radiant win frequency is **0.654** across 788 minute rows from 103 matches. Those rows come from the held-out set and are correlated within games, not 788 independent outcomes. The shift in Radiant win rate between train and test may contribute to this underprediction. Excluding the last two recorded minutes favors M1 on log loss (difference −0.0136, 95% CI [−0.0306, −0.0002]) and Brier (−0.0040, [−0.0075, −0.0002]); unlike the headline intervals, these exclude zero. This prespecified sensitivity does not replace all-minute results or drive model selection.

![Figure 1. Held-out reliability of M1 and the mandatory gold-only baseline. Numbers label minute rows, not independent matches.](docs/figures/heldout_reliability.png)
*Figure 1. Held-out reliability. Each annotation is a minute-row count; observations from the same game are dependent.*


## An inconclusive game-level check and shipping decision

I also fixed a descriptive check at minute 20: among held-out games with an absolute gold lead of at least 3,000, how often did the current gold leader eventually lose? Deteriorating means the current gold lead and the preceding five-minute gold change have opposite signs. Among **44** stable/improving leads, **5** leaders lost (11.4%, Wilson 95% interval 5.0%–24.0%). Among **8** deteriorating leads, **1** lost (12.5%, interval 2.2%–47.1%). The comparison is underpowered and inconclusive; it cannot support a comeback mechanism, and it was not used for model selection.

**What I would ship:** keep the gold-only baseline as a dependable reference, and run M1 in shadow mode with versioned `(match_id, minute, model, probability)` outputs and checks for source completeness, calibration by phase/patch, and inference latency. I would not replace the baseline operationally until the overall gain and calibration replicate on later series. The notebook's timestamped item-purchase model is development-only, not a release candidate. Historical OpenDota parsing is not an authenticated live feed.

Limitations are material. All match data are retrospectively parsed; game-clock timestamps do not establish the historical arrival time of a live data feed. Match minutes share a winner, series may be dependent, the 30+ sample is selected by game duration, and patch distribution is confounded with the chronological split. No market prices, trade execution or profitability are studied.

![Figure 2. Gold-lead and minute-by-minute probability traces in one held-out match, selected by gold-range variation rather than outcome.](docs/figures/illustrative_game.png)

*Figure 2. One illustrative held-out trajectory, selected using gold-range variation rather than realized outcome or predictive accuracy.*

## Reproduction and assistance

The candidate family was committed before real evaluation (e49e853); the 500 IDs were frozen at 3258a76 before held-out scores were read. No earlier development run scored the real held-out set. The one self-contained notebook embeds all IDs and saves full held-out predictions (match ID, minute, both probabilities, winner), plots, package versions, and the development-only item ablation/fold scores. A cold run needs Internet, around 500 OpenDota calls, keyless, paced at 37.5 calls/minute. Its source digest records upstream reparses for **manual comparison** against the saved receipt; it does not automatically abort on drift. An earlier four-model version passed an independent private Kaggle CPU Run All, reproducing all 3,837 held-out probabilities and the evaluation scores across different Python/scikit-learn versions (largest probability discrepancy 4.44e-16). The complete raw OpenDota JSON content digest differed across runs; checks of selected matches found changed auxiliary player computed_mmr values, which this model does not use. Identical raw source payloads are not claimed. The latest notebook records separate model-input, label, development-item and cohort-metadata hashes; its three TRAIN fingerprints match an independently implemented earlier lineage audit exactly. The extended item-timing notebook passed both a local 500-match Run All and a fresh private Kaggle CPU Run All: all eight exported CSV tables, including the item ablation, match the local results to within 4.44e-16, and all 26 notebook source cells were verified against the hosted source. After the source-clock and malformed-payload guards were added on 14 November, a separate full 500-match BigLinux rerun again reproduced all eight scientific output tables (maximum absolute change 4.44e-16) and 51 offline tests passed. A hosted Colab Run All remains an acceptance gate.

**Time spent:** Active human work time to be recorded before submission; elapsed API/runtime time is not a substitute.

**Assistance disclosure:** ChatGPT assisted with notebook/test implementation and report drafting; Claude Sonnet independently reviewed an earlier code/report draft. No external Dota win-prediction implementation was copied. All reported numerical results come from executed analysis, not illustrative or synthetic data.
