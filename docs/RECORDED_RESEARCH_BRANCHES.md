# Recorded research branches and delivery boundary

This index covers the 18 published research branches on GitHub as of 19 November 2026, not every idea or attempt ever considered. It distinguishes the **500-game March Vexil submission** from exploratory research. The one submitted notebook executes M0-M3 and a development-only item diagnostic. The reviewer ZIP also includes the P01-P28 numerical register; those 28 adaptive screens are historical, use previously inspected validation labels and predate a terminal-row correction.

| Branch under `research/` | Tested question | Recorded outcome and limitation |
| --- | --- | --- |
| `quant-bible-path-risk-train-only-20261117` | Q1 gold path | Better TRAIN-forward point loss, grouped CI vs M1 crosses zero |
| `vexil-rich-feature-lab-20261117` | 81 engineered inputs | Roshan ownership parser bug discovered later; old results historical |
| `vexil-all-feature-families-20261118` | Rich gold/XP/players/objectives | Some negative fixed-model results; no new TEST |
| `vexil-quant-path-signatures-20261118` | Gold/XP path shape | C4 lost to simpler Q1 |
| `vexil-minimal-economy-score-20261118` | Equal-match weighting and concentration | Mixed results by time period |
| `vexil-role-dynamics-and-robust-consensus-20261118` | Role allocation and rank | October worse than Q1; November small and inconclusive |
| `vexil-disagreement-reliability-20261118` | Multi-model disagreement | Weaker failure ranking than M1 uncertainty |
| `vexil-oct-nov-external-feature-falsification-20261118` | October/November transfer | Results differ by cohort; post-selection |
| `vexil-october-historical-holdout-20261117` | 180 October games (out-of-time historical) | M1−M0 LL −0.005883, 95% series CI [−0.013481,+0.001528] includes zero; minute-30+ worse. Seven leagues, no live receipt times; research-only, not a new 500-game TEST |
| `vexil-prospective-holdout-20261117` | 22 newly selected November games | M1 LL 0.442682 vs M0 0.456167, but only 9 series groups versus 30 required; ECE worse and match-bootstrap LL CI includes zero. Underpowered retrospective study, not a prospective live-feed validation |
| `vexil-event-delay-hostile-20261118` | ALL/ALL60 with artificial delay | ALL60 beats M1 in old TRAIN folds but not Q1 convincingly; pre-Roshan fix |
| `vexil-stale-feed-reliability-20261118` | Delayed feed and missing data | Actual receipt timestamps not available |
| `vexil-hostile-stale-feed-20261118` | Clock/HOLD stale-source stress | Initial NO_DATA handling bug found |
| `vexil-causal-forecast-filter-20261118` | Corrected NO_DATA and smoothing | Repair recorded; no live predictive validation |
| `vexil-fresh-nov17-cohort-20261118` | Small Nov 17 cohort | Insufficient games/groups |
| `vexil-xgb-lgbm-20261118` | Fixed 3/84-input boosters | Failed TRAIN-forward gate against Q1 |
| `vexil-xgb-lgbm-nested-train-20261118` | Nested booster complexity | Conservative settings, historic Roshan caveat |
| `vexil-september-external-20261118` | Out-of-time September transfer | **RESEARCH ONLY, NOT IN SUBMISSION.** 200 frozen IDs, 199 scored, 3 leagues; M1 LL 0.544803 vs M0 0.584431; series bootstrap [−0.074261,−0.010790]. Team/league dependence, influential games and absent received_at prevent generalization |

**September provenance and scope.** March-trained models were frozen in commit `90203d7` before outcomes, match IDs in `5b9c96e` and scoring code in `fb5aadc`; the results and post-hoc influence audit are on the separate research branch. The procedure and scores are retrospective, not prospective live results or permission to expand the 500-game assignment. The original selected M0/M1 notebook and TEST forecast CSV remained untouched.

The original private research PR #3-#16 heads are mapped in [HISTORY.md](../HISTORY.md) and [REVIEWER_HISTORY_MAP.md](REVIEWER_HISTORY_MAP.md). PR comments live in another private repository and require separate access. Some raw match caches and code needed to replay supplementary trials are not in the recruiter ZIP. A failed promotion gate means **insufficient evidence**, not proven uselessness. No global multiplicity/power guarantee covers every adaptive experiment. This repository is public, as permitted by the take-home brief. Original private PR discussions and unbundled raw caches are separate; public visibility does not make these extra studies independent validation.
