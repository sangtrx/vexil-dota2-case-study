# Locked external holdout protocol — 17 November 2026

**Scope:** This is a prospective-to-this-analysis, *retrospective match-data*
follow-up to the original Vexil 500-game take-home. It is **not** a live feed
latency experiment, a second pristine TEST for the original 500-game
development workflow, or a permission to retune a model. Do not merge this
research branch into the reviewer package unless a separate review confirms
all submission constraints.

## Commitment before discovery, match details or outcomes

- Exact original source: private Draft PR #9 commit
  `4eb95765567cd4216001fac46aacc4b3a53afebd`.
- M0: frozen original TRAIN (291 games; 10,675 per-minute rows),
  logistic on `gold_k`. Frozen fitted fingerprint:
  `c7ca7c9fa28cfee258f37bc482f23f8d1d4e7b8df30f7c2dcb20384a2d4f9558`.
- M1: same original TRAIN; logistic on `gold_k`, `minute10`,
  `gold_x_time`; fingerprint:
  `33c458955f3fe512b985c3d983c9349a433c97bd44b769d8897a7cc15f21d91a`.
- Both models extracted by existing
  `research/posttest_temporal/collect_and_score.py`, using original frozen
  notebook's preprocessing and estimators. No fitting on October/November
  matches, new matches, previous TEST, or new holdout; no recalibration.
- Only the two OpenDota endpoints explicitly allowed by Vexil:
  `/proMatches` and `/matches/{match_id}`, no API key.

## Cohort, exclusions and immutable sequence

1. Discover `/proMatches` in descending `match_id` order with
   `less_than_match_id`, **at most 10 pages**. Archive full page bytes
   privately and save their SHA256s before detail requests. Freeze a
   label-*uninspected* listing of IDs, start times and known series IDs
   in Git. Note that raw API page objects **may contain outcomes**;
   selection code must not access that field. This is not human-blinded
   outcome adjudication.
2. Fixed match start window: **[2026-11-16T00:00:00Z,
   2026-11-17T09:00:00Z)**, cutoff set before discovery. Exclude match IDs
   already present in the original 500 and the prior 100-game November
   stress test; exclude nonzero series IDs already present in either
   previous cohort. No league, winner, team, patch or gold-based
   selection.
3. Download **every candidate in the frozen listing** in descending ID
   order, maximum 300 details; no cherry-picking first N after scoring.
   Eligibility: 600+ second duration, parsed gold and XP arrays, 10 player
   slots, original strict minute-clock verification, parseable per-minute
   features, valid patch and final Boolean outcome. Exclude on validity
   only, record every exclusion *before* score. Treat exhausted network
   retries as BLOCKED, not as sample-quality exclusion. Do not alter the
   window, target count or thresholds after seeing any outcome.
4. If fewer than **50 eligible games or 30 independent series/singleton
   clusters**, display scores as descriptive/underpowered only; do not
   imply confirmatory uplift. Include **all** eligible matches (no manual
   removing a hard case). Keep exact original pro-match page and parsed
   match payload hashes; OpenDota may change later.

## Predeclared evaluation

- Use original strictly past-visible `snapshot_features`,
  `make_minute_table`, and `60*t < duration` prediction horizon.
- Primary: minute-row-weighted log loss M1−M0, with **10,000** paired
  percentile resamples of **whole series** (positive `series_id`)
  or match singletons (otherwise), seed **20261117**.
- Sensitivity: 10,000 paired **whole-match** resamples, same seed.
- Secondary: Brier score and same CIs, ECE-10 for each model, equal-match
  mean loss, game phase breakdown 0–9 / 10–19 / 20–29 / 30+, sample
  counts, patch/league distribution, team overlap and largest game
  contribution. Report every phase, including negative ones; phase CIs
  are descriptive/unadjusted. No tuning, multiple-try fishing, or
  significance claims from changed cluster assumptions.
- Decision: this analysis alone authorizes **NO M1 promotion**.
  Report the point estimate, uncertainty and domain shift whether it
  favors M0 or M1. Any future production gate would require independent
  evidence of label+feature `received_at` and reliability monitoring.
- Original TEST and personal AI/public-code disclosure remain untouched.
  No recruiter email, private sharing changes or main/PR merge.

**Stop conditions:** If immutable discovery, strict eligibility, source
model fingerprints, series exclusion, source hash, or full independent
replay cannot be verified, mark HOLD/NOT VERIFIED, preserve receipts and
do not silently resample a more favorable cohort.
