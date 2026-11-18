# Pre-scoring protocol: minimal economy representation and loss weighting

Recorded 18 Nov 2026 ICT before new candidate scoring. Exploratory retrospective study in heavily reused data, NOT blind, NOT an employer submission amendment. Exactly three new candidates target a different mechanism from prior 81+ features: the units of economic lead and row-level overrepresentation of long matches.

## Frozen data and controls
- TRAIN only: original 291 March 2026 pro matches, 10,675 preterminal minute rows. No original 103 VAL or 106 TEST labels/predictions used in this study. Baseline model train_time_effect_ci.model() is median imputer + StandardScaler + LogisticRegression L2 C=1, max_iter 1000, random_state 20261113.
- Retrospective evaluations: October 180 games / 7,346 minutes / 107 series/singletons; November 22 games / 952 minutes / 9 series/singletons. They are previously seen datasets. Immutable original raw gzip files and collection/hash manifests; no new API calls. Existing M0, M1 and Q1 scores must exactly match previously locked scores to absolute 1e-10, and saved M0/M1 probabilities to 1e-7, or STOP.
- M0 original gold-only, M1 original gold_k+minute10+gold_x_time, Q1 original PathRisk; same March-only fit.

## Exactly 3 models, no search or tune
E_SHARE1: original M1 3 columns plus one extra earned_share_lead = (radiant_earned_gold - dire_earned_gold)/(radiant_earned_gold + dire_earned_gold + 1000); the denominator is raw gold units and the additive +1000 is fixed a priori. Both team totals are contemporaneous cumulative EARNED gold computed from five player gold_t arrays per team, not net worth/inventory. Side-odd, finite, [-1,1]. There is no patch/league/team identity predictor.

SAT_ASINH3: replace original gold_k with z = asinh(gold_k/3.0), where gold_k is thousands of earned-gold difference; replace gold_x_time with z*log1p(minute10). Retain original minute10. Fixed symmetric 3k soft scale, not outcome-tuned. Train original same model, three inputs.

MATCH_EQUAL: original M1 feature columns unchanged. Fit the LogisticRegression only with train-sample weights w = n_train_minute_rows/(n_train_matches * n_minutes_in_complete_historical_match), so each completed TRAIN match receives equal total weight. Sum weights equals 10,675; n_minutes_in_match is never an inference feature. Imputer and StandardScaler retain original unweighted fitting; only logistic__sample_weight is supplied. No calibration or coefficient adaptation to October/November.

## Provenance and falsification
Every forecast uses prefix up to t, with 60t < duration. Verify exact player vectors (10 players), team totals and original radiant_gold_adv at each minute, source hashes, 291 TRAIN and 202 later game IDs. Verify side reversal, within-team reordering invariance and future suffix poisoning. The actual packet received_at remains unavailable; postmatch replay game clock does not prove live availability.

Score all six fixed models separately in October and November: minute-weighted log loss/Brier, equal-match log loss, 30+ minute Brier. For 3 candidates versus both M1 and Q1 in 2 periods (12 paired comparisons), 5,000 whole-series bootstrap seed 20261118; report two-sided descriptive 95% and within-screen Bonferroni 99.5833% percentile LL confidence intervals. Group jackknife leave-one-series-out effect range. Prior extensive searches are not corrected by this within-screen adjustment.

Strict research-only gate: single candidate must exceed both M1 and Q1 by at least 0.005 lower LL in each period, upper 99.5833% CI <0 in all four comparisons, and never worsen overall/late30 Brier. Even if passed, report only a promising post-hoc hypothesis; no model promotion without genuinely untouched prospective data and receive-time proof. If failed, NO-GO. No cherry-picking period, later blend, or retuning constants.

External motivation: 2025 Dota 2 study distinguishes gold, net worth and phase predictors (https://www.mdpi.com/2504-2289/9/12/302). 2024 sport analytics methodology examines proper scoring and estimand interpretation (https://link.springer.com/article/10.1007/s10994-024-06585-0).

Only independent research branch modifications. Applicant notebook, original TEST, report/PDF, ZIP, private draft PR #9, submission, permissions, Gmail unchanged. No GitHub Actions.
