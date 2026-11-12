# Live Dota 2 Win Probability

**Vexil Capital · Senior Data Scientist take-home · 13 November 2026**

## Question, dataset, and information cutoff

The target is the probability that Radiant eventually wins, estimated at each game minute. I treat this as a forecasting and calibration problem, not a last-minute classification contest.

I retrieved **500 distinct parsed professional matches** from the permitted OpenDota endpoints. The sample has exactly 250 games from patch 59 (21–24 March 2026) and 250 from patch 60 (24–26 March 2026). I located the patch boundary by probing only a few match details per page, then selected the nearest eligible games on each side without using the winner. The discovery used 705 API calls, with 49 cache hits; 45 candidate games were outside the target patches and one was unparsed/too short. This is deliberately a **patch-transition sample**, not a representative draw of November 2026 games.

The 500 games produce **18,304 minute-level observations**; median match duration is 34.2 minutes. For each prediction at minute *t*, gold/XP features use array indices no later than *t*, and event features use times at or before 60*t* seconds, including events before the horn. End-of-match totals, the winner, and match duration do not enter the model. Duration is used only to determine which minute rows exist. A prefix-truncation test and deliberately poisoned future/post-game fields check this invariant. A separate audit passed on 128 real games at 512 cutoffs; the executable notebook repeats the assertion across both patches. All selected games had the XP series and objective/kill logs required by the implemented features, and none needed a stale gold-series tail.

## Split and candidate models

I sorted matches by start time, then chose chronological boundaries that do not split a match or professional series. All imputation and scaling are fitted on training rows only. The actual split is **291 train / 103 validation / 106 held-out test games**, corresponding to **10,683 / 3,784 / 3,837 minute rows**. Training contains 250 patch-59 games and 41 patch-60 games; validation and test contain only patch 60. That is an intentionally difficult later-match holdout, but it is **not** a clean unseen-patch experiment.

I fixed a small nested family before observing held-out scores. Every candidate uses the same regularized logistic-regression pipeline, so incremental value is attributable to added features rather than a more powerful model class.

| Model | Features added to the preceding model | Validation log loss | Validation Brier |
|---|---|---:|---:|
| M0, mandatory baseline | Current gold lead only | 0.5321 | 0.1809 |
| **M1, time-value** | Game minute and gold × log elapsed time | **0.5193** | **0.1758** |
| M2, lead fragility | XP lead and trailing five-minute gold/XP changes | 0.5220 | 0.1777 |
| M3, objective conversion | Timestamped towers, barracks, Roshan and kill differential | 0.5278 | 0.1805 |

**M1 was selected on validation log loss**, before opening the held-out scores. The more complex candidates did not improve validation. In this sample, a lead's game-time context added more reliable signal than the extra momentum or objective variables. This is an ablation result, not proof that those game mechanics are unimportant.

## Held-out scoring and uncertainty

The primary estimand is proper loss per **minute-level forecast opportunity**. This weights longer games more heavily, so I also calculated an equal-match-weighted sensitivity. The uncertainty analysis uses **2,000 paired bootstrap resamples of whole matches**. The table reports M0 → M1, followed by the 95% confidence interval for the **difference M1 minus M0**. Negative differences favor M1.

| Phase (matches) | Log loss M0 → M1 | Difference 95% CI | Brier M0 → M1 | Difference 95% CI |
|---|---|---|---|---|
| **Overall (106)** | 0.5163 → **0.5039** | [−0.0303, +0.0014] | 0.1719 → **0.1683** | [−0.0069, +0.0002] |
| 0–9 (106) | 0.6651 → 0.6507 | [−0.0251, −0.0030] | 0.2362 → 0.2295 | [−0.0116, −0.0014] |
| 10–19 (106) | 0.5695 → 0.5500 | [−0.0342, −0.0031] | 0.1927 → 0.1853 | [−0.0131, −0.0013] |
| 20–29 (105) | 0.4127 → 0.4061 | [−0.0110, −0.0015] | 0.1311 → 0.1291 | [−0.0036, −0.0001] |
| 30+ (79) | 0.3623 → 0.3554 | [−0.0945, +0.0414] | **0.1028 → 0.1074** | [−0.0037, +0.0109] |

M1 improves both overall point estimates, but **both overall confidence intervals include zero**. I therefore do not claim a conclusive overall advantage. The 0–29-minute phases favor M1 under this resampling scheme; late-game uncertainty is much wider and Brier is actually worse at 30+. Game-phase samples also differ because short games never reach later phases.

The two reliability diagrams are in the notebook. They indicate that neither model is fully calibrated on this holdout. In M1's 0.5–0.6 prediction bin, the mean forecast is **0.540** but the observed Radiant win frequency is **0.654** across 788 minute rows from 103 matches. Those rows are correlated within games; they must not be treated as 788 independent outcomes. A preregistered sensitivity excluding the final two recorded minutes still favors M1 (log-loss difference −0.0136, 95% CI [−0.0306, −0.0002]), but it does not replace the required all-minute headline result.

## A falsifiable game-level insight and shipping decision

I also fixed a descriptive check at minute 20: among held-out games with an absolute gold lead of at least 3,000, how often did the current gold leader eventually lose? In **44** games with stable or strengthening five-minute momentum, **5** leaders lost (11.4%). In **8** games with deteriorating momentum, **1** leader lost (12.5%). The deteriorating group has a Wilson 95% interval of approximately **2.2%–47.1%**; the apparent difference cannot support a comeback claim. This negative result is worth keeping: a plausible narrative about momentum is not evidence of incremental prediction.

**What I would ship:** keep the gold-only baseline as a dependable reference, and run M1 in shadow mode for forward evaluation on additional games and patches. M1 is computationally cheap, point-in-time auditable and better in the early/middle phases here; I would not replace the baseline operationally until the overall gain and calibration are replicated prospectively. I would not ship M2 or M3 on this evidence.

Limitations are material. All match data are retrospectively parsed; game-clock timestamps do not establish the historical arrival time of a live data feed. Match minutes share a winner, series may be dependent, the 30+ sample is selected by game duration, and patch distribution is confounded with the chronological split. No market prices, trade execution or profitability are studied.

## Reproduction and assistance

The single notebook embeds all 500 match IDs, calls only the two allowed OpenDota endpoints, fixes its seed, records package versions and both manifest and source-content hashes, and saves the full held-out predictions table and plots. The repository pins local Python requirements. An independent Kaggle CPU rerun and fresh-Colab acceptance remain separate release gates.

**Time spent:** Active human work time to be recorded before submission; elapsed API/runtime time is not a substitute.

**Assistance disclosure:** ChatGPT assisted with notebook/test implementation and report drafting; Claude Sonnet provided an independent code review. No external Dota win-prediction implementation was copied. All reported numerical results come from executed analysis, not illustrative or synthetic data.
