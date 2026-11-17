# Pre-scoring contract: fixed March feature challengers on October/November historical matches

**18 November 2026**, before this candidate's predictions are computed on the two later cohorts. This is **EXPLORATORY AND NOT BLIND**: October and November labels and M0/M1 prediction results have already been scored and read in earlier work. The five-family ALL candidate was selected after many March TRAIN screens; no claims of unbiased new holdout, robust superiority or employer release are permissible even if metrics look strong.

## Frozen input sources and immutable provenance

- Development: original 291 chronological TRAIN games, March 21–24 2026, exactly 10,675 point-in-time-prefix historical minute rows. Use exact SHA-pinned research rich-feature CSV and raw cache. March VAL (103) and TEST (106) labels/predictions NEVER used to refit or score this experiment.
- October historical reuse: exactly **180** already-collected games, October 20–31 UTC, 7,346 evaluated minutes, 107 independent series/singletons; source folder /srv/ai/tmp/vexil-october-raw-20261117, prior collection receipt SHA256 700ecf86ad7245cb9acf72d3a67321050c4eafa488565a7f61bdc2ce7de55bb8, metadata SHA256 03cded4444dfed2286af7f20add8e59433fe67dbddbe2e4c71741a6bf3c54e4d, saved predictions SHA256 3c0a4404294fbafec61bd518bdc41b95d7b631c830da31af6d90c91c663ebdf0.
- November historical reuse: exactly **22** already-collected games, November 15–16 UTC, 952 evaluated minutes, 9 series/singletons; /srv/ai/tmp/vexil-prospective-nov17-data-20261117, collection receipt SHA256 347729971519f1a65ad00e93c1ab739c0b2ab8db2d7864f763f4d, metadata SHA256 911d8589d0ad44948ea1ed66cf41b708c6ee565e3fbfcb3e9908936a2faa580e, saved predictions SHA256 b8fba05d2be581c797b35dbf28506e95bf378960dd6b60dc223d1220eeda9788.
- These cohorts do not overlap each other or March original 500; no new HTTP queries or downloads. Verify raw gzip hash against each collection receipt's per-match manifest; do not collect new games or inspect employer TEST outcomes.

## Exactly 4 models, no tuning on later cohorts

Fixed training fit ONCE on all 291 original March TRAIN games using frozen original logistic C=1, median imputer and StandardScaler per column, original gold/time definitions:
1. M0: original gold_k only.
2. M1: original gold_k, minute10, gold_k * log1p(minute10).
3. Q1 PathRisk: five already frozen inputs from last ten prior gold increments (gold, time, adverse excursion, signed realized vol, directional efficiency).
4. ALL: M1 plus exactly nine previously declared online regime, ordinal, tower objective-conversion and BKB/Blink purchase-log features (feature-family HEAD 851a1c1); no extra fit, model combination, weighting or calibration.

Recompute inputs from cached historical raw matches only through minute t; filter 60*t < duration; no terminal inventory, hero final attributes, match outcome, patch or opponent ID as predictors. Check every frozen later match has 10 players; verify original team economy series equals sums of player gold/XP at every index and 0,60,120... clocks. Forecast rows must match exact saved (match_id,minute). M0/M1 prediction probabilities must reproduce prior saved October and November predictions.csv within max absolute 1e-7. Otherwise STOP and report blocker, do not compare unlike models.

## Descriptive metrics and publication gate

For each period separately (never choose best period), minute-weighted proper LL and Brier for four models; delta ALL−Q1, ALL−M0 and ALL−M1, Q1−M1; equal-match LL; Brier after minute>=30; series/singleton-resampled 5000 bootstrap draws seed 20261118 for 95% paired LL intervals. Track leave-one-series-out LL ranges and largest series gain share; per-league diagnostics only with >=10 games, labelled exploratory; no model selection/recalibration.

**Fixed falsifier:** ALL−Q1 LL >= +0.005 in either later cohort REFUTES claim that ALL wins robustly on later periods. Near-zero changes or interval including zero means NOT VERIFIED. Even if ALL wins both with improvement >=0.005 and upper 95% CI <0, report promising post-hoc transfer ONLY and require future never-scored period; never promote employer submission. Source event arrival unverified.

No further feature search. Original notebook, 3,836 TEST predictions, reviewer ZIP, 4-page report, main and Draft PR #9 remain byte-identical. Code/tests/receipts only in separate research branch. No GitHub Actions. No edits to human hours or AI disclosure.
