# September 2026: locked external transfer audit (outside the required 500)

This supplementary study was conducted on 18 November 2026 and was **not**
used to train, tune or replace M0/M1 in the 500-match applicant notebook.
The full source history and original locked scripts remain on branch
[research/vexil-september-external-20261118](https://github.com/sangtrx/vexil-dota2-case-study/tree/research/vexil-september-external-20261118).

The sequence in Git is:
- [90203d7](https://github.com/sangtrx/vexil-dota2-case-study/commit/90203d7596ef4279bf4f7c16c1f20e50045d02e7): freeze study rules and the original March-trained model coefficients
- [5b9c96e](https://github.com/sangtrx/vexil-dota2-case-study/commit/5b9c96e3042943af56ca8eb2b2fb6e9cabf947b1): freeze 200 September match IDs from outcome-blind metadata
- [fb5aadc](https://github.com/sangtrx/vexil-dota2-case-study/commit/fb5aadc09a5c6659155e82e358189b8b3dacd8d3): seal scoring code, before fetching outcomes
- [7ac654d](https://github.com/sangtrx/vexil-dota2-case-study/commit/7ac654d044f0af4825ff09b7d347b432cb3378aa): save predictions and results
- [611dd36](https://github.com/sangtrx/vexil-dota2-case-study/commit/611dd36732844917735a6cd3ccfb2d07f482c79d): post-hoc additive/null, game-influence and team-dependence checks

The 200 preselected IDs were all attempted. One invalid minute-clock parse was
excluded without replacement, leaving **199 games, 8,740 minute forecasts,
104 series/singleton groups and three professional leagues**. The same
March-trained coefficients produce:

| Proper score | M0 gold-only | M1 gold + time interaction |
| --- | ---: | ---: |
| Minute-weighted log loss | 0.584431 | **0.544803** |
| Brier | 0.192739 | **0.186450** |
| Minute-30+ Brier | 0.177526 | **0.162432** |

The predeclared M1-minus-M0 log-loss comparison is **-0.039628**, with a
5,000-draw series-resampled 95% interval **[-0.074261, -0.010790]**.
It passes the study's *limited external-support gate*. It does not establish
population-general superiority or production readiness.

The three leagues have overlapping teams: the team-match graph has
three connected components, with the largest containing 20 teams.
A single match supplies 24.6% of the observed log-loss improvement;
dropping the five most favourable matches makes a post-hoc series interval
include zero. The October/November studies have different selection and
outcome-inspection histories. The September result should not be pooled with
them as independent replications.

The later strong-null comparison was **post-hoc**: additive gold + time log
loss 0.586152 versus M1 0.544803, difference -0.041349, grouped interval
[-0.076263,-0.012239]. It supports this September sample descriptively, not
a second preregistered success. Real feed receipt timestamps are absent.

## Offline verification

From the repository root with the pinned Python dependencies:

```bash
python research/september_external/verify_external_results.py
```

This script independently recomputes log loss, Brier, 104-group bootstrap,
precommitted gate, cohort coverage and file hashes from the **unchanged archived
forecast CSV**. The raw September match JSON is not committed, so fully
redownloading and rebuilding feature rows is a separate network-dependent task.
The original `score_locked.py` and model-freezing source are on the linked
Git branch and are not disguised as a runnable fresh blind test here.

The employer notebook, its 500 frozen match IDs and the 3,836 original TEST
predictions remain byte-identical to their previous version. Until the
recruiter explicitly confirms scope, the September evidence is maintained
as separately labelled research rather than a replacement for the required
500-game evaluation.
