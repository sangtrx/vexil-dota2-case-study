# Decisions (research decision record)

## ADR-001 — Kaggle computes; GitHub owns history (2026-11-13)
**Decision:** one source notebook in GitHub; private Kaggle kernel is an execution mirror. No copy-paste forks, cloud-only changes, or GPU dependency.
**Why:** the evaluator receives GitHub with outputs and must be able to rerun on Colab/local. Kaggle version history is not a substitute for reviewable Git commits.
**Verification:** Kaggle Internet/API smoke test is mandatory before the 500-match pull.
**Status:** implemented; one-account Kaggle CPU/Internet smoke passed; original full scan stopped, revised collection pending.

## ADR-002 — Series-purged chronological holdout (2026-11-13)
**Decision:** hold out the most recent roughly 100 matches; tune on preceding ~100; train on earliest ~300; never split a best-of series.
**Why:** adjacent minutes share one label and games in a series share strategy/context. Random row splitting would inflate evidence.
**Trade-off:** recent patch shift may make results worse; this is scientifically useful. If groups cross cut boundaries, sizes vary slightly.
**Status:** planned; verify 500-match series distribution.

## ADR-003 — Simplicity first, falsifiable novelty (2026-11-13)
**Decision:** gold-only logistic baseline, then small interpretable candidate with time/XP/momentum/objective ablations. Optional shallow tree only if warranted.
**Why:** with ~500 matches, errors in leakage, evaluation or calibration matter more than model capacity.
**Evidence gate:** improvements must survive validation and be discussed with paired match bootstrap CIs on untouched test.
**Status:** planned.

## ADR-004 — Deterministic upstream selection (2026-11-13)
**Decision:** freeze 500 selected match IDs in notebook source after selecting 250 eligible matches from each of two chronologically adjacent patch cohorts around the first observed patch transition; only the two allowed OpenDota endpoints are used.
**Why:** live recent-match pagination changes as new matches arrive. Reproducibility cannot rely on 'the most recent 500' changing daily.
**Caveat:** OpenDota may reparse matches; document source drift and content checksums if feasible.
**Status:** planned, contingent on initial collection.

## ADR-005 — Whole-match uncertainty (2026-11-13)
**Decision:** bootstrap match IDs, not individual minute rows; pair model/baseline differences.
**Why:** within-match minute predictions are heavily correlated.
**Status:** planned.

## ADR-006 — Prediction only, no trading overlays (2026-11-13)
**Decision:** do not add market pricing, PnL, Sharpe/DSR, Kelly, transaction costs or CPCV to a Dota binary-forecast assignment.
**Why:** the target is match outcome, not an executable financial payoff. A good classifier is not a trading strategy. Reference methodology: Bible v1.4.1 §§1.1, 7.7, 12.1.
**Status:** adopted.

## ADR-007 — OpenDota historical observability caveat (2026-11-13)
**Decision:** use the explicit minute-array and timestamp convention in the brief, verify with prefix truncation and future-data poisoning, and state that actual historical reception latency is unobserved.
**Why:** the endpoint returns retrospectively parsed replays, not a timestamped live delivery log. Reference: Bible v1.4.1 §§3.1, 3.3, 13.2.
**Status:** implemented with offline tests, real-data tests pending.

## ADR-008 — Avoid replacing binary libraries inside a live Kaggle kernel (2026-11-13)
**Observed failure:** first full Kaggle run reached Setup but failed with a NumPy/SciPy binary mismatch after `pip install` replaced packages inside Kaggle Python 3.13. No 500-match empirical evaluation occurred.
**Decision:** use Kaggle's preinstalled scientific stack and record its actual versions. Colab installs the notebook's inline-pinned analysis requirements; local installs `requirements.txt`. Do not claim bitwise numerical identity across different cloud base images until verified.
**Status:** corrected in notebook; real Kaggle retry pending.

## ADR-009 — Kaggle runtime detection takes precedence over Colab release tag (2026-11-13)
**Observed evidence:** the Kaggle Python 3.13 kernel sets both `KAGGLE_KERNEL_RUN_TYPE` and `COLAB_RELEASE_TAG`. The latter is not a reliable discriminator for Colab. Clean Kaggle environment imported numpy 2.1.3 / scipy 1.16.3 / sklearn 1.6.1 and fetched OpenDota correctly.
**Decision:** detect Kaggle first; only treat the environment as Colab when Kaggle detection is false. This prevents in-kernel binary reinstallation in Kaggle while preserving Colab's separate setup logic.
**Test:** `test_kaggle_detection_overrides_colab_release_tag` includes the contradictory flags from the actual environment.
**Status:** corrected and offline-verified; full Kaggle rerun pending.

## ADR-010 — Patch boundary discovery before payload collection (2026-11-13)
**Evidence:** A 30-page proMatches metadata preflight, covering roughly 3,000 recent professional games from June–November 2026, still sampled patch 60. We did not use outcomes or model scores.
**Decision:** find the first observed transition using up to three parsed-match detail probes per page. Then select the nearest 250 eligible matches on each side of two adjacent patch cohorts. This is an outcome-blind patch-transition sample, **not a representative random sample of present-day pro games**; report that limitation.
**Recovery:** deleted only our scratch Kaggle kernel for the unproductive full-payload scan before it produced model results, avoiding unnecessary unauthenticated OpenDota API requests.
**Verification:** 17 offline tests include patch discovery and bounded detail calls. Full 500-match acceptance pending.
**Bible:** v1.4.1 §§1.2–1.4, 3.1–3.6, 5.1–5.6, 14.1.
