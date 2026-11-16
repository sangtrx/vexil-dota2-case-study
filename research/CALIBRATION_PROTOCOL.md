# Development-only calibration audit (protocol saved before first execution)

**Evidence:** original TEST labels have been opened repeatedly, so the 106 TEST games are prohibited here. The 103-game validation was also used to select M1 and repeatedly inspected; its comparison is EXPLORATORY, not independent evidence of external calibration.

## Question
Can a one-degree-of-freedom, TRAIN-only forward-out-of-fold log-odds intercept correction reduce calibration error relative to validation-selected M1 without refitting on VAL or touching TEST? A negative finding is valid.

## Frozen design
- Reconstruct M1's three features from cached OpenDota JSON using only TRAIN and VALIDATION games from the frozen 500-game manifest. Fail closed on unexpected IDs/outcomes/clock indices or dataset drift. Strict pre-terminal rule: 60*minute < duration. The 291/103 game and 10,675/3,781 minute-row counts are invariants.
- M1 model: gold in thousands; minute/10; gold * log1p(minute/10); StandardScaler, SimpleImputer(median) and LogisticRegression(C=1, random_state=20261113) on minute-weighted TRAIN.
- Generate four chronological series-disjoint TRAIN out-of-fold blocks. Nominal TRAIN cut fractions: 0.45, 0.65, 0.75, 0.88, 1.00. Snap cuts to feasible series-safe boundaries; embargo older games whose approximate game end exceeds first evaluated OOF start.
- Calibrator is one scalar b, the root of sum(sigmoid(logit(p_oof) + b)-y)=0 in TRAIN OOF. Solve with deterministic scipy brentq; slope fixed to 1, no validation tuning.
- Fit M1 on full TRAIN. Compare frozen unadjusted validation probabilities with offset-adjusted probabilities on 103 previously inspected VAL games. No VAL label used for fitting or selection.
- Report Brier, log loss, ten-bin ECE, bias-in-the-large, paired 54? series-resampling with actual VAL series count (5000 draws, seed 20261115), and equal-match weighting. Evaluate all original 103 VAL games. Never compare this intervention on TEST.
- Keep original M1, original PDF and release ZIP unchanged. Promotion would require a new untouched future-series cohort with fixed primary loss and feed-receipt timestamps.

## Limitations
OOF blocks are temporally nonexchangeable; minute labels are dependent; 10-bin ECE depends on bin choice; correction of global mean does not imply conditional calibration. Event timestamps are retrospective, not authenticated receipt times.

## Label-blind chronology feasibility amendment — 15 Nov 2026, before any model score

The initial fractions 0.45/0.58/0.71/0.84 snapped to 154/168/220/247/291 games because a large professional series spans much of early TRAIN. The first OOF evaluation block contained only 14 games, below the predeclared 15-game minimum; script stopped at the chronology gate **before fitting or scoring any OOF candidate**. Inspecting the series-safe *match ID/start-time/group boundaries only*, we amended the nominal fractions to 0.45/0.65/0.75/0.88, which snap to 154/176/220/252/291 and yield 22/44/32/39 OOF games. No labels or loss values informed this design correction. This amendment is a recorded exception; it does not make reused VAL independent.

## Independent hostile-review correction (append-only)

See [CALIBRATION_ERRATA.md](CALIBRATION_ERRATA.md). The phrase "54?" in the frozen procedure was a placeholder; actual VAL has 53 series/singleton groups. The original amendment changed cutpoints 2 AND 4, not the last two; changing cutpoint 4 was unnecessary to satisfy the 15-game minimum. This does not erase the original procedure or retroactively preregister follow-up sensitivities.
