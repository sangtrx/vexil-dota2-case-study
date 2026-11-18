# Fixed novel Dota role-dynamics / intra-team gold-XP coupling falsification

18 Nov 2026 ICT, precommitted **before** running any new role-dynamics candidate predictions on October/November. This remains **post-selection, retrospective, not blind**: several earlier feature searches, including 81 rich features, and October/November M0/M1/Q1/ALL outcomes have already been seen. Never call any gains statistically independent validation or put them into employer submission. Research objective: discover negative/fragile mechanisms, not maximize leaderboard metric.

## Feasibility and substantive distinction

The existing 81-feature rich study ALREADY included gold Gini, top-one share, top-two share, XP Gini, gold growth of top two and last-hit trends; DO NOT repeat static Gini/share as novel. Instead test *order turnover* among the five distinct players, *distribution of recent five-minute income* and *gold-vs-XP coupling* as new mechanisms. Professional game outcome work shows individual hero/role and time-phase economies matter, but old snapshots may be post-replay reconstructions and no real source received_at is known. Source: Dota 2025 decision-tree ensemble paper DOI 10.3390/bdcc9120302; Hodge et al. 2019 DOI 10.1109/TG.2019.2948469. Per-player gold_t is cumulative EARNED gold, not spendable net worth.

## Exactly three fitted candidates (one frozen training recipe) + one unfitted conservative ensemble

**Common:** fit using **ONLY original 291 March TRAIN matches**, 10,675 preterminal minute snapshots, no March VAL or TEST and no prior October/November outcomes. Every candidate uses original M1 three base features, fixed median-imputed StandardScaled L2 logistic regression C=1 and random_state=20261113. Never retune regularization, choose a subgroup, add an arbitrary quadratic term, select a candidate from scores, or update candidate feature definitions after first score. March fitted baselines M0, M1, Q1 must reproduce saved October/November p_M0/p_M1 to <=1e-7; previous original Q1 and ALL scores are prior-known descriptive comparators.

**RANK3** (M1 + 3 new player features):
1. `role_rank_turnover5`: Radiant minus Dire fraction of pairwise gold-t earning-rank reversals among 10 unordered pairs between minute t and t-5; ties ignored; t<5 ->0.
2. `flow_hhi5_gap`: difference of team Herfindahl concentration in **nonnegative per-player earned-gold gains over last 5 minutes** (normalization by own team total income, empty ->0).
3. `flow_funnel_shift5_gap`: difference between each team's (largest share of positive earned-gold gains in last 5min) minus (largest share of cumulative earned gold at t). HHI and max share are applied to *flow*, not the previously tested current stock.

**COUPLING3** (M1 + 3 new features):
4. `star_xp_share_gap`: XP share of each team's top cumulative gold earning player vs other side, averaged across tied top earners (nonnegative finite XP).
5. `gold_xp_rank_alignment_gap`: difference between teams in pairwise signs of (gold_i-gold_j)*(XP_i-XP_j) over ten pairs; ties contribute zero. This is per-team contemporaneous rank concordance, not XP Gini.
6. `leader_flow_funnel`: signed indicator of team with higher cumulative earned-gold total times that leading team's `flow HHI5 - 1/5`; neutral gold advantage ->0. This is side-odd, not a terminal outcome. t=0 ->0.

**RANK_COUPLING6**: original M1 features + the exact union of those 6, one fitted model only; no ensemble of learned candidates.

**CONSENSUS**: **unfitted** arithmetic probability pool `0.5*p_M1 + 0.5*p_Q1` with strictly frozen coefficient 0.5, applied only after both original March-trained forecasts. No outcome-based or phase-based gate.

All six new features must be finite, bounded and precisely side-odd under team swap, invariant to within-team player permutations, and unchanged by future appended player-statistic suffix. Construct from 10 per-player [0,60,120,..] arrays only through t, with source hash and clock length checks already enforced by prior source auditor. No final player gold, last-hits final, winner, patch, player ID, opponent, hero, result or death timestamp is allowed in predictors.

## Data frozen

Same already-collected cohorts from immutable existing source manifests:
- October 20-31 2026: 180 games / 7,346 minute rows / 107 series+singletons, source /srv/ai/tmp/vexil-october-raw-20261117.
- November 15-16 2026: 22 games / 952 minute rows / 9 series+singletons, source /srv/ai/tmp/vexil-prospective-nov17-data-20261117.
- Original March complete 500 matches ID-disjoint from the cohorts. Pinned raw gz cache and original model source; no external queries and no new download. These later cohort outcomes have previously been read; no new holdout claim.

For **each cohort independently**, print LL/Brier for M0/M1/Q1/ALL(previous known), RANK3, COUPLING3, RANK_COUPLING6, CONSENSUS; delta LL/Brier versus Q1 and M1; minute30+ Brier; equal-match-weight LL; 5,000 series-group bootstrap 95% CI (seed 20261118); leave-one-series-out effect; and n series. All four new recipes are compared to Q1 and M1 => eight comparisons; provide 99.375% individual intervals as a crude within-screen Bonferroni correction and note the very extensive *older* search is not corrected. A research lead is only a future hypothesis if the same candidate beats **both Q1 and M1** by >=0.005 LL in **each** later period, negative 99.375% CI upper vs both for both periods, and Brier overall/30+ no worse than both. Passing that impossible-to-certify gate still DOES NOT promote or ship; requires never-inspected prospective matches and true live-as-of data receipt proof. Fail/NO GO otherwise.

## Immutability

User-facing applicant Vexil notebook, original TEST predictions, report, PDF, delivery ZIP and draft PR #9 stay unmodified, no recruiter contact or sharing changed, no GitHub Actions. All tests run BigLinux epic on independent research branch; source read-only.
