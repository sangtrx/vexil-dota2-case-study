# Correct interaction null, patch split and series influence — hostile audit

This is an author-controlled, **post-result TRAIN-only** sensitivity,
conducted after seeing the originally favorable fitted conditional
gold effect. It is not a newly opened holdout, production evaluation
or human peer review.

## 1. Appropriate null for an interaction

The correct nested null is **gold + elapsed minute without gold-by-minute
interaction**, NOT only gold. On the four frozen chronological TRAIN OOF
blocks (137 unique games, 5,081 minute rows), comparing M1
(gold+time+interaction) to gold+time:

- M1−null mean log loss **−0.002020**, 70-series/bootstrap percentile
  95% interval **[−0.014801,+0.008984]** — includes zero.
- M1−null Brier **+0.000405** (worse point estimate), 95% interval
  **[−0.003059,+0.003857]** — includes zero.

Therefore no robust predictive improvement attributable specifically
to gold-by-time interaction has been established. This supersedes no
original validation or TEST result and does not refit/promote any model.

## 2. Patch-environment sensitivity

Fit M1 to two disjoint original TRAIN patch subsets separately:

| TRAIN patch | Games | Minute rows | Model-fit D, t10−t30 gold effect |
| --- | ---: | ---: | ---: |
| 59 | 250 | 9,181 | +0.300675 |
| 60 | 41 | 1,494 | +0.029227 |

The effect is **much smaller in patch 60**. Sample sizes, gold
distributions, surviving-game composition and overall game conditions
differ; these are two descriptive subgroup model fits. No confidence
interval was preregistered for the patch contrast, and 41 games cannot
support a confident drift diagnosis. Do not describe D as a stable
universal relationship across patches.

## 3. Original TRAIN group influence

The global TRAIN D is +0.278661. Sequentially omitting one of 171
series/singleton groups at a time yields positive fitted D between
**+0.186716 and +0.293556**. Omitting the five highest-leverage groups
*at once* gives **+0.185067**. This is a post-hoc perturbation of
nested training samples, NOT 171 independent replications or a
confidence interval, and not a patch-robustness fix.

**Decision:** maintain HOLD on elevating the positive TRAIN-only D
as a recruiter claim. Fitted coefficients can be influential and
environment-dependent while predictive skill is not supported.
The original M0 reference and shadow-mode M1 stay untouched.

Receipt keys identify the *gold-plus-minute* null explicitly as
M1_minus_gold_time_null; these are NOT M1-minus-gold-only baseline
values from the earlier forward audit.

See the [pre-execution protocol](GOLD_INTERACTION_HOSTILE_PROTOCOL.md),
[replay source](gold_interaction_null_influence.py), and
[immutable receipt](GOLD_INTERACTION_NULL_INFLUENCE_RECEIPT.json).
No original TEST or reused VAL labels were loaded.
