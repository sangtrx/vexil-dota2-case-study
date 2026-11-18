# Hostile Senior Data Scientist Review — Vexil Dota 2 follow-on research
**18 Nov 2026 ICT | Research branch only | Original applicant take-home not edited**

## Verdict by claim

- **Verified within historical replay:** On 17 previously unscored professional games from 17 Nov (711 minute forecasts, 10 distinct series/singletons, 4 leagues), the existing March-TRAIN-only MATCH_EQUAL logistic model had lower minute/equal-game log loss than M1 and Q1 (research/FRESH_NOV17_EXTERNAL_RECEIPT.json). It was selected after extensive older searches. No new hyperparameters or model tuning based on these games was done prior to scoring.
- **Scientific generalization claim — HOLD:** A source-respecting 17-game cohort cannot clear the original preregistered minimum of 30 games and 15 independent series; Q1 contrast 98.75% bootstrap interval [−0.036681,+0.002497] includes zero and MATCH_EQUAL has *worse* late30 Brier than Q1 (+0.000829). Small-sample bootstrap percentile intervals need not have nominal frequentist coverage, and the selected candidate's older multiple-trial history remains uncorrected.
- **Actual live deployment claim — NO-GO:** No independently captured live packet timestamps (received_at, watermark), missingness/retention mechanism, actual source feed semantics or online reconciliation exist. OpenDota replay source and its games' internal times are not a live capture. The true packet delay rate and operational value are unknown. No production proof.
- **Applicant take-home release — unchanged:** The original 500-game March study already reports its corrected original TEST as not blind after prior inspection, five immature train labels under end-time proxy, no proven gold×time increment beyond additive model, and holds to M0 reference + M1 shadow. The separate creative research is not a valid reason to alter applicant claims on the eve of due 19 Nov 2026.

## Issue ledger

### P0 — incorrect NO_DATA state in the **old research latency simulation**, not in applicant notebook
**Affected:** research/stale_feed_reliability.py:lagged_views (the old logic computes old=max(0,minute-lag), then uses history[old] and fresh[old] even for t<lag).

**Reproduced:** At lag3, [t0,t1,t2] get gold[0] and first p[0] instead of no data, despite a stipulated three-minute receive delay. Deterministic regression now reproduces the old wrong behavior, and the new explicitly supported statechart is:

- scheduled minute t, snapshot lag d: if t<d => NO_DATA -> p=0.5, no model call;
- t>=d => STALE_READY: CLOCK re-evaluates only gold/path through s=t−d using current *known* clock t; HOLD retains the p computed at the old source time s;
- match end => do not emit a new score; source/state never persists across matches.

**Repair evidence:** research/causal_stale_feed_hostile.py, tests/test_causal_stale_feed_hostile.py and research/CAUSAL_STALE_FEED_HOSTILE_RECEIPT.json. On Nov17, NO_DATA rows: lag1=17, lag3=51, all exactly p=.5. Side inversion, no future suffix and zero-lag feature/source parity regression tested. Original research artifact kept immutable.

**Hostile check of materiality, to avoid overclaiming:** The separate mature-label chronological TRAIN-forward correction, 137 games / 5,081 minutes / 70 independent series, quantifies the numerical impact rather than treating a bug as proof of a changed model winner. Corrected CLOCK3 log loss **0.648852 vs 0.648923 old** (−0.000071); corrected HOLD3 **0.653924 vs 0.654000** (−0.000075). HOLD−CLOCK remains +0.005072 (worse) with 97.5% series CI [+0.000065,+0.010414]. The old **directional policy conclusion on TRAIN did not flip**. The old receipt was not rewritten. This is a P0 availability-contract defect with **small observed aggregate numerical impact** under this old population, not evidence of catastrophic quality failure everywhere.

### P0 — live as-of arrival/field semantics unproven
**Affected claims:** Real-live probability at exact t using historical per-minute OpenDota replay arrays.

