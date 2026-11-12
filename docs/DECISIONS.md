# Decisions (research decision record)

## ADR-001 — Kaggle computes; GitHub owns history (2026-11-13)
**Decision:** one source notebook in GitHub; private Kaggle kernel is an execution mirror. No copy-paste forks, cloud-only changes, or GPU dependency.
**Why:** the evaluator receives GitHub with outputs and must be able to rerun on Colab/local. Kaggle version history is not a substitute for reviewable Git commits.
**Verification:** Kaggle Internet/API smoke test is mandatory before the 500-match pull.
**Status:** adopted; Kaggle CLI/account verification pending.

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
**Decision:** store selected match IDs / fixed cursor in notebook source, not an external file; still fetch data through two allowed OpenDota endpoints.
**Why:** live recent-match pagination changes as new matches arrive. Reproducibility cannot rely on 'the most recent 500' changing daily.
**Caveat:** OpenDota may reparse matches; document source drift and content checksums if feasible.
**Status:** planned, contingent on initial collection.

## ADR-005 — Whole-match uncertainty (2026-11-13)
**Decision:** bootstrap match IDs, not individual minute rows; pair model/baseline differences.
**Why:** within-match minute predictions are heavily correlated.
**Status:** planned.
