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
**Verification:** 24 offline tests include patch discovery and bounded detail calls. Full 500-match acceptance pending.
**Bible:** v1.4.1 §§1.2–1.4, 3.1–3.6, 5.1–5.6, 14.1.


## ADR-011 — Do not confuse unavailable events with true zero events (2026-11-13)
**Decision:** objectives=None produces NaN tower/barracks/Roshan features; missing player kill logs produce NaN kill differential. A present empty log is an observed zero. Keep the required gold-only baseline untouched; impute optional proposed-model columns only on training data.
**Evidence:** an independent code audit identified silent zero-filling; new offline fixtures verify the distinction. A per-patch data-quality table reports optional-log coverage and the staleness of gold array tails.
**Bible:** §§3.1–3.6 and 14.2.
**Status:** 26 offline tests pass; still awaiting real-data coverage.

## ADR-012 — Evaluate terminal sensitivity without changing the primary estimand (2026-11-13)
**Decision:** score all requested minute snapshots as primary, and score again after excluding the last two recorded minutes of each held-out match as a labeled robustness analysis. Keep match-level paired bootstrap, no model refitting or tuning based on the sensitivity.
**Why:** near-terminal outcomes are nearly determined; excluding them entirely would violate the brief's all-minute evaluation. Sensitivity isolates their influence without erasing them.
**Bible:** §§4.3, 6.5, 7.2–7.7.
**Status:** code and synthetic tests pass; no held-out evidence yet.

## ADR-013 — Missing-data semantics must survive the leakage oracle (2026-11-13)
**Problem:** initial prefix truncation converted objectives=None and kills_log=None to empty arrays, which falsely changed absent information into observed-zero events. The PIT checker therefore used different missingness semantics from the production feature engine.
**Change:** prefix truncation now filters only existing event lists, preserving None. Added a regression test asserting feature invariance for missing objectives/player-kill logs.
**Evidence:** 26/26 offline tests pass. No model family, split boundary or data sample was altered.
**Bible:** §§3.1–3.6, 14.3.

## ADR-014 — Hash source payloads separately from the ID manifest (2026-11-13)
**Decision:** the executed notebook computes and saves both a SHA-256 of its match-ID/time/patch manifest and a canonical hash over all fetched match payloads in its run receipt. This adds no input files or API endpoints.
**Why:** OpenDota may reparse an unchanged match ID, changing the feature values. A frozen manifest alone does not prove identical input data; a payload hash makes such changes observable.
**Tests:** synthetic end-to-end Run All executes the hash code and produces a valid 64-character digest. Real-data acceptance remains pending.
**Bible:** §§3.1–3.2, 14.1–14.2.


## ADR-015 — Conservative one-account free API pacing (2026-11-13)
**Observation:** the initial Kaggle bulk attempt exhausted bounded retries on one match, but a later Kaggle and BigLinux request for the same match returned HTTP 200. The cause could be a transient/shared-IP limit; no definitive HTTP 429 trace was retained.
**Decision:** set the notebook to at most one request every 1.6 seconds (37.5/minute) and seven bounded retries, below the brief's approximate 50/minute guidance. Missing/unparsed snapshots are not permanently cached. This affects fetch reliability only, not sample rules, features or estimators.
**Status:** implementation and unit tests pass; full frozen run remains to be verified.


## ADR-016 — Frozen patch-boundary manifest accepted (2026-11-13)
**Evidence:** A 500-unique-ID outcome-blind cohort from patches 59 (250) and 60 (250), spanning March 21–26, 2026, was verified and embedded in source before viewing held-out scores. This historical transition-focused sample does not represent the current professional match population.
**Deterministic identity:** SHA256 f2be53e16ae29df1f62aa9907187fdba846d9af9fb7a3f69e7dd7504be43b776 over the ordered JSON match-ID list. The notebook separately records a content digest of the fetched payloads.
**Selection accounting:** 705 API calls, 49 cache hits, 46 candidate exclusions (wrong patch 45, unparsed/short 1).
**Code contract:** Frozen mode calls /matches/{id} only and refuses silent resampling when any match becomes unparseable. Two new offline tests establish this.
**Status:** Accepted for test, but not submission-ready; independent Kaggle/Colab execution and report still pending.
