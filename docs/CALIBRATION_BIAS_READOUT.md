# Original VALIDATION and TEST: calibration-in-the-large sensitivity

**Research-only, post-hoc diagnostic.** The exact 3,836 original TEST
probabilities and 106 winners are held fixed. There is **no
calibration model fit, rescaling, feature selection or new threshold**.
This document is not a population calibration finding, new validation
run, or live-feed check.

The original TEST has **63/106 Radiant-winning games (59.43%)**.
Because longer games contribute more forecast opportunities, the
Radiant-win fraction across all 3,836 minute forecasts is **60.45%**.
M1's mean predicted probability is **54.29%** on those minutes. These
are two distinct estimands; repeated within-game outcome labels
must not be treated as independent wins.

| M1 predicted minus observed Radiant-win rate | Point estimate | 95% series-bootstrap CI |
| --- | ---: | ---: |
| All minute opportunities (longer games heavier) | -0.0617 | [-0.1410,+0.0250] |
| Equal weighting of the 106 games | -0.0523 | [-0.1308,+0.0316] |

The corresponding M0 bias is **-0.0621** minute-weighted
([-0.1419,+0.0245]) and **-0.0531** equal-game weighted
([-0.1332,+0.0328]). Both models underpredict **in the observed
sample**, but every interval crosses zero and is too wide to
exclude large underprediction in future tournaments. This is a
weak-calibration-signal diagnostic, not evidence of a stable bias.

## Reconstructed VALIDATION: an observed sign change, not confirmed drift

The frozen original 500-match source cache, exact notebook series split,
the original 291-game TRAIN-only model pipeline and at-time features
were re-executed **without fitting to VALIDATION or TEST or
reselecting a model**, reconstructing all **3,781** minute
forecasts in the original **103 VALIDATION games** (53
professional-series or singleton clusters). The source reconstruction
returns the original notebook scores: M0 log loss **0.532490**,
M1 **0.519714**, M0 Brier **0.181075**, M1 **0.175902**.
Both validation and TEST consist only of OpenDota patch-60 games.

| M1 predicted minus observed winner | VALIDATION (used to select M1) | TEST (already inspected) |
| --- | ---: | ---: |
| Mean predicted probability | 0.5174 | 0.5429 |
| Observed winner per minute row | 0.4874 | 0.6045 |
| Prediction bias (minute-weighted) | **+0.0300** | **-0.0617** |
| 95% clustered bootstrap CI | **[-0.0436,+0.1001]** (53 groups) | **[-0.1410,+0.0250]** (54 groups) |
| Descriptive ECE of M1, 10 bins | 0.0492 | 0.0750 |

The direction of the **sample's** mean bias reverses. Both
confidence intervals contain zero. The source of this change is
**not identified**: league/team/duration composition, sampling noise
or unrecorded balance changes remain plausible, despite a shared
major OpenDota patch ID. M0 also shows the same qualitative behavior.
Because M1 was selected using VALIDATION, its validation diagnostics
are **post-selection descriptions**, not a new blind assessment.

Reviewers can rerun the numbers **without raw match files**:

    python scripts/verify_validation_bias.py

The included **artifacts/validation_m0_m1_predictions.csv** contains
all 3,781 validation probabilities, labels and minute/series identity.
**docs/VALIDATION_BIAS_RECEIPT.json** binds the generated CSV by
SHA-256 and records original TRAIN-model fingerprints, **not** hashes
of the unbundled raw API payloads.
The optional **research/validation_bias_reconstruct.py** regenerates
them from the author's original 500 cached raw OpenDota match
payloads; those raw source files are **not bundled**, and fresh API
responses may change. Neither script recalibrates or evaluates a
replacement model. Do not treat the 103 validation games as another
unopened test.

## Reproducible method and evidence boundary

Source: the SHA-pinned original **artifacts/heldout_predictions.csv**
and **docs/SERIES_GROUPS_TEST.json**, both included in the package.
Series membership is preserved; unknown-series games are independent
singletons. Using 10,000 seeded draws over **54 professional-series
or singleton clusters**, each draw samples intact clusters with
replacement. The minute-weighted estimator divides sampled total
residual by sampled total minute rows. The equal-game estimator
divides the sum of sampled game-level average residuals by the sampled
count of games. These ratio estimators allow the numbers of rows
and games to vary across bootstrap draws.

Run from the project root:

    python research/calibration_bias_sensitivity.py

The output must exactly match **docs/CALIBRATION_BIAS_RECEIPT.json**,
and the script raises on numerical/provenance differences.
**tests/test_calibration_bias_sensitivity.py** independently checks
point estimates with pandas groupby and exercises corruption tests.
No model is refitted; no network or original raw JSON is needed.

The result is descriptive after original TEST inspection, not
prespecified confirmatory calibration inference. The existing 10-bin
ECE curve is bin-sensitive and also pools dependent minute outcomes.
M1's 10-bin ECE is 0.0750, at least as large as the absolute
minute-weighted mean bias of 0.0617 (a mathematical lower bound);
this alone does not identify calibration-slope error. The separate
100-game November sample reverses the sign of the row-mean bias:
M1 predicted about 0.4713 against 0.4466 winners. That sample is
highly concentrated in four leagues and shares 68 games with an
earlier cohort; it is not independent proof of time/patch drift.
The 54-series bootstrap also cannot capture shared team/league
dependence across different professional series.
A defensible future calibration decision would require a fresh,
unopened multi-tournament/league series cohort, a predeclared
weighting and dependence unit, point-of-arrival timestamps, and
separate calibration data. **No TEST recalibration was performed.**
