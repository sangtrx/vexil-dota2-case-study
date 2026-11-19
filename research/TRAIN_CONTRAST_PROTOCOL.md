# TRAIN-only effect contrast: protocol

Date: 15 Nov 2026. Design is saved and committed **before** running the new series bootstrap. Not a new independent experiment and not an uncertainty interval on unseen performance.

**Target:** The original M1 has +2,000 Radiant gold conditional probabilities about 0.665 at minute 10 and 0.594 at minute 30 (single model fit). We want descriptive uncertainty of their difference from *training series resampling*, with no use of 103 VAL or 106 TEST labels and no model reselection.

**Locked data:** frozen original 291 TRAIN games (10,675 minute rows) from the exact TRAIN/VAL development artifact, filtered by partition TRAIN, verified by full 500-game original match/partition/series manifest SHA256. Do not use VAL or TEST for model fit, resample, bootstrap CIs or the conditional scenario. The derived TRAIN-only feature CSV was recreated in an earlier author-run
raw-cache audit in separate calibration research; that raw source evidence
was not independently certified and is not bundled here. Validate source SHA before use.

**Fixed model:** same exact M1 Pipeline: median imputer, StandardScaler and L2 binary LogisticRegression(C=1, random_state=20261113, max_iter=1000), features [gold_k, minute10, gold_x_time]. No retuning or new feature families.

**Fixed scenario:** p(Radiant wins | +2000 gold, minute=10) minus p(Radiant wins | +2000 gold, minute=30), with gold_x_time = gold_k * log1p(minute10). Report individual probabilities, point contrast, and **95% percentile interval from 2,000 resamples of whole professional TRAIN series** (or singleton game when series_id=0), seed 20261115, with replacement. Training fitting remains minute-weighted inside each resample. Duplicate observations keep cluster multiplicity; never resample minute rows independently.

**Primary interpretive gate:** If the 95% bootstrap CI of p10−p30 crosses zero, report the scenario contrast as not robust and DO NOT improve headline or suggest causal time effects. If the CI excludes zero, only say *within-TRAIN descriptive fitted contrast is stable to grouped resampling*; this does NOT prove a live price impact, out-of-sample accuracy or causal relationship. Do not promote a new model on the basis of this test.

**Sensitivity (planned, secondary):** equal-game bootstrap weighting (one row per match per chosen moment is not a refit of the minute-weighted model; use resampled games as clustered units only in second explanatory analysis), and five incomplete TRAIN matches overlapping first VAL boundary excluded **only as a diagnostic** if time allows. Do not select best result across sensitivity variants.

**Integrity constraints:** original main M1 coefficients and forecast data unchanged. This is optional explanatory research until reviewer signoff and truthfulness QA. All code/tests run locally on BigLinux, no GitHub CI.


## Authored-source chronology and unresolved sensitivity limits

The original frozen procedure was committed as curated-repo commit **07ddc6a**;
the exact code/data hash-bound TRAIN source as **476a841**, before first
evaluation receipt. These are author-controlled Git timestamps, not an
external experiment registration or independent attestation. The feature CSV
is derived from previously cached OpenDota data; the original raw /matches
JSON payloads are **not** bundled in the handoff. The original 500-game
split manifest contains only match metadata; all 291 outcome labels used
for this contrast come exclusively from TRAIN features.

The 171 resampling groups are **149 known professional series plus 22
standalone games lacking a series ID**. Those standalone groups may still
share teams/leagues, so a 171-group percentile bootstrap cannot establish
population-level independence. Of 2,000 bootstrap replicates, **95.1%**
give a positive point contrast, but the *predeclared percentile* interval
includes zero. Alternative interval families were **not preregistered** and
must not replace it after seeing the result.

The two optional secondary diagnostics proposed above (equal-game
resampling and removing the five training games with potentially immature
labels at VAL start) **have not been run**. They are not missing evidence
supporting the primary contrast and may not be inferred from the distinct
original model-selection sensitivity. The original single-fit scenario and
selected M1 are unchanged.
