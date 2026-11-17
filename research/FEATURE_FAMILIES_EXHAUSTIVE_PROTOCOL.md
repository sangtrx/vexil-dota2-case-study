# Bounded four-family Dota feature falsification: registry fixed before scoring

**18 November 2026 ICT.** Private historical research only. The full original 500-game TEST has already been opened and numerous historical feature screens have been run, so nothing here is new independent validation or permissible employer model-promotion evidence. This registry, exact feature sets, and gates are committed BEFORE any scoring this trial. Prior research HEAD: 62ed7dc8c123b620c3a79998f803617d67a3aacf.

## Freeze scope

Original frozen rich features: 291 TRAIN matches, 10,675 minute rows, 70 professional series/singletons in the existing 137-match / 5,081-row chronological mature-label TRAIN-forward evaluation; 4 folds with frozen boundaries [154,176,220,252,291]. Source raw cache pinned to prior aggregate blob digest; do not download new matches. Cross-check original M0, additive, M1 and Q1 proper scores against existing prior receipts to abs 1e-10. NEVER score original VAL, TEST or use their outcomes/derived summaries in model fitting, decisions or selection.

Five and ONLY five logistic candidates, all original M1 three inputs + candidate fixed features, same original M1 pipeline (median imputation, StandardScaler, LogisticRegression(C=1, max_iter=1000, random_state=20261113)). No hyperparameter search; no changes after scoring:

- **R (online gold regime)**: 2 features. Signed two-sided CUSUM from gold changes in last 10 minutes. Standardize each past increment by 0.25 + median absolute preceding <=5 increments, clip z to [-5,5]; plus=max(0,plus+z-0.5), minus=max(0,minus-z-0.5), output (plus-minus)/(1+number of increments). Secondary signed change in mean increments recent 3 vs preceding 3, divided by 0.5+RMS <=6 increments, 0 if fewer than 4 increments. Historical indicators, not backdated regime alarm or hypothesis test of a break.
- **O (ordinal flow)**: 2 features from last 10 gold-increment intervals. Difference of frequency of strictly positive-positive adjacent increments and negative-negative adjacent increments (normalize by total adjacent pairs; fewer than 2 ->0). Second current-gold-sign times Shannon entropy of (++, +-, -+, --) adjacent pairs / log(4); ignore tied-zero increments (no pairs ->0).
- **C (objective conversion)**: 2 features from past building_kill events with numeric 0<=time<=t*60 and valid goodguys/badguys tower/rax keys only. Killed badguys -> Radiant side +1, killed goodguys -> Dire side -1. Each event has event-minute floor(time/60), bounded by current minute. For last <=5 min, sum side*(abs(gold_t)-abs(gold_at_event_minute))/(1+event count); for last <=10 min, same sum weighted exp(-age_seconds/300)/(1+event count). Both odd under team swap. Co-occurrence after objectives, NOT causal impacts or guaranteed live event delivery.
- **I (item completion milestones)**: 3 features from immutable per-player purchase_log with numeric 0<=time<=t*60 and named keys. First observed purchase of black_king_bar and blink per player, at most one per player/item and side (Radiant/Dire from player_slot). Signed cumulative team count difference of BKB, signed cumulative difference of Blink, and signed first BKB/Blink purchases within previous <=5 minutes. Pregame negative-time purchases excluded; final inventory, ability_upgrades_arr and terminal player level never used. Patch numbers 59/60 are diagnostics only, not model training or tuning. Power-spike proxy, NOT verified hero spell/level timing.
- **ALL**: union of exactly 9 new features from R/O/C/I + three M1 features (12 total). No extra selection or ablation after seeing outcomes.

Candidate features must be finite and negate under Radiant/Dire mirror; prefix/suffix poisoning and match resets tested. Features built from numeric histories and events <=current minute t; cache match ID and duration compared to source; exclude negative/future event timestamps. Tests must fail if future objective or purchase injected. Never read original VAL/TEST payloads.

## Quantitative decision

Primary: minute-weighted proper log loss candidate minus M1, candidate minus Q1. Negative means better. All five results visible, no best-of claim. Secondary: overall Brier, Brier after minute 30, four-fold LLs, time phases 0-9/10-19/20-29/30+, match-weighted LL, patch-59 vs patch-60 diagnostic, nonzero feature prevalence. Cluster by series/singletons (70 groups), 5000 paired cluster bootstrap draws, seed 20261118. Predeclare two-sided 99.5% percentile intervals for 5 candidates x 2 comparators (Bonferroni across this new family), plus descriptive 95%. This does NOT correct prior screens.

Fixed exploratory gate for each family: delta LL <=-0.0025 vs BOTH M1 and Q1; BOTH 99.5% CI upper<0; win >=3/4 folds against BOTH; overall and >=30 Brier no worse than BOTH; single cluster accounts for less than half of positive gain vs M1. Even passing only merits a new independent study and NEVER an employer model-promotion claim.

## Feasibility and blockers

All 291 TRAIN payloads have purchase_log. BKB and Blink timestamped entries are prevalent. Ability-upgrade arrays lack independently verified event times; therefore patch-aware hero skill-level spikes BLOCKED until new data available. Only the explicitly labeled item proxy can be tested. Missing real received_at blocks claims of true live PIT despite historical as-of filtering. If raw event parsing contradicts source, fail closed.

No patch-selected winners, no retuning, no fabricated independent TEST. Keep failures. Applicant notebook, original TEST CSV, PDF, ZIP, Draft PR #9, main, submission, AI disclosure and human-work hours unmodified.
