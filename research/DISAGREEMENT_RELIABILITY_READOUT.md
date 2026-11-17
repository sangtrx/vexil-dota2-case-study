# Is model disagreement an honest forecast reliability signal?

**Scope:** fixed, post-result exploratory TRAIN-forward; no original VAL, TEST, external holdout, applicant narrative, or deploy changes.

Evaluated 5,081 minute predictions / 137 games / 70 independent series/singletons. Wrong-side labels: 1,783 (35.1%).

## Primary falsifier

| Risk score | Wrong-side AUROC |
| --- | ---: |
| D: max model disagreement | 0.51856 |
| U: M1 confidence-based uncertainty | 0.66576 |

**D minus U AUROC:** -0.14721; series-cluster bootstrap 95% interval [-0.20475, -0.09307] (2000 paired draws).

## Retrospective alert budget — NOT deployable thresholds

| Score | Top20% alerts | Wrong alerts | Precision | Error recall |
| --- | ---: | ---: | ---: | ---: |
| disagreement | 1017 | 382 | 0.376 | 0.214 |
| uncertainty | 1017 | 497 | 0.489 | 0.279 |

## Four chronological TRAIN folds

| Fold | Games | Wrong-sided | D AUROC | U AUROC | D-U |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 22 | 260 (33.7%) | 0.5389 | 0.6120 | -0.07305 |
| 2 | 44 | 558 (33.8%) | 0.5026 | 0.6499 | -0.14724 |
| 3 | 32 | 435 (35.4%) | 0.4788 | 0.6725 | -0.19369 |
| 4 | 39 | 530 (37.0%) | 0.5557 | 0.7044 | -0.14869 |

## Mechanism/negative-control diagnostics

- Component |M1−M0| AUROC: 0.45282; component |M1−Q1| AUROC: 0.51549. Do not select components after seeing their scores.
- Within fixed uncertainty/time cells: 19/19 usable cells, 5081 included rows / 0 excluded. High-D minus low-D wrong-sided rate: -0.02400. This is an offline coarse-stratification diagnostic, not fitted adjustment.
- High-confidence (max M1 p >=0.75) n=1927, wrong-sided=381; outcome is only used for retrospective scoring.

**Future independent study gate:** REJECT / not supported by fixed gate

**Limits:** minute labels share match outcomes; bootstrap respects series but uncertainty is descriptive for this repeatedly explored TRAIN cohort; top20% offline ranking has no calibrated real-time threshold; coarse confidence/time matching leaves residual confounding. Actual feed arrival timestamps are not known. This experiment says nothing about official Vexil grading, calibration superiority, or trading returns.

Original 500-game notebook, locked 3,836 TEST forecasts, applicant report/ZIP and human disclosure remain unchanged.