**Evidence:** train_time_effect_ci.py enforces 60*t<duration and the internal data audit cross_array_time_alignment.py verifies per-player time vectors match top-level team gold/XP advantages. Both arrays are produced by the same parser, so this is not an independent witness of packet arrival. The Oct 2026 Zenodo v3 audit (https://zenodo.org/records/23166182) removed 1,849 matches with shifted/irregular time-axis arrays; this project's sampled 17 source games pass internal array checks but still have no independent received_at. The source's gold_t measures cumulative earned gold, not directly the real-time net worth resource.

**Minimum actual-world repair:** Instrument a live collector with both server event clock, local received_at, parse/ingestion lag, source identity, payload hashes, missingness, source watermarks and forecast emission logs. Join strictly at actual arrival, not parser reconstruction, and compare the same live input units/training semantics. Do not call these retrospective experiments deployment validated.

### P1 — model/metric selection still post-result
**Affected:** Treating MATCH_EQUAL's result as a newly confirmed superior general model.

**Evidence:** Predecessor 81 static/player features, path risk, objective family, ensemble, negative October/November screens and reweighted M1 experiments were run before selecting MATCH_EQUAL. The protocol for Nov17 was committed before *those 17* matches were selected/scored, but the candidate itself was post-selected. October 180 games Q1 minute LL **0.489278** vs MATCH_EQUAL **0.491557** (the candidate is worse on the original minute estimand), though MATCH_EQUAL equal-game LL **0.466953** vs Q1 **0.468959**. November15–16 only 22 games/9 clusters, and Nov17 only 17/10 clusters. No original TEST re-use for new fits, but an untouched original-march TEST cannot be claimed now.

**Repair:** Select target estimand and freeze a single model/comparator before a genuinely future, independently sourced, sufficiently sized cohort. Treat the stored strong Q1 as a real comparator and retain negative results. Never promote based on a favorable retrospective slice.

### P1 — weighting changes target distribution and implicit regularization, not only class balance
**Affected:** The causal story for MATCH_EQUAL.

**Measured in March TRAIN only:** 291 games / 10,675 minute rows. Radiant win prevalence by random minute **0.503513**; by random game **0.512027**. Mean observed minute count of Radiant-loss matches **37.324** vs Radiant-win **36.074**. Match-weighted logistic weights range **0.426556–3.056987** normalized to total 10,675, Kish row-weight ESS approx **9,938.2** (and the actual dependence unit is closer to games/series, not 9,938 IID minutes). Original M1 logistic coefficients [3.521937,−0.017156,−2.111705], intercept 0.004595; weighted [3.880770,−0.025796,−2.352719], intercept 0.016950, using unchanged original global train scaler. Equal match influence is plausible but does not isolate the effect from changes in the effective L2 trade-off, calibration, opponent mix, duration-conditional feature distribution or patch changes.

**Repair:** Distinguish estimand (random game vs random decision-minute), train class/duration weighting, C-penalty sensitivity and calibration drift on future fixed data. Do not choose one metric *because* it has a better point estimate.

### P1 — predictable degradation under delayed gold; cannot pick one state policy
**Fixed post-result lag stress on previously observed Nov17:** 4 March-trained models × FRESH/CLOCK1/HOLD1/CLOCK3/HOLD3; 1/3-minute synthetic delay only. FRESH MATCH_EQUAL LL **0.415423**, CLOCK1 **0.433393**, HOLD1 **0.430456**, CLOCK3 **0.467240**, HOLD3 **0.458900**. M1 FRESH **0.423054**, CLOCK1 **0.440946**, HOLD1 **0.437919**, CLOCK3 **0.474476**, HOLD3 **0.465932**. On this small future-date retrospective cohort HOLD beats CLOCK for M1/MATCH_EQUAL, but the corrected **TRAIN-forward 137-game** cohorts favor CLOCK over HOLD. That sign disagreement strongly cautions against choosing a single learned or hardcoded phase-gate from reused cohorts; perhaps source/phase/patch-dependent behavior, not proven. Q1 HOLD vs CLOCK also differs.

**Deliberately impossible negative control:** Using gold from future minute t+1 at forecast time t for MATCH_EQUAL changed log loss by **−0.018495** on 694 nonterminal snapshots vs same-row valid model. This does not imply live information advantage: it is a leakage-sensitivity test showing how artificially favorable a one-minute time shift might appear. Never ship/tune using future signals.

### P2 — completeness and communicability
The 17 newly selected matches were all 17/17 accepted with source-only checks, 4 leagues and 10 series; no winner-based exclusion. However one day's matches can be thin and nonrepresentative; sample sizes/CI are not strong future robustness. Show both objective measures and no-data rates; separate status Engineering QA from Scientific GO. Keep honest AI assistance and original applicant ownership/disclosure, no fabricated external review or unverified live API claims.

## Reproducible quality evidence

At research snapshot under BigLinux epic:
- tests: /srv/ai/tmp/vexil-review-runtime-20261116/bin/python3 -m unittest discover -s tests -q => **277 tests PASS**.
- regression specifically catches the old t<lag lookahead and new no-data neutral behavior; independent replay of both new reports with no overwrite yields identical JSON/Markdown bytes.
- frozen 17-game source collection and trained coefficient hashes from earlier sealed chronological commits are preserved.
- new Nov17 stress JSON SHA256 **d4c5f6fbc732c7a039013a3905381f86909d798f725f274dc24173163bedd381**; Markdown **9220f1385936dc6cf326e616c3b4fbdceb1ca065f0b981eacf836332b3c17e56**.
- corrective 137-game old study JSON SHA256 **a1f69563137d45ccb26b47283259c8667c45a44e8fb9e3556d2d84ba57eb0f9d**; Markdown **a456a14fd82b44a2c89f83799d08738ce4889197662bb48b54cf77020fe4b01d**.
- original applicant notebook SHA256 **e4318f15a0b34e5900cff1fcaa741d953046b74add4e5f95472d025facf7d61f**; original 3,836-forecast held-out CSV **03b4f6d67e7cb5b7af8097be145fc8cfdd510beefbe85e052bb0445ba7a0c441**; reviewer ZIP **8c97c9041a249ce5f7f540d461de30d41e4fe8423964f92b95c1717529ec02a3** — byte-identical.

## Decision and smallest meaningful next experiment

**Engineering: PASS** for the observed research runs and regression tests. **Scientific model promotion: NO-GO. Live deployment: NO-GO. Employer submission state: unchanged; not sent.**

Next creative evidence should be a real-live stamped-feed observational audit, not another replay-trained model:
1. Record per-snapshot source event minute, receive/ingress time, content completeness, parse version, and gold_t/net-worth semantics; write a hard NO_DATA/STALE_READY/FRESH transition oracle that rejects retroactive feature revisions.
2. Specify whether the business wants per-game or per-minute probability quality, and a unit of independent sampling. Freeze the target/comparators/acceptable missingness.
3. Collect enough future **never-scored** professional series, with group-bootstrap or uncertainty appropriate to temporal/series dependence. Only then compare MATCH_EQUAL, Q1 and M1; no adaptive model switch before this gate.
4. Keep applicant repo report faithful to the original assignment with 19 Nov deadline. This research is **not** included in the recruiter package.
