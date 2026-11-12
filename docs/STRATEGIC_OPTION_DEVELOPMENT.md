# When Gold Is Not Control: measured result and research disposition

**Independent original hypothesis; negative development result; no deployment claim.**
13 November 2026. Hypothesis and prior-art review committed at
43b0c1c; pure feature extractor and PIT tests at 0ecbd90; finite
development ablation spec at 5cc7233 (one early run stopped before
printing results because series-safe fold boundaries were too sparse,
repaired without examining outcomes at 67f7eaf). See
NOVELTY_RESEARCH_PROPOSAL.md and OPEN_SOURCE_PRIOR_ART.md.

## What we could contribute

The original take-home's M3 objective model used CUMULATIVE
tower, barracks, Roshan and kill counters. It gave a worse validation
log loss than M1. Such counters erase an important distinction:
a tower destroyed at 5 minutes remains gone, while the recent
pickup of a temporary revive item does not have an infinite lifetime.
Likewise a buyback is a time-stamped use of resources, rather than
a permanent positive combat resource.

We registered three interpretable, strict-PIT proxies:

| Feature | What it represents | Information and limitation |
|---|---|---|
| Aegis claim5 | Team-signed, linearly aged Aegis pickup events over 300 seconds | A recent acquisition; **not actual remaining possession** (may be consumed on death or later pickup) |
| Buyback commitment5 | Signed buyback events aged over an analytic 300-second window | Recent buybacks; 300 seconds is an analytic horizon, **not the game's ability cooldown** |
| Unconverted gold k | Gold-leading team when the opposing team has superior tower/barracks destruction | Economic/control mismatch; structure weighting is a declared heuristic, not a learned causal value |

The combined M4 adds only these three to the previously selected
M1 gold × time logistic model. Fit/scaler/imputer/C=1 were identical.
No neural-model training or hyperparameter search was introduced.
The hypothesis is our analytical formulation, **not an assertion
that time-limited event features or win-condition analysis are new
to the worldwide literature**.

## Exhaustive sample-specific point-in-time integrity

A reproducible cache-only script independently audited all 900
already-collected professional games from the three prior cohorts,
containing 9,000 player series and **32,106 minute-index records**.
For every observed minute, all 10 players' time arrays matched the
actual clock 60*t, all series lengths for gold/XP/last hits matched,
and the signed sum of the ten players' gold was exactly the
match-level gold-advantage value. **Zero anomalies, zero API calls.**
Original500: 18,308 indices, first forward200: 6,970,
second forward200: 6,828. One other published 2026 dataset
excluded 1,849 games with time-axis anomalies, showing why this
audit matters. This certificate is scoped to THESE 900 records;
it does not establish network receive time in a live feed.

The option features themselves also passed **2,754 direct
feature-prefix invariance checks** on 394 development games at
game-minute cutoffs. Additional unit tests cover missing event logs,
future/label poisoning, exact second cutoffs, and Radiant/Dire
side-exchange antisymmetry. The new research worktree has 33/33
offline tests passing.

## Registered exploratory validation ablation

**Crucial:** these 103 validation games were already previously
examined during model development. These results are EXPLORATORY,
not unbiased evidence from a virgin held-out test.

| Model | Predictors | Validation log loss ↓ | Brier ↓ | Difference from M1 |
|---|---:|---:|---:|---:|
| M1 gold/time | 3 | **0.519346** | **0.175767** | 0 |
| M1 + temporary event windows | 5 | 0.519907 | 0.175778 | +0.000561 |
| M1 + structural disagreement | 4 | 0.520337 | 0.176473 | +0.000991 |
| M4 all new features | 6 | 0.520596 | 0.176369 | **+0.001251** |
| Older M3 cumulative objectives | 10 | 0.527826 | 0.180500 | +0.008481 |

M4−M1 paired whole-match 95% interval:
[-0.004483,+0.006751] on 103 matches. Series-grouped interval:
**[-0.004386,+0.006336]** across 53 series clusters,
5,000 fixed-seed draws. Both span zero. The value is
POSITIVE on average (M4 worse).

Three chronological, series-safe training-only folds:
M4−M1 loss changes **+0.010073, −0.008026, −0.003626**
with evaluation groups of 22, 44 and 49 games respectively.
Two folds favor M4 and one disfavors it sharply.
The precommitted screening rule required at least −0.005
validation log-loss difference, an upper confidence bound below 0,
Brier no worse, and favorable direction in at least two folds.
**M4 FAILS. No fourth forward holdout is consumed.**

### Why the negative result is scientifically informative

Feature support varied substantially across phases in the 103-game
validation sample:

