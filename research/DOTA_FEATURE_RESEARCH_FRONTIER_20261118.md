# Dota 2 feature-engineering research frontier (18 Nov 2026)

**Purpose:** Source-backed possible Dota state representations after negative 81-feature wide-model Q2/Q3, Q1 PathRisk exploration, and the single seven-input C4 path-geometry trial. This is research synthesis, **not** applicant-authored submission material, not evidence that an untested model improves win probabilities, and not permission to search original TEST/VAL.

## Source-backed mechanisms, not leaderboard claims

1. **Time-dependent objectives and economy:** Hodge et al., *Win Prediction in Multi-Player Esports: Live Professional Match Prediction* (IEEE Transactions on Games, DOI 10.1109/TG.2019.2948469) study live professional prediction. *DotA 2 Match Outcome Prediction System Using Decision Tree Ensemble Algorithms* (2025, DOI 10.3390/bdcc9120302) discusses changing relevance of economy, towers and teamfights with game phase. We already have time, towers, kills, 81 broad features; no license for unvalidated nonlinear nets or causal interpretation from feature importance.
2. **Low-order sequential lead/lag geometry:** Choi (2026), *Efficient Computation of Lead–Lag Signature Features for Financial Time-Series Forecasting*, DOI 10.1002/for.70176, describes tractable depth-2 signatures. Cross-asset gains were heterogeneous. Our Dota transfer uses fixed 10-minute gold/XP oriented area + one-step flow asymmetry, lead occupation and integrated drawdown in one C4 predictor; **it failed** the TRAIN-only gate against M1/Q1. This negative transfer is evidence, not permission to tune the window until it wins.
3. **Online rather than retrospective regimes:** A survey of time-series change-point detection (2017, https://pmc.ncbi.nlm.nih.gov/articles/PMC5464762/) distinguishes online from retrospective. Sang Quant Research Bible v1.10.1 §13.16 forbids backdated alarms. A future candidate is prior-only, standardized mismatch between current gold flow and trailing volatility; benchmark against existing gold, gold_d and gold_acc before claiming information gain.
4. **Ordinal temporal ordering:** Permutation/ordinal patterns encode fluctuation order without fitting large models (https://www.nature.com/articles/s42005-021-00696-z). A future hypothesis is directional up-down-up frequency against a first-difference null. It likely overlaps existing gold_flips, gold_eff and volatility; 10 minutes contain very few patterns.
5. **Typed hero power spikes, not unrestricted one-hot draft:** Patch-aware, as-of hero level/item completion windows and interaction with objectives could be mechanically interesting. Earlier P20 items screens were unstable across forward folds; 291 matches cannot support 160+ free hero effects. Require patch-correct item data, event timestamps and minimal frozen priors; never use final inventory or future matchup win rates.
6. **Communication as separate source:** 2025 AIIDE chat-log paper (DOI 10.1609/aiide.v21i1.36822) studies chat-based prediction on 50,000 ranked games. This does not establish pro-match transportability or as-of availability. Do not use unaligned chat timestamps or transfer the paper's accuracy to 291 professional games.

## Priority obstacle: indexed arrays are not a receipt clock

A separate professional dataset released October 2026 (Zenodo v3 DOI 10.5281/zenodo.23166182) removed 1,849 matches after a positional-index versus actual time error. That **specific failure has not been established in our 291-game cohort**.

Our source-hash-verified raw 291-TRAIN / 2,910-player structural audit (research/QUANT_PATH_RAW_TIME_AUDIT.md) finds **0 arrays shorter than floor(duration/60)+1** and 84 extra terminal slots across only two matches (42 per match). This establishes only length compatibility, not exact clock alignment or live data receipt. Without trustworthy per-sample arrival timestamps, actual live observability remains **INDETERMINATE**.

## Priorities and stop conditions

| Mechanism | Distinct from 81 old? | Source feasibility | Current decision |
| --- | --- | --- | --- |
| Gold/XP signature + durability bundle | Partly | Existing TRAIN histories | **EXECUTED, FAILED gate**; do not tune |
| Live-aware clock vs stale inputs | Operational, not feature alpha | No actual received-at | Prior synthetic stress only; no live claim |
| Online change-point feature | Partly | Historical trajectory, live clock uncertain | Hypothesis only; stop reused-fold optimization |
| Patch-aware item/hero power spikes | Potentially | Needs patch-aligned as-of events | **BLOCKED** until provenance + independent data |
| Objective conversion response time | Overlaps tower and P19 | Timed building events and gold history | First validate as-of; no repeated validation screen |
| Ordinal pattern entropy | Weak distinctiveness at 10 minutes | Historical gold yes | Low priority, untested |

**Decision:** Future work needs independent, chronologically later professional matches with truly timestamp-aligned ingestion, then one frozen candidate. Employer's one-notebook/four-page assignment due **19 Nov 2026**, exact hour unverified. Draft PR #9 stays unchanged; no new branch is a justified model promotion. Applicant-owned hours, contributions, AI disclosure and reviewer access remain submission gates.
