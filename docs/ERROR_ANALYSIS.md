# Error analysis | Why M1 is a challenger, not a release decision

**Evidence class: post-hoc diagnostics on an already inspected TEST cohort.**
The model choice (M1) was frozen before TEST; no fitting, feature selection, recalibration, or new thresholds are based on these diagnostics.

The corrected Vexil submission is one executable notebook plus the three-page REPORT.pdf. This additional document makes the *failure cases* independently inspectable. For the full search history, including negative results, see [EXPERIMENT_REGISTER.md](EXPERIMENT_REGISTER.md).


## Strict pre-terminal source boundary

The original notebook included 12 rows exactly at match end where duration was divisible by 60 (8 TRAIN, 3 VALIDATION, 1 TEST). The corrected notebook and item-feature loop both require 60*t < duration. It was refitted and executed in full on the same frozen 500-game cache (zero new HTTP calls; 14/14 code cells). The frozen corrected dataset has 18,292 minute rows and 3,836 TEST predictions. Earlier Kaggle/Colab cold runs covered the prior inclusive-endpoint code, not this exact correction.

## Does the gold-by-time effect help consistently?

| TEST phase | Matches / minute rows | Δ log loss, M1−M0 | Δ Brier, M1−M0 | ECE M0 → M1 |
|---|---|---:|---:|---:|
| 0–9 | 106 / 1,060 | −0.01451 | −0.00672 | 0.1097 → 0.0840 |
| 10–19 | 106 / 1,060 | −0.01960 | −0.00741 | 0.1028 → 0.0786 |
| 20–29 | 105 / 997 | −0.00667 | −0.00195 | 0.1019 → 0.0901 |
| **30+** | **79 / 719** | −0.00678 | **+0.00455, worse** | **0.0559 → 0.0680, worse** |

All values are descriptive point estimates from the fixed test forecasts. ECE uses ten equal-width probability bins and has limited interpretability when labels recur within matches. The original report presents confidence intervals for log loss and Brier; those remain the primary inferential results. The 30+ phase samples longer games selectively, and its intervals are wide.

![Phase calibration and Brier error, directly computed from saved held-out probabilities.](figures/phase_error_audit.png)

*Figure: Descriptive phase ECE and Brier-score differences. The direction reverses on late-game Brier and calibration; no hypothesis was selected using this plot.*

## Is the global improvement driven by a few matches?

The corrected TEST contains **106 games and 3,836 forecast opportunities**. M1–M0 mean log-loss difference is **−0.012430**. Match **8744971178** contains 55 minute rows and contributes **54.92% of the total signed log-loss improvement**. If this match is removed for influence diagnosis, the remaining 105 games have mean M1−M0 difference **−0.005685**: the sign survives, but the gain is materially smaller.

Late-game M1 Brier is worse even though its log-loss point estimate improves slightly. Excluding that influential match's 25 late-minute rows reverses the remaining late-phase log-loss point advantage to **+0.0314** (M1 worse). This is not a new primary metric or a license to delete inconvenient games.

This illustrates why a single overall proper score is not an adequate model-governance decision. Match-group and series-group dependence remain; a leave-one-out sign check is not a confidence interval.

## What else could make the result fail in deployment?

The 500 selected games span **5.26 days** across one patch boundary (250 patch 59, 250 patch 60). Validation and TEST are entirely patch 60; the study does not establish unseen-patch performance. TRAIN/VALIDATION/TEST Radiant game-win fractions are **51.2% / 48.5% / 59.4%**. On TEST M1 predicts an average Radiant win probability of **0.5429**, versus an actual row-weighted win share **0.6045**. Such misalignment may combine model error, side prevalence variation, league/team composition and sampling noise. We cannot separate those mechanisms with this small cohort.

The OpenDota endpoint returns a *parsed, completed match*. Its event time is retrospective game time, **not** the timestamp when a live consumer actually received an event. The forecast code demonstrates correctness under the brief's event-time cutoff; reliable production scoring would additionally need a received-at clock, input watermark, feature-staleness controls, label maturity and future-state replay assertions.

## An actionable Senior Data Scientist decision

**Retain M0 as the reference, shadow-test M1** and log source version, event/arrival times and phase-specific proper scores. For further research, predeclare **one** mechanistic gold-history or objective-state hypothesis, check its actual time availability, compare it with a simpler alternative and evaluate on a fresh series/tournament cohort. Require stable aggregate and late-game calibration and uncertainty before model promotion. A lower development loss after screening many feature ideas is not proof of a reliable new model.

### Reproduction (no API, no model fitting)

From repository root, using Python 3.11+:

    python research/error_diagnostics.py --check --json docs/ERROR_AUDIT_RECEIPT.json

This standard-library script reads only the included **artifacts/heldout_predictions.csv**, checks the frozen SHA-256, recomputes the original log loss, Brier, 10-bin ECE, phase scores and match influence, and fails if the numerical contract changes. The separate optional chart renderer uses the pinned scientific environment:

    python research/render_error_figure.py

The receipt and figure are committed as review artifacts. They are **not inputs** to the submission notebook. The corrected 3,836 forecasts were frozen after the pre-terminal source repair and were not used to select a new model.