| Phase | Recent Aegis claim nonzero | Recent buyback nonzero | Economic/structural disagreement nonzero |
|---|---:|---:|---:|
| 0–9 | 0.00% | 0.49% | 0.58% |
| 10–19 | 5.63% | 1.26% | 12.91% |
| 20–29 | 31.91% | 6.78% | 11.05% |
| 30+ | 44.05% | 39.61% | 15.56% |

These are shares of minute rows for which a *computed proxy* is
nonzero, not item-possession or causal-effect rates. A static
coefficient trained on all minute rows may not transport equally
well between early- and late-game; however this is a hypothesis
for NEW research, not a post-result excuse to tune phase thresholds
on the consumed development data. Other possibilities include
the events already being reflected in gold, noisy option-proxy
semantics or simply insufficient independent samples.

## Outcome-blind matched observational case

The case-selection algorithm was committed **before looking at
the selected pair's outcomes** (27b0295). It fixed minute 25,
restricted to the original TRAIN cohort, identical patch and
gold-lead side, no series overlap and an ordered ladder of
gold/XP tolerances. Both games are patch 59, different series:

| At minute 25 | Match 8739246794 | Match 8739992397 |
|---|---:|---:|
| Radiant gold advantage | +1,901 | +1,929 |
| Radiant XP advantage | +6,964 | +6,862 |
| Recent Radiant Aegis claim | +0.93 proxy | 0 |
| Unconverted economic lead | 0 | +1.929k |
| Relevant event | Radiant picked up Aegis at 24:39 | No pickup within last 5 minutes |

The gold advantage differs by only **28**, XP by **102**,
yet the game states differ along the researched event channels.
**Both games ended with Radiant winning**, so these examples
CANNOT demonstrate a better prediction, a counterfactual effect,
or the impact of Aegis on winning. Their only valid purpose is to
illustrate a measurement/representation difference which a simpler
economy-only model ignores.

See the PNG matched_option_case.png and frozen timeline CSV in
research/results for reproducible, timestamped context.

## Forecast-path coherence: secondary, descriptive only

A second, non-fitting diagnostic uses the old M1 predictions
from the two previously consumed 200-game cohorts. The
**martingale identity E[p(t+h)−p(t)|F_t]=0** follows from
conditional probability theory and has formal published
sequential-calibration treatment (Wilkinson & Ferro 2026,
arXiv:2606.31621). It is NOT our theorem.

Our finite, stage-and-risk-binned descriptive check used t={10,20,30},
h=5, terminal absorption at the already-realized outcome for games
that end by t+5, and 5,000 series-cluster bootstrap draws.
Overall t=10 five-minute revision is +0.0179
(CI [-0.00145,+0.03753]) in the first forward cohort, and
+0.0143 ([-0.00259,+0.03125]) in the second.
The confidence intervals both contain zero; other
risk-bin patterns were not consistently replicated.
Subgroup intervals are exploratory and NOT multiplicity-adjusted.
This motivates investigation of path-level calibration, not
a statistically proven drift opportunity or financial alpha.

## Decision and the strongest defensible story

**HOLD** M4, retain the existing M1 as the take-home proposed model.
There is no credible new predictive improvement from the tested
option-value features. The contribution of this research work is
an explicitly falsifiable *representation hypothesis*, a
source-specific 32,106-index PIT audit, a real matched contrast
that does not use labels for selection, temporal ablation and
uncertainty-corrected negative evidence.

A later PhD-scale research direction would need an independent
prospective/chronological cohort, better observation of Aegis
consumption and item lifecycle, and explicit auditing of
model probability paths. The limited, retrospective two-endpoint
take-home cannot establish causal game mechanics, global
methodological novelty or betting profitability.

**Submission guidance:** preserve original PR #3's notebook
and ≤4-page REPORT as authoritative. At most present this study
as an honest, concise exploratory case/negative ablation,
with full data/code and citation in a separate research appendix;
do not substitute its unproven M4 model or claim a better score.

## Artifacts

- docs/NOVELTY_RESEARCH_PROPOSAL.md — registered research question,
  mathematical hypotheses, falsification and stage-specific plan.
- docs/OPEN_SOURCE_PRIOR_ART.md — external literature/open-source gap
  table with URLs and the explicit novelty boundary.
- research/strategic_option_value.py — pure time-bounded features.
- research/development_option_experiment.py — finite exploratory
  ablation plus series-aware loss and train-only walk-forward.
- research/matched_option_case.py — outcome-blind matched case.
- research/forecast_path_coherence.py — no-fitting martingale audit.
- research/pit_axis_audit.py — complete 900-game gold/time audit.
- research/results — exact derived CSVs, JSON receipts and PNG.
