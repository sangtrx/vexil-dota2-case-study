# Senior DS hostile decision: Do XGBoost or LightGBM belong in the Vexil submission?
18 November 2026 ICT. Research-only, deterministic rerun on BigLinux epic by the same research workflow; not an external independent reviewer.

## Decisive answer
**No direct model promotion on the available evidence.** The Vexil applicant-provided assignment asks for a gold-only logistic regression reference and applicant-developed forecast; it does **not** require XGBoost or LightGBM. Original submission correctly keeps M0 reference and M1 shadow since grouped primary held-out intervals include zero and M1 late30 Brier can regress.

Two XGBoost and two LightGBM CPU models were actually trained on the same **original March TRAIN-only** 4 chronological mature-label group-forward evaluation blocks (291 TRAIN games / 10,675 total source minute rows; 137 OOF evaluation games / 5,081 forecast rows / 70 professional series/singletons). All four were predeclared before first scores in separate protocol and source commits. No original March VAL/TEST labels or Oct/Nov outcome data were loaded for new fits or scoring. This only checks old TRAIN folds and **is not a new unseen dataset**. Pre-existing many candidate screens and the inspected original TEST limit all inferential claims.

## Fixed 90-round model results: primary per-minute proper log loss lower is better
| Frozen candidate | Inputs | LL | Brier | vs Q1 path LL | Forward fold wins vs Q1 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Original M0 logistic | 1 | 0.612312 | 0.211828 | +0.006349 | N/A |
| Original M1 logistic | 3 | 0.612086 | 0.212744 | +0.006123 | N/A |
| Q1 path logistic | 5 | 0.605963 | 0.210050 | +0.000000 | N/A |
| Prior sklearn HistGradientBoosting | 84 | 0.621266 | 0.216617 | +0.015303 | 1/4 |
| MATCH_EQUAL M1 logistic | 3 | 0.618253 | 0.214388 | +0.012290 | N/A |
| XGBoost3 | 3 | 0.615597 | 0.213477 | +0.009634 | 1/4 |
| LightGBM3 | 3 | 0.616196 | 0.213476 | +0.010233 | 1/4 |
| XGBoost84 | 84 | 0.621809 | 0.216463 | +0.015846 | 1/4 |
| LightGBM84 | 84 | 0.622936 | 0.217009 | +0.016974 | 1/4 |

Point and uncertainty: XGB3−Q1 Δ minute LL = +0.009634, grouped series 95% [+0.002548,+0.017021], within-8-comparison 99.375% [-0.000397,+0.020085]. LGB3−Q1 = +0.010233, 95% [+0.003146,+0.018082], 99.375% [+0.000454,+0.020920]. Positive means boosting is worse, **on this historical repeated TRAIN OOF only**. All four failed primary improvement, uncertainty, Brier, late30 and >=3-of-4 fold guardrails. A 5,081-minute sample does not contain 5,081 independent outcomes; clustered series count is 70.

## Fairness test after observing fixed result (NOT a new blind test)
A separately committed, clearly post-result protocol tested three fixed regularization profiles per XGB/LGB family, selected by two chronological professional-series inner folds drawn only from each outer TRAIN prefix, with completed-label proxy before each inner validation starts. Twelve profile choices in the grid; for four model families across four outer folds **all 16 selected conservative**. In every one of 16 profile selections, moderate and flexible had higher inner log loss than conservative. Therefore nested-selected OUTER scores are byte-for-byte equivalent to the original fixed results; profile search did not rescue boosted trees.

The purpose was bounded falsification of the underregularization/overregularization concern, not unlimited tuning. This grid does not prove **all possible** XGBoost/LightGBM configurations will fail, and its protocol was set after earlier evidence, which is a remaining model-search bias. Do not expand the grid on reused folds to chase a positive result.

## Root-cause hypotheses to carry to any future genuinely independent study
- **Repeated minute rows from a small number of games:** Boosted trees can fit match-specific patterns and early patches despite many 10k minute samples. Effective independence is games/series, not minutes. Even conservative leaf constraints may not generalize.
- **Noisy redundant features:** 81 hand-engineered telemetry inputs are correlated, and 84-input trees fared worse than 3-input trees on all pooled metrics except some late30 slices. More columns do not necessarily add signal.
- **Data distribution and chronological drift:** Original March cohort only covers ~5 days near patch boundary, TRAIN contains patch60 too; later professional games/teams/patches are not validated by this OOF.
- **Label-maturity and actual live packet availability:** Inner/outer training uses (start_time+duration) proxy to avoid future completed match labels, but no independently captured received_at exists. Full OpenDota replay arrays are not proof of true real-time feed readiness.
- **Target metric matters:** Equal-match and per-minute loss differ; MATCH_EQUAL previously improved certain October/November retrospective slices, but is WORSE than M1 on the March TRAIN-forward primary (0.618253 vs 0.612086).

## Verification & reproducibility
Original frozen TRAIN rich CSV and 291 raw provenance hash verified against previously sealed receipt; 4 complete source/label maturity splits; independent group IDs; 8 candidate-control bootstrap contrasts; fixed calibration bins with row counts and original controls M0/A/M1/Q1 and Q3 numerical parity. This screen's protocol and code were committed before its own fixed candidate scores at 228939cacd1cb089d1b423e1efa25ec1e369b1f7; the overall research program was **not preregistered**, and these reused TRAIN folds are not independent validation. Native isolated packages: xgboost 3.4.1, lightgbm 4.7.0, narwhals 2.21.2, sklearn 1.7.2, numpy 2.2.6.

The initial request for xgboost 3.4.2 failed since the BigLinux pip index offered only up to 3.4.1; an explicit pre-fit amendment was committed at 7a4514d6d2637c22095181c12d3f1724434c0625. Other hyperparameters/folds/decision rules did not change. Do not represent this as 3.4.2.

Historical BigLinux **research-branch** test suite: **292/292 PASS** on 18 November (separate from the **174** offline tests in the reviewer ZIP). The direct and nested research outputs were re-scored with matching numerical summaries; their full raw JSON and markdown report hashes belong to the research branch and **are not bundled** in this reviewer ZIP. No outside committee review or fresh independent sample was performed.

Frozen applicant science artifacts remain unchanged by the 19 November documentation repair:
- Executed notebook SHA256 e4318f15a0b34e5900cff1fcaa741d953046b74add4e5f95472d025facf7d61f
- 3,836 TEST forecasts SHA256 03b4f6d67e7cb5b7af8097be145fc8cfdd510beefbe85e052bb0445ba7a0c441

**Research limitation:** This is post-result TRAIN-forward falsification, not a new blind cohort or verified live-feed latency analysis; no fresh received_at observations were collected. The revised applicant report documents these negative findings and keeps the M0-reference / M1-shadow decision.
