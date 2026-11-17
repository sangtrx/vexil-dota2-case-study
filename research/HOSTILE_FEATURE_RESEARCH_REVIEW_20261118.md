# Vexil hostile review: feature richness vs actual evidence
_Date: 18 November 2026 · historical research branch only_

## Decision

**NO-GO to new model promotion. Engineering replay is testable; external scientific generalization is NOT VERIFIED.** The original recruiter-facing four-page report correctly recommends the gold-only M0 reference and M1 as shadow. A strong original M1 advantage on an already-inspected 106-game TEST is insufficient because the paired CI contains zero, late-game Brier is adverse, one 55-minute match drives >half of improvement, and the original TEST was corrected after inspection. Adding a rich feature family does not fix these design limitations.

**Independent reviewer challenge:** the target is final match winner Y_m; forecasting every minute does not create new independent terminal labels. 137 forward OOF games represent 70 professional series/singletons, all from a very short March 2026 period. Model search has reused those 70 groups repeatedly. New-family confidence intervals within a screen cannot erase earlier feature-hunting. Claiming any C4/ALL/R/C feature is proven superior would overstate evidence.

## Findings by severity and provenance

**P0 scientific-claim blocker — true live-time availability unproven.** OpenDota's raw parsed replay gives *game-clock* timestamps but not application/observer packet receive times. One synthetic 60s delay experiment cannot prove which fields would actually be accessible by the button press minute. The user-facing report already states the limitation; keep it. Evidence: source audit on 291 raw TRAIN payloads, 2,910 player timelines, 10,685 player-team economy snapshots, 10 terminal slots excluded, zero internal consistency mismatches; it does NOT provide independent live arrival proof. Report this as an evidence blocker, not a discovered software bug.

**P1 narrow sampling and effective independence.** Original 500 games occurred 21-26 March 2026; original TRAIN subset spans 21-24 March. TRAIN includes both nominal patches 59 and 60; evaluation on later same patch is not a held-out patch transfer. Even well-constructed 4 series-disjoint forward folds are only historical stability over a few days. The 90,530-match 2026 Zenodo corrected dataset ends on 18 March 2026 and cannot be a later-than-original forward holdout.

**P1 gold feature semantics.** OpenDota gold_t is cumulative *earned* gold (m_iTotalEarnedGold) rather than current *net worth* (m_iNetWorth); this distinction appears in primary replay parser documentation. Original 291 TRAIN raw team radiant_gold_adv and radiant_xp_adv were exact differences of player gold_t/xp_t at all 10,685 sampled indices. Existing user-facing report calls this 'gold lead', not a net-worth lead, so do **not** portray it as an observed employer-report error. If extending mechanisms, express gold-flow features as *earned-economy trajectories*, never item inventory valuation.

**P1 availability vs retrospectively reconstructed features.** BKB/Blink completion and building kill event logs contain event-game-clock timestamps and can be projected to t or t-60; they were parsed after game. Ability upgrade entries (50,783) have zero independent event timestamps. Chat has 12,704 events in TRAIN, including 2,166 pregame and 417 after duration. Neither ability array nor chat is eligible for a fresh as-of feature without a proven availability contract.

**P1 strongest candidate is still unstable vs proper baseline.** In the precommitted five-family exploration on 137 series-disjoint OOF games, R/O/C individually beat M1 in 4/4 folds, ALL beat M1 by −0.007760 in minute-weighted log loss but ALL beat Q1 by only −0.001637 (2/4 folds, 99.5% bootstrap CI crossing zero). Because Q1 has already been tested, this is an exploratory after-search comparison, not a fresh unbiased estimate. The new event-delay hostile test freezes original ALL features, delays only objective/purchase logs by 60s, and refits one fixed ALL60 logistic on preceding mature TRAIN games. ALL60−ALL0 LL −0.000310 with CI overlapping zero; ALL60−Q1 LL −0.001947, 97.5% cluster CI [−0.012623,+0.008586], only 2/4 folds. Leave-one-series-out shifts ALL60−Q1 between −0.003752 and +0.000628. **No gate passes.** Synthetic latency robustness is not equivalent to live model improvement.

**P2 research complexity trap.** The 2025 ensemble Dota paper uses many postgame/inventory predictors and reports high phase-bucket classification accuracy. That number is NOT comparable with a 500-match strictly minute-t probability study that demands live observability and proper scoring; never borrow its reported accuracy as expected performance. External large replay datasets are good for scientific design but differ in patch, data provenance and source time.

## Research that would actually change the conclusion

1. Collect a new, never-scored *chronologically later* professional cohort after 26 March 2026 with game/series/league/patch IDs and per-packet received_at or documented observer transport; do not fold it back into the original 500-match recruiter deliverable.
2. Independently reconstruct event-time vs receive-time for economy and objectives. A documented replay parser shows that wall time and game time need correct handling of pregame and pauses. Require complete-as-of vs missing-source flags; do not substitute postmatch parsed final inventory.
3. Freeze exactly one simple challenger, Q1 and M0 baselines, model and calibration recipe, predictor availability cutoff, minimum effect, block labels by whole series, per-match vs per-minute estimands, and an unopened final evaluation period.
4. Primary: proper log loss with original match and series cluster sensitivity. Secondary overall + 30+ Brier, phase calibration, league/patch heterogeneity, missingness/latency. Count all attempted models in selection penalty. If no genuine independent data, **stop fitting additional candidates**; preserve the extensive negative feature record.

## Checked external sources and transport restrictions

- OpenDota parser original gold/net-worth semantics: https://github.com/DoubleGremlin181/odota-parser/blob/master/src/main/java/opendota/Parse.java
- Independent replay parser and game-clock/wall-clock + pause reconciliation: https://github.com/Resolut1onEDL/dota-replay-parser
- OpenDota source data API vs replay parsing distinction: https://blog.opendota.com/2014/08/01/faq/
- Zenodo corrected professional game snapshots v3 (90,530 matches, 1,007,768 snapshots, through 18 March 2026): https://zenodo.org/records/23166182
- Betty Dota 2 parsed professional 2025 per-second decision state, 9,385 games and ~9.65 GB: https://huggingface.co/datasets/wolframko/betty-dota2
- Dota 2 2025 decision-tree ensemble and phase feature importance, results not transportable as live true PIT: https://doi.org/10.3390/bdcc9120302
- Source-backed technical policy: Sang Quant Research Bible v1.10.1 (private) §§7.2–7.4, 8.5–8.6, 13.12–13.13, 13.16.

## Integrity

This file is a new research-only review. It does not change the employer notebook, original test predictions, report/PDF, ZIP, PR #9, main, applicant-owned time estimate, AI disclosure or reviewer sharing. The original submission deadline is **19 November 2026**, exact hour not independently verified. The research code and source audit cannot certify an applicant's work hours or a true real-time feed.
