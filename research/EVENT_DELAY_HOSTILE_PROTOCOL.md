# Hostile audit: as-of event delay and series influence, not a model search

**Frozen 18 Nov 2026 BEFORE computing outcomes for this particular stress.** This is retrospective research after repeated TRAIN screens and an inspected original TEST. Preserve existing Vexil reviewer package and model decision. This experiment can at most *discredit* the earlier positive ALL-vs-M1 exploratory association, never promote anything.

## External motivation & source semantics

- OpenDota raw parsed replay/player total-gold timeline is cumulative **earned gold**, NOT current net worth. Parser's m_iTotalEarnedGold (also reported for OpenDota's gold_t) is distinct from m_iNetWorth; no within-game feature is treated as current net worth. Original radiant_gold_adv exactly equals team differences in cumulative earned gold in inspected TRAIN. Sources: OpenDota parser Java Parse.java and October 2026 replay parser independent public docs. Applicant report calls gold advantage rather than net worth; this is a semantic note not an invented report error.
- Replay timestamps are *game-clock event times*, not actual application receipt times. Observer can receive delayed TV stream; real live observer pipeline requires ingress proof (Hodge et al., IEEE pro Dota study, DOI 10.1109/TG.2019.2948469). Offline purchase_log time=t does not prove available to live API by t.
- Original cohort 21–26 Mar 2026, TRAIN 21–24 Mar, across one patch transition, so folds do not certify long-term patch/league generalization. Zenodo 90,530 matches v3 ends 18 March 2026; not independent *forward* period for this March-21+ cohort.

## Exactly one clock-stress experiment + fixed original comparison

Frozen original data: research/RICH_FEATURE_TRAIN_ONLY.csv.gz, 291 TRAIN matches/10,675 rows. Original five-family receipt research/ALL_FAMILY_RESULTS.json HEAD 851a1c1, candidate ALL has 9 raw-only features + 3 base gold/time. No hyperparameter retune or family/phase selection.

- **Original ALL0**: prior exact as-of protocol (events with 0<=game-clock time<=t*60).
- **Conservative ALL60**: for **only building_kill and item purchase events**, use events timestamped <=t*60-60 at forecast minute t (at t=0 no events available); still compute current gold/time, CUSUM and ordinal. Event ages and last-five-minute windows measured against current minute, NOT delayed source cutoff. Synthetic one-minute event source delay, not inferred actual latency. Other 12 regression inputs, splits and logistic C=1 unchanged. Exactly one new prediction stream refitted on same mature TRAIN games: ALL60.
- Controls: previously scored ALL0, original M1 and strongest Q1. Fit only on mature, chronologically earlier TRAIN games. Parity of ALL0/M1/Q1 per-fold LL/Brier vs locked research receipts at abs 1e-10. Check gold/time/R/O family identical between ALL0 and ALL60. No VAL/TEST labels or new games.

## Frozen evaluation and failure criteria

Four forward folds [154,176,220,252,291]; expected 137/5,081 OOF and 70 series/singletons. Primary: minute-weighted LL(ALL60)-LL(ALL0) and LL(ALL60)-LL(Q1). Secondary overall and late30 Brier, LL(ALL60)-LL(M1), equal-**match** weighted LL, four fold effects, leave-one-series-out effect range (no retraining), biggest cluster gain share. Exactly 5,000 whole-series bootstrap draws seed 20261118; descriptive 95% and two-sided 97.5% CIs for **two** primary comparisons, without claiming adjustment for historical searches.

**Stability gate (descriptive only)**: adverse LL(ALL60)-LL(ALL0) <=+0.002; ALL60 vs Q1 LL <=-0.0025; upper 97.5% CI of ALL60 vs Q1 <0; wins >=3/4 folds vs Q1; and ALL60 Brier <=Q1 overall and minute>=30. If fails, reject claim ALL adds reliable live value under 60s source delay. Even passing means **no promotion** given TEST inspected and heavily reused 4-day TRAIN folds.

Tests: t=0 no event in ALL60, event time t*60 visible in ALL0 but NOT ALL60, t*60-60 visible in ALL60, future appended logs cannot affect past, Radiant/Dire mirroring, duplicate purchase semantics unchanged, original artifact SHA256 unchanged. Deterministic byte-identical rerun required. Model quality != source availability.
